from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from database.core import DATABASE_PATH, database_connection


@dataclass(frozen=True)
class SpotifyToken:
    access_token: str
    refresh_token: str | None
    expires_at: str
    scope: str | None


def save_spotify_token(
    token_data,
    database_path=DATABASE_PATH,
    previous_refresh_token=None,
):
    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(seconds=token_data["expires_in"])
    ).isoformat(timespec="seconds")
    refresh_token = (
        token_data.get("refresh_token")
        or previous_refresh_token
    )

    with database_connection(database_path) as connection:
        with connection:
            connection.execute(
                """
                INSERT INTO spotify_auth (
                    id,
                    access_token,
                    refresh_token,
                    expires_at,
                    scope
                )
                VALUES (1, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    access_token = excluded.access_token,
                    refresh_token = excluded.refresh_token,
                    expires_at = excluded.expires_at,
                    scope = excluded.scope
                """,
                (
                    token_data["access_token"],
                    refresh_token,
                    expires_at,
                    token_data.get("scope"),
                ),
            )

    return get_spotify_token(database_path)


def get_spotify_token(database_path=DATABASE_PATH):
    with database_connection(database_path) as connection:
        row = connection.execute(
            "SELECT * FROM spotify_auth WHERE id = 1"
        ).fetchone()

    if row is None:
        return None

    return SpotifyToken(
        access_token=row["access_token"],
        refresh_token=row["refresh_token"],
        expires_at=row["expires_at"],
        scope=row["scope"],
    )


def token_is_expired(token):
    expires_at = datetime.fromisoformat(token.expires_at)
    return expires_at <= (
        datetime.now(timezone.utc)
        + timedelta(seconds=30)
    )
