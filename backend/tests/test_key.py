import unittest
from unittest.mock import patch

import numpy as np

from audio.key import MAJOR_PROFILE, estimate_key


SAMPLE_RATE = 22050


def chord(frequencies, duration=2):
    time = np.arange(SAMPLE_RATE * duration) / SAMPLE_RATE
    tones = [
        np.sin(2 * np.pi * frequency * time)
        for frequency in frequencies
    ]
    return np.mean(tones, axis=0)


def progression(chords):
    return np.concatenate([chord(frequencies) for frequencies in chords])


class EstimateKeyTests(unittest.TestCase):
    def test_empty_audio_returns_none(self):
        self.assertIsNone(estimate_key(np.array([]), SAMPLE_RATE))

    def test_silence_returns_none(self):
        audio = np.zeros(SAMPLE_RATE * 4)

        self.assertIsNone(estimate_key(audio, SAMPLE_RATE))

    def test_c_major_progression(self):
        audio = progression([
            (261.63, 329.63, 392.00),
            (349.23, 440.00, 523.25),
            (392.00, 493.88, 587.33),
            (261.63, 329.63, 392.00),
        ])

        self.assertEqual(
            estimate_key(audio, SAMPLE_RATE),
            {"key": "C", "mode": "major"},
        )

    def test_a_minor_progression(self):
        audio = progression([
            (220.00, 261.63, 329.63),
            (293.66, 349.23, 440.00),
            (329.63, 392.00, 493.88),
            (220.00, 261.63, 329.63),
        ])

        self.assertEqual(
            estimate_key(audio, SAMPLE_RATE),
            {"key": "A", "mode": "minor"},
        )

    def test_single_tone_is_not_enough_to_establish_mode(self):
        audio = chord((261.63,))

        self.assertIsNone(estimate_key(audio, SAMPLE_RATE))

    @patch("audio.key.librosa.feature.chroma_cqt")
    def test_strong_harmonic_frame_outweighs_weak_competing_frame(
        self,
        mock_chroma_cqt,
    ):
        strong_c_major = MAJOR_PROFILE * 10
        weak_g_major = np.roll(MAJOR_PROFILE, 7)
        mock_chroma_cqt.return_value = np.stack(
            [strong_c_major, weak_g_major],
            axis=1,
        )

        result = estimate_key(np.ones(4096), SAMPLE_RATE)

        self.assertEqual(
            result,
            {"key": "C", "mode": "major"},
        )

    @patch("audio.key.librosa.feature.chroma_cqt")
    def test_moderate_but_distinct_key_profile_is_accepted(
        self,
        mock_chroma_stft,
    ):
        mock_chroma_stft.return_value = np.array([
            0.34387136, 0.32407397, 0.39887547, 0.51704466,
            0.69922590, 0.60363543, 0.52205229, 0.51759279,
            0.43370935, 0.44391054, 0.44803372, 0.47099623,
        ]).reshape(12, 1)

        result = estimate_key(np.ones(4096), SAMPLE_RATE)

        self.assertEqual(
            result,
            {"key": "E", "mode": "minor"},
        )

    @patch("audio.key.librosa.feature.chroma_cqt")
    def test_e_major_profile_with_smaller_margin_is_accepted(
        self,
        mock_chroma_stft,
    ):
        mock_chroma_stft.return_value = np.array([
            0.28726980, 0.21841513, 0.18239535, 0.32797804,
            0.53592402, 0.26837993, 0.25498542, 0.18532373,
            0.36281484, 0.23531599, 0.23111582, 0.61560386,
        ]).reshape(12, 1)

        result = estimate_key(np.ones(4096), SAMPLE_RATE)

        self.assertEqual(
            result,
            {"key": "E", "mode": "major"},
        )

    @patch("audio.key.librosa.feature.chroma_cqt")
    def test_strong_e_major_profile_with_close_runner_up_is_accepted(
        self,
        mock_chroma_stft,
    ):
        mock_chroma_stft.return_value = np.array([
            0.39637488, 0.27970469, 0.24667819, 0.35563242,
            0.59537399, 0.33504927, 0.32629064, 0.25309598,
            0.39907730, 0.27805030, 0.28667578, 0.72114360,
        ]).reshape(12, 1)

        result = estimate_key(np.ones(4096), SAMPLE_RATE)

        self.assertEqual(
            result,
            {"key": "E", "mode": "major"},
        )

    def test_invalid_input_raises_value_error(self):
        invalid_inputs = (
            (np.zeros((2, 100)), SAMPLE_RATE),
            (np.zeros(100), 0),
            (np.array([0.0, np.nan]), SAMPLE_RATE),
        )

        for audio, sample_rate in invalid_inputs:
            with self.subTest(sample_rate=sample_rate):
                with self.assertRaises(ValueError):
                    estimate_key(audio, sample_rate)


if __name__ == "__main__":
    unittest.main()
