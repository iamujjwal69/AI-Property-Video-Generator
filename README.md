# AI Property Video Generator

> **Architecture & Transparency Notice:** "AI" in this project refers strictly to deterministic, rule-based template synthesis and algorithmic scene assembly. **No generative AI model (such as OpenAI, Claude, or Midjourney) or paid API is used.** Captions, scene durations, and narration text are produced directly and predictably from the facts typed by the user, guaranteeing zero hallucinations, complete data privacy, and deterministic output.

---

## 1. What It Does

The **AI Property Video Generator** is a single-process, modular Python monolith that converts property details and 4–8 photographs into a high-definition (1280×720, 24 fps), promotional real estate MP4 video (20–30 seconds in duration) with on-screen lower-third captions, price badges, intro/outro cards, smooth transitions, and optional audio voiceover narration.

---

## 2. Key Features

- **Streamlit Web UI:** Form input, instant sample auto-fill, real-time image validation, progress tracking, in-browser video playback, and one-click MP4 download.
- **Strict Input Validation:** Gatekeeper validation enforcing required fields, lenient currency regex matching, image count boundaries (4–8 images), file formats (`jpg`, `jpeg`, `png`, `webp`), and minimum image dimensions (400×300 px).
- **Rule-Based Script Generator:** Deterministic caption generation cycling through property features, computing optimal scene durations to keep the total video duration strictly between 20 and 30 seconds.
- **Pillow Still Frame Composition:** Composes full 1280×720 still frames with high-contrast typography, frosted glassmorphism overlays, and blurred background letterbox fills before feeding into MoviePy. **Eliminates ImageMagick dependencies entirely.**
- **MoviePy Video Timeline Assembly:** Applies timed fades (`0.4s` crossfades), stitches scenes, muxes optional audio, and exports H.264 / AAC MP4 files.
- **Graceful Narration Fallback:** Narration via Google Text-to-Speech (`gTTS`) is optional and fails gracefully—if internet is disconnected or unavailable, a friendly warning is displayed and the video renders silently without crashing.
- **Automatic Cleanup:** Temporary scene PNG frames and intermediate audio are guaranteed to be cleaned up after export.

---

## 3. Tech Stack

- **Language:** Python 3.10 – 3.12 (tested on 3.12)
- **Frontend / Application Server:** Streamlit 1.36+
- **Image Processing & Typography:** Pillow (PIL) 10.4+ / 11.x
- **Video Assembly:** MoviePy 1.0.3 / 2.x
- **Video Encoding:** FFmpeg (via `imageio-ffmpeg` or system FFmpeg)
- **Voiceover Narration:** gTTS (Google Text-to-Speech) 2.5+
- **Unit Testing:** Pytest

---

## 4. Prerequisites

1. **Python 3.10 – 3.12** installed on your system.
2. **FFmpeg**: Automatically provided via `imageio-ffmpeg` (included in `requirements.txt`), or system FFmpeg installed on your PATH (`ffmpeg -version`).

---

## 5. Installation

```bash
# 1. Clone or navigate to the repository
cd AI-Property-Video-Generator

# 2. Create a virtual environment
python -m venv .venv

# 3. Activate the virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Windows (Command Prompt):
.venv\Scripts\activate.bat
# Linux / macOS:
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
```

---

## 6. How to Run

### Streamlit Web Application (Primary Interface)

