from .handler import router as handlers_router
from .instagram import router as instagram_router
from .pinterest import router as pinterest_router
from .soundcloud import router as soundcloud_router
from .tiktok import router as tiktok_router
from .youtube import router as youtube_router

__all__ = [
    "pinterest_router",
    "handlers_router",
    "instagram_router",
    "youtube_router",
    "tiktok_router",
    "soundcloud_router",
]
