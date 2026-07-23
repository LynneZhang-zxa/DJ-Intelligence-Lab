import sqlite3
from contextlib import contextmanager
from pathlib import Path


DATABASE_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "library.db"
)

ANALYSIS_HISTORY_SCHEMA = """
CREATE TABLE IF NOT EXISTS analysis_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    duration REAL NOT NULL CHECK (duration >= 0),
    sample_rate INTEGER NOT NULL CHECK (sample_rate > 0),
    bpm REAL CHECK (bpm IS NULL OR bpm > 0),
    key TEXT,
    mode TEXT CHECK (
        mode IS NULL OR mode IN ('major', 'minor')
    ),
    created_at TEXT NOT NULL,
    CHECK (
        (key IS NULL AND mode IS NULL)
        OR (key IS NOT NULL AND mode IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_analysis_history_created_at
ON analysis_history(created_at DESC);
"""

LIBRARY_TRACKS_SCHEMA = """
CREATE TABLE IF NOT EXISTS library_tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    artist TEXT,
    album TEXT,
    cover_image TEXT,
    source TEXT NOT NULL CHECK (
        source IN ('local', 'spotify')
    ),
    file_path TEXT,
    spotify_id TEXT,
    bpm REAL CHECK (bpm IS NULL OR bpm > 0),
    key TEXT,
    mode TEXT CHECK (
        mode IS NULL OR mode IN ('major', 'minor')
    ),
    duration REAL CHECK (
        duration IS NULL OR duration >= 0
    ),
    added_at TEXT NOT NULL,
    CHECK (
        (key IS NULL AND mode IS NULL)
        OR (key IS NOT NULL AND mode IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_library_tracks_added_at
ON library_tracks(added_at DESC);

CREATE UNIQUE INDEX IF NOT EXISTS idx_library_spotify_id
ON library_tracks(spotify_id)
WHERE spotify_id IS NOT NULL;
"""

SPOTIFY_AUTH_SCHEMA = """
CREATE TABLE IF NOT EXISTS spotify_auth (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    expires_at TEXT NOT NULL,
    scope TEXT
);
"""

PLAYLISTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS playlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    spotify_id TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS playlist_tracks (
    playlist_id INTEGER NOT NULL,
    library_track_id INTEGER NOT NULL,
    position INTEGER NOT NULL CHECK (position >= 0),
    added_at TEXT NOT NULL,
    PRIMARY KEY (playlist_id, library_track_id),
    UNIQUE (playlist_id, position),
    FOREIGN KEY (playlist_id)
        REFERENCES playlists(id) ON DELETE CASCADE,
    FOREIGN KEY (library_track_id)
        REFERENCES library_tracks(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_playlist_tracks_position
ON playlist_tracks(playlist_id, position);
"""


@contextmanager
def database_connection(database_path=DATABASE_PATH):
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(
        database_path,
        timeout=5,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")

    try:
        yield connection
    finally:
        connection.close()


def _table_exists(connection, table_name):
    return connection.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
        """,
        (table_name,),
    ).fetchone() is not None


def _migrate_legacy_tracks(connection):
    if (
        _table_exists(connection, "tracks")
        and not _table_exists(
            connection,
            "analysis_history",
        )
    ):
        connection.execute(
            "ALTER TABLE tracks RENAME TO analysis_history"
        )


def init_database(database_path=DATABASE_PATH):
    with database_connection(database_path) as connection:
        connection.execute("PRAGMA journal_mode = WAL")

        with connection:
            _migrate_legacy_tracks(connection)
            connection.executescript(
                ANALYSIS_HISTORY_SCHEMA
            )
            connection.executescript(
                LIBRARY_TRACKS_SCHEMA
            )
            connection.executescript(
                SPOTIFY_AUTH_SCHEMA
            )
            connection.executescript(
                PLAYLISTS_SCHEMA
            )
