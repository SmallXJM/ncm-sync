"""
    搜索相关API
"""

from .search import search as get
from .search_hot import search_hot as hot

__all__ = [
    "get",
    "hot",

]

