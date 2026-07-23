from datetime import datetime, timezone

from database.core import DATABASE_PATH, database_connection
from database.models import AnalysisHistoryRecord


def _history_record_from_row(row):
    return AnalysisHistoryRecord(
        id=row["id"],
        filename=row["filename"],
        duration=row["duration"],
        sample_rate=row["sample_rate"],
        bpm=row["bpm"],
        key=row["key"],
        mode=row["mode"],
        created_at=row["created_at"],
    )


def save_analysis(
    filename,
    duration,
    sample_rate,
    bpm,
    key,
    mode,
    database_path=DATABASE_PATH,
    created_at=None,
):
    created_at = created_at or datetime.now(
        timezone.utc
    ).isoformat(timespec="seconds")

    with database_connection(database_path) as connection:
        with connection:
            cursor = connection.execute(
                """
                INSERT INTO analysis_history (
                    filename,
                    duration,
                    sample_rate,
                    bpm,
                    key,
                    mode,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    filename,
                    duration,
                    sample_rate,
                    bpm,
                    key,
                    mode,
                    created_at,
                ),
            )

        row = connection.execute(
            """
            SELECT *
            FROM analysis_history
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()

    return _history_record_from_row(row)


def list_analysis_history(
    database_path=DATABASE_PATH,
):
    with database_connection(database_path) as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM analysis_history
            ORDER BY created_at DESC, id DESC
            """
        ).fetchall()

    return [
        _history_record_from_row(row)
        for row in rows
    ]
