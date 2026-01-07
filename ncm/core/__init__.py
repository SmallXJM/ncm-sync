"""Core functionality for NCM API."""

from .crypto import CryptoType, encrypt_weapi, encrypt_eapi, encrypt_linuxapi
from .exceptions import NCMError, APIError, NetworkError, AuthenticationError
from .options import RequestOptions, APIResponse
# from .request import BaseClient

__all__ = [
    "CryptoType",
    "encrypt_weapi", 
    "encrypt_eapi",
    "encrypt_linuxapi",
    "NCMError",
    "APIError",
    "NetworkError", 
    "AuthenticationError",
    "RequestOptions",
    "APIResponse",
    # "BaseClient"
]