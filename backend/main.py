from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.analyze import router as analyze_router
from api.library import router as library_router
from api.playlists import router as playlists_router
from api.spotify import router as spotify_router
from database.core import init_database


@asynccontextmanager
async def lifespan(app):
    init_database()
    yield


app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(analyze_router)
app.include_router(library_router)
app.include_router(playlists_router)
app.include_router(spotify_router)


@app.get("/")
def home():

    return {
        "message": "Resonanca API running"
    }
