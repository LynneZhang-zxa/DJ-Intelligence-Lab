import unittest

import numpy as np

from audio.tempo import estimate_bpm


SAMPLE_RATE = 22050


def click_track(bpm, duration=20):
    audio = np.zeros(SAMPLE_RATE * duration)
    seconds_per_beat = 60 / bpm
    beat_times = np.arange(0, duration, seconds_per_beat)
    beat_samples = (beat_times * SAMPLE_RATE).astype(int)
    audio[beat_samples[beat_samples < len(audio)]] = 1.0
    return audio


class EstimateBpmTests(unittest.TestCase):
    def test_empty_audio_returns_none(self):
        self.assertIsNone(estimate_bpm(np.array([]), SAMPLE_RATE))

    def test_silence_returns_none(self):
        audio = np.zeros(SAMPLE_RATE * 10)

        self.assertIsNone(estimate_bpm(audio, SAMPLE_RATE))

    def test_known_120_bpm_click_track(self):
        bpm = estimate_bpm(click_track(120), SAMPLE_RATE)

        self.assertIsInstance(bpm, float)
        self.assertAlmostEqual(bpm, 120, delta=5)

    def test_multiple_click_track_tempos(self):
        for expected_bpm in (90, 150):
            with self.subTest(expected_bpm=expected_bpm):
                bpm = estimate_bpm(
                    click_track(expected_bpm),
                    SAMPLE_RATE,
                )

                self.assertIsInstance(bpm, float)
                self.assertAlmostEqual(bpm, expected_bpm, delta=5)

    def test_short_audio_returns_none(self):
        audio = click_track(120, duration=1)

        self.assertIsNone(estimate_bpm(audio, SAMPLE_RATE))


if __name__ == "__main__":
    unittest.main()
