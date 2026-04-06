import asyncio
from fastapi import APIRouter, HTTPException, UploadFile, File
from app.core.searcher import index_image, search_similar, get_index_count
from app.core.validate import validate_image

router = APIRouter(prefix="/api/v1/cv", tags=["image-search"])


@router.post("/index")
async def index(file: UploadFile = File(...)):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    validate_image(file, content)
    try:
        return await asyncio.get_running_loop().run_in_executor(None, index_image, file.filename, content)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing error: {e}")


@router.post("/search")
async def search(file: UploadFile = File(...)):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    validate_image(file, content)
    try:
        return await asyncio.get_running_loop().run_in_executor(None, search_similar, content)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {e}")


@router.get("/index/count")
def index_count():
    return {"indexed_images": get_index_count()}
