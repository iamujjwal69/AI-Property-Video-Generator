"""
Pillow-based image processing and scene frame compositor.
Composes full 1280x720 still frames with typography, overlays, and badges,
completely eliminating the need for ImageMagick.
"""

import io
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageOps
from src.config import (
    COLOR_ACCENT,
    COLOR_BADGE_BG,
    COLOR_OVERLAY_BG,
    COLOR_PRICE_BG,
    COLOR_PRIMARY_BG,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    VIDEO_HEIGHT,
    VIDEO_WIDTH,
)
from src.utils import load_font


class ImageProcessingError(Exception):
    """Raised when an uploaded image cannot be processed into a scene frame."""
    pass


def _open_image_safely(img_input) -> Image.Image:
    """Safely open an uploaded file or file path into an RGB Pillow Image."""
    try:
        if hasattr(img_input, "seek"):
            img_input.seek(0)
            img = Image.open(img_input)
        else:
            img = Image.open(img_input)

        img = ImageOps.exif_transpose(img)
        return img.convert("RGB")
    except Exception as exc:
        raise ImageProcessingError(f"Could not decode image: {exc}") from exc


def _create_cinematic_background(
    img: Image.Image,
    target_size: tuple[int, int] = (VIDEO_WIDTH, VIDEO_HEIGHT),
) -> Image.Image:
    """
    Create a blurred, darkened background from the image for letterbox padding.
    Gives a modern TV/cinema aesthetic rather than harsh black bars.
    """
    tw, th = target_size
    # Fill target size for background
    bg = ImageOps.fit(img, (tw, th), method=Image.Resampling.LANCZOS)
    # Heavy blur
    bg = bg.filter(ImageFilter.GaussianBlur(radius=28))
    # Darken overlay
    overlay = Image.new("RGBA", (tw, th), (10, 14, 24, 160))
    bg_rgba = bg.convert("RGBA")
    combined = Image.alpha_composite(bg_rgba, overlay)
    return combined.convert("RGB")


def _draw_text_with_shadow(
    draw: ImageDraw.ImageDraw,
    pos: tuple[int, int],
    text: str,
    font,
    fill=COLOR_TEXT_PRIMARY,
    shadow_fill=(0, 0, 0, 180),
    offset=(2, 2),
):
    """Draw crisp text with a subtle drop shadow for maximum readability."""
    x, y = pos
    dx, dy = offset
    draw.text((x + dx, y + dy), text, font=font, fill=shadow_fill)
    draw.text((x, y), text, font=font, fill=fill)


def _draw_rounded_badge(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    radius: int,
    fill_color: tuple[int, int, int],
    outline_color: tuple[int, int, int] | None = None,
):
    """Draw rounded rectangle pill badge."""
    draw.rounded_rectangle(xy, radius=radius, fill=fill_color, outline=outline_color, width=1)


