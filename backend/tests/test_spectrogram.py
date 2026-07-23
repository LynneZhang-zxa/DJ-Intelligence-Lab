import unittest
import warnings

import numpy as np

from audio.spectrogram import compute_spectrogram


SAMPLE_RATE = 44100


def sine_wave(frequency, duration=1.0):
    time = np.arange(int(SAMPLE_RATE * duration)) / SAMPLE_RATE
    return np.sin(2 * np.pi * frequency * time)


def expected_frequency_index(frequency, frequency_bins):
    nyquist = SAMPLE_RATE / 2
    return round((frequency / nyquist) * (frequency_bins - 1))


class ComputeSpectrogramTests(unittest.TestCase):
    def test_empty_audio_returns_empty_matrix(self):
        result = compute_spectrogram(np.array([]), SAMPLE_RATE)

        self.assertEqual(result["values"].shape, (0, 0))
        self.assertEqual(result["frequency_bins"], 0)
        self.assertEqual(result["time_bins"], 0)
        self.assertEqual(result["orientation"], "frequency_time")

    def test_440_hz_sine_wave_has_peak_near_440_hz(self):
        result = compute_spectrogram(sine_wave(440), SAMPLE_RATE)
        values = result["values"]
        frequency_profile = values.mean(axis=1)
        peak_index = int(np.argmax(frequency_profile))
        expected_index = expected_frequency_index(440, values.shape[0])

        self.assertLessEqual(abs(peak_index - expected_index), 2)
        self.assertGreaterEqual(values.min(), -80)
        self.assertLessEqual(values.max(), 0)
        self.assertLessEqual(values.shape[0], 256)
        self.assertLessEqual(values.shape[1], 512)

    def test_two_sine_waves_create_two_strong_frequency_regions(self):
        audio = 0.5 * sine_wave(440) + 0.5 * sine_wave(4000)
        values = compute_spectrogram(audio, SAMPLE_RATE)["values"]
        frequency_profile = values.mean(axis=1)
        background_level = float(np.median(frequency_profile))

        for frequency in (440, 4000):
            expected_index = expected_frequency_index(
                frequency,
                values.shape[0],
            )
            region = frequency_profile[
                max(0, expected_index - 2):expected_index + 3
            ]

            self.assertGreater(float(region.max()), background_level + 30)

    def test_impulse_is_localized_in_time_and_broad_in_frequency(self):
        audio = np.zeros(SAMPLE_RATE)
        audio[len(audio) // 2] = 1.0
        values = compute_spectrogram(audio, SAMPLE_RATE)["values"]
        time_activity = values.max(axis=0)
        active_frames = np.count_nonzero(time_activity > -79)
        peak_frame = int(np.argmax(time_activity))

        self.assertGreater(active_frames, 0)
        self.assertLess(active_frames, values.shape[1] // 4)
        self.assertAlmostEqual(
            float(np.ptp(values[:, peak_frame])),
            0.0,
            places=6,
        )

    def test_very_short_audio_returns_finite_bounded_matrix(self):
        audio = np.array([0.25, -0.25])

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            result = compute_spectrogram(audio, SAMPLE_RATE)

        values = result["values"]

        self.assertGreater(values.size, 0)
        self.assertTrue(np.isfinite(values).all())
        self.assertGreaterEqual(values.min(), -80)
        self.assertLessEqual(values.max(), 0)
        self.assertLessEqual(values.shape[0], 256)
        self.assertLessEqual(values.shape[1], 512)


if __name__ == "__main__":
    unittest.main()
