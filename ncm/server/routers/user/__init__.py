"""User ncm package."""

from .qr import QRAuthController
from .profile import ProfileController
from .session import SessionController

qr = QRAuthController()
profile = ProfileController()
session = SessionController()

__all__ = [
    "qr",
    "profile",
    "session"
]
