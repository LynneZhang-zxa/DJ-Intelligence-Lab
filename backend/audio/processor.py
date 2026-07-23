import numpy as np


def downsample_waveform(audio, target_points=1000):

    step = len(audio) // target_points

    samples = []

    for i in range(0, len(audio), step):

        chunk = audio[i:i+step]

        samples.append(np.max(chunk))
        samples.append(np.min(chunk))

    return np.array(samples)