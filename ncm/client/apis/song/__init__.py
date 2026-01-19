"""
    歌曲相关API
"""

from .detail import song_detail as detail
from .song_url import song_url as url
from .song_url_v1 import song_url_v1 as url_v1
from .song_download_url import song_download_url as download_url
from .song_download_url_v1 import song_download_url_v1 as download_url_v1
from .lyric import lyric, lyric_new

__all__ = [
    "detail",
    "url",
    "url_v1",
    "download_url",
    "download_url_v1",
    "lyric",
    "lyric_new",

]

