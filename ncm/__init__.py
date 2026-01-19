"""
NCM Sync - 音乐同步工具


"""

from .core.exceptions import (
    NCMError,
    APIError,
    NetworkError,
    AuthenticationError,
    RateLimitError,
    EncryptionError,
    ValidationError
)

__version__ = "0.1.0"
__author__ = "smallxjm"

__all__ = [
    # "Client",
    "NCMError",
    "APIError", 
    "NetworkError",
    "AuthenticationError",
    "RateLimitError",
    "EncryptionError",
    "ValidationError"
]