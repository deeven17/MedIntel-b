from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import Optional
import io, logging
from dependencies import get_current_user

router = APIRouter(prefix="/voice-assistant", tags=["Voice Assistant"])
logger = logging.getLogger(__name__)

_voice_assistant = None

def get_voice_assistant():
    global _voice_assistant
    if _voice_assistant is None:
        try:
            from voice_assistant import VoiceAssistant
            _voice_assistant = VoiceAssistant()
        except Exception as e:
            logger.critical(f"Voice engine init failed: {e}")
            return None
    return _voice_assistant

@router.get("/ping")
def ping():
    return {"voice": "online"}

@router.post("/process-public")
async def public(file: UploadFile = File(...), language_hint: Optional[str] = Form(None)):
    va = get_voice_assistant()
    if not va:
        raise HTTPException(503, "Voice unavailable")
    audio = await file.read()
    return {"ok": True, "bytes": len(audio)}
