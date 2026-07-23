from datetime import datetime, timezone

from database.core import DATABASE_PATH, database_connection
from database.library import _library_track_from_row
from database.models import Playlist


def _playlist_from_row(row):
    return Playlist(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        spotify_id=row["spotify_id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        track_count=row["track_count"],
    )


def create_playlist(
    name,
    spotify_id,
    description=None,
    database_path=DATABASE_PATH,
    created_at=None,
):
    timestamp = created_at or datetime.now(
        timezone.utc
    ).isoformat(timespec="seconds")

    with database_connection(database_path) as connection:
        with connection:
            cursor = connection.execute(
                """
                INSERT INTO playlists (
                    name,
                    description,
                    spotify_id,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    name,
                    description,
                    spotify_id,
                    timestamp,
                    timestamp,
                ),
            )

        row = connection.execute(
            """
            SELECT playlists.*, 0 AS track_count
            FROM playlists
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()

    return _playlist_from_row(row)


def list_playlists(database_path=DATABASE_PATH):
    with database_connection(database_path) as connection:
        rows = connection.execute(
            """
            SELECT
                playlists.*,
                COUNT(playlist_tracks.library_track_id)
                    AS track_count
            FROM playlists
            LEFT JOIN playlist_tracks
                ON playlist_tracks.playlist_id = playlists.id
            GROUP BY playlists.id
            ORDER BY playlists.updated_at DESC, playlists.id DESC
            """
        ).fetchall()

    return [_playlist_from_row(row) for row in rows]


def get_playlist(playlist_id, database_path=DATABASE_PATH):
    with database_connection(database_path) as connection:
        row = connection.execute(
            """
            SELECT
                playlists.*,
                COUNT(playlist_tracks.library_track_id)
                    AS track_count
            FROM playlists
            LEFT JOIN playlist_tracks
                ON playlist_tracks.playlist_id = playlists.id
            WHERE playlists.id = ?
            GROUP BY playlists.id
            """,
            (playlist_id,),
        ).fetchone()

    return _playlist_from_row(row) if row else None


def list_playlist_tracks(
    playlist_id,
    database_path=DATABASE_PATH,
):
    with database_connection(database_path) as connection:
        rows = connection.execute(
            """
            SELECT library_tracks.*
            FROM playlist_tracks
            JOIN library_tracks
                ON library_tracks.id =
                    playlist_tracks.library_track_id
            WHERE playlist_tracks.playlist_id = ?
            ORDER BY playlist_tracks.position
            """,
            (playlist_id,),
        ).fetchall()

    return [_library_track_from_row(row) for row in rows]


def add_track_to_playlist(
    playlist_id,
    library_track_id,
    database_path=DATABASE_PATH,
    added_at=None,
):
    timestamp = added_at or datetime.now(
        timezone.utc
    ).isoformat(timespec="seconds")

    with database_connection(database_path) as connection:
        with connection:
            next_position = connection.execute(
                """
                SELECT COALESCE(MAX(position) + 1, 0)
                FROM playlist_tracks
                WHERE playlist_id = ?
                """,
                (playlist_id,),
            ).fetchone()[0]
            connection.execute(
                """
                INSERT INTO playlist_tracks (
                    playlist_id,
                    library_track_id,
                    position,
                    added_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    playlist_id,
                    library_track_id,
                    next_position,
                    timestamp,
                ),
            )
            connection.execute(
                """
                UPDATE playlists
                SET updated_at = ?
                WHERE id = ?
                """,
                (timestamp, playlist_id),
            )

    return get_playlist(playlist_id, database_path)
