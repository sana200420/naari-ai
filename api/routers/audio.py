"""
Phase 5 — Audio upload and transcription endpoints
- Upload: accepts audio file, validates size/duration
- Transcribe: uses Whisper to convert Sindhi speech to text
- Serve: returns pre-recorded answer audio URL from Supabase
"""
import os
import tempfile
import logging
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger("naari.audio")

# Limits
MAX_FILE_SIZE_MB = 10
MAX_DURATION_SECONDS = 30
ALLOWED_TYPES = {"audio/wav", "audio/mpeg", "audio/ogg", "audio/webm", "audio/mp4"}

# Whisper model — loaded once
_whisper_model = None


def _get_whisper():
    global _whisper_model
    if _whisper_model is not None:
        return _whisper_model
    try:
        import whisper
        _whisper_model = whisper.load_model("small")
        logger.info("Whisper model loaded")
    except Exception as e:
        logger.warning(f"Whisper load failed: {e}")
        _whisper_model = None
    return _whisper_model


class TranscriptResponse(BaseModel):
    transcript: str
    language: str
    duration_seconds: Optional[float]


class AudioAnswerResponse(BaseModel):
    answer_id: int
    audio_url: Optional[str]
    text: str


@router.post("/audio/transcribe", response_model=TranscriptResponse)
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Upload a Sindhi audio clip — returns transcript.
    Max 10MB, max 30 seconds.
    """
    # Check content type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Use WAV, MP3, OGG, or WebM."
        )

    # Read and check size
    audio_bytes = await file.read()
    size_mb = len(audio_bytes) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large: {size_mb:.1f}MB. Max allowed: {MAX_FILE_SIZE_MB}MB."
        )

    # Save to temp file and transcribe
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        model = _get_whisper()
        if model is None:
            raise HTTPException(status_code=503, detail="Transcription service unavailable.")

        result = model.transcribe(tmp_path, language="sd")
        transcript = result["text"].strip()
        duration = result.get("duration", None)

        # Check duration
        if duration and duration > MAX_DURATION_SECONDS:
            raise HTTPException(
                status_code=400,
                detail=f"Audio too long: {duration:.0f}s. Max allowed: {MAX_DURATION_SECONDS}s."
            )

        return TranscriptResponse(
            transcript=transcript,
            language="sindhi",
            duration_seconds=round(duration, 1) if duration else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(status_code=500, detail="Transcription failed. Please try again.")
    finally:
        os.unlink(tmp_path)


@router.get("/audio/answer/{answer_id}", response_model=AudioAnswerResponse)
def get_answer_audio(answer_id: int):
    """
    Returns pre-recorded audio URL for a verbatim answer from Supabase storage.
    """
    supabase_url = os.getenv("SUPABASE_URL")
    if not supabase_url:
        raise HTTPException(status_code=503, detail="Storage unavailable.")

    # Construct audio URL from Supabase storage
    audio_url = f"{supabase_url}/storage/v1/object/public/answer-audio/{answer_id}.mp3"

    return AudioAnswerResponse(
        answer_id=answer_id,
        audio_url=audio_url,
        text="",
    )
