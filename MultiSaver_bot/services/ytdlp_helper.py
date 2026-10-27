"""yt-dlp helpers."""

import logging
from pathlib import Path
from typing import Optional

import yt_dlp

from config import get_settings
from utils.errors import NetworkError, PrivateContentError, UnsupportedPlatformError

logger = logging.getLogger(__name__)
logging.getLogger("yt_dlp").setLevel(logging.CRITICAL)


def _base_opts(extra: Optional[dict] = None) -> dict:
    settings = get_settings()
    opts = {
        "quiet": True,
        "no_warnings": True,
        "verbose": False,
        "noplaylist": True,
        "restrictfilenames": True,
        "socket_timeout": 15,
        "retries": 1,
        "fragment_retries": 1,
        "concurrent_fragment_downloads": 8,
        "writethumbnail": False,
        "writeinfojson": False,
        "ignoreerrors": False,
        "noprogress": True,
        "geo_bypass": True,
        "extractor_args": {
            "youtube": {"player_client": ["android"], "skip": ["dash", "hls"]},
        },
    }
    browser = (getattr(settings, "cookies_from_browser", "") or "").strip().lower()
    if browser in ("chrome", "edge", "firefox", "opera", "brave"):
        opts["cookiesfrombrowser"] = (browser,)
    if extra:
        opts.update(extra)
    return opts


def _map_error(exc: Exception) -> None:
    msg = str(exc).lower()
    if any(
        k in msg
        for k in (
            "private", "login", "auth", "restricted", "not available",
            "empty media", "cookies", "logged-in", "only available for registered",
        )
    ):
        raise PrivateContentError(str(exc)) from exc
    if "unsupported url" in msg or "no video" in msg:
        raise UnsupportedPlatformError(str(exc)) from exc
    raise NetworkError(str(exc)) from exc


def extract_direct_url(
    url: str,
    format_selector: str = "best[ext=mp4][height<=480]/best[height<=480]/best",
):
    ydl_opts = _base_opts({"format": format_selector, "skip_download": True})
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return None, None, None
            media_url = info.get("url")
            filesize = info.get("filesize") or info.get("filesize_approx")
            title = info.get("title")
            if not media_url and info.get("formats"):
                for f in reversed(info["formats"]):
                    if f.get("url") and f.get("vcodec") != "none":
                        media_url = f["url"]
                        filesize = f.get("filesize") or f.get("filesize_approx") or filesize
                        break
            return media_url, title, filesize
    except yt_dlp.utils.DownloadError as exc:
        _map_error(exc)
    except Exception as exc:
        logger.exception("extract_direct_url")
        raise NetworkError(str(exc)) from exc
    return None, None, None


def yt_dlp_download(
    url: str,
    output_dir: Path,
    format_selector: str = "best",
    extra_opts: Optional[dict] = None,
) -> list:
    settings = get_settings()
    outtmpl = str(output_dir / "%(id)s.%(ext)s")
    ydl_opts = _base_opts(
        {
            "outtmpl": outtmpl,
            "format": format_selector,
            "max_filesize": settings.max_file_size_bytes,
            "merge_output_format": "mp4",
        }
    )
    if extra_opts:
        ydl_opts.update(extra_opts)
    downloaded = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info is None:
                return []
            entries = [e for e in info["entries"] if e] if "entries" in info else [info]
            for entry in entries:
                path = Path(ydl.prepare_filename(entry))
                if path.exists():
                    downloaded.append(path)
                else:
                    for ext in (".mp4", ".webm", ".mkv", ".jpg", ".png", ".webp", ".m4a"):
                        alt = path.with_suffix(ext)
                        if alt.exists():
                            downloaded.append(alt)
                            break
    except yt_dlp.utils.DownloadError as exc:
        _map_error(exc)
    except Exception as exc:
        logger.exception("yt_dlp_download")
        raise NetworkError(str(exc)) from exc
    return downloaded