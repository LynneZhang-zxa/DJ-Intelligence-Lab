import base64
import json
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
SAVED_TRACKS_URL = "https://api.spotify.com/v1/me/tracks"
LIBRARY_SCOPE = (
    "user-library-read playlist-modify-private"
)


class SpotifyError(RuntimeError):
    pass


def build_authorization_url(settings, state):
    return f"{AUTHORIZE_URL}?{urlencode({
        'response_type': 'code',
        'client_id': settings.client_id,
        'scope': LIBRARY_SCOPE,
        'redirect_uri': settings.redirect_uri,
        'state': state,
    })}"


def _request_json(
    url,
    method="GET",
    headers=None,
    form_data=None,
    json_data=None,
):
    if form_data is not None:
        body = urlencode(form_data).encode("utf-8")
    elif json_data is not None:
        body = json.dumps(json_data).encode("utf-8")
    else:
        body = None
    request = Request(
        url,
        data=body,
        headers=headers or {},
        method=method,
    )

    try:
        with urlopen(request, timeout=20) as response:
            response_body = response.read().decode("utf-8")
            return json.loads(response_body) if response_body else {}
    except HTTPError as error:
        detail = error.read().decode("utf-8")
        raise SpotifyError(
            f"Spotify request failed ({error.code}): {detail}"
        ) from error


def _basic_authorization(settings):
    credentials = (
        f"{settings.client_id}:{settings.client_secret}"
        .encode("utf-8")
    )
    encoded = base64.b64encode(credentials).decode("ascii")
    return f"Basic {encoded}"


def exchange_code(settings, code):
    return _request_json(
        TOKEN_URL,
        method="POST",
        headers={
            "Authorization": _basic_authorization(settings),
            "Content-Type": "application/x-www-form-urlencoded",
        },
        form_data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.redirect_uri,
        },
    )


def refresh_access_token(settings, refresh_token):
    return _request_json(
        TOKEN_URL,
        method="POST",
        headers={
            "Authorization": _basic_authorization(settings),
            "Content-Type": "application/x-www-form-urlencoded",
        },
        form_data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
    )


def get_saved_tracks(access_token):
    url = f"{SAVED_TRACKS_URL}?limit=50"
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    tracks = []

    while url:
        page = _request_json(url, headers=headers)
        tracks.extend(
            normalize_saved_track(item)
            for item in page.get("items", [])
            if item.get("track")
        )
        url = page.get("next")

    return tracks


def create_spotify_playlist(
    access_token,
    name,
    description=None,
):
    return _request_json(
        "https://api.spotify.com/v1/me/playlists",
        method="POST",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json_data={
            "name": name,
            "description": description or "",
            "public": False,
        },
    )


def add_spotify_track_to_playlist(
    access_token,
    playlist_id,
    spotify_track_id,
):
    return _request_json(
        (
            "https://api.spotify.com/v1/playlists/"
            f"{playlist_id}/items"
        ),
        method="POST",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json_data={
            "uris": [f"spotify:track:{spotify_track_id}"],
        },
    )


def normalize_saved_track(item):
    track = item["track"]
    album = track.get("album") or {}
    artists = track.get("artists") or []
    images = album.get("images") or []

    return {
        "title": track["name"],
        "artist": ", ".join(
            artist["name"]
            for artist in artists
            if artist.get("name")
        ) or None,
        "album": album.get("name"),
        "cover_image": (
            images[0].get("url")
            if images
            else None
        ),
        "source": "spotify",
        "spotify_id": track["id"],
        "duration": (
            track.get("duration_ms", 0) / 1000
            if track.get("duration_ms") is not None
            else None
        ),
        "added_at": item.get("added_at"),
    }
