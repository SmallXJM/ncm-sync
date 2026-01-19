from pathlib import Path
from typing import Optional


def guess_audio_mime(path: Path) -> str:
    """Guess MIME type for audio file based on extension."""
    suffix = path.suffix.lower()
    return {
        ".mp3": "audio/mpeg",
        ".m4a": "audio/mp4",
        ".mp4": "audio/mp4",
        ".aac": "audio/aac",
        ".wav": "audio/wav",
        ".flac": "audio/flac",
    }.get(suffix, "application/octet-stream")


def is_within(child: Path, parent: Path) -> bool:
    """Check if child path is within parent path."""
    try:
        child_resolved = child.resolve()
        parent_resolved = parent.resolve()
        return child_resolved == parent_resolved or parent_resolved in child_resolved.parents
    except Exception:
        return False


def guess_image_mime(data: bytes) -> str:
    """Guess MIME type for image data."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    return "application/octet-stream"


def extract_cover_bytes(file_path: Path) -> Optional[bytes]:
    """Extract cover art from audio file."""
    try:
        from mutagen.mp3 import MP3
        from mutagen.id3 import ID3
        from mutagen.flac import FLAC
        from mutagen.mp4 import MP4
    except Exception:
        return None

    suffix = file_path.suffix.lower().lstrip(".")
    try:
        if suffix == "mp3":
            audio = MP3(str(file_path))
            if not audio.tags:
                return None
            id3 = ID3(str(file_path))
            for tag in id3.values():
                if tag.FrameID == "APIC":
                    return bytes(tag.data)
            return None

        if suffix in {"m4a", "mp4", "aac"}:
            audio = MP4(str(file_path))
            covr = audio.tags.get("covr") if audio.tags else None
            if not covr:
                return None
            first = covr[0]
            return bytes(first)

        if suffix == "flac":
            audio = FLAC(str(file_path))
            if not audio.pictures:
                return None
            return bytes(audio.pictures[0].data)

        return None
    except Exception:
        return None


def extract_lyrics(file_path: Path) -> Optional[str]:
    """Extract lyrics from audio file."""
    try:
        from mutagen.mp3 import MP3
        from mutagen.id3 import ID3
        from mutagen.flac import FLAC
        from mutagen.mp4 import MP4
    except Exception:
        return None

    suffix = file_path.suffix.lower().lstrip(".")
    try:
        if suffix == "mp3":
            audio = MP3(str(file_path))
            if not audio.tags:
                return None
            id3 = ID3(str(file_path))
            uslt = id3.getall("USLT")
            if uslt:
                return str(uslt[0].text)
            sylt = id3.getall("SYLT")
            if sylt:
                pieces = [p[0] for p in sylt[0].text if p and isinstance(p[0], str)]
                return "\n".join(pieces) if pieces else None
            return None

        if suffix in {"m4a", "mp4", "aac"}:
            audio = MP4(str(file_path))
            lyr = audio.tags.get("\xa9lyr") if audio.tags else None
            if lyr:
                return str(lyr[0])
            return None

        if suffix == "flac":
            audio = FLAC(str(file_path))
            lyr = audio.get("LYRICS")
            if lyr:
                return str(lyr[0])
            return None

        return None
    except Exception:
        return None
