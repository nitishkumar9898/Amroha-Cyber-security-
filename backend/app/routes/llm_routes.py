from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Optional
from ..services.llm_service import LLMService

router = APIRouter()

@router.get("/api/sentinel/status")
def get_status():
    try:
        return LLMService.get_system_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/chat")
def chat(message: str):
    try:
        return LLMService.process_chat(message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/sentinel/multimodal")
async def multimodal_chat(
    message: str = Form(...),
    files: List[UploadFile] = File(...)
):
    try:
        file_names = [f.filename for f in files]
        return LLMService.process_multimodal(message, len(files), file_names)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
