"""
    歌曲列表相关API
"""

from .create import playlist_create as create
from .detail import playlist_detail as detail
from .subscribe import playlist_subscribe as subscribe
from .track_all import playlist_track_all as track_all
from .track_add import playlist_track_add as track_add
from .track_delete import playlist_track_delete as track_delete

__all__ = [
    "create",
    "detail",
    "subscribe",
    "track_all",
    "track_add",
    "track_delete",
]
