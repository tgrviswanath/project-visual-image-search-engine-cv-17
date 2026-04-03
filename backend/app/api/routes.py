from fastapi import APIRouter, HTTPException, UploadFile, File
from app.core.service import search_images, index_image
import httpx

router = APIRouter(prefix="/api/v1", tags=["image-search"])

def _handle(e):
    if isinstance(e, httpx.ConnectError):
        raise HTTPException(status_code=503, detail="CV service unavailable")
    if isinstance(e, httpx.HTTPStatusError):
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    raise HTTPException(status_code=500, detail=str(e))

@router.post("/index")
async def index(file: UploadFile = File(...)):
    try:
        content = await file.read()
        return await index_image(file.filename, content, file.content_type or "image/jpeg")
    except Exception as e:
        _handle(e)

@router.post("/search")
async def search(file: UploadFile = File(...)):
    try:
        content = await file.read()
        return await search_images(file.filename, content, file.content_type or "image/jpeg")
    except Exception as e:
        _handle(e)
