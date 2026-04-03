from fastapi import APIRouter, HTTPException, UploadFile, File
from app.core.searcher import index_image, search_similar

router = APIRouter(prefix="/api/v1/cv", tags=["image-search"])
ALLOWED = {"jpg", "jpeg", "png", "bmp", "webp"}

def _validate(filename: str):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED:
        raise HTTPException(status_code=400, detail=f"Unsupported format: .{ext}")

@router.post("/index")
async def index(file: UploadFile = File(...)):
    _validate(file.filename)
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    return index_image(file.filename, content)

@router.post("/search")
async def search(file: UploadFile = File(...)):
    _validate(file.filename)
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    return search_similar(content)

@router.get("/index/count")
def index_count():
    from app.core.searcher import get_index_count
    return {"indexed_images": get_index_count()}
