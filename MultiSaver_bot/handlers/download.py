"""Handle media downloads for MultiSaver_bot."""

import asyncio
import logging
import re
from pathlib import Path

from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    Message,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import get_settings
from database.models import User
from keyboards.media_actions import media_actions_kb
from services.downloader import download_media
from services.file_manager import get_file_manager
from services.job_store import get_job_store
from services.url_validator import detect_platform, is_supported_url
from utils.errors import MultiSaverError, RateLimitError
from utils.i18n import get_text

logger = logging.getLogger(__name__)

router = Router(name="download")

_HOURGLASS = ["⏳", "⌛"]
_URL_RE = re.compile(r"https?://[^\s]+", re.IGNORECASE)

_pending_urls: dict[int, str] = {}
_user_locks: dict[int, asyncio.Lock] = {}


def _get_lock(user_id: int) -> asyncio.Lock:
    if user_id not in _user_locks:
        _user_locks[user_id] = asyncio.Lock()
    return _user_locks[user_id]


def _choice_kb(lang: str):
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=get_text("download.choose_video", lang),
            callback_data="dl:video",
        ),
        InlineKeyboardButton(
            text=get_text("download.choose_audio", lang),
            callback_data="dl:audio",
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text=get_text("common.cancel", lang),
            callback_data="dl:cancel",
        )
    )

    return builder.as_markup()


async def _safe_delete(message: Message) -> None:
    try:
        await message.delete()
    except Exception:
        pass


async def _safe_edit(message: Message, text: str) -> None:
    try:
        await message.edit_text(text)
    except Exception:
        try:
            await message.answer(text)
        except Exception:
            logger.exception("Could not send status message")


async def _record_history(
    user_id: int,
    platform: str,
    status: str,
    media_type: str = "unknown",
    error_category: str | None = None,
    file_size: int = 0,
) -> None:
    """Save download history if the project's repository is available."""
    try:
        from database.repositories import HistoryRepository
        from database.session import async_session_factory

        async with async_session_factory() as session:
            repository = HistoryRepository(session)

            await repository.add(
                user_id=user_id,
                platform=platform,
                status=status,
                media_type=media_type,
                error_category=error_category,
                file_size=file_size,
            )

            await session.commit()

    except Exception:
        logger.exception("Could not save download history")


async def _stop_animation(
    task: asyncio.Task,
    stop_event: asyncio.Event,
) -> None:
    stop_event.set()

    if task.done():
        return

    try:
        await asyncio.wait_for(task, timeout=1.0)
    except asyncio.TimeoutError:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    except asyncio.CancelledError:
        pass
    except Exception:
        logger.exception("Animation task error")


async def _animate_status(
    status_msg: Message,
    lang: str,
    stop_event: asyncio.Event,
) -> None:
    index = 0

    while not stop_event.is_set():
        index = (index + 1) % len(_HOURGLASS)

        try:
            await status_msg.edit_text(
                f"{_HOURGLASS[index]} "
                f"{get_text('download.processing', lang)}"
            )
        except Exception:
            pass

        try:
            await asyncio.wait_for(
                stop_event.wait(),
                timeout=0.8,
            )
        except asyncio.TimeoutError:
            continue


@router.callback_query(F.data == "menu:download")
async def cb_download_prompt(
    callback: CallbackQuery,
    lang: str,
) -> None:
    await callback.answer()

    if callback.message:
        await callback.message.answer(
            get_text("download.prompt", lang)
        )


@router.message(F.text.regexp(r"https?://"))
async def handle_url(
    message: Message,
    db_user: User,
    lang: str,
) -> None:
    """Handle supported media links."""
    if not message.text:
        return

    text = message.text.strip()

    if text.startswith("/"):
        return

    match = _URL_RE.search(text)

    if not match:
        return

    url = match.group(0).rstrip(".,)>]")

    if not is_supported_url(url):
        await message.answer(
            get_text("download.invalid_url", lang)
        )
        return

    platform = detect_platform(url) or "unknown"

    # Pinterest: download immediately, without video/audio selection.
    if platform == "pinterest":
        lock = _get_lock(message.from_user.id)

        if lock.locked():
            await message.answer(
                get_text("download.wait", lang)
            )
            return

        async with lock:
            await _download_pinterest(
                message=message,
                db_user=db_user,
                lang=lang,
                url=url,
            )

        return

    # Other platforms require the user to choose video or audio.
    _pending_urls[db_user.telegram_id] = url

    await message.answer(
        get_text(
            "download.choose_type",
            lang,
            platform=platform,
        ),
        reply_markup=_choice_kb(lang),
    )


