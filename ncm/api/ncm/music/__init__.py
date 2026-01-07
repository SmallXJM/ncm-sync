"""Music ncm package."""

from .search import SearchController
from .user import UserController
from .playlist import PlaylistController
from .download import DownloadController
from .song import SongController

search = SearchController()
user = UserController()
playlist = PlaylistController()
download = DownloadController()
song = SongController()

__all__ = [
    "search",
    "user",
    "playlist",
    "download",
    "song"
]