def create_opening_frame(script: dict, out_path: str, bg_image: Image.Image | None = None) -> str:
    """Build the opening title card (Scene 1)."""
    tw, th = VIDEO_WIDTH, VIDEO_HEIGHT
    if bg_image:
        base = _create_cinematic_background(bg_image, (tw, th))
    else:
        base = Image.new("RGB", (tw, th), COLOR_PRIMARY_BG)

    frame = base.convert("RGBA")
    overlay = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Center card container
    card_w, card_h = 1040, 480
    cx1 = (tw - card_w) // 2
    cy1 = (th - card_h) // 2
    cx2 = cx1 + card_w
    cy2 = cy1 + card_h

    # Card background with glassmorphism dark tint
    draw.rounded_rectangle((cx1, cy1, cx2, cy2), radius=24, fill=(15, 20, 32, 225), outline=(255, 255, 255, 35), width=2)

    # Fonts
    font_badge = load_font(20)
    font_title = load_font(46)
    font_sub = load_font(26)
    font_price = load_font(30)

    # Top Category Pill
    prop_type = script.get("property_type", "EXCLUSIVE PROPERTY").upper()
    pill_text = f"  FEATURED LISTING  •  {prop_type}  "
    bbox = draw.textbbox((0, 0), pill_text, font=font_badge)
    pw = bbox[2] - bbox[0] + 20
    px1 = (tw - pw) // 2
    py1 = cy1 + 50
    _draw_rounded_badge(draw, (px1, py1, px1 + pw, py1 + 36), radius=18, fill_color=COLOR_BADGE_BG)
    draw.text((px1 + 10, py1 + 6), pill_text, font=font_badge, fill=COLOR_TEXT_PRIMARY)

    # Main Title (Property Name)
    prop_name = script.get("property_name", "Featured Property")
    _draw_text_with_shadow(draw, ((tw - draw.textlength(prop_name, font=font_title)) // 2, cy1 + 120), prop_name, font_title)

    # Golden Accent Line
    line_w = 260
    lx1 = (tw - line_w) // 2
    ly = cy1 + 205
    draw.line((lx1, ly, lx1 + line_w, ly), fill=COLOR_ACCENT, width=4)

    # Location
    loc = script.get("location", "")
    loc_text = f"📍 {loc}"
    _draw_text_with_shadow(draw, ((tw - draw.textlength(loc_text, font=font_sub)) // 2, cy1 + 235), loc_text, font_sub, fill=COLOR_TEXT_SECONDARY)

    # Price Pill
    price_str = script.get("price_line", "")
    bbox_p = draw.textbbox((0, 0), price_str, font=font_price)
    prw = bbox_p[2] - bbox_p[0] + 40
    prx1 = (tw - prw) // 2
    pry1 = cy1 + 320
    _draw_rounded_badge(draw, (prx1, pry1, prx1 + prw, pry1 + 58), radius=28, fill_color=COLOR_PRICE_BG, outline_color=(255, 255, 255, 60))
    draw.text((prx1 + 20, pry1 + 10), price_str, font=font_price, fill=COLOR_TEXT_PRIMARY)

    final_img = Image.alpha_composite(frame, overlay).convert("RGB")
    final_img.save(out_path, format="PNG")
    return out_path


def create_closing_frame(script: dict, out_path: str, bg_image: Image.Image | None = None) -> str:
    """Build the closing contact card (Outro Scene)."""
    tw, th = VIDEO_WIDTH, VIDEO_HEIGHT
    if bg_image:
        base = _create_cinematic_background(bg_image, (tw, th))
    else:
        base = Image.new("RGB", (tw, th), COLOR_PRIMARY_BG)

    frame = base.convert("RGBA")
    overlay = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Center card container
    card_w, card_h = 1040, 480
    cx1 = (tw - card_w) // 2
    cy1 = (th - card_h) // 2
    cx2 = cx1 + card_w
    cy2 = cy1 + card_h

    draw.rounded_rectangle((cx1, cy1, cx2, cy2), radius=24, fill=(15, 20, 32, 230), outline=(255, 255, 255, 35), width=2)

    font_head = load_font(42)
    font_subhead = load_font(24)
    font_contact = load_font(34)
    font_small = load_font(20)

    # Head
    h_text = "Schedule a Private Viewing"
    _draw_text_with_shadow(draw, ((tw - draw.textlength(h_text, font=font_head)) // 2, cy1 + 55), h_text, font_head, fill=COLOR_ACCENT)

    sub_text = "Don't miss the opportunity to make this dream property yours."
    _draw_text_with_shadow(draw, ((tw - draw.textlength(sub_text, font=font_subhead)) // 2, cy1 + 130), sub_text, font_subhead, fill=COLOR_TEXT_SECONDARY)

    # Contact Box
    contact_text = script.get("closing", "Contact Agent")
    bbox_c = draw.textbbox((0, 0), contact_text, font=font_contact)
    cw = min(card_w - 80, bbox_c[2] - bbox_c[0] + 60)
    cw = max(cw, 500)
    c_x1 = (tw - cw) // 2
    c_y1 = cy1 + 200
    _draw_rounded_badge(draw, (c_x1, c_y1, c_x1 + cw, c_y1 + 80), radius=16, fill_color=(25, 35, 55), outline_color=(255, 179, 0, 180))
    _draw_text_with_shadow(draw, ((tw - draw.textlength(contact_text, font=font_contact)) // 2, c_y1 + 20), contact_text, font_contact)

    # Footer note
    footer = f"{script.get('title', '')} • {script.get('price_line', '')}"
    _draw_text_with_shadow(draw, ((tw - draw.textlength(footer, font=font_small)) // 2, cy1 + 370), footer, font_small, fill=(180, 190, 205))

    final_img = Image.alpha_composite(frame, overlay).convert("RGB")
    final_img.save(out_path, format="PNG")
    return out_path


def compose_image_scene_frame(
    img: Image.Image,
    caption: str,
    price_text: str,
    scene_num: int,
    total_scenes: int,
    out_path: str,
) -> str:
    """
    Compose an individual property photograph into a 1280x720 video scene frame.
    - Preserves aspect ratio with blurred background fill
    - Adds lower third glassmorphism overlay bar with typography & price badge
    """
    tw, th = VIDEO_WIDTH, VIDEO_HEIGHT

    # 1. Background (Cinematic blurred fill)
    bg = _create_cinematic_background(img, (tw, th))

    # 2. Foreground Photo (Aspect-ratio fit)
    # Give some vertical margin for lower third and header
    fg = img.copy()
    fg.thumbnail((tw - 80, th - 120), Image.Resampling.LANCZOS)
    fw, fh = fg.size

    # Position photo centered
    paste_x = (tw - fw) // 2
    paste_y = max(20, (th - 110 - fh) // 2 + 10)

    # Paste foreground onto background
    bg.paste(fg, (paste_x, paste_y))

    # 3. Compositing overlay graphics
    frame = bg.convert("RGBA")
    overlay = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Fonts
    font_caption = load_font(28)
    font_price = load_font(22)
    font_index = load_font(18)

    # Lower Third Banner
    bar_h = 100
    bar_y = th - bar_h
    # Dark gradient-like background bar
    draw.rectangle((0, bar_y, tw, th), fill=COLOR_OVERLAY_BG)
    # Accent top border on lower third
    draw.line((0, bar_y, tw, bar_y), fill=(255, 179, 0, 190), width=3)

    # Left: Scene caption
    caption_clean = caption.strip()
    _draw_text_with_shadow(draw, (40, bar_y + 32), caption_clean, font_caption, fill=COLOR_TEXT_PRIMARY)

    # Right: Price Badge
    price_badge_text = price_text.strip()
    if price_badge_text:
        bbox_p = draw.textbbox((0, 0), price_badge_text, font=font_price)
        pw = bbox_p[2] - bbox_p[0] + 30
        px2 = tw - 40
        px1 = px2 - pw
        py1 = bar_y + 24
        py2 = py1 + 48
        _draw_rounded_badge(draw, (px1, py1, px2, py2), radius=12, fill_color=COLOR_PRICE_BG)
        draw.text((px1 + 15, py1 + 11), price_badge_text, font=font_price, fill=COLOR_TEXT_PRIMARY)

    # Top-right scene counter pill
    counter_text = f"Photo {scene_num} of {total_scenes}"
    bbox_c = draw.textbbox((0, 0), counter_text, font=font_index)
    cw = bbox_c[2] - bbox_c[0] + 24
    cx2 = tw - 24
    cx1 = cx2 - cw
    cy1 = 20
    cy2 = cy1 + 32
    draw.rounded_rectangle((cx1, cy1, cx2, cy2), radius=8, fill=(10, 15, 25, 200), outline=(255, 255, 255, 40), width=1)
    draw.text((cx1 + 12, cy1 + 6), counter_text, font=font_index, fill=COLOR_TEXT_SECONDARY)

    final_img = Image.alpha_composite(frame, overlay).convert("RGB")
    final_img.save(out_path, format="PNG")
    return out_path


def prepare_scene_frames(
    images: list,
    script: dict,
    temp_dir: str,
    size: tuple[int, int] = (VIDEO_WIDTH, VIDEO_HEIGHT),
) -> list[str]:
    """
    Prepare all video scene frames (Opening + Image Scenes + Closing).

    Args:
        images: List of uploaded files or file paths.
        script: Dictionary produced by generate_property_script.
        temp_dir: Directory where scene frames should be saved.
        size: Target video resolution.

    Returns:
        List of absolute file paths to PNG frames in sequential order.
    """
    frames_dir = Path(temp_dir) / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    frame_paths: list[str] = []
    num_images = len(images)

    # First decode first image to use as background for title & outro
    first_img = None
    if num_images > 0:
        try:
            first_img = _open_image_safely(images[0])
        except Exception as e:
            raise ImageProcessingError(f"Image 1 is unusable: {e}")

    # 1. Scene 0: Opening Title Card
    opening_path = str((frames_dir / "scene_00_opening.png").resolve())
    create_opening_frame(script, opening_path, bg_image=first_img)
    frame_paths.append(opening_path)

    # 2. Scenes 1 to N: Property Photo Frames
    captions = script.get("captions", [])
    price_text = script.get("price_line", "")

    for idx, img_input in enumerate(images, start=1):
        try:
            img = _open_image_safely(img_input)
        except Exception as exc:
            raise ImageProcessingError(f"Image {idx} is unusable: {exc}")

        caption = captions[idx - 1] if idx - 1 < len(captions) else f"Photo {idx}"
        scene_filename = f"scene_{idx:02d}.png"
        scene_path = str((frames_dir / scene_filename).resolve())

        compose_image_scene_frame(
            img=img,
            caption=caption,
            price_text=price_text,
            scene_num=idx,
            total_scenes=num_images,
            out_path=scene_path,
        )
        frame_paths.append(scene_path)

    # 3. Scene N+1: Closing Outro Card
    closing_path = str((frames_dir / f"scene_{num_images + 1:02d}_closing.png").resolve())
    create_closing_frame(script, closing_path, bg_image=first_img)
    frame_paths.append(closing_path)

    return frame_paths
