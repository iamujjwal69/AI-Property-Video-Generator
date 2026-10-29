"""
Optional narration generator using Google Text-to-Speech (gTTS).
Designed to fail gracefully: if network fails, audio generation is skipped
without interrupting video rendering.
"""

from pathlib import Path


def build_narration(
    narration_text: str,
    out_path: str,
    enabled: bool = True,
    lang: str = "en",
) -> tuple[str | None, str | None]:
    """
    Synthesize narration audio into an MP3 file via gTTS.

    Args:
        narration_text: Text to speak.
        out_path: Destination path for .mp3.
        enabled: If False, returns immediately without attempting generation.
        lang: Language code (default 'en').

    Returns:
        tuple (mp3_path or None, warning_message or None)
        Never raises exceptions; all network and I/O failures return friendly warnings.
    """
    if not enabled:
        return None, None

    if not narration_text or not narration_text.strip():
        return None, "Narration text was empty; rendering video without voiceover."

    try:
        from gtts import gTTS  # Lazy import
    except ImportError:
        return None, "gTTS package is not installed; continuing with silent video."

    try:
        out_file = Path(out_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)

        tts = gTTS(text=narration_text.strip(), lang=lang, slow=False)
        tts.save(str(out_file))

        if out_file.exists() and out_file.stat().st_size > 0:
            return str(out_file.resolve()), None
        else:
            return None, "Audio file was created but appears empty. Continuing without audio."

    except Exception as exc:
        # Gracefully handle network timeouts, HTTP errors, DNS errors, etc.
        warning = (
            f"Narration generation was skipped due to network/gTTS issue ({exc}). "
            "Video will render silently."
        )
        return None, warning
