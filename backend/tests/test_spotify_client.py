import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from config import SpotifySettings
from integrations.spotify import (
    add_spotify_track_to_playlist,
    build_authorization_url,
    create_spotify_playlist,
    get_saved_tracks,
    normalize_saved_track,
)


class SpotifyClientTests(unittest.TestCase):
    def setUp(self):
        self.settings = SpotifySettings(
            client_id="client-id",
            client_secret="client-secret",
            redirect_uri=(
                "http://127.0.0.1:8000/"
                "auth/spotify/callback"
            ),
        )

    def test_authorization_url_uses_read_only_scope_and_state(self):
        url = build_authorization_url(
            self.settings,
            "secure-state",
        )
        query = parse_qs(urlparse(url).query)

        self.assertEqual(query["client_id"], ["client-id"])
        self.assertEqual(query["state"], ["secure-state"])
        self.assertEqual(
            query["scope"],
            ["user-library-read playlist-modify-private"],
        )
        self.assertEqual(
            query["redirect_uri"],
            [self.settings.redirect_uri],
        )

    def test_saved_tracks_follow_spotify_pagination(self):
        pages = [
            {
                "items": [self._saved_track("first")],
                "next": "https://api.spotify.com/page-2",
            },
            {
                "items": [self._saved_track("second")],
                "next": None,
            },
        ]

        with patch(
            "integrations.spotify._request_json",
            side_effect=pages,
        ) as request:
            tracks = get_saved_tracks("access-token")

        self.assertEqual(
            [track["spotify_id"] for track in tracks],
            ["first", "second"],
        )
        self.assertEqual(request.call_count, 2)

    def test_saved_track_is_normalized_to_library_metadata(self):
        result = normalize_saved_track(
            self._saved_track("track-id")
        )

        self.assertEqual(result["title"], "Test Track")
        self.assertEqual(result["artist"], "Artist One, Artist Two")
        self.assertEqual(result["album"], "Test Album")
        self.assertEqual(result["source"], "spotify")
        self.assertEqual(result["spotify_id"], "track-id")
        self.assertEqual(result["duration"], 180.5)
        self.assertEqual(
            result["cover_image"],
            "https://example.com/cover.jpg",
        )

    @patch("integrations.spotify._request_json")
    def test_create_private_spotify_playlist(self, request):
        request.return_value = {
            "id": "playlist-id",
            "name": "DJ Set",
        }

        result = create_spotify_playlist(
            "token",
            "DJ Set",
            "Description",
        )

        self.assertEqual(result["id"], "playlist-id")
        request.assert_called_once_with(
            "https://api.spotify.com/v1/me/playlists",
            method="POST",
            headers={
                "Authorization": "Bearer token",
                "Content-Type": "application/json",
            },
            json_data={
                "name": "DJ Set",
                "description": "Description",
                "public": False,
            },
        )

    @patch("integrations.spotify._request_json")
    def test_add_track_to_spotify_playlist(self, request):
        add_spotify_track_to_playlist(
            "token",
            "playlist-id",
            "track-id",
        )

        request.assert_called_once_with(
            (
                "https://api.spotify.com/v1/playlists/"
                "playlist-id/items"
            ),
            method="POST",
            headers={
                "Authorization": "Bearer token",
                "Content-Type": "application/json",
            },
            json_data={
                "uris": ["spotify:track:track-id"],
            },
        )

    @staticmethod
    def _saved_track(spotify_id):
        return {
            "added_at": "2026-07-23T10:00:00Z",
            "track": {
                "id": spotify_id,
                "name": "Test Track",
                "duration_ms": 180500,
                "artists": [
                    {"name": "Artist One"},
                    {"name": "Artist Two"},
                ],
                "album": {
                    "name": "Test Album",
                    "images": [{
                        "url": "https://example.com/cover.jpg",
                    }],
                },
            },
        }


if __name__ == "__main__":
    unittest.main()
