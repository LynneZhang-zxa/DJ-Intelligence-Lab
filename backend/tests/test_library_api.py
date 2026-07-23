import json
import unittest
from unittest.mock import patch

from api.library import get_library
from database.models import LibraryTrack


class LibraryApiTests(unittest.TestCase):
    @patch("api.library.list_library_tracks")
    def test_empty_library(self, list_tracks):
        list_tracks.return_value = []

        self.assertEqual(get_library(), [])

    @patch("api.library.list_library_tracks")
    def test_library_tracks_are_json_safe(self, list_tracks):
        list_tracks.return_value = [
            LibraryTrack(
                id=1,
                title="Track",
                artist="Artist",
                album="Album",
                cover_image="https://example.com/cover.jpg",
                source="spotify",
                file_path=None,
                spotify_id="spotify-id",
                bpm=None,
                key=None,
                mode=None,
                duration=180.5,
                added_at="2026-07-23T10:00:00Z",
            ),
        ]

        result = get_library()

        json.dumps(result)
        self.assertEqual(result[0]["title"], "Track")
        self.assertEqual(result[0]["source"], "spotify")
        self.assertIsNone(result[0]["file_path"])


if __name__ == "__main__":
    unittest.main()