async def _download_pinterest(
    message: Message,
    db_user: User,
    lang: str,
    url: str,
) -> None:
    """Download Pinterest media immediately."""
    status_msg = await message.answer(
        f"⏳ {get_text('download.processing', lang)}"
    )

    stop_event = asyncio.Event()
    animation_task = asyncio.create_task(
        _animate_status(status_msg, lang, stop_event)
    )

    fm = get_file_manager()
    job_store = get_job_store()
    result = None
    job_id = None
    keep_files = False

    try:
        result = await download_media(url)

        await _stop_animation(animation_task, stop_event)

        if (
            getattr(result, "media_type", None) == "link"
            and getattr(result, "direct_url", None)
        ):
            await _safe_edit(
                status_msg,
                get_text(
                    "download.link_ready",
                    lang,
                    url=result.direct_url,
                ),
            )

            await _record_history(
                db_user.telegram_id,
                "pinterest",
                "success",
                media_type="link",
            )
            return

        files = [
            Path(file_path)
            for file_path in (result.files or [])
        ]

        files = [
            file_path
            for file_path in files
            if file_path.is_file() and file_path.stat().st_size > 0
        ]

        if not files:
            await _safe_edit(
                status_msg,
                get_text("download.failed", lang),
            )
            return

        job_id = job_store.create(
            user_id=db_user.telegram_id,
            files=files,
            media_type=result.media_type,
            platform=result.platform or "pinterest",
            original_url=result.original_url or url,
            can_extract_audio=getattr(
                result,
                "can_extract_audio",
                False,
            ),
        )

        keyboard = media_actions_kb(
            job_id=job_id,
            lang=lang,
            media_type=result.media_type,
            can_extract_audio=getattr(
                result,
                "can_extract_audio",
                False,
            ),
        )

        await _safe_delete(status_msg)

        sent_any = False

        for index, file_path in enumerate(files):
            ext = file_path.suffix.lower()

            caption = (
                get_text("download.success", lang)
                if index == 0
                else None
            )

            markup = (
                keyboard
                if index == len(files) - 1
                else None
            )

            try:
                if ext in {
                    ".jpg",
                    ".jpeg",
                    ".png",
                    ".webp",
                    ".gif",
                }:
                    await message.answer_photo(
                        FSInputFile(file_path),
                        caption=caption,
                        reply_markup=markup,
                    )
                elif ext in {
                    ".mp4",
                    ".webm",
                    ".mov",
                    ".mkv",
                }:
                    await message.answer_video(
                        FSInputFile(file_path),
                        caption=caption,
                        reply_markup=markup,
                        supports_streaming=True,
                    )
                else:
                    await message.answer_document(
                        FSInputFile(file_path),
                        caption=caption,
                        reply_markup=markup,
                    )

                sent_any = True

            except Exception:
                logger.exception(
                    "Failed to send Pinterest file: %s",
                    file_path,
                )

        if sent_any:
            keep_files = True

            await _record_history(
                db_user.telegram_id,
                "pinterest",
                "success",
                media_type=result.media_type,
                file_size=sum(
                    fm.get_size(file_path)
                    for file_path in files
                    if file_path.exists()
                ),
            )
        else:
            await message.answer(
                get_text("download.failed", lang)
            )

    except RateLimitError as exc:
        await _stop_animation(animation_task, stop_event)

        await _safe_edit(
            status_msg,
            get_text(
                "download.rate_limit",
                lang,
                seconds=getattr(exc, "seconds", 30),
            ),
        )

    except MultiSaverError as exc:
        await _stop_animation(animation_task, stop_event)

        error_key = getattr(
            exc,
            "error_key",
            "download.failed",
        )

        kwargs = {}

        if error_key == "download.too_large":
            kwargs["max_mb"] = get_settings().max_file_size_mb

        await _safe_edit(
            status_msg,
            get_text(error_key, lang, **kwargs),
        )

    except Exception:
        logger.exception("Pinterest download failed")

        await _stop_animation(animation_task, stop_event)

        await _safe_edit(
            status_msg,
            get_text("download.failed", lang),
        )

    finally:
        await _stop_animation(animation_task, stop_event)

        if not keep_files and result is not None:
            for file_path in getattr(result, "files", []) or []:
                try:
                    await fm.cleanup(Path(file_path))
                except Exception:
                    logger.exception(
                        "Pinterest cleanup failed: %s",
                        file_path,
                    )

            if job_id is not None:
                try:
                    job_store.remove(job_id)
                except Exception:
                    logger.exception("Could not remove Pinterest job")


