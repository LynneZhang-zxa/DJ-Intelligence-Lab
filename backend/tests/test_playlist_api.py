import unittest
from unittest.mock import patch

from api.playlists import (
    PlaylistCreateRequest,
    PlaylistTrackRequest,
    add_playlist_track,
    create_dj_playlist,
    get_playlist_detail,
    get_playlists,
)
from database.models import LibraryTrack, Playlist


class PlaylistApiTests(unittest.TestCase):
    def setUp(self):
        self.playlist = Playlist(
            id=1,
            name="DJ Set",
            description="Test set",
            spotify_id="spotify-playlist",
            created_at="2026-07-23T10:00:00Z",
            updated_at="2026-07-23T10:00:00Z",
            track_count=0,
        )
        self.track = LibraryTrack(
            id=2,
            title="Track",
            artist="Artist",
            album="Album",
            cover_image=None,
            source="spotify",
            file_path=None,
            spotify_id="spotify-track",
            bpm=None,
            key=None,
            mode=None,
            duration=180.0,
            added_at="2026-07-23T10:00:00Z",
        )

    @patch("api.playlists.list_playlists")
    def test_get_playlists_serializes_records(self, list_records):
        list_records.return_value = [self.playlist]

        result = get_playlists()

        self.assertEqual(result[0]["name"], "DJ Set")
        self.assertEqual(result[0]["track_count"], 0)

    @patch("api.playlists.list_playlist_tracks")
    @patch("api.playlists.get_playlist")
    def test_playlist_detail_includes_tracks(
        self,
        get_record,
        list_tracks,
    ):
        get_record.return_value = self.playlist
        list_tracks.return_value = [self.track]

        result = get_playlist_detail(1)

        self.assertEqual(result["tracks"][0]["title"], "Track")

    @patch("api.playlists.create_playlist")
    @patch("api.playlists.create_spotify_playlist")
    @patch("api.playlists._current_access_token")
    def test_create_playlist_syncs_to_spotify(
        self,
        access_token,
        create_spotify,
        create_local,
    ):
        access_token.return_value = "token"
        create_spotify.return_value = {
            "id": "spotify-playlist",
            "name": "DJ Set",
        }
        create_local.return_value = self.playlist

        result = create_dj_playlist(
            PlaylistCreateRequest(
                name="DJ Set",
                description="Test set",
            )
        )

        create_spotify.assert_called_once_with(
            "token",
            "DJ Set",
            "Test set",
        )
        self.assertEqual(result["spotify_id"], "spotify-playlist")

    @patch("api.playlists.add_track_to_playlist")
    @patch("api.playlists.add_spotify_track_to_playlist")
    @patch("api.playlists._current_access_token")
    @patch("api.playlists.get_library_track")
    @patch("api.playlists.get_playlist")
    def test_add_track_syncs_to_spotify(
        self,
        get_playlist_record,
        get_track,
        access_token,
        add_spotify,
        add_local,
    ):
        get_playlist_record.return_value = self.playlist
        get_track.return_value = self.track
        access_token.return_value = "token"
        add_local.return_value = Playlist(
            **{
                **self.playlist.__dict__,
                "track_count": 1,
            }
        )

        result = add_playlist_track(
            1,
            PlaylistTrackRequest(library_track_id=2),
        )

        add_spotify.assert_called_once_with(
            "token",
            "spotify-playlist",
            "spotify-track",
        )
        add_local.assert_called_once_with(1, 2)
        self.assertEqual(result["track_count"], 1)


if __name__ == "__main__":
    unittest.main()
