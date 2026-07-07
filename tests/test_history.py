"""Prueba del endpoint de historial `GET /api/v1/history` (andamiaje).

Por ahora el historial no consulta la base de datos y devuelve una lista vacía;
la prueba fija ese contrato hasta que Sprint 2 conecte PostgreSQL.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_history_returns_empty_list() -> None:
    response = client.get("/api/v1/history")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert body == []
