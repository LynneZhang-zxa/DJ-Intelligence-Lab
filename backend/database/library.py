from datetime import datetime, timezone

from database.core import DATABASE_PATH, database_connection
from database.models import LibraryTrack


def _library_track_from_row(row):
    return LibraryTrack(
        id=row["id"],
        title=row["title"],
        artist=row["artist"],
        album=row["album"],
        cover_image=row["cover_image"],
        source=row["source"],
        file_path=row["file_path"],
        spotify_id=row["spotify_id"],
        bpm=row["bpm"],
        key=row["key"],
        mode=row["mode"],
        duration=row["duration"],
        added_at=row["added_at"],
    )


def add_library_track(
    title,
    source,
    artist=None,
    album=None,
    cover_image=None,
    file_path=None,
    spotify_id=None,
    bpm=None,
    key=None,
    mode=None,
    duration=None,
    database_path=DATABASE_PATH,
    added_at=None,
):
    added_at = added_at or datetime.now(
        timezone.utc
    ).isoformat(timespec="seconds")

    with database_connection(database_path) as connection:
        with connection:
            cursor = connection.execute(
                """
                INSERT INTO library_tracks (
                    title,
                    artist,
                    album,
                    cover_image,
                    source,
                    file_path,
                    spotify_id,
                    bpm,
                    key,
                    mode,
                    duration,
                    added_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    title,
                    artist,
                    album,
                    cover_image,
                    source,
                    file_path,
                    spotify_id,
                    bpm,
                    key,
                    mode,
                    duration,
                    added_at,
                ),
            )

        row = connection.execute(
            """
            SELECT *
            FROM library_tracks
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()

    return _library_track_from_row(row)


def get_library_track(
    track_id,
    database_path=DATABASE_PATH,
):
    with database_connection(database_path) as connection:
        row = connection.execute(
            """
            SELECT *
            FROM library_tracks
            WHERE id = ?
            """,
            (track_id,),
        ).fetchone()

    return (
        _library_track_from_row(row)
        if row
        else None
    )


def list_library_tracks(
    database_path=DATABASE_PATH,
):
    with database_connection(database_path) as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM library_tracks
            ORDER BY added_at DESC, id DESC
            """
        ).fetchall()

    return [
        _library_track_from_row(row)
        for row in rows
    ]


def upsert_spotify_track(
    title,
    spotify_id,
    source="spotify",
    artist=None,
    album=None,
    cover_image=None,
    duration=None,
    added_at=None,
    database_path=DATABASE_PATH,
):
    if source != "spotify":
        raise ValueError(
            "Spotify imports must use source='spotify'."
        )

    added_at = added_at or datetime.now(
        timezone.utc
    ).isoformat(timespec="seconds")

    with database_connection(database_path) as connection:
        with connection:
            connection.execute(
                """
                INSERT INTO library_tracks (
                    title,
                    artist,
                    album,
                    cover_image,
                    source,
                    spotify_id,
                    duration,
                    added_at
                )
                VALUES (?, ?, ?, ?, 'spotify', ?, ?, ?)
                ON CONFLICT(spotify_id)
                WHERE spotify_id IS NOT NULL
                DO UPDATE SET
                    title = excluded.title,
                    artist = excluded.artist,
                    album = excluded.album,
                    cover_image = excluded.cover_image,
                    duration = excluded.duration,
                    added_at = excluded.added_at
                """,
                (
                    title,
                    artist,
                    album,
                    cover_image,
                    spotify_id,
                    duration,
                    added_at,
                ),
            )

        row = connection.execute(
            """
            SELECT *
            FROM library_tracks
            WHERE spotify_id = ?
            """,
            (spotify_id,),
        ).fetchone()

    return _library_track_from_row(row)


def update_library_track_analysis(
    track_id,
    duration,
    bpm,
    key,
    mode,
    database_path=DATABASE_PATH,
):
    with database_connection(database_path) as connection:
        with connection:
            connection.execute(
                """
                UPDATE library_tracks
                SET duration = ?, bpm = ?, key = ?, mode = ?
                WHERE id = ?
                """,
                (
                    duration,
                    bpm,
                    key,
                    mode,
                    track_id,
                ),
            )

        row = connection.execute(
            """
            SELECT *
            FROM library_tracks
            WHERE id = ?
            """,
            (track_id,),
        ).fetchone()

    return (
        _library_track_from_row(row)
        if row
        else None
    )
