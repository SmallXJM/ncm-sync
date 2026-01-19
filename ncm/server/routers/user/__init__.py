"""User ncm package."""

from .auth import AuthController
from .profile import ProfileController
from .management import ManagementController

auth = AuthController()
profile = ProfileController()
manage = ManagementController()

__all__ = [
    "auth",
    "profile",
    "manage"
]
