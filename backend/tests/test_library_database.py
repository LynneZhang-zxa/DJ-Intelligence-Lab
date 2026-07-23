import sqlite3
import tempfile
import unittest
from pathlib import Path

from database.core import init_database
from database.library import (
    add_library_track,
    get_library_track,
    list_library_tracks,
    upsert_spotify_track,
    update_library_track_analysis,
)


class LibraryDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = (
            Path(self.temp_directory.name)
            / "library.db"
        )
        init_database(self.database_path)

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_add_and_get_local_track(self):
        saved = add_library_track(
            title="House",
            artist="DJ Test",
            album="Lab Sessions",
            source="local",
            file_path="/managed/house.mp3",
            duration=180.0,
            database_path=self.database_path,
        )

        loaded = get_library_track(
            saved.id,
            self.database_path,
        )

        self.assertEqual(loaded, saved)
        self.assertEqual(saved.source, "local")
        self.assertIsNone(saved.spotify_id)

    def test_schema_supports_future_spotify_track(self):
        saved = add_library_track(
            title="Future Track",
            artist="Artist",
            source="spotify",
            spotify_id="spotify-track-id",
            cover_image="https://example.com/cover.jpg",
            duration=205.0,
            database_path=self.database_path,
        )

        self.assertEqual(saved.source, "spotify")
        self.assertEqual(
            saved.spotify_id,
            "spotify-track-id",
        )
        self.assertIsNone(saved.file_path)

    def test_spotify_ids_are_unique(self):
        for attempt in range(2):
            if attempt == 1:
                with self.assertRaises(
                    sqlite3.IntegrityError
                ):
                    add_library_track(
                        title="Duplicate",
                        source="spotify",
                        spotify_id="same-id",
                        database_path=self.database_path,
                    )
            else:
                add_library_track(
                    title="Original",
                    source="spotify",
                    spotify_id="same-id",
                    database_path=self.database_path,
                )

    def test_spotify_import_updates_existing_metadata(self):
        upsert_spotify_track(
            title="Old Title",
            artist="Artist",
            spotify_id="spotify-upsert-id",
            database_path=self.database_path,
        )

        updated = upsert_spotify_track(
            title="New Title",
            artist="Updated Artist",
            spotify_id="spotify-upsert-id",
            database_path=self.database_path,
        )

        tracks = list_library_tracks(self.database_path)
        self.assertEqual(len(tracks), 1)
        self.assertEqual(updated.title, "New Title")
        self.assertEqual(updated.artist, "Updated Artist")

    def test_tracks_are_listed_newest_first(self):
        add_library_track(
            title="Older",
            source="local",
            file_path="/managed/older.mp3",
            added_at="2026-07-22T10:00:00+00:00",
            database_path=self.database_path,
        )
        add_library_track(
            title="Newer",
            source="local",
            file_path="/managed/newer.mp3",
            added_at="2026-07-23T10:00:00+00:00",
            database_path=self.database_path,
        )

        titles = [
            track.title
            for track in list_library_tracks(
                self.database_path
            )
        ]

        self.assertEqual(titles, ["Newer", "Older"])

    def test_analysis_metadata_can_be_updated(self):
        saved = add_library_track(
            title="Analyze Me",
            source="local",
            file_path="/managed/analyze.mp3",
            database_path=self.database_path,
        )

        updated = update_library_track_analysis(
            track_id=saved.id,
            duration=33.82,
            bpm=127.8,
            key="C#",
            mode="minor",
            database_path=self.database_path,
        )

        self.assertEqual(updated.duration, 33.82)
        self.assertEqual(updated.bpm, 127.8)
        self.assertEqual(updated.key, "C#")
        self.assertEqual(updated.mode, "minor")


if __name__ == "__main__":
    unittest.main()
