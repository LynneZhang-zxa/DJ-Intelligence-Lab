import sqlite3
import tempfile
import unittest
from pathlib import Path

from database.core import database_connection, init_database
from database.history import (
    list_analysis_history,
    save_analysis,
)


class AnalysisHistoryDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = (
            Path(self.temp_directory.name)
            / "library.db"
        )
        init_database(self.database_path)

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_database_initialization_is_idempotent(self):
        init_database(self.database_path)

        with database_connection(
            self.database_path
        ) as connection:
            table = connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                  AND name = 'analysis_history'
                """
            ).fetchone()

        self.assertIsNotNone(table)

    def test_save_and_list_complete_analysis(self):
        saved = save_analysis(
            filename="track.mp3",
            duration=180.5,
            sample_rate=44100,
            bpm=128.0,
            key="C#",
            mode="minor",
            database_path=self.database_path,
        )

        records = list_analysis_history(
            self.database_path
        )

        self.assertEqual(records, [saved])
        self.assertEqual(saved.filename, "track.mp3")
        self.assertEqual(saved.bpm, 128.0)

    def test_nullable_analysis_values(self):
        saved = save_analysis(
            filename="ambient.wav",
            duration=45.0,
            sample_rate=48000,
            bpm=None,
            key=None,
            mode=None,
            database_path=self.database_path,
        )

        self.assertIsNone(saved.bpm)
        self.assertIsNone(saved.key)
        self.assertIsNone(saved.mode)

    def test_legacy_tracks_are_migrated_without_data_loss(self):
        legacy_path = (
            Path(self.temp_directory.name)
            / "legacy.db"
        )
        connection = sqlite3.connect(legacy_path)
        connection.executescript(
            """
            CREATE TABLE tracks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                duration REAL NOT NULL,
                sample_rate INTEGER NOT NULL,
                bpm REAL,
                key TEXT,
                mode TEXT,
                created_at TEXT NOT NULL
            );

            INSERT INTO tracks (
                filename,
                duration,
                sample_rate,
                bpm,
                key,
                mode,
                created_at
            )
            VALUES (
                'legacy.mp3',
                90.0,
                44100,
                120.0,
                'A',
                'minor',
                '2026-07-23T10:00:00+00:00'
            );
            """
        )
        connection.commit()
        connection.close()

        init_database(legacy_path)

        records = list_analysis_history(legacy_path)

        self.assertEqual(len(records), 1)
        self.assertEqual(
            records[0].filename,
            "legacy.mp3",
        )

        with database_connection(legacy_path) as connection:
            legacy_table = connection.execute(
                """
                SELECT 1
                FROM sqlite_master
                WHERE type = 'table' AND name = 'tracks'
                """
            ).fetchone()

        self.assertIsNone(legacy_table)


if __name__ == "__main__":
    unittest.main()
