"""Pruebas del endpoint de reconocimiento (andamiaje)."""

import io

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_recognition_returns_latex() -> None:
    file = ("expr.png", io.BytesIO(b"fake-image-bytes"), "image/png")
    response = client.post("/api/v1/recognition", files={"image": file})
    assert response.status_code == 200
    body = response.json()
    assert "latex" in body
    assert "provider" in body
