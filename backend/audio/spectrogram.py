import librosa
import numpy as np


N_FFT = 2048
HOP_LENGTH = 512
MIN_DB = -80.0
MAX_DB = 0.0
MAX_FREQUENCY_BINS = 256
MAX_TIME_BINS = 512


def _pool_frequency_bins(spectrogram, target_bins):
    if spectrogram.shape[0] <= target_bins:
        return spectrogram

    frequency_groups = np.array_split(spectrogram, target_bins, axis=0)
    return np.stack(
        [group.mean(axis=0) for group in frequency_groups],
        axis=0,
    )


def _pool_time_bins(spectrogram, target_bins):
    if spectrogram.shape[1] <= target_bins:
        return spectrogram

    time_groups = np.array_split(spectrogram, target_bins, axis=1)
    return np.stack(
        [group.max(axis=1) for group in time_groups],
        axis=1,
    )


def compute_spectrogram(audio, sample_rate):
    """Compute a bounded, frequency-by-time decibel spectrogram."""

    audio = np.asarray(audio, dtype=float)

    if audio.ndim != 1:
        raise ValueError("audio must be a one-dimensional array")

    if sample_rate <= 0:
        raise ValueError("sample_rate must be greater than zero")

    if audio.size == 0:
        values = np.empty((0, 0))
    else:
        stft = librosa.stft(
            audio,
            n_fft=N_FFT,
            hop_length=HOP_LENGTH,
            window="hann",
            center=True,
            pad_mode="constant",
        )
        magnitude = np.abs(stft)
        if np.max(magnitude) == 0:
            values = np.full(magnitude.shape, MIN_DB)
        else:
            values = librosa.amplitude_to_db(
                magnitude,
                ref=np.max,
                top_db=abs(MIN_DB),
            )
        values = np.clip(values, MIN_DB, MAX_DB)
        values = _pool_frequency_bins(values, MAX_FREQUENCY_BINS)
        values = _pool_time_bins(values, MAX_TIME_BINS)

    frequency_bins, time_bins = values.shape

    return {
        "values": values,
        "orientation": "frequency_time",
        "frequency_scale": "linear",
        "frequency_bins": frequency_bins,
        "time_bins": time_bins,
        "min_frequency": 0.0,
        "max_frequency": sample_rate / 2,
        "min_db": MIN_DB,
        "max_db": MAX_DB,
        "fft_size": N_FFT,
        "hop_length": HOP_LENGTH,
    }
