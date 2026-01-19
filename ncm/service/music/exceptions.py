class LocalMusicError(Exception):
    """Base exception for local music service."""
    pass


class LocalMusicNotFoundError(LocalMusicError):
    """Raised when local music task or file is not found."""
    pass


class LocalMusicNoCoverError(LocalMusicError):
    """Raised when no cover art can be extracted."""
    pass
