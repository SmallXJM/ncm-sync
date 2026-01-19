"""
modules 层约定：
- 面向前端与 ncm 的基础 API
- 不包含流程、状态、副作用
- 不访问数据库、不操作文件
"""

from . import user
from .user import login
from .user import register
from . import search
from . import playlist
from . import song

__all__ = [
    "user",
    "login",
    "register",
    "search",
    "playlist",
    "song",

]