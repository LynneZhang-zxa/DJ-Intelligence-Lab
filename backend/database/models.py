from dataclasses import dataclass


@dataclass(frozen=True)
class AnalysisHistoryRecord:
    id: int
    filename: str
    duration: float
    sample_rate: int
    bpm: float | None
    key: str | None
    mode: str | None
    created_at: str


@dataclass(frozen=True)
class LibraryTrack:
    id: int
    title: str
    artist: str | None
    album: str | None
    cover_image: str | None
    source: str
    file_path: str | None
    spotify_id: str | None
    bpm: float | None
    key: str | None
    mode: str | None
    duration: float | None
    added_at: str


@dataclass(frozen=True)
class Playlist:
    id: int
    name: str
    description: str | None
    spotify_id: str
    created_at: str
    updated_at: str
    track_count: int = 0
