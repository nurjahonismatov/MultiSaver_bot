from adapters.base import BaseAdapter, MediaResult
from adapters.facebook import FacebookAdapter
from adapters.instagram import InstagramAdapter
from adapters.pinterest import PinterestAdapter
from adapters.snapchat import SnapchatAdapter
from adapters.telegram_media import TelegramMediaAdapter
from adapters.youtube import YouTubeAdapter

__all__ = [
    "BaseAdapter",
    "MediaResult",
    "YouTubeAdapter",
    "InstagramAdapter",
    "TelegramMediaAdapter",
    "FacebookAdapter",
    "PinterestAdapter",
    "SnapchatAdapter",
]
