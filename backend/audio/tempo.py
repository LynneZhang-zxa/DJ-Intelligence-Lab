import librosa
import numpy as np


MIN_DURATION_SECONDS = 2.0


def estimate_bpm(audio, sample_rate):
    """Estimate one global tempo in beats per minute."""

    audio = np.asarray(audio, dtype=float)

    if audio.ndim != 1:
        raise ValueError("audio must be a one-dimensional array")

    if sample_rate <= 0:
        raise ValueError("sample_rate must be greater than zero")

    if not np.isfinite(audio).all():
        raise ValueError("audio must contain only finite values")

    if (
        audio.size == 0
        or audio.size < sample_rate * MIN_DURATION_SECONDS
        or np.max(np.abs(audio)) == 0
    ):
        return None

    tempo, beat_frames = librosa.beat.beat_track(
        y=audio,
        sr=sample_rate,
    )

    tempo_values = np.asarray(tempo).reshape(-1)

    if len(beat_frames) < 2 or tempo_values.size == 0:
        return None

    bpm = float(tempo_values[0])

    if not np.isfinite(bpm) or bpm <= 0:
        return None

    return bpm
