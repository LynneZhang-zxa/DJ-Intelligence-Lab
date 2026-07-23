import shutil
import os

from fastapi import APIRouter, UploadFile, File

from audio.key import estimate_key
from audio.loader import load_audio
from audio.processor import downsample_waveform
from audio.spectrogram import compute_spectrogram
from audio.tempo import estimate_bpm
from database.history import save_analysis


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

    spectrogram = compute_spectrogram(audio, sr)

    bpm = estimate_bpm(audio, sr)

    key = estimate_key(audio, sr)

    spectrogram_response = {
        **spectrogram,
        "values": spectrogram["values"].round().astype("int8").tolist()
    }


    duration = len(audio) / sr


    os.remove(file_path)

    save_analysis(
        filename=file.filename,
        duration=duration,
        sample_rate=sr,
        bpm=bpm,
        key=key["key"] if key else None,
        mode=key["mode"] if key else None,
    )


    return {
        "filename": file.filename,
        "duration": duration,
        "sample_rate": sr,
        "waveform": waveform.tolist(),
        "spectrogram": spectrogram_response,
        "bpm": bpm,
        "key": key
    }
