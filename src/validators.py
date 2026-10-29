"""
Input validation for property form fields and uploaded images.
All validation errors return friendly, human-readable messages.
"""

import io
import re
from pathlib import Path
from PIL import Image
from src.config import (
    ALLOWED_EXTENSIONS,
    MAX_IMAGE_COUNT,
    MIN_IMAGE_COUNT,
    MIN_IMAGE_HEIGHT,
    MIN_IMAGE_WIDTH,
)

# Lenient price pattern: matches INR 85,00,000, $250,000, 45 Lakh, 1.2 Cr, ₹75,00,000, 500000, etc.
PRICE_PATTERN = re.compile(
    r"^[\$€£₹\s]*(?:INR|USD|EUR|GBP)?\s*[\d,]+(?:\.\d+)?\s*(?:Lakh|Lakhs|Lac|Lacs|Cr|Crore|Crores|k|M|B|Million|k|K)?\b",
    re.IGNORECASE,
)


def validate_single_image(file) -> tuple[bool, str]:
    """
    Validate a single image file object or path.
    Checks file extension, Pillow readability, and minimum resolution (400x300).
    Returns (True, "") or (False, "error reason").
    """
    if file is None:
        return False, "Image file is missing."

    # Determine filename
    filename = getattr(file, "name", str(file))
    ext = Path(filename).suffix.lower().lstrip(".")

    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported file type (.{ext}). Allowed formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}."

    try:
        # If it's a file-like object with read(), seek to start
        if hasattr(file, "seek"):
            file.seek(0)
            img = Image.open(file)
            img.verify()  # Verify integrity
            # After verify, we must re-open to inspect dimensions
            file.seek(0)
            img = Image.open(file)
        else:
            with Image.open(file) as img:
                img.verify()
            with Image.open(file) as img:
                w, h = img.size
                if w < MIN_IMAGE_WIDTH or h < MIN_IMAGE_HEIGHT:
                    return False, f"Image resolution ({w}x{h}) is too small. Minimum required: {MIN_IMAGE_WIDTH}x{MIN_IMAGE_HEIGHT} px."
                return True, ""

        w, h = img.size
        if w < MIN_IMAGE_WIDTH or h < MIN_IMAGE_HEIGHT:
            return False, f"Image resolution ({w}x{h}) is too small. Minimum required: {MIN_IMAGE_WIDTH}x{MIN_IMAGE_HEIGHT} px."

        return True, ""
    except Exception as e:
        return False, f"Corrupted or unreadable image file: {e}"


def validate_property_data(
    data: dict[str, str],
    images: list,
) -> tuple[bool, list[str]]:
    """
    Validate all form fields and the uploaded image list.

    data keys:
        - property_name: str
        - location: str
        - price: str
        - property_type: str
        - key_features: str (optional/recommended)
        - contact_info: str

    images: list of Streamlit UploadedFile objects or file paths.

    Returns:
        (is_valid: bool, errors: list[str])
    """
    errors: list[str] = []

    # 1. Required string checks
    required_fields = {
        "property_name": "Property Name",
        "location": "Location / Address",
        "price": "Price",
        "property_type": "Property Type",
        "contact_info": "Contact Information / Agent Details",
    }

    for key, label in required_fields.items():
        val = data.get(key, "")
        if not isinstance(val, str) or not val.strip():
            errors.append(f"'{label}' is required and cannot be blank.")

    # 2. Price format validation
    price_val = data.get("price", "").strip()
    if price_val:
        # Check if contains at least one digit
        if not re.search(r"\d", price_val):
            errors.append(
                f"Price format '{price_val}' looks invalid. Must contain numbers (e.g. 'INR 85,00,000' or '$450,000')."
            )
        elif not PRICE_PATTERN.search(price_val):
            errors.append(
                f"Price format '{price_val}' is unrecognized. Use standard numeric or currency formats."
            )

    # 3. Image count check
    if images is None:
        images = []

    image_count = len(images)
    if image_count < MIN_IMAGE_COUNT:
        errors.append(
            f"At least {MIN_IMAGE_COUNT} images are required (you uploaded {image_count})."
        )
    elif image_count > MAX_IMAGE_COUNT:
        errors.append(
            f"Maximum {MAX_IMAGE_COUNT} images allowed (you uploaded {image_count}). Please remove {image_count - MAX_IMAGE_COUNT}."
        )

    # 4. Individual image validation
    for idx, img_file in enumerate(images, start=1):
        is_ok, reason = validate_single_image(img_file)
        if not is_ok:
            img_name = getattr(img_file, "name", f"Image #{idx}")
            errors.append(f"Image #{idx} ('{img_name}') is invalid: {reason}")

    return len(errors) == 0, errors
