import librosa
import numpy as np


KEY_NAMES = (
    "C", "C#", "D", "D#", "E", "F",
    "F#", "G", "G#", "A", "A#", "B",
)

MAJOR_PROFILE = np.array([
    6.35, 2.23, 3.48, 2.33, 4.38, 4.09,
    2.52, 5.19, 2.39, 3.66, 2.29, 2.88,
])

MINOR_PROFILE = np.array([
    6.33, 2.68, 3.52, 5.38, 2.60, 3.53,
    2.54, 4.75, 3.98, 2.69, 3.34, 3.17,
])

N_FFT = 4096
HOP_LENGTH = 512
MIN_CORRELATION = 0.5
HIGH_CONFIDENCE_CORRELATION = 0.7
MIN_SCORE_MARGIN = 0.08


def estimate_key(audio, sample_rate):
    """Estimate a global musical key from mono audio samples."""

    audio = np.asarray(audio, dtype=float)

    if audio.ndim != 1:
        raise ValueError("audio must be a one-dimensional array")

    if sample_rate <= 0:
        raise ValueError("sample_rate must be greater than zero")

    if not np.isfinite(audio).all():
        raise ValueError("audio must contain only finite values")

    if (
        audio.size < N_FFT
        or np.max(np.abs(audio), initial=0) == 0
    ):
        return None

    chroma = librosa.feature.chroma_cqt(
        y=audio,
        sr=sample_rate,
        hop_length=HOP_LENGTH,
        norm=None,
    )
    frame_energy = chroma.sum(axis=0)

    if frame_energy.sum() == 0:
        return None

    pitch_class_energy = np.average(
        chroma,
        axis=1,
        weights=frame_energy,
    )

    scores = []

    for mode, profile in (
        ("major", MAJOR_PROFILE),
        ("minor", MINOR_PROFILE),
    ):
        for tonic_index, tonic in enumerate(KEY_NAMES):
            rotated_profile = np.roll(profile, tonic_index)
            correlation = np.corrcoef(
                pitch_class_energy,
                rotated_profile,
            )[0, 1]
            scores.append((float(correlation), tonic, mode))

    scores.sort(reverse=True)
    best_score, key, mode = scores[0]
    second_best_score = scores[1][0]

    if (
        not np.isfinite(best_score)
        or best_score < MIN_CORRELATION
        or (
            best_score < HIGH_CONFIDENCE_CORRELATION
            and best_score - second_best_score < MIN_SCORE_MARGIN
        )
    ):
        return None

    return {
        "key": key,
        "mode": mode,
    }
