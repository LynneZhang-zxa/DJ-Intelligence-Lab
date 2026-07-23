import os
from dataclasses import dataclass
from pathlib import Path


ENV_PATH = Path(__file__).resolve().parent / ".env"


def _load_env_file(path=ENV_PATH):
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        name, value = line.split("=", 1)
        os.environ.setdefault(
            name.strip(),
            value.strip().strip("\"'"),
        )


@dataclass(frozen=True)
class SpotifySettings:
    client_id: str
    client_secret: str
    redirect_uri: str


def get_spotify_settings():
    _load_env_file()

    values = {
        "client_id": os.getenv("SPOTIFY_CLIENT_ID"),
        "client_secret": os.getenv("SPOTIFY_CLIENT_SECRET"),
        "redirect_uri": os.getenv("SPOTIFY_REDIRECT_URI"),
    }
    missing = [
        name
        for name, value in values.items()
        if not value
    ]
    if missing:
        names = ", ".join(
            f"SPOTIFY_{name.upper()}"
            for name in missing
        )
        raise RuntimeError(
            f"Missing Spotify configuration: {names}"
        )

    return SpotifySettings(**values)
