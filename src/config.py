"""
Configuration and constants for the AI Property Video Generator.
"""

from pathlib import Path

# Base Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
TEMP_DIR = PROJECT_ROOT / "temp"
ASSETS_DIR = PROJECT_ROOT / "assets"
SAMPLE_DATA_DIR = PROJECT_ROOT / "sample_data"
SAMPLE_IMAGES_DIR = PROJECT_ROOT / "sample_images"

# Bundled Font
FONT_PATH = ASSETS_DIR / "font.ttf"

# Video Specifications
VIDEO_WIDTH = 1280
VIDEO_HEIGHT = 720
VIDEO_SIZE = (VIDEO_WIDTH, VIDEO_HEIGHT)
FPS = 24
VIDEO_CODEC = "libx264"
AUDIO_CODEC = "aac"

# Scene Durations (seconds)
OPENING_DURATION = 3.0
CLOSING_DURATION = 4.0
DEFAULT_IMAGE_DURATION = 3.0
FADE_DURATION = 0.4

# Target Total Duration Constraints (20 - 30 seconds)
TARGET_MIN_TOTAL_DURATION = 20.0
TARGET_MAX_TOTAL_DURATION = 30.0

# Image Constraints
MIN_IMAGE_COUNT = 4
MAX_IMAGE_COUNT = 8
MIN_IMAGE_WIDTH = 400
MIN_IMAGE_HEIGHT = 300
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

# Color Palette (RGB)
COLOR_PRIMARY_BG = (20, 24, 33)          # Dark modern slate
COLOR_ACCENT = (255, 179, 0)              # Warm gold / amber accent
COLOR_TEXT_PRIMARY = (255, 255, 255)      # White
COLOR_TEXT_SECONDARY = (210, 215, 225)    # Light gray/blue
COLOR_OVERLAY_BG = (10, 14, 22, 215)      # Semi-transparent dark overlay (RGBA)
COLOR_BADGE_BG = (220, 110, 20)           # Warm terracotta/orange badge
COLOR_PRICE_BG = (22, 101, 52)            # Emerald green badge
