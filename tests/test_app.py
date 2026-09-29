import os
os.environ["IMAGE_PROVIDER"] = "placeholder"
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert "ComicCraft" in response.text

def test_placeholder_image():
    response = client.post(
        "/test-image",
        json={"prompt": "A friendly fox walking through an enchanted forest"},
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
