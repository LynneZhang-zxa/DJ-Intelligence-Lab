import sqlite3
from dataclasses import asdict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.spotify import _current_access_token
from database.library import get_library_track
from database.playlists import (
    add_track_to_playlist,
    create_playlist,
    get_playlist,
    list_playlist_tracks,
    list_playlists,
)
from integrations.spotify import (
    SpotifyError,
    add_spotify_track_to_playlist,
    create_spotify_playlist,
)


router = APIRouter()


class PlaylistCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(
        default=None,
        max_length=300,
    )


class PlaylistTrackRequest(BaseModel):
    library_track_id: int


def _playlist_response(playlist, include_tracks=False):
    response = asdict(playlist)
    if include_tracks:
        response["tracks"] = [
            asdict(track)
            for track in list_playlist_tracks(playlist.id)
        ]
    return response


@router.get("/playlists")
def get_playlists():
    return [
        _playlist_response(playlist)
        for playlist in list_playlists()
    ]


@router.get("/playlists/{playlist_id}")
def get_playlist_detail(playlist_id: int):
    playlist = get_playlist(playlist_id)
    if playlist is None:
        raise HTTPException(
            status_code=404,
            detail="Playlist not found.",
        )
    return _playlist_response(
        playlist,
        include_tracks=True,
    )


@router.post("/playlists", status_code=201)
def create_dj_playlist(request: PlaylistCreateRequest):
    try:
        spotify_playlist = create_spotify_playlist(
            _current_access_token(),
            request.name.strip(),
            request.description,
        )
        playlist = create_playlist(
            name=spotify_playlist["name"],
            description=request.description,
            spotify_id=spotify_playlist["id"],
        )
    except SpotifyError as error:
        raise HTTPException(
            status_code=502,
            detail=str(error),
        ) from error

    return _playlist_response(playlist)


@router.post(
    "/playlists/{playlist_id}/tracks",
    status_code=201,
)
def add_playlist_track(
    playlist_id: int,
    request: PlaylistTrackRequest,
):
    playlist = get_playlist(playlist_id)
    if playlist is None:
        raise HTTPException(
            status_code=404,
            detail="Playlist not found.",
        )

    track = get_library_track(request.library_track_id)
    if track is None:
        raise HTTPException(
            status_code=404,
            detail="Library track not found.",
        )
    if not track.spotify_id:
        raise HTTPException(
            status_code=400,
            detail="Only Spotify tracks can sync to Spotify playlists.",
        )

    try:
        add_spotify_track_to_playlist(
            _current_access_token(),
            playlist.spotify_id,
            track.spotify_id,
        )
        updated = add_track_to_playlist(
            playlist_id,
            track.id,
        )
    except SpotifyError as error:
        raise HTTPException(
            status_code=502,
            detail=str(error),
        ) from error
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail="Track is already in this playlist.",
        ) from error

    return _playlist_response(updated)
