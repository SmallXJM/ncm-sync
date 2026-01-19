"""
    用户相关API
"""
# from . import login
# from . import register

from .user_detail import user_detail as detail
from .user_playlist import user_playlist as playlist

__all__ = [
    # "login",
    # "register",

    "detail",
    "playlist",

]