@router.callback_query(F.data == "dl:cancel")
async def dl_cancel(
    callback: CallbackQuery,
    db_user: User,
    lang: str,
) -> None:
    _pending_urls.pop(db_user.telegram_id, None)

    await callback.answer()

    if callback.message:
        await callback.message.answer(
            get_text("cancel.ok", lang)
        )


@router.callback_query(F.data.in_({"dl:video", "dl:audio"}))
async def dl_start(
    callback: CallbackQuery,
    db_user: User,
    lang: str,
) -> None:
    await callback.answer()

    if not callback.message:
        return

    user_id = db_user.telegram_id
    url = _pending_urls.pop(user_id, None)

    if not url:
        await callback.message.answer(
            get_text("media.expired", lang)
        )
        return

    lock = _get_lock(user_id)

    if lock.locked():
        await callback.message.answer(
            get_text("download.wait", lang)
        )
        return

    async with lock:
        await _run_download(
            callback=callback,
            db_user=db_user,
            lang=lang,
            url=url,
            want_audio=callback.data == "dl:audio",
        )


async def _run_download(
    callback: CallbackQuery,
    db_user: User,
    lang: str,
    url: str,
    want_audio: bool,
) -> None:
    """Download media and send it to Telegram."""
    message = callback.message

    if not message:
        return

    user_id = db_user.telegram_id
    settings = get_settings()
    fm = get_file_manager()
    job_store = get_job_store()

    status_msg = await message.answer(
        f"⏳ {get_text('download.processing', lang)}"
    )
    wait_msg = await message.answer(
        get_text("download.wait", lang)
    )

    stop_event = asyncio.Event()
    animation_task = asyncio.create_task(
        _animate_status(status_msg, lang, stop_event)
    )

    result = None
    job_id = None
    keep_files = False

    try:
        result = await download_media(url)

        await _stop_animation(animation_task, stop_event)

        if (
            getattr(result, "media_type", None) == "link"
            and getattr(result, "direct_url", None)
        ):
            await _safe_delete(status_msg)
            await _safe_delete(wait_msg)

            title = getattr(result, "title", None) or "Media"

            await message.answer(
                f"🎬 {title}\n\n"
                + get_text(
                    "download.link_ready",
                    lang,
                    url=result.direct_url,
                )
            )

            await _record_history(
                user_id,
                result.platform or "unknown",
                "success",
                media_type="link",
            )
            return

        files = [
            Path(file_path)
            for file_path in (result.files or [])
        ]

        files = [
            file_path
            for file_path in files
            if file_path.is_file() and file_path.stat().st_size > 0
        ]

        if not files:
            await _safe_edit(
                status_msg,
                get_text("download.failed", lang),
            )
            await _safe_delete(wait_msg)
            return

        if want_audio:
            try:
                from services.audio_extractor import extract_audio

                video = next(
                    (
                        file_path
                        for file_path in files
                        if file_path.suffix.lower()
                        in {
                            ".mp4",
                            ".webm",
                            ".mkv",
                            ".mov",
                        }
                    ),
                    None,
                )

                if video is None:
                    await message.answer(
                        get_text("media.audio_failed", lang)
                    )
                    return

                await _safe_edit(
                    status_msg,
                    get_text("media.audio_processing", lang),
                )

                audio_path = Path(await extract_audio(video))

                await _safe_delete(status_msg)
                await _safe_delete(wait_msg)

                await message.answer_audio(
                    FSInputFile(audio_path),
                    caption=get_text("media.audio_ready", lang),
                )

                await fm.cleanup(audio_path)

                await _record_history(
                    user_id,
                    result.platform or "unknown",
                    "success",
                    media_type="audio",
                )
                return

            except Exception:
                logger.exception("Audio extraction failed")

                await message.answer(
                    get_text("media.audio_failed", lang)
                )
                return

        job_id = job_store.create(
            user_id=user_id,
            files=files,
            media_type=result.media_type,
            platform=result.platform,
            original_url=result.original_url or url,
            can_extract_audio=getattr(
                result,
                "can_extract_audio",
                False,
            ),
        )

        keyboard = media_actions_kb(
            job_id=job_id,
            lang=lang,
            media_type=result.media_type,
            can_extract_audio=getattr(
                result,
                "can_extract_audio",
                False,
            ),
        )

        await _safe_delete(status_msg)
        await _safe_delete(wait_msg)

        sent_any = False

        for index, file_path in enumerate(files):
            ext = file_path.suffix.lower()

            caption = (
                get_text("download.success", lang)
                if index == 0
                else None
            )

            markup = (
                keyboard
                if index == len(files) - 1
                else None
            )

            try:
                if (
                    result.media_type == "video"
                    or ext in {
                        ".mp4",
                        ".webm",
                        ".mov",
                        ".mkv",
                    }
                ):
                    await message.answer_video(
                        FSInputFile(file_path),
                        caption=caption,
                        reply_markup=markup,
                        supports_streaming=True,
                    )

                elif ext in {
                    ".jpg",
                    ".jpeg",
                    ".png",
                    ".webp",
                }:
                    await message.answer_photo(
                        FSInputFile(file_path),
                        caption=caption,
                        reply_markup=markup,
                    )

                elif ext in {
                    ".mp3",
                    ".m4a",
                    ".ogg",
                    ".opus",
                }:
                    await message.answer_audio(
                        FSInputFile(file_path),
                        caption=caption,
                        reply_markup=markup,
                    )

                else:
                    await message.answer_document(
                        FSInputFile(file_path),
                        caption=caption,
                        reply_markup=markup,
                    )

                sent_any = True

            except Exception:
                logger.exception(
                    "Could not send media file: %s",
                    file_path,
                )

                try:
                    await message.answer_document(
                        FSInputFile(file_path),
                        caption=get_text("download.success", lang),
                        reply_markup=keyboard,
                    )
                    sent_any = True
                except Exception:
                    logger.exception(
                        "Document fallback failed: %s",
                        file_path,
                    )

        if not sent_any:
            await message.answer(
                get_text("download.failed", lang)
            )
            return

        keep_files = True

        await _record_history(
            user_id,
            result.platform or "unknown",
            "success",
            media_type=result.media_type,
            file_size=sum(
                fm.get_size(file_path)
                for file_path in files
                if file_path.exists()
            ),
        )

    except RateLimitError as exc:
        await _stop_animation(animation_task, stop_event)

        await _safe_edit(
            status_msg,
            get_text(
                "download.rate_limit",
                lang,
                seconds=getattr(exc, "seconds", 30),
            ),
        )

        await _record_history(
            user_id,
            detect_platform(url) or "unknown",
            "failed",
            error_category="rate_limit",
        )

    except MultiSaverError as exc:
        await _stop_animation(animation_task, stop_event)

        error_key = getattr(
            exc,
            "error_key",
            "download.failed",
        )

        kwargs = {}

        if error_key == "download.too_large":
            kwargs["max_mb"] = settings.max_file_size_mb

        await _safe_edit(
            status_msg,
            get_text(error_key, lang, **kwargs),
        )

        await _record_history(
            user_id,
            detect_platform(url) or "unknown",
            "failed",
            error_category=error_key,
        )

    except Exception:
        logger.exception("Download failed")

        await _stop_animation(animation_task, stop_event)

        await _safe_edit(
            status_msg,
            get_text("download.internal_error", lang),
        )

        await _record_history(
            user_id,
            detect_platform(url) or "unknown",
            "failed",
            error_category="internal",
        )

    finally:
        await _stop_animation(animation_task, stop_event)

        await _safe_delete(wait_msg)

        if not keep_files and result is not None:
            for file_path in getattr(result, "files", []) or []:
                try:
                    await fm.cleanup(Path(file_path))
                except Exception:
                    logger.exception(
                        "Temporary file cleanup failed: %s",
                        file_path,
                    )

            if job_id is not None:
                try:
                    job_store.remove(job_id)
                except Exception:
                    logger.exception("Could not remove failed job")