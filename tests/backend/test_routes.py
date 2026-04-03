from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from PIL import Image
import io, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../backend"))
from app.main import app

client = TestClient(app)

def _img():
    buf = io.BytesIO()
    Image.new("RGB", (128, 128), (100, 150, 200)).save(buf, format="JPEG")
    return buf.getvalue()

def test_health():
    assert client.get("/health").status_code == 200

def test_index():
    with patch("app.api.routes.index_image", new=AsyncMock(return_value={"indexed": "t.jpg", "total_indexed": 1})):
        r = client.post("/api/v1/index", files={"file": ("t.jpg", _img(), "image/jpeg")})
    assert r.status_code == 200
    assert r.json()["total_indexed"] == 1

def test_search():
    with patch("app.api.routes.search_images", new=AsyncMock(return_value={"results": [], "total_indexed": 0})):
        r = client.post("/api/v1/search", files={"file": ("t.jpg", _img(), "image/jpeg")})
    assert r.status_code == 200

def test_503():
    import httpx
    with patch("app.api.routes.index_image", new=AsyncMock(side_effect=httpx.ConnectError("x"))):
        r = client.post("/api/v1/index", files={"file": ("t.jpg", _img(), "image/jpeg")})
    assert r.status_code == 503
