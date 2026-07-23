import json
import unittest
from io import BytesIO
from unittest.mock import patch

import numpy as np
from fastapi import UploadFile

from api.analyze import analyze_audio


class AnalyzeApiTests(unittest.IsolatedAsyncioTestCase):
    @patch("api.analyze.compute_spectrogram")
    @patch("api.analyze.downsample_waveform")
    @patch("api.analyze.load_audio")
    async def test_analyze_adds_json_safe_spectrogram_and_keeps_waveform(
        self,
        mock_load_audio,
        mock_downsample_waveform,
        mock_compute_spectrogram,
    ):
        audio = np.array([0.25, -0.5, 0.75, -1.0])
        waveform = np.array([0.75, -1.0])
        mock_load_audio.return_value = (audio, 4)
        mock_downsample_waveform.return_value = waveform
        mock_compute_spectrogram.return_value = {
            "values": np.array([
                [-80.0, -40.4],
                [-20.6, 0.0],
            ]),
            "orientation": "frequency_time",
            "frequency_scale": "linear",
            "frequency_bins": 2,
            "time_bins": 2,
            "min_frequency": 0.0,
            "max_frequency": 2.0,
            "min_db": -80.0,
            "max_db": 0.0,
            "fft_size": 2048,
            "hop_length": 512,
        }

        result = await analyze_audio(
            UploadFile(
                filename="api-test.wav",
                file=BytesIO(b"test audio"),
            )
        )

        json.dumps(result)
        self.assertEqual(result["filename"], "api-test.wav")
        self.assertEqual(result["duration"], 1.0)
        self.assertEqual(result["sample_rate"], 4)
        self.assertEqual(result["waveform"], waveform.tolist())
        self.assertEqual(
            result["spectrogram"]["values"],
            [[-80, -40], [-21, 0]],
        )
        self.assertEqual(
            result["spectrogram"]["orientation"],
            "frequency_time",
        )
        self.assertEqual(result["spectrogram"]["frequency_bins"], 2)
        self.assertEqual(result["spectrogram"]["time_bins"], 2)
        self.assertEqual(result["spectrogram"]["fft_size"], 2048)
        self.assertEqual(result["spectrogram"]["hop_length"], 512)

        mock_downsample_waveform.assert_called_once_with(audio)
        mock_compute_spectrogram.assert_called_once_with(audio, 4)

    @patch("api.analyze.compute_spectrogram")
    @patch("api.analyze.downsample_waveform")
    @patch("api.analyze.load_audio")
    async def test_analyze_serializes_empty_spectrogram_matrix(
        self,
        mock_load_audio,
        mock_downsample_waveform,
        mock_compute_spectrogram,
    ):
        mock_load_audio.return_value = (np.array([]), 44100)
        mock_downsample_waveform.return_value = np.array([])
        mock_compute_spectrogram.return_value = {
            "values": np.empty((0, 0)),
            "orientation": "frequency_time",
            "frequency_scale": "linear",
            "frequency_bins": 0,
            "time_bins": 0,
            "min_frequency": 0.0,
            "max_frequency": 22050.0,
            "min_db": -80.0,
            "max_db": 0.0,
            "fft_size": 2048,
            "hop_length": 512,
        }

        result = await analyze_audio(
            UploadFile(
                filename="empty.wav",
                file=BytesIO(),
            )
        )

        json.dumps(result)
        self.assertEqual(result["spectrogram"]["values"], [])


if __name__ == "__main__":
    unittest.main()