```bash
streamlit run app.py
```
Open your browser to [http://localhost:8501](http://localhost:8501).

### CLI End-to-End Pipeline Verification

To test the entire pipeline headlessly from the command line:

```bash
python generate_sample_video.py
```
This reads `sample_data/property.json`, processes the 5 bundled photos in `sample_images/`, generates the narration, renders the MP4, and outputs the result to `output/`.

### Run Unit Tests

```bash
pytest tests/ -v
```

---

## 7. User Guide (Streamlit UI)

1. **Quick Test (One-Click):**
   - In the sidebar, click **"✨ Load Sample Property Data"**.
   - Check the **"Use 5 Bundled Sample Images"** checkbox.
   - Click **"🎬 Generate Property Video"**.
2. **Custom Listing:**
   - Enter Property Name, Location, Price, Property Type, Key Features, and Contact CTA.
   - Upload 4 to 8 photos (`.jpg`, `.png`, `.webp`).
   - Toggle voiceover narration on or off.
   - Click **Generate Property Video**.
3. **Preview & Download:**
   - Watch the rendered promotional video in the built-in video player.
   - Click **"⬇️ Download MP4 Promotional Video"** to save the file locally.

---

## 8. Project Directory Structure

```
AI-Property-Video-Generator/
│
├── app.py                     # Streamlit web entry point (form, preview, download)
├── generate_sample_video.py   # CLI verification script for headless MP4 generation
├── requirements.txt           # Pinned Python package dependencies
├── README.md                  # Complete documentation and user guide
├── .gitignore                 # Excludes temp files, venv, and large MP4 outputs
│
├── src/
│   ├── __init__.py            # Python package declaration
│   ├── config.py              # Constants: 1280x720, 24fps, durations, palettes
│   ├── validators.py          # Form field and image integrity validation
│   ├── script_generator.py    # Deterministic rule-based caption & timing generator
│   ├── image_processor.py     # Pillow composition: blurred padding, badges, lower thirds
│   ├── narration.py           # Optional gTTS voiceover with silent fallback
│   ├── video_generator.py     # MoviePy stitching, fade transitions, and H.264 export
│   └── utils.py               # Temp dirs, path cleanup, font loaders, filename utilities
│
├── assets/
│   └── font.ttf               # Bundled TrueType font for deterministic text rendering
│
├── sample_data/
│   └── property.json          # Synthetic real estate listing facts for testing
│
├── sample_images/             # 5 synthetic high-resolution property images
│   ├── 01_exterior.jpg
│   ├── 02_living_room.jpg
│   ├── 03_kitchen.jpg
│   ├── 04_master_bedroom.jpg
│   └── 05_balcony_view.jpg
│
├── tests/
│   └── test_pipeline.py       # Automated unit tests for validation and scripts
│
├── temp/                      # Isolated runtime temp directory (auto-cleaned)
└── output/                    # Final rendered MP4 deliverables
    └── sample_property_video_*.mp4
```

---

## 9. Sample Data & Expected Output

### Input (`sample_data/property.json`):
```json
{
  "property_name": "Sunrise Residency",
  "location": "Whitefield, Bengaluru",
  "price": "INR 85,00,000",
  "property_type": "3 BHK Apartment",
  "key_features": "Covered parking, 24x7 security, children's play area, clubhouse",
  "contact_info": "Call 98765 43210 to schedule a site visit"
}
```

### Generated Scenes Timeline:

| Scene | Type | Content / Overlay | Duration |
|---|---|---|---|
| 1 | Opening Card | `Sunrise Residency — Whitefield, Bengaluru` · Price Badge | 3.0 s |
| 2 | Photo 1 | Exterior · `3 BHK Apartment · Covered parking` · Price Badge | 3.4 s |
| 3 | Photo 2 | Living Room · `3 BHK Apartment · 24x7 security` · Price Badge | 3.4 s |
| 4 | Photo 3 | Kitchen · `3 BHK Apartment · children's play area` · Price Badge | 3.4 s |
| 5 | Photo 4 | Bedroom · `3 BHK Apartment · clubhouse` · Price Badge | 3.4 s |
| 6 | Photo 5 | Balcony · `3 BHK Apartment · Covered parking` · Price Badge | 3.4 s |
| 7 | Closing Card | `Schedule a Private Viewing` · Contact Details & Summary | 4.0 s |

**Total Duration:** **24.0 seconds** (strictly compliant with the 20–30s requirement).

---

## 10. Known Limitations

1. **Rule-Based Captions:** Captions cycle through user-entered features; they do not perform deep visual scene understanding of individual photo rooms.
2. **Network Dependency for Narration:** gTTS relies on Google's public TTS endpoint. If no internet connection is active, voiceover is skipped and the video renders silently with a non-blocking notification.
3. **Single Process Monolith:** Designed for local single-user execution; concurrent multi-user rendering would benefit from a task queue (e.g. Celery / Redis) in production.

---

## 11. Troubleshooting

- **FFmpeg Not Found:**
  - `imageio-ffmpeg` is installed automatically and provides a static binary. If MoviePy cannot find it, install FFmpeg on your system (`winget install Gyan.FFmpeg` on Windows, or `brew install ffmpeg` on macOS) and ensure it is on your `PATH`.
- **ImageMagick Missing Error:**
  - This project **does not require ImageMagick**. All text and graphical overlays are composed using Pillow directly into PNG frames. If you encounter an ImageMagick error, ensure you are running `app.py` or `generate_sample_video.py` from this repository.
- **Narration Skipped Warning:**
  - This indicates a temporary network outage or timeout reaching the gTTS server. The video will still be generated cleanly without audio.

---

## 12. Libraries and External Services Used

- **Streamlit** (Web application framework)
- **MoviePy** (Video editing and composition)
- **Pillow** (Image manipulation and typography rendering)
- **imageio-ffmpeg** (H.264 / AAC encoding)
- **gTTS** (Optional free text-to-speech service)
- **No paid APIs, subscriptions, or external cloud accounts are required.**
