from audio.loader import load_audio
from audio.waveform import plot_waveform
from audio.processor import downsample_waveform


audio, sr = load_audio("test.wav")


small_audio = downsample_waveform(audio)


plot_waveform(
    small_audio,
    len(small_audio) / (len(audio) / sr)
)