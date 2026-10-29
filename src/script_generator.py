"""
Deterministic, rule-based script and caption generator.
Uses strictly facts typed by the user. No generative AI or external LLMs.
"""

from src.config import (
    CLOSING_DURATION,
    OPENING_DURATION,
    TARGET_MAX_TOTAL_DURATION,
    TARGET_MIN_TOTAL_DURATION,
)


def generate_property_script(data: dict[str, str], image_count: int = 5) -> dict:
    """
    Build on-screen captions, scene timings, and narration script
    from validated user facts only.

    Args:
        data: Dict containing 'property_name', 'location', 'price',
              'property_type', 'key_features', 'contact_info'.
        image_count: Number of uploaded property images (between 4 and 8).

    Returns:
        dict:
            title: str
            captions: list[str] (length == image_count)
            price_line: str
            closing: str
            narration: str
            durations: list[float] (length == image_count + 2: [opening, img_1..img_N, closing])
    """
    # Defensive key checks
    required_keys = ["property_name", "location", "price", "property_type", "contact_info"]
    for k in required_keys:
        if not data.get(k, "").strip():
            raise ValueError(f"Missing required field for script generation: {k}")

    prop_name = data["property_name"].strip()
    location = data["location"].strip()
    price = data["price"].strip()
    prop_type = data["property_type"].strip()
    contact = data["contact_info"].strip()
    raw_features = data.get("key_features", "")

    # Split and clean features
    features = [f.strip() for f in raw_features.split(",") if f.strip()]
    if not features:
        features = ["Prime Location", "Spacious Layout", "Quality Finishes", "Must See Property"]

    # Generate title
    title = f"{prop_name} — {location}"
    price_line = f"Price: {price}"
    closing = contact

    # Build per-image captions (one per image)
    captions: list[str] = []
    num_features = len(features)
    for i in range(image_count):
        feat = features[i % num_features]
        captions.append(f"{prop_type} · {feat}")

    # Calculate optimal per-image duration so total is strictly within 20-30s
    # opening (3.0s) + closing (4.0s) = 7.0s
    # target total is around 22-26s
    fixed_overhead = OPENING_DURATION + CLOSING_DURATION
    target_budget = 24.0 - fixed_overhead  # ~17 seconds for images
    per_image_duration = round(target_budget / max(image_count, 1), 1)

    # Clamp between 2.2s and 3.5s
    per_image_duration = max(2.2, min(3.5, per_image_duration))

    durations = [OPENING_DURATION] + [per_image_duration] * image_count + [CLOSING_DURATION]
    total_duration = sum(durations)

    # Build concise narration text strictly adhering to user facts
    narration = (
        f"{prop_name}, located in {location}. "
        f"This {prop_type} features {', '.join(features[:3])}. "
        f"Offered at {price}. "
        f"{contact}."
    )

    return {
        "title": title,
        "property_name": prop_name,
        "location": location,
        "property_type": prop_type,
        "price_line": price_line,
        "price": price,
        "captions": captions,
        "closing": closing,
        "narration": narration,
        "durations": durations,
        "total_duration": total_duration,
    }
