"""Custom exception classes for NCM API."""

from typing import Optional, Dict, Any


class NCMError(Exception):
    """Base exception for all NCM-related errors."""
    
    def __init__(self, message: str, code: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class APIError(NCMError):
    """API-related errors (4xx, 5xx responses)."""
    pass


class NetworkError(NCMError):
    """Network connectivity issues."""
    pass


class AuthenticationError(APIError):
    """Authentication failed or required."""
    pass


class RateLimitError(APIError):
    """Rate limit exceeded."""
    pass


class EncryptionError(NCMError):
    """Encryption/decryption failed."""
    pass


class ValidationError(NCMError):
    """Input validation failed."""
    pass