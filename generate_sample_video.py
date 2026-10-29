"""
CLI verification script to generate a sample property MP4 from sample_data/property.json
and sample_images/. Ensures complete end-to-end functionality.
"""

import json
import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Force UTF-8 on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.config import OUTPUT_DIR, SAMPLE_DATA_DIR, SAMPLE_IMAGES_DIR
from src.image_processor import prepare_scene_frames
from src.narration import build_narration
from src.script_generator import generate_property_script
from src.utils import cleanup_paths, ensure_directories, make_temp_dir, timestamped_filename
from src.validators import validate_property_data
from src.video_generator import create_video


def run_sample_generation():
    print("=" * 60)
    print("AI Property Video Generator -- Pipeline Verification")
    print("=" * 60)

    ensure_directories()

    # 1. Load sample property data
    json_path = SAMPLE_DATA_DIR / "property.json"
    with open(json_path, "r", encoding="utf-8") as f:
        property_data = json.load(f)
    print(f"[OK] Loaded property data from {json_path.name}: {property_data['property_name']}")

    # 2. Gather sample images
    image_files = sorted(list(SAMPLE_IMAGES_DIR.glob("*.jpg")) + list(SAMPLE_IMAGES_DIR.glob("*.png")))
    print(f"[OK] Found {len(image_files)} sample images in {SAMPLE_IMAGES_DIR.name}")

    # 3. Validate
    is_valid, errors = validate_property_data(property_data, image_files)
    if not is_valid:
        print("[FAIL] Validation failed:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    print("[OK] Validation passed with 0 errors")

    # 4. Generate Script Bundle
    script = generate_property_script(property_data, image_count=len(image_files))
    print("[OK] Generated deterministic script bundle:")
    print(f"    Title: {script['title']}")
    print(f"    Scenes: {len(script['durations'])} (Durations: {script['durations']})")
    print(f"    Expected Total Duration: {script['total_duration']}s")
    print(f"    Narration: {script['narration']}")

    # 5. Prepare Frames in Temp Directory
    temp_dir = make_temp_dir()
    created_temp_files = []

    try:
        print(f"[...] Composing scene frames in Pillow ({temp_dir})...")
        frame_paths = prepare_scene_frames(image_files, script, temp_dir)
        created_temp_files.extend(frame_paths)
        print(f"[OK] Successfully composed {len(frame_paths)} frames:")
        for p in frame_paths:
            print(f"    - {Path(p).name}")

        # 6. Optional Narration
        narration_mp3_path = str(Path(temp_dir) / "narration.mp3")
        print("[...] Synthesizing optional narration audio...")
        mp3_path, warning = build_narration(script["narration"], narration_mp3_path, enabled=True)
        if mp3_path:
            created_temp_files.append(mp3_path)
            print(f"[OK] Narration MP3 ready: {Path(mp3_path).name} ({Path(mp3_path).stat().st_size} bytes)")
        else:
            print(f"[!] Narration skipped/warned: {warning}")

        # 7. Assemble Video
        out_filename = timestamped_filename("sample_property_video", "mp4")
        out_path = str((OUTPUT_DIR / out_filename).resolve())
        print(f"[...] Rendering MP4 video with MoviePy -> {out_filename}...")

        final_video_path = create_video(
            frame_paths=frame_paths,
            durations=script["durations"],
            audio_path=mp3_path,
            output_path=out_path,
        )

        size_mb = Path(final_video_path).stat().st_size / (1024 * 1024)
        print("[SUCCESS] VIDEO GENERATION SUCCESSFUL!")
        print(f"    File: {final_video_path}")
        print(f"    Size: {size_mb:.2f} MB")
        return final_video_path

    finally:
        print("[...] Running cleanup for temporary frame files...")
        cleanup_paths(created_temp_files)
        cleanup_paths([temp_dir])
        print("[OK] Cleanup complete. Temp frames removed.")


if __name__ == "__main__":
    run_sample_generation()
