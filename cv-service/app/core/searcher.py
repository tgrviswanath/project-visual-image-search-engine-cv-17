"""
Visual image search using ResNet18 CNN embeddings + cosine similarity.
Images are indexed in-memory. In production, replace with FAISS or a vector DB.
"""
import torch
import torchvision.transforms as T
from torchvision.models import resnet18, ResNet18_Weights
from PIL import Image
import io
import base64
import numpy as np
from typing import List, Dict
from app.core.config import settings

_model = None
_index: List[Dict] = []  # in-memory index: [{name, embedding, thumbnail}]

_transform = T.Compose([
    T.Resize((settings.MAX_IMAGE_SIZE, settings.MAX_IMAGE_SIZE)),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

def _get_model():
    global _model
    if _model is None:
        base = resnet18(weights=ResNet18_Weights.DEFAULT)
        # Remove final classification layer to get 512-d embeddings
        _model = torch.nn.Sequential(*list(base.children())[:-1])
        _model.eval()
    return _model

def _embed(image_bytes: bytes) -> np.ndarray:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    tensor = _transform(img).unsqueeze(0)
    with torch.no_grad():
        emb = _get_model()(tensor).squeeze().numpy()
    return emb / (np.linalg.norm(emb) + 1e-8)

def _thumbnail(image_bytes: bytes) -> str:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img.thumbnail((128, 128))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=70)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def index_image(filename: str, image_bytes: bytes) -> dict:
    emb = _embed(image_bytes)
    thumb = _thumbnail(image_bytes)
    _index.append({"name": filename, "embedding": emb, "thumbnail": thumb})
    return {"indexed": filename, "total_indexed": len(_index)}

def search_similar(image_bytes: bytes) -> dict:
    if not _index:
        return {"results": [], "total_indexed": 0, "message": "Index is empty. Please index some images first."}
    query_emb = _embed(image_bytes)
    scores = [(item["name"], float(np.dot(query_emb, item["embedding"])), item["thumbnail"])
              for item in _index]
    scores.sort(key=lambda x: x[1], reverse=True)
    top = scores[:settings.TOP_K]
    return {
        "results": [{"name": n, "similarity": round(s, 4), "thumbnail": t} for n, s, t in top],
        "total_indexed": len(_index),
    }

def get_index_count() -> int:
    return len(_index)
