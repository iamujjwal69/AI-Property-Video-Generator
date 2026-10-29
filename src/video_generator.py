"""
Video assembly and export module using MoviePy and FFmpeg.
Assembles still image frames into a seamless video with fade transitions and optional audio.
Compatible with both MoviePy 1.x and MoviePy 2.x.
"""

import shutil
from pathlib import Path
from src.config import (
    AUDIO_CODEC,
    FADE_DURATION,
    FPS,
    VIDEO_CODEC,
    VIDEO_HEIGHT,
    VIDEO_WIDTH,
)


class VideoGenerationError(Exception):
    """Raised when video rendering or MP4 export fails."""
    pass


def check_ffmpeg_available() -> tuple[bool, str]:
    """Check if FFmpeg is available via PATH or imageio-ffmpeg."""
    # Check system PATH
    sys_ffmpeg = shutil.which("ffmpeg")
    if sys_ffmpeg:
        return True, f"Found system FFmpeg at {sys_ffmpeg}"

    # Check imageio-ffmpeg
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        if ffmpeg_exe and Path(ffmpeg_exe).exists():
            return True, f"Found imageio-ffmpeg binary at {ffmpeg_exe}"
    except Exception:
        pass

    return False, "FFmpeg was not found on PATH and imageio-ffmpeg is unavailable."


def _apply_duration_and_fade(clip, duration: float, fade_sec: float = FADE_DURATION):
    """
    Set duration and fade effects adaptively for MoviePy 1.x or 2.x.
    """
    # 1. Set duration
    if hasattr(clip, "with_duration"):
        # MoviePy 2.x
        c = clip.with_duration(duration)
    elif hasattr(clip, "set_duration"):
        # MoviePy 1.x
        c = clip.set_duration(duration)
    else:
        c = clip

    # 2. Set fades if duration is long enough
    if duration > fade_sec * 2:
        try:
            # Check MoviePy 2.x vfx
            from moviepy import vfx
            if hasattr(vfx, "FadeIn") and hasattr(c, "with_effects"):
                c = c.with_effects([vfx.FadeIn(fade_sec), vfx.FadeOut(fade_sec)])
                return c
        except Exception:
            pass

        try:
            # MoviePy 1.x methods
            if hasattr(c, "fadein") and hasattr(c, "fadeout"):
                c = c.fadein(fade_sec).fadeout(fade_sec)
                return c
        except Exception:
            pass

        try:
            # MoviePy 1.x fx imports
            from moviepy.video.fx.all import fadein, fadeout
            c = fadein(c, fade_sec)
            c = fadeout(c, fade_sec)
            return c
        except Exception:
            pass

    return c


def create_video(
    frame_paths: list[str],
    durations: list[float],
    audio_path: str | None,
    output_path: str,
    fps: int = FPS,
    size: tuple[int, int] = (VIDEO_WIDTH, VIDEO_HEIGHT),
) -> str:
    """
    Build the MP4 video from ordered frame paths.

    Args:
        frame_paths: Ordered list of frame PNG file paths.
        durations: Per-frame duration in seconds.
        audio_path: Optional path to narration .mp3.
        output_path: Destination path for .mp4.
        fps: Target frames per second.
        size: Target video resolution.

    Returns:
        str: Absolute path to the generated MP4.

    Raises:
        VideoGenerationError: If rendering or encoding fails.
    """
    if not frame_paths:
        raise VideoGenerationError("Cannot create video: No frame paths provided.")

    if len(frame_paths) != len(durations):
        raise VideoGenerationError(
            f"Frame count ({len(frame_paths)}) does not match duration count ({len(durations)})."
        )

    # Validate output path writable
    out_file = Path(output_path).resolve()
    try:
        out_file.parent.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        raise VideoGenerationError(
            f"Cannot create output directory '{out_file.parent}': {exc}"
        ) from exc

    # Import MoviePy based on installed version
    try:
        try:
            from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips
        except ImportError:
            from moviepy import AudioFileClip, ImageClip, concatenate_videoclips
    except ImportError as e:
        raise VideoGenerationError(
            f"MoviePy is not installed or importable: {e}. Run 'pip install moviepy'."
        ) from e

    clips = []
    audio_clip = None
    final_video = None

    try:
        # Build individual clips
        for idx, (frame_path, dur) in enumerate(zip(frame_paths, durations)):
            if not Path(frame_path).exists():
                raise VideoGenerationError(f"Frame file not found: {frame_path}")

            clip = ImageClip(str(frame_path))
            clip = _apply_duration_and_fade(clip, dur)
            clips.append(clip)

        # Concatenate scenes
        final_video = concatenate_videoclips(clips, method="compose")
        total_duration = sum(durations)

        # Attach audio if present
        if audio_path and Path(audio_path).exists() and Path(audio_path).stat().st_size > 0:
            try:
                audio_clip = AudioFileClip(str(audio_path))
                # Subclip audio if it exceeds video duration
                if audio_clip.duration > total_duration:
                    if hasattr(audio_clip, "subclipped"):
                        audio_clip = audio_clip.subclipped(0, total_duration)
                    elif hasattr(audio_clip, "subclip"):
                        audio_clip = audio_clip.subclip(0, total_duration)

                # Attach audio
                if hasattr(final_video, "with_audio"):
                    final_video = final_video.with_audio(audio_clip)
                elif hasattr(final_video, "set_audio"):
                    final_video = final_video.set_audio(audio_clip)
            except Exception as audio_err:
                # If audio attachment fails, don't abort video generation
                pass

        # Export video file
        save_video(final_video, str(out_file), fps=fps)

        if not out_file.exists() or out_file.stat().st_size == 0:
            raise VideoGenerationError(
                f"Export completed, but output MP4 file '{out_file}' is missing or empty."
            )

        return str(out_file)

    except VideoGenerationError:
        raise
    except Exception as exc:
        has_ffmpeg, ffmpeg_info = check_ffmpeg_available()
        tip = ""
        if not has_ffmpeg:
            tip = " Hint: FFmpeg may not be installed or reachable. Ensure FFmpeg or imageio-ffmpeg is installed."
        raise VideoGenerationError(
            f"Video rendering failed ({type(exc).__name__}: {exc}).{tip}"
        ) from exc

    finally:
        # Ensure all resources are closed
        if audio_clip is not None:
            try:
                audio_clip.close()
            except Exception:
                pass
        for c in clips:
            try:
                c.close()
            except Exception:
                pass
        if final_video is not None:
            try:
                final_video.close()
            except Exception:
                pass


def save_video(clip, output_path: str, fps: int = FPS) -> str:
    """Thin wrapper around write_videofile ensuring safe parameters and lightweight CPU usage."""
    clip.write_videofile(
        output_path,
        codec=VIDEO_CODEC,
        audio_codec=AUDIO_CODEC,
        fps=fps,
        preset="ultrafast",  # Drastically reduces CPU rendering time on cloud containers
        threads=1,           # Prevents spiking multiple shared vCPUs
        logger=None,         # Clean non-spammy stdout
    )
    return output_path
