import matplotlib.pyplot as plt
import numpy as np


def plot_waveform(audio, sample_rate):

    time = np.linspace(
        0,
        len(audio) / sample_rate,
        len(audio)
    )

    plt.figure(figsize=(12, 4))

    plt.plot(time, audio)

    plt.xlabel("Time (seconds)")
    plt.ylabel("Amplitude")

    plt.title("Waveform")

    plt.show()