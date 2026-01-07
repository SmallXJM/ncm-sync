"""
NCM (Netease Cloud Music) Python API

A Python implementation of the Netease Cloud Music API that provides a clean,
Pythonic interface for accessing Netease Cloud Music services.
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
__author__ = "NCM Python Team"

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