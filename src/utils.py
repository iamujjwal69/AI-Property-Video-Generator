"""
Utility functions for temporary directory management, path cleanup, and filename generation.
"""

import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from PIL import ImageFont
from src.config import TEMP_DIR, OUTPUT_DIR, FONT_PATH


def ensure_directories() -> None:
    """Ensure required runtime directories exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)


def make_temp_dir(base: str = "temp") -> str:
    """
    Create a clean, isolated temporary directory under the base temp folder.
    Returns the absolute path as a string.
    """
    base_path = Path(base)
    if not base_path.is_absolute():
        base_path = Path(__file__).resolve().parent.parent / base
    base_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    run_dir = base_path / f"run_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return str(run_dir.resolve())


def cleanup_paths(paths: list[str]) -> None:
    """
    Best-effort deletion of specified files or directories.
    Swallows individual OSError / PermissionError so cleanup never crashes the app.
    """
    for p in paths:
        if not p:
            continue
        try:
            path_obj = Path(p)
            if path_obj.is_file() or path_obj.is_symlink():
                path_obj.unlink(missing_ok=True)
            elif path_obj.is_dir():
                shutil.rmtree(path_obj, ignore_errors=True)
        except Exception:
            # Cleanup must never raise
            pass


def timestamped_filename(prefix: str = "property_video", ext: str = "mp4") -> str:
    """
    Generate a timestamped filename, e.g. property_video_20261029_113000.mp4
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_ext = ext.lstrip(".")
    return f"{prefix}_{timestamp}.{clean_ext}"


def safe_filename(name: str) -> str:
    """Sanitize a string for safe use in file paths."""
    sanitized = re.sub(r'[\\/*?:"<>|]', "", name)
    sanitized = re.sub(r"\s+", "_", sanitized.strip())
    return sanitized[:50] or "property"


def load_font(size: int = 32) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """
    Load bundled TrueType font, or fallback to default Windows/system font or PIL default.
    Guaranteed not to raise an unhandled exception.
    """
    # 1. Try bundled font
    if FONT_PATH.exists():
        try:
            return ImageFont.truetype(str(FONT_PATH), size=size)
        except Exception:
            pass

    # 2. Try common system fonts on Windows
    system_font_candidates = [
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for font_path in system_font_candidates:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size=size)
            except Exception:
                continue

    # 3. Fallback to PIL default
    return ImageFont.load_default()
