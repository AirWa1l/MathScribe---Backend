"""Pruebas de los endpoints de autenticación (andamiaje).

Hoy `register` y `login` son stubs (no tocan la base de datos ni firman un JWT
real); estas pruebas documentan el contrato actual —códigos de estado y forma de
la respuesta— para que la integración real de Sprint 2 no lo rompa sin querer.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_register_returns_created_user() -> None:
    payload = {"email": "nuevo@example.com", "name": "Nuevo Usuario", "password": "secreta123"}
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == payload["email"]
    assert body["name"] == payload["name"]
    assert "id" in body
    # El stub no debe exponer la contraseña en la respuesta.
    assert "password" not in body


def test_register_rejects_invalid_email() -> None:
    payload = {"email": "no-es-un-correo", "name": "X", "password": "secreta123"}
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


def test_login_returns_bearer_token() -> None:
    payload = {"email": "nuevo@example.com", "password": "secreta123"}
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
