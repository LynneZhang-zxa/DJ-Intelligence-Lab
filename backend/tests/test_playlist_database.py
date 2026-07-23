import sqlite3
import tempfile
import unittest
from pathlib import Path

from database.core import init_database
from database.library import add_library_track
from database.playlists import (
    add_track_to_playlist,
    create_playlist,
    get_playlist,
    list_playlist_tracks,
    list_playlists,
)


class PlaylistDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = (
            Path(self.temp_directory.name)
            / "library.db"
        )
        init_database(self.database_path)

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_create_and_list_playlist(self):
        created = create_playlist(
            name="Warm-up Set",
            description="Opening tracks",
            spotify_id="spotify-playlist",
            database_path=self.database_path,
        )

        self.assertEqual(
            get_playlist(created.id, self.database_path),
            created,
        )
        self.assertEqual(
            list_playlists(self.database_path),
            [created],
        )
        self.assertEqual(created.track_count, 0)

    def test_add_tracks_preserves_playlist_order(self):
        playlist = create_playlist(
            name="Peak Time",
            spotify_id="peak-time",
            database_path=self.database_path,
        )
        first = add_library_track(
            title="First",
            source="spotify",
            spotify_id="first",
            database_path=self.database_path,
        )
        second = add_library_track(
            title="Second",
            source="spotify",
            spotify_id="second",
            database_path=self.database_path,
        )

        add_track_to_playlist(
            playlist.id,
            first.id,
            self.database_path,
        )
        updated = add_track_to_playlist(
            playlist.id,
            second.id,
            self.database_path,
        )

        tracks = list_playlist_tracks(
            playlist.id,
            self.database_path,
        )
        self.assertEqual(
            [track.title for track in tracks],
            ["First", "Second"],
        )
        self.assertEqual(updated.track_count, 2)

    def test_duplicate_track_is_rejected(self):
        playlist = create_playlist(
            name="No Duplicates",
            spotify_id="no-duplicates",
            database_path=self.database_path,
        )
        track = add_library_track(
            title="Track",
            source="spotify",
            spotify_id="track",
            database_path=self.database_path,
        )
        add_track_to_playlist(
            playlist.id,
            track.id,
            self.database_path,
        )

        with self.assertRaises(sqlite3.IntegrityError):
            add_track_to_playlist(
                playlist.id,
                track.id,
                self.database_path,
            )


if __name__ == "__main__":
    unittest.main()
