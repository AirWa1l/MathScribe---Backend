"""Pruebas del endpoint de resolución `POST /api/v1/solve` (andamiaje).

Documentan el contrato actual: el endpoint responde 200 y devuelve un objeto con
las llaves `result` y `steps`. La resolución simbólica real (SymPy) llega en
Sprint 2; por ahora la prueba fija la forma de la respuesta.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_solve_returns_result_and_steps() -> None:
    response = client.post("/api/v1/solve", json={"latex": r"\int_0^1 x^2\,dx"})
    assert response.status_code == 200
    body = response.json()
    assert "result" in body
    assert "steps" in body
    assert isinstance(body["steps"], list)


def test_solve_requires_latex() -> None:
    response = client.post("/api/v1/solve", json={})
    assert response.status_code == 422
