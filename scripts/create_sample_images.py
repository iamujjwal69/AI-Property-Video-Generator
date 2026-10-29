"""
Generate 5 high-resolution synthetic property photographs for sample_images/.
Produces realistic, visually appealing property interior/exterior frames.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
from src.config import SAMPLE_IMAGES_DIR
from src.utils import load_font


def create_sample_photo(filename: str, scene_type: str, palette: tuple, detail_tags: list[str]):
    width, height = 1280, 720
    img = Image.new("RGB", (width, height), palette[0])
    draw = ImageDraw.Draw(img)

    # 1. Gradient background
    c1, c2, c3 = palette
    for y in range(height):
        ratio = y / height
        if ratio < 0.5:
            r = int(c1[0] * (1 - ratio * 2) + c2[0] * (ratio * 2))
            g = int(c1[1] * (1 - ratio * 2) + c2[1] * (ratio * 2))
            b = int(c1[2] * (1 - ratio * 2) + c2[2] * (ratio * 2))
        else:
            sub_r = (ratio - 0.5) * 2
            r = int(c2[0] * (1 - sub_r) + c3[0] * sub_r)
            g = int(c2[1] * (1 - sub_r) + c3[1] * sub_r)
            b = int(c2[2] * (1 - sub_r) + c3[2] * sub_r)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # 2. Architectural perspective lines (walls, floor, ceiling)
    draw.line([(0, height - 160), (width, height - 160)], fill=(255, 255, 255, 60), width=2)
    draw.line([(180, 0), (0, height - 160)], fill=(255, 255, 255, 40), width=2)
    draw.line([(width - 180, 0), (width, height - 160)], fill=(255, 255, 255, 40), width=2)

    # Subtle floor grid lines
    for fx in range(100, width, 180):
        draw.line([(fx, height - 160), (fx + (fx - width // 2) * 2, height)], fill=(255, 255, 255, 25), width=1)

    # Center window / focal frame
    win_x1, win_y1, win_x2, win_y2 = 340, 100, 940, 480
    draw.rounded_rectangle((win_x1, win_y1, win_x2, win_y2), radius=16, fill=(245, 248, 255), outline=(210, 220, 235), width=4)
    # Window panes
    mid_x = (win_x1 + win_x2) // 2
    draw.line([(mid_x, win_y1), (mid_x, win_y2)], fill=(200, 210, 225), width=3)
    draw.line([(win_x1, win_y1 + 180), (win_x2, win_y1 + 180)], fill=(200, 210, 225), width=3)

    # 3. Soft lighting glow
    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((width // 2 - 250, 40, width // 2 + 250, 400), fill=(255, 255, 220, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=50))
    img.paste(glow, (0, 0), glow)

    # 4. Stylized room label watermark card
    card_w, card_h = 560, 140
    cx1 = (width - card_w) // 2
    cy1 = height - 240
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    odraw.rounded_rectangle((cx1, cy1, cx1 + card_w, cy1 + card_h), radius=14, fill=(15, 22, 36, 210), outline=(255, 255, 255, 40), width=1)

    font_main = load_font(32)
    font_sub = load_font(20)

    # Room title
    odraw.text((cx1 + 30, cy1 + 25), scene_type.upper(), font=font_main, fill=(255, 255, 255))
    # Detail pills
    details = "  •  ".join(detail_tags)
    odraw.text((cx1 + 30, cy1 + 80), details, font=font_sub, fill=(255, 179, 0))

    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    dest = SAMPLE_IMAGES_DIR / filename
    img.save(dest, format="JPEG", quality=95)
    print(f"Created sample image: {dest.name}")


def main():
    SAMPLE_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    samples = [
        (
            "01_exterior.jpg",
            "Modern Architecture & Facade",
            ((40, 60, 90), (70, 95, 130), (30, 40, 50)),
            ["Grand Entrance", "Landscaped Garden", "24x7 Gated Security"],
        ),
        (
            "02_living_room.jpg",
            "Designer Living & Dining",
            ((70, 65, 55), (140, 130, 115), (45, 40, 35)),
            ["High Ceilings", "Expansive Glazing", "Italian Marble Finish"],
        ),
        (
            "03_kitchen.jpg",
            "Chef's Modular Kitchen",
            ((50, 70, 80), (100, 130, 145), (35, 45, 55)),
            ["Quartz Countertops", "Soft-Close Cabinets", "Dedicated Pantry"],
        ),
        (
            "04_master_bedroom.jpg",
            "Master Suite & Retreat",
            ((60, 50, 65), (120, 105, 130), (35, 30, 40)),
            ["Hardwood Flooring", "Walk-in Wardrobe", "Ensuite Bath"],
        ),
        (
            "05_balcony_view.jpg",
            "Panoramic Balcony Lounge",
            ((45, 75, 70), (90, 140, 130), (30, 50, 45)),
            ["Unobstructed Skyline", "Sunset Facing", "Spacious Deck"],
        ),
    ]

    for fname, name, pal, tags in samples:
        create_sample_photo(fname, name, pal, tags)


if __name__ == "__main__":
    main()
