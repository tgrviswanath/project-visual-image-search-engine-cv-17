from fastapi.testclient import TestClient
from PIL import Image
import io, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../cv-service"))
from app.main import app

client = TestClient(app)

def _img():
    buf = io.BytesIO()
    Image.new("RGB", (128, 128), (100, 150, 200)).save(buf, format="JPEG")
    return buf.getvalue()

def test_health():
    assert client.get("/health").status_code == 200

def test_index_count():
    r = client.get("/api/v1/cv/index/count")
    assert r.status_code == 200

def test_unsupported_format():
    r = client.post("/api/v1/cv/index", files={"file": ("t.gif", b"GIF89a", "image/gif")})
    assert r.status_code == 400

def test_empty_file():
    r = client.post("/api/v1/cv/search", files={"file": ("t.jpg", b"", "image/jpeg")})
    assert r.status_code == 400
