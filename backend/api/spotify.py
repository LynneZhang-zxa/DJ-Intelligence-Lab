import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from config import get_spotify_settings
from database.library import upsert_spotify_track
from database.spotify_auth import (
    get_spotify_token,
    save_spotify_token,
    token_is_expired,
)
from integrations.spotify import (
    SpotifyError,
    build_authorization_url,
    exchange_code,
    get_saved_tracks,
    refresh_access_token,
)


router = APIRouter()
FRONTEND_LIBRARY_URL = (
    "http://localhost:5173/?view=library"
)
OAUTH_STATE_LIFETIME = timedelta(minutes=10)
pending_states = {}


def _remove_expired_states():
    now = datetime.now(timezone.utc)
    for state, expires_at in list(pending_states.items()):
        if expires_at <= now:
            pending_states.pop(state, None)


def _current_access_token():
    token = get_spotify_token()
    if token is None:
        raise HTTPException(
            status_code=401,
            detail="Connect Spotify before importing tracks.",
        )

    if not token_is_expired(token):
        return token.access_token

    if not token.refresh_token:
        raise HTTPException(
            status_code=401,
            detail="Spotify authorization has expired. Connect again.",
        )

    try:
        refreshed = refresh_access_token(
            get_spotify_settings(),
            token.refresh_token,
        )
    except SpotifyError as error:
        raise HTTPException(
            status_code=502,
            detail=str(error),
        ) from error

    saved = save_spotify_token(
        refreshed,
        previous_refresh_token=token.refresh_token,
    )
    return saved.access_token


@router.get("/auth/spotify/login")
def spotify_login():
    _remove_expired_states()
    state = secrets.token_urlsafe(24)
    pending_states[state] = (
        datetime.now(timezone.utc)
        + OAUTH_STATE_LIFETIME
    )
    return RedirectResponse(
        build_authorization_url(
            get_spotify_settings(),
            state,
        )
    )


@router.get("/auth/spotify/callback")
def spotify_callback(
    state: str | None = None,
    code: str | None = None,
    error: str | None = None,
):
    _remove_expired_states()
    expires_at = pending_states.pop(state, None)
    if not state or expires_at is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired Spotify OAuth state.",
        )
    if error:
        return RedirectResponse(
            f"{FRONTEND_LIBRARY_URL}&spotify=denied"
        )
    if not code:
        raise HTTPException(
            status_code=400,
            detail="Spotify did not return an authorization code.",
        )

    try:
        token_data = exchange_code(
            get_spotify_settings(),
            code,
        )
        save_spotify_token(token_data)
    except SpotifyError as spotify_error:
        raise HTTPException(
            status_code=502,
            detail=str(spotify_error),
        ) from spotify_error

    return RedirectResponse(
        f"{FRONTEND_LIBRARY_URL}&spotify=connected"
    )


@router.post("/library/import/spotify")
def import_spotify_library():
    try:
        spotify_tracks = get_saved_tracks(
            _current_access_token()
        )
    except SpotifyError as error:
        raise HTTPException(
            status_code=502,
            detail=str(error),
        ) from error

    for track in spotify_tracks:
        upsert_spotify_track(**track)

    return {
        "imported": len(spotify_tracks),
    }
