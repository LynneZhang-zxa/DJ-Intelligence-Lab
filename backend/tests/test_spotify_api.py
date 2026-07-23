import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi import HTTPException

from api import spotify
from database.spotify_auth import SpotifyToken


class SpotifyApiTests(unittest.TestCase):
    def setUp(self):
        spotify.pending_states.clear()

    @patch("api.spotify.get_spotify_settings")
    @patch("api.spotify.build_authorization_url")
    def test_login_redirects_to_spotify(
        self,
        build_url,
        get_settings,
    ):
        build_url.return_value = "https://accounts.spotify.com/authorize"

        response = spotify.spotify_login()

        self.assertEqual(response.status_code, 307)
        self.assertEqual(
            response.headers["location"],
            "https://accounts.spotify.com/authorize",
        )
        state = build_url.call_args.args[1]
        self.assertIn(state, spotify.pending_states)

    def test_callback_rejects_unknown_state(self):
        with self.assertRaises(HTTPException) as context:
            spotify.spotify_callback(
                state="unknown",
                code="code",
            )

        self.assertEqual(context.exception.status_code, 400)

    @patch("api.spotify.save_spotify_token")
    @patch("api.spotify.exchange_code")
    @patch("api.spotify.get_spotify_settings")
    def test_callback_exchanges_code_and_saves_token(
        self,
        get_settings,
        exchange_code,
        save_token,
    ):
        spotify.pending_states["valid"] = (
            datetime.now(timezone.utc)
            + timedelta(minutes=5)
        )
        exchange_code.return_value = {
            "access_token": "access",
            "refresh_token": "refresh",
            "expires_in": 3600,
        }

        response = spotify.spotify_callback(
            state="valid",
            code="authorization-code",
        )

        self.assertIn(
            "spotify=connected",
            response.headers["location"],
        )
        exchange_code.assert_called_once_with(
            get_settings.return_value,
            "authorization-code",
        )
        save_token.assert_called_once_with(
            exchange_code.return_value
        )

    @patch("api.spotify.get_spotify_token")
    def test_import_requires_spotify_connection(self, get_token):
        get_token.return_value = None

        with self.assertRaises(HTTPException) as context:
            spotify.import_spotify_library()

        self.assertEqual(context.exception.status_code, 401)

    @patch("api.spotify.upsert_spotify_track")
    @patch("api.spotify.get_saved_tracks")
    @patch("api.spotify.get_spotify_token")
    def test_import_saves_every_spotify_track(
        self,
        get_token,
        get_tracks,
        upsert,
    ):
        get_token.return_value = SpotifyToken(
            access_token="access",
            refresh_token="refresh",
            expires_at=(
                datetime.now(timezone.utc)
                + timedelta(hours=1)
            ).isoformat(),
            scope="user-library-read",
        )
        get_tracks.return_value = [
            {
                "title": "One",
                "spotify_id": "one",
                "source": "spotify",
            },
            {
                "title": "Two",
                "spotify_id": "two",
                "source": "spotify",
            },
        ]

        result = spotify.import_spotify_library()

        self.assertEqual(result, {"imported": 2})
        self.assertEqual(upsert.call_count, 2)


if __name__ == "__main__":
    unittest.main()
