from dataclasses import asdict

from fastapi import APIRouter

from database.library import list_library_tracks


router = APIRouter()


@router.get("/library")
def get_library():
    return [
        asdict(track)
        for track in list_library_tracks()
    ]
