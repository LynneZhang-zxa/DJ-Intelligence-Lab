import numpy as np


def downsample_waveform(audio, target_points=1000):

    if len(audio) == 0:
        return np.array([])

    bucket_count = min(len(audio), max(1, target_points // 2))
    chunks = np.array_split(audio, bucket_count)

    return np.array([
        amplitude
        for chunk in chunks
        for amplitude in (np.max(chunk), np.min(chunk))
    ])
