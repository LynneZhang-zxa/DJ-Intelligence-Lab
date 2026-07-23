import librosa


def load_audio(file_path):
    audio, sample_rate = librosa.load(
        file_path,
        sr=None # keep original data
    )

    return audio, sample_rate