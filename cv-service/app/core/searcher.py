"""
Persistent visual image search using ResNet18 CNN embeddings + FAISS.
- FAISS index saved to disk (data/search.faiss)
- Metadata saved to JSON (data/search_meta.json)
- Survives service restarts
"""
import torch
import torchvision.transforms as T
from torchvision.models import resnet18, ResNet18_Weights
from PIL import Image
import io
import base64
import numpy as np
import json
import os
import faiss
from app.core.config import settings

INDEX_PATH = "data/search.faiss"
META_PATH  = "data/search_meta.json"

_model = None
_index: faiss.IndexFlatIP | None = None
_meta: list[dict] = []

_transform = T.Compose([
    T.Resize((settings.MAX_IMAGE_SIZE, settings.MAX_IMAGE_SIZE)),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


def _ensure_dir():
    os.makedirs("data", exist_ok=True)


def _get_model():
    global _model
    if _model is None:
        base = resnet18(weights=ResNet18_Weights.DEFAULT)
        _model = torch.nn.Sequential(*list(base.children())[:-1])
        _model.eval()
    return _model


def _load():
    global _index, _meta
    _ensure_dir()
    if os.path.exists(INDEX_PATH) and os.path.exists(META_PATH):
        _index = faiss.read_index(INDEX_PATH)
        with open(META_PATH, "r") as f:
            _meta = json.load(f)
    else:
        _index = faiss.IndexFlatIP(512)
        _meta = []


def _get_index() -> faiss.IndexFlatIP:
    global _index
    if _index is None:
        _load()
    return _index


def _save():
    _ensure_dir()
    faiss.write_index(_get_index(), INDEX_PATH)
    with open(META_PATH, "w") as f:
        json.dump(_meta, f)


def _embed(image_bytes: bytes) -> np.ndarray:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    tensor = _transform(img).unsqueeze(0)
    with torch.no_grad():
        emb = _get_model()(tensor).squeeze().numpy()
    norm = np.linalg.norm(emb)
    return (emb / (norm + 1e-8)).astype(np.float32)


def _thumbnail(image_bytes: bytes) -> str:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img.thumbnail((128, 128))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=70)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def index_image(filename: str, image_bytes: bytes) -> dict:
    emb = _embed(image_bytes).reshape(1, -1)
    thumb = _thumbnail(image_bytes)
    _get_index().add(emb)
    _meta.append({"name": filename, "thumbnail": thumb})
    _save()
    return {"indexed": filename, "total_indexed": len(_meta)}


def search_similar(image_bytes: bytes) -> dict:
    if not _meta:
        return {"results": [], "total_indexed": 0,
                "message": "Index is empty. Please index some images first."}
    query_emb = _embed(image_bytes).reshape(1, -1)
    k = min(settings.TOP_K, len(_meta))
    scores, indices = _get_index().search(query_emb, k)
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(_meta):
            continue
        item = _meta[idx]
        results.append({"name": item["name"], "similarity": round(float(score), 4),
                         "thumbnail": item["thumbnail"]})
    return {"results": results, "total_indexed": len(_meta)}


def get_index_count() -> int:
    return len(_meta)
