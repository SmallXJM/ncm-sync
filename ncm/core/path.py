"""
Path management utility module for NCM Sync.

This module provides a unified way to handle file paths across the application,
ensuring consistent behavior between development and frozen (PyInstaller) environments.

Usage Guide:

1. **Get Project Root**:
   Use `get_app_base()` to get the base directory of the application.
   - In Dev: The project root directory.
   - In Frozen: The directory containing the executable.

   ```python
   from ncm.core.path import get_app_base
   root = get_app_base()
   ```

2. **Resolve Writable Paths**:
   Use `get_data_path(relative_path)` for files that need to be read/written in the project directory
   (e.g., config files, databases, logs, downloads).

   ```python
   from ncm.core.path import get_data_path
   config_path = get_data_path("config/settings.json")
   ```

3. **Get Bundled Resources**:
   Use `get_static_path(relative_path)` for static assets bundled with the application.
   - In Dev: Resolves from project root.
   - In Frozen: Resolves from `sys._MEIPASS` (temp directory).

   ```python
   from ncm.core.path import get_static_path
   template_path = get_static_path("templates/index.html")
   ```

4. **Ensure Directory Exists**:
   Use `prepare_path(path)` to automatically create directories.
   - If path has an extension, it assumes it's a file and creates the parent directory.
   - If path has no extension, it creates the directory itself.

   ```python
   from ncm.core.path import prepare_path
   prepare_path("downloads/music/song.mp3") # Creates downloads/music/
   ```

5. **Sanitize Filenames**:
   Use `sanitize_filename(name)` to make strings safe for use as filenames.

   ```python
   from ncm.core.path import sanitize_filename
   safe_name = sanitize_filename("Artist: Title?") # -> "Artist_ Title_"
   ```
"""

__all__ = [
    "get_app_base",
    "get_static_path",
    "get_data_path",
    "get_config_path",
    "prepare_path",
    "normalize_path",
    "sanitize_filename",
    "PathLike",
]

import sys
import os
from pathlib import Path
from typing import Union
from ncm.core.constants import CONFIG_DIR_NAME

# Type alias for path-like objects
PathLike = Union[str, Path]


def get_app_base() -> Path:
    """
    Get the absolute path to the project root directory.

    In a development environment, this is the directory containing the 'ncm' package.
    In a frozen (PyInstaller) environment, this is the directory containing the executable.

    Returns:
        Path: The absolute path to the project root.
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller: executable is in the root
        return Path(sys.executable).parent.resolve()
    else:
        # Development: this file is in ncm/core/path.py
        # root is 3 levels up: ncm/core/ -> ncm/ -> root
        return Path(__file__).resolve().parents[2]


def get_static_path(relative_path: PathLike) -> Path:
    """
    Get the absolute path to a resource file.

    Handles the difference between development and PyInstaller temp directory (sys._MEIPASS).
    Use this for read-only bundled resources (e.g. templates, static files).

    Args:
        relative_path: Relative path to the resource from the project root.

    Returns:
        Path: The absolute path to the resource.
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = get_app_base()
    
    return (base_path / relative_path).resolve()


def get_data_path(relative_path: PathLike) -> Path:
    """
    Resolve a relative path against the project root.

    Use this for writable files (config, logs, database, cache).

    Args:
        relative_path: The relative path to resolve.

    Returns:
        Path: The absolute path.
    """
    return (get_app_base() / relative_path).resolve()


def get_config_path(filename: str = "") -> Path:
    """
    Get the absolute path to the configuration directory or a file within it.

    Args:
        filename: Optional filename to append to the config directory path.

    Returns:
        Path: The absolute path to the config directory or file.
    """
    config_dir = get_data_path(CONFIG_DIR_NAME)
    if filename:
        return (config_dir / filename).resolve()
    return config_dir


def prepare_path(path: PathLike) -> Path:
    """
    Ensure that the directory for the given path exists.
    If the path is a file (has suffix), ensures its parent exists.
    If the path is a directory (no suffix), ensures it exists.

    Args:
        path: The path to ensure exists.

    Returns:
        Path: The resolved Path object.
    """
    p = Path(path).resolve()
    
    # If it looks like a file (has extension), use parent
    # Note: This is a heuristic. For explicit directory creation, use directory path without extension
    target_dir = p.parent if p.suffix else p
    
    target_dir.mkdir(parents=True, exist_ok=True)
    return p


def normalize_path(path: PathLike) -> str:
    """
    Normalize a path string for the current OS.

    Args:
        path: The path to normalize.

    Returns:
        str: The normalized path string.
    """
    return str(Path(path).resolve())


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing or replacing illegal characters.

    Args:
        filename: The original filename.

    Returns:
        str: The sanitized filename safe for filesystem use.
    """
    if not filename:
        return "Unknown"

    # Replace illegal characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')

    # Strip leading/trailing spaces and dots
    filename = filename.strip(' .')

    # Limit length (optional, but good practice)
    if len(filename) > 200:
        filename = filename[:200]

    return filename or "Unknown"

