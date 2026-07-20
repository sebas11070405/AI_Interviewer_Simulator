"""
Voice delivery analysis.
Extracts pitch, speech rate, pauses, and volume variation from an audio file
using librosa, then translates the raw numbers into plain-language feedback.

This is NOT a clinical or diagnostic tool — it gives rough, encouraging
signal about delivery style, not a judgment about the person's emotional state.
"""

import librosa
import numpy as np


def analyze_voice_delivery(audio_path: str) -> dict:
    """
    Analyze an audio file and return delivery metrics + a plain-language summary.

    Returns:
        {
            "pitch_variation": float,      # standard deviation of pitch (Hz)
            "avg_volume": float,           # average RMS energy
            "volume_variation": float,     # standard deviation of RMS energy
            "speech_rate_label": str,      # "slow" | "moderate" | "fast"
            "pause_count": int,            # number of detected silences > 0.5s
            "pause_ratio": float,          # fraction of total time spent paused
            "summary": str,                # one-line plain-language takeaway
            "tips": list[str],             # 1-2 actionable suggestions
        }
    """
    y, sr = librosa.load(audio_path, sr=None)
    duration = librosa.get_duration(y=y, sr=sr)

    if duration < 1.0:
        return _empty_result("Recording too short to analyze.")

    # --- Pitch (fundamental frequency) ---
    f0, voiced_flag, _ = librosa.pyin(
        y, fmin=librosa.note_to_hz("C2"), fmax=librosa.note_to_hz("C7")
    )
    voiced_f0 = f0[voiced_flag] if voiced_flag is not None else np.array([])
    pitch_variation = float(np.std(voiced_f0)) if len(voiced_f0) > 0 else 0.0

    # --- Volume (RMS energy) ---
    rms = librosa.feature.rms(y=y)[0]
    avg_volume = float(np.mean(rms))
    volume_variation = float(np.std(rms))

    # --- Pauses (silence detection) ---
    intervals = librosa.effects.split(y, top_db=30)  # non-silent regions
    speech_duration = sum((end - start) for start, end in intervals) / sr
    pause_duration = duration - speech_duration
    pause_ratio = pause_duration / duration if duration > 0 else 0.0

    # Count gaps between non-silent regions longer than 0.5s
    pause_count = 0
    for i in range(1, len(intervals)):
        gap = (intervals[i][0] - intervals[i - 1][1]) / sr
        if gap > 0.5:
            pause_count += 1

    # --- Speech rate (rough proxy: voiced frames per second) ---
    voiced_ratio = len(voiced_f0) / len(f0) if len(f0) > 0 else 0
    words_per_second_proxy = voiced_ratio * (1 - pause_ratio)

    if words_per_second_proxy < 0.35:
        speech_rate_label = "slow"
    elif words_per_second_proxy > 0.55:
        speech_rate_label = "fast"
    else:
        speech_rate_label = "moderate"

    summary, tips = _build_feedback(
        pitch_variation, volume_variation, speech_rate_label, pause_ratio, pause_count
    )

    return {
        "pitch_variation": round(pitch_variation, 1),
        "avg_volume": round(avg_volume, 4),
        "volume_variation": round(volume_variation, 4),
        "speech_rate_label": speech_rate_label,
        "pause_count": pause_count,
        "pause_ratio": round(pause_ratio, 2),
        "summary": summary,
        "tips": tips,
    }


def _build_feedback(
    pitch_variation: float,
    volume_variation: float,
    speech_rate_label: str,
    pause_ratio: float,
    pause_count: int,
) -> tuple[str, list[str]]:
    """Translate raw metrics into a short, encouraging summary + tips."""
    tips = []

    # Pacing
    if speech_rate_label == "fast":
        tips.append("Try slowing down slightly — pausing briefly before key points can add clarity.")
    elif speech_rate_label == "slow":
        tips.append("Your pacing was deliberate. A bit more energy could help engagement.")

    # Pauses
    if pause_ratio > 0.4:
        tips.append("There were several long pauses — practicing the answer aloud may help it flow more smoothly.")
    elif pause_count == 0 and pause_ratio < 0.05:
        tips.append("You spoke continuously with no pauses — brief pauses can help emphasize key points.")

    # Pitch / volume variation -> energy and engagement
    monotone = pitch_variation < 15 and volume_variation < 0.02
    if monotone:
        summary = "Your delivery was steady and calm, though fairly monotone."
        tips.append("Adding some vocal variation can make your answers sound more engaged.")
    elif pitch_variation > 40 or volume_variation > 0.05:
        summary = "Your delivery had good energy and natural variation."
    else:
        summary = "Your delivery was clear and well-paced."

    if not tips:
        tips.append("Solid delivery overall — keep this pacing and energy.")

    return summary, tips[:2]


def _empty_result(reason: str) -> dict:
    return {
        "pitch_variation": 0.0,
        "avg_volume": 0.0,
        "volume_variation": 0.0,
        "speech_rate_label": "unknown",
        "pause_count": 0,
        "pause_ratio": 0.0,
        "summary": reason,
        "tips": [],
    }