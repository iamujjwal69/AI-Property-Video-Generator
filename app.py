"""
AI Property Video Generator - Streamlit Application
A modular, single-process Python monolith converting real estate facts
and photos into promotional MP4 videos.
"""

import io
import json
import os
import sys
from pathlib import Path
import streamlit as st

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (
    ALLOWED_EXTENSIONS,
    MAX_IMAGE_COUNT,
    MIN_IMAGE_COUNT,
    OUTPUT_DIR,
    SAMPLE_DATA_DIR,
    SAMPLE_IMAGES_DIR,
    VIDEO_HEIGHT,
    VIDEO_WIDTH,
)
from src.image_processor import ImageProcessingError, prepare_scene_frames
from src.narration import build_narration
from src.script_generator import generate_property_script
from src.utils import cleanup_paths, ensure_directories, make_temp_dir, timestamped_filename
from src.validators import validate_property_data
from src.video_generator import VideoGenerationError, check_ffmpeg_available, create_video

# Streamlit Page Configuration
st.set_page_config(
    page_title="AI Property Video Generator",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom High-End Styling (Vanilla CSS)
st.markdown(
    """
    <style>
    /* Global Styles */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .main-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        padding: 2.2rem 2.5rem;
        border-radius: 16px;
        color: #FFFFFF;
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        background: linear-gradient(90deg, #FFFFFF 0%, #F59E0B 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .main-header p {
        margin: 0.6rem 0 0 0;
        font-size: 1.05rem;
        color: #94A3B8;
    }

    .notice-card {
        background: rgba(30, 41, 59, 0.7);
        border-left: 4px solid #F59E0B;
        padding: 1rem 1.4rem;
        border-radius: 8px;
        margin-bottom: 1.8rem;
        font-size: 0.92rem;
        color: #CBD5E1;
        line-height: 1.5;
    }

    .stats-card {
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
    }
    
    .stats-card .stat-val {
        font-size: 1.8rem;
        font-weight: 700;
        color: #F59E0B;
    }
    
    .stats-card .stat-label {
        font-size: 0.85rem;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def load_sample_json():
    """Load sample property data from sample_data/property.json."""
    json_path = SAMPLE_DATA_DIR / "property.json"
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "property_name": "Sunrise Residency",
        "location": "Whitefield, Bengaluru",
        "price": "INR 85,00,000",
        "property_type": "3 BHK Apartment",
        "key_features": "Covered parking, 24x7 security, children's play area, clubhouse",
        "contact_info": "Call 98765 43210 to schedule a site visit",
    }


def get_sample_image_files():
    """Get list of sample images from sample_images/ directory."""
    if SAMPLE_IMAGES_DIR.exists():
        files = sorted(
            list(SAMPLE_IMAGES_DIR.glob("*.jpg"))
            + list(SAMPLE_IMAGES_DIR.glob("*.jpeg"))
            + list(SAMPLE_IMAGES_DIR.glob("*.png"))
        )
        return files
    return []


def main():
    ensure_directories()

    # Session State Initialization for Sample Data
    if "form_data" not in st.session_state:
        st.session_state.form_data = {
            "property_name": "",
            "location": "",
            "price": "",
            "property_type": "Apartment / Flat",
            "key_features": "",
            "contact_info": "",
        }
    if "use_sample_images" not in st.session_state:
        st.session_state.use_sample_images = False

    # Header Banner
    st.markdown(
        """
        <div class="main-header">
            <h1>🏡 AI Property Video Generator</h1>
            <p>Generate professional 720p real estate promotional videos with deterministic templates, cinematic transitions, and optional voiceover.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Architectural Honesty Notice
    st.markdown(
        """
        <div class="notice-card">
            <strong>ℹ️ Deterministic Template Notice:</strong> This application generates video captions and narration using 
            <strong>rule-based templates</strong> derived solely from user-entered facts. No generative AI or external LLM is invoked, 
            guaranteeing zero hallucinations, predictable durations, and complete local privacy.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Sidebar Information & Quick Setup
    with st.sidebar:
        st.header("⚙️ Configuration & Quick Fill")
        st.markdown("Use presets to test the pipeline immediately.")

        if st.button("✨ Load Sample Property Data", use_container_width=True):
            sample = load_sample_json()
            st.session_state.form_data.update(sample)
            st.session_state.use_sample_images = True
            st.rerun()

        if st.button("🔄 Reset Form", use_container_width=True):
            st.session_state.form_data = {
                "property_name": "",
                "location": "",
                "price": "",
                "property_type": "Apartment / Flat",
                "key_features": "",
                "contact_info": "",
            }
            st.session_state.use_sample_images = False
            st.rerun()

        st.divider()

        # System Diagnostics
        st.subheader("System Health")
        has_ffmpeg, ffmpeg_info = check_ffmpeg_available()
        if has_ffmpeg:
            st.success(f"FFmpeg: Detected", icon="✅")
        else:
            st.warning("FFmpeg not found on PATH. Ensure imageio-ffmpeg is installed.", icon="⚠️")

        st.divider()
        st.markdown(
            """
            **Video Specifications:**
            - **Resolution:** 1280 × 720 (HD 16:9)
            - **Frame Rate:** 24 fps
            - **Duration:** 20 – 30 seconds
            - **Output Format:** MP4 (H.264 / AAC)
            - **Image Range:** 4 to 8 photos
            """
        )

    # Main Grid: Left = Form Inputs, Right = Preview & Details
    col_form, col_preview = st.columns([1.1, 0.9], gap="large")

    with col_form:
        st.subheader("1. Property Details")

        with st.form("property_form"):
            prop_name = st.text_input(
                "Property Name *",
                value=st.session_state.form_data.get("property_name", ""),
                placeholder="e.g. Sunrise Residency, Oakwood Villa",
                help="The official marketing name of the property.",
            )

            col_loc, col_price = st.columns(2)
            with col_loc:
                location = st.text_input(
                    "Location / Address *",
                    value=st.session_state.form_data.get("location", ""),
                    placeholder="e.g. Whitefield, Bengaluru",
                )
            with col_price:
                price = st.text_input(
                    "Price *",
                    value=st.session_state.form_data.get("price", ""),
                    placeholder="e.g. INR 85,00,000 or $450,000",
                )

            property_type = st.selectbox(
                "Property Type *",
                options=[
                    "3 BHK Apartment",
                    "2 BHK Luxury Flat",
                    "Independent Villa",
                    "Penthouse Suite",
                    "Residential Studio",
                    "Commercial Office Space",
                    "Plot / Land Parcel",
                ],
                index=0 if not st.session_state.form_data.get("property_type") else [
                    "3 BHK Apartment",
                    "2 BHK Luxury Flat",
                    "Independent Villa",
                    "Penthouse Suite",
                    "Residential Studio",
                    "Commercial Office Space",
                    "Plot / Land Parcel",
                ].index(st.session_state.form_data.get("property_type")) if st.session_state.form_data.get("property_type") in [
                    "3 BHK Apartment",
                    "2 BHK Luxury Flat",
                    "Independent Villa",
                    "Penthouse Suite",
                    "Residential Studio",
                    "Commercial Office Space",
                    "Plot / Land Parcel",
                ] else 0,
            )

            key_features = st.text_area(
                "Key Features & Amenities (comma-separated)",
                value=st.session_state.form_data.get("key_features", ""),
                placeholder="e.g. Covered parking, 24x7 security, children's play area, clubhouse",
                help="Each feature will be paired with an uploaded photograph caption.",
            )

            contact_info = st.text_input(
                "Contact Information / Call to Action *",
                value=st.session_state.form_data.get("contact_info", ""),
                placeholder="e.g. Call 98765 43210 to schedule a site visit",
            )

            st.subheader("2. Property Photographs (4 to 8 required)")

            # Checkbox to use sample images
            use_samples = st.checkbox(
                "Use 5 Bundled Sample Images (from sample_images/)",
                value=st.session_state.use_sample_images,
                help="Convenient option to test generation without uploading your own images.",
            )

            uploaded_files = st.file_uploader(
                "Upload Property Photos (JPG, PNG, WebP)",
                type=list(ALLOWED_EXTENSIONS),
                accept_multiple_files=True,
                disabled=use_samples,
                help="Upload between 4 and 8 landscape or portrait photos.",
            )

            st.subheader("3. Audio & Narration Options")
            enable_narration = st.toggle(
                "Enable Voiceover Narration (gTTS)",
                value=True,
                help="Requires internet access for synthesis. If internet is unavailable, video renders silently.",
            )

            submit_button = st.form_submit_button(
                "🎬 Generate Property Video",
                type="primary",
                use_container_width=True,
            )

    # Process Form Submission
    if submit_button:
        # Resolve images list
        images_to_process = []
        if use_samples:
            sample_files = get_sample_image_files()
            if len(sample_files) < MIN_IMAGE_COUNT:
                st.error(f"Sample images folder has {len(sample_files)} images. At least 4 required.")
                st.stop()
            images_to_process = sample_files
        else:
            images_to_process = uploaded_files or []

        form_data = {
            "property_name": prop_name,
            "location": location,
            "price": price,
            "property_type": property_type,
            "key_features": key_features,
            "contact_info": contact_info,
        }

        # Step 1: Input Validation
        with st.spinner("Validating property facts and photos..."):
            is_valid, errors = validate_property_data(form_data, images_to_process)

        if not is_valid:
            with col_preview:
                st.error("### ⚠️ Validation Errors")
                st.markdown("Please correct the following issues to proceed:")
                for err in errors:
                    st.markdown(f"- **{err}**")
            st.stop()

        # Step 2: Script Generation
        with col_preview:
            status_container = st.container()
            progress_bar = st.progress(0.1, text="Analyzing facts & generating script templates...")

            script = generate_property_script(form_data, image_count=len(images_to_process))

            # Display Script Preview
            with st.expander("📋 Review Deterministic Script & Timings", expanded=False):
                st.json({
                    "Title Scene": script["title"],
                    "Captions": script["captions"],
                    "Price Strip": script["price_line"],
                    "Outro CTA": script["closing"],
                    "Narration Voiceover": script["narration"],
                    "Scene Durations (s)": script["durations"],
                    "Total Estimated Length": f"{script['total_duration']} seconds",
                })

            # Create isolated temp workspace for this run
            temp_dir = make_temp_dir()
            temp_files_to_clean = []

            try:
                # Step 3: Image Processing with Pillow
                progress_bar.progress(0.3, text=f"Composing 1280x720 frames for {len(images_to_process)} photos...")
                try:
                    frame_paths = prepare_scene_frames(images_to_process, script, temp_dir)
                    temp_files_to_clean.extend(frame_paths)
                except ImageProcessingError as img_err:
                    st.error(f"❌ Image Processing Error: {img_err}")
                    st.stop()

                # Step 4: Optional Audio Narration
                mp3_path = None
                if enable_narration:
                    progress_bar.progress(0.55, text="Synthesizing narration audio via gTTS...")
                    narration_out = str(Path(temp_dir) / "narration.mp3")
                    mp3_path, warn_msg = build_narration(script["narration"], narration_out, enabled=True)
                    if warn_msg:
                        st.warning(warn_msg, icon="⚠️")
                    if mp3_path:
                        temp_files_to_clean.append(mp3_path)

                # Step 5: MoviePy Assembly
                progress_bar.progress(0.75, text="Stitching scenes, fades, and encoding MP4 video...")
                out_filename = timestamped_filename("property_video", "mp4")
                final_out_path = str((OUTPUT_DIR / out_filename).resolve())

                try:
                    video_path = create_video(
                        frame_paths=frame_paths,
                        durations=script["durations"],
                        audio_path=mp3_path,
                        output_path=final_out_path,
                    )
                except VideoGenerationError as vid_err:
                    st.error(f"❌ Video Generation Failed: {vid_err}")
                    st.info("Tip: Ensure FFmpeg is available and disk permissions are granted.")
                    st.stop()

                progress_bar.progress(1.0, text="Video rendered successfully! 🎉")

                # Step 6: Presentation & Download
                st.success("### 🎉 Property Video Ready!")

                # Video Player
                st.video(video_path)

                # Video Metrics
                file_size_mb = Path(video_path).stat().st_size / (1024 * 1024)
                m1, m2, m3 = st.columns(3)
                with m1:
                    st.metric("Resolution", "1280 × 720 (HD)")
                with m2:
                    st.metric("Duration", f"{script['total_duration']:.1f} s")
                with m3:
                    st.metric("File Size", f"{file_size_mb:.2f} MB")

                # Download Button
                with open(video_path, "rb") as vf:
                    video_bytes = vf.read()

                st.download_button(
                    label="⬇️ Download MP4 Promotional Video",
                    data=video_bytes,
                    file_name=out_filename,
                    mime="video/mp4",
                    type="primary",
                    use_container_width=True,
                )

            finally:
                # Cleanup temporary frame images and intermediate mp3
                cleanup_paths(temp_files_to_clean)
                cleanup_paths([temp_dir])

    else:
        # Default preview column state
        with col_preview:
            st.subheader("Video Preview & Deliverables")
            st.info("Fill out the property details and upload photos on the left, then click **Generate Property Video**.")

            # Check if any videos already exist in output/
            existing_videos = sorted(
                list(OUTPUT_DIR.glob("*.mp4")),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            if existing_videos:
                latest = existing_videos[0]
                st.markdown(f"**Latest Rendered Video:** `{latest.name}`")
                st.video(str(latest))
                with open(latest, "rb") as f:
                    st.download_button(
                        label=f"⬇️ Download {latest.name}",
                        data=f.read(),
                        file_name=latest.name,
                        mime="video/mp4",
                        use_container_width=True,
                    )


if __name__ == "__main__":
    main()
