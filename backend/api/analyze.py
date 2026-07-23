import shutil
import os

from fastapi import APIRouter, UploadFile, File

from audio.loader import load_audio
from audio.processor import downsample_waveform


router = APIRouter()


@router.post("/analyze")
async def analyze_audio(
    file: UploadFile = File(...)
):

    file_path = f"temp_{file.filename}"


    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(
            file.file,
            buffer
        )


    audio, sr = load_audio(file_path)


    waveform = downsample_waveform(audio)


    duration = len(audio) / sr


    os.remove(file_path)


    return {
        "filename": file.filename,
        "duration": duration,
        "sample_rate": sr,
        "waveform": waveform.tolist()
    }
