import json
import unittest
from io import BytesIO
from unittest.mock import patch

import numpy as np
from fastapi import UploadFile

from api.analyze import analyze_audio


class AnalyzeApiTests(unittest.IsolatedAsyncioTestCase):
    @patch("api.analyze.save_analysis")
    @patch("api.analyze.estimate_key")
    @patch("api.analyze.estimate_bpm")
    @patch("api.analyze.compute_spectrogram")
    @patch("api.analyze.downsample_waveform")
    @patch("api.analyze.load_audio")
    async def test_analyze_adds_json_safe_spectrogram_and_keeps_waveform(
        self,
        mock_load_audio,
        mock_downsample_waveform,
        mock_compute_spectrogram,
        mock_estimate_bpm,
        mock_estimate_key,
        mock_save_analysis,
    ):
        audio = np.array([0.25, -0.5, 0.75, -1.0])
        waveform = np.array([0.75, -1.0])
        mock_load_audio.return_value = (audio, 4)
        mock_downsample_waveform.return_value = waveform
        mock_estimate_bpm.return_value = 128.25
        mock_estimate_key.return_value = {
            "key": "C",
            "mode": "major",
        }
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
        self.assertEqual(result["bpm"], 128.25)
        self.assertEqual(
            result["key"],
            {"key": "C", "mode": "major"},
        )
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
        mock_estimate_bpm.assert_called_once_with(audio, 4)
        mock_estimate_key.assert_called_once_with(audio, 4)
        mock_save_analysis.assert_called_once_with(
            filename="api-test.wav",
            duration=1.0,
            sample_rate=4,
            bpm=128.25,
            key="C",
            mode="major",
        )

    @patch("api.analyze.save_analysis")
    @patch("api.analyze.estimate_key")
    @patch("api.analyze.estimate_bpm")
    @patch("api.analyze.compute_spectrogram")
    @patch("api.analyze.downsample_waveform")
    @patch("api.analyze.load_audio")
    async def test_analyze_serializes_empty_spectrogram_matrix(
        self,
        mock_load_audio,
        mock_downsample_waveform,
        mock_compute_spectrogram,
        mock_estimate_bpm,
        mock_estimate_key,
        mock_save_analysis,
    ):
        mock_load_audio.return_value = (np.array([]), 44100)
        mock_downsample_waveform.return_value = np.array([])
        mock_estimate_bpm.return_value = None
        mock_estimate_key.return_value = None
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
        self.assertIsNone(result["bpm"])
        self.assertIsNone(result["key"])
        mock_save_analysis.assert_called_once_with(
            filename="empty.wav",
            duration=0.0,
            sample_rate=44100,
            bpm=None,
            key=None,
            mode=None,
        )


if __name__ == "__main__":
    unittest.main()
