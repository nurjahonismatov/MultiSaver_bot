import logging
from pathlib import Path

from aiogram import F, Router
from aiogram.types import CallbackQuery, FSInputFile

from services.audio_extractor import extract_audio
from services.file_manager import get_file_manager
from services.job_store import get_job_store
from services.sharing import build_share_text, build_telegram_share_url
from utils.errors import AudioExtractionError, MediaExpiredError
from utils.i18n import get_text

logger = logging.getLogger(__name__)
router = Router(name="media_actions")


def _get_job(callback: CallbackQuery, job_id: str):
    store = get_job_store()
    user_id = callback.from_user.id
    job = store.get(job_id, user_id)
    return job


@router.callback_query(F.data.startswith("act:audio:"))
async def act_audio(callback: CallbackQuery, lang: str) -> None:
    job_id = callback.data.split(":")[-1]
    job = _get_job(callback, job_id)
    if job is None:
        await callback.answer(get_text("media.expired", lang), show_alert=True)
        return

    if not job.can_extract_audio or not job.files:
        await callback.answer(get_text("media.audio_failed", lang), show_alert=True)
        return

    await callback.answer()
    status = await callback.message.answer(get_text("media.audio_processing", lang))

    video_path = job.files[0]
    fm = get_file_manager()
    try:
        audio_path = await extract_audio(video_path)
        await status.delete()
        await callback.message.answer_audio(
            FSInputFile(audio_path),
            caption=get_text("media.audio_ready", lang),
        )
        # Cleanup audio after send (optional keep briefly)
        await fm.cleanup(audio_path)
    except AudioExtractionError:
        await status.edit_text(get_text("media.audio_failed", lang))
    except Exception:
        logger.exception("Audio extraction error")
        await status.edit_text(get_text("media.audio_failed", lang))


@router.callback_query(F.data.startswith("act:save:"))
async def act_save(callback: CallbackQuery, lang: str) -> None:
    job_id = callback.data.split(":")[-1]
    job = _get_job(callback, job_id)
    if job is None:
        await callback.answer(get_text("media.expired", lang), show_alert=True)
        return

    await callback.answer()
    # Re-send the file so user can use Telegram native save
    for fpath in job.files:
        if not Path(fpath).exists():
            await callback.message.answer(get_text("media.expired", lang))
            return
        try:
            await callback.message.answer_document(
                FSInputFile(fpath),
                caption=get_text("media.save_hint", lang),
            )
        except Exception:
            logger.exception("Save re-send failed")
            await callback.message.answer(get_text("media.save_hint", lang))


@router.callback_query(F.data.startswith("act:share:"))
async def act_share(callback: CallbackQuery, lang: str) -> None:
    job_id = callback.data.split(":")[-1]
    job = _get_job(callback, job_id)
    if job is None:
        await callback.answer(get_text("media.expired", lang), show_alert=True)
        return

    await callback.answer()
    url = job.original_url or "https://t.me/MultiSaver_bot"
    text = build_share_text(url, lang)
    share_url = build_telegram_share_url(text)
    await callback.message.answer(
        f"{text}\n\n🔗 {share_url}"
    )


@router.callback_query(F.data.startswith("act:again:"))
async def act_again(callback: CallbackQuery, lang: str) -> None:
    job_id = callback.data.split(":")[-1]
    job = _get_job(callback, job_id)
    if job is None or not job.original_url:
        await callback.answer(get_text("media.expired", lang), show_alert=True)
        return

    await callback.answer()
    # Ask user to resend or we can re-trigger by sending the URL as text instruction
    await callback.message.answer(
        get_text("download.prompt", lang) + f"\n\n`{job.original_url}`",
        parse_mode="Markdown",
    )   
