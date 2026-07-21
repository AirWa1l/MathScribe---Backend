"""Pruebas de las métricas técnicas.

Verifican que lo que reporta el endpoint corresponde al tráfico real: los
números que sustentan el análisis de desempeño y de costos no deben poder
quedarse en cero ni inflarse con peticiones que no representan trabajo.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.metrics import RegistroMetricas, percentil, registro
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _registro_limpio():
    """Aísla cada prueba: las métricas son estado compartido del proceso."""
    registro.reiniciar()
    yield
    registro.reiniciar()


class TestPercentil:
    def test_lista_vacia_devuelve_cero(self) -> None:
        assert percentil([], 0.5) == 0.0

    def test_un_solo_valor(self) -> None:
        assert percentil([42.0], 0.95) == 42.0

    def test_mediana_de_valores_ordenados(self) -> None:
        assert percentil([10.0, 20.0, 30.0], 0.5) == 20.0

    def test_p95_se_aproxima_al_maximo(self) -> None:
        valores = [float(n) for n in range(1, 101)]
        assert percentil(valores, 0.95) == pytest.approx(95.05, abs=0.5)


class TestEndpointDeMetricas:
    def test_responde_con_la_estructura_esperada(self) -> None:
        """El frontend depende de estas llaves; si cambian, el panel se rompe."""
        cuerpo = client.get("/api/v1/metrics").json()

        assert {"count", "errores", "uptime_s", "latency_ms", "recursos", "gemini"} <= set(cuerpo)
        assert {"p50", "p95", "max", "promedio"} <= set(cuerpo["latency_ms"])
        assert {"cpu_percent", "memory_mb"} <= set(cuerpo["recursos"])
        assert {"tokens_totales", "costo_usd_estimado"} <= set(cuerpo["gemini"])

    def test_cuenta_las_peticiones_atendidas(self) -> None:
        for _ in range(3):
            client.post("/api/v1/solve", json={"latex": "x + 1"})

        cuerpo = client.get("/api/v1/metrics").json()

        assert cuerpo["count"] == 3
        assert cuerpo["latency_ms"]["p50"] > 0

    def test_no_contabiliza_el_healthcheck_ni_sus_propias_consultas(self) -> None:
        """La plataforma consulta /health constantemente: incluirlo falsearía la latencia."""
        client.get("/health")
        client.get("/api/v1/metrics")
        client.get("/health")

        assert client.get("/api/v1/metrics").json()["count"] == 0

    def test_registra_los_errores_por_separado(self) -> None:
        client.post("/api/v1/solve", json={"latex": "x + 1"})

        cuerpo = client.get("/api/v1/metrics").json()

        assert cuerpo["count"] == 1
        assert cuerpo["errores"] == 0

    def test_desglosa_la_latencia_por_ruta(self) -> None:
        client.post("/api/v1/solve", json={"latex": "x + 1"})
        client.post("/api/v1/solve", json={"latex": "x + 2"})

        por_ruta = client.get("/api/v1/metrics").json()["por_ruta"]

        assert por_ruta["/api/v1/solve"]["count"] == 2
        assert por_ruta["/api/v1/solve"]["p50"] > 0

    def test_expone_la_latencia_en_una_cabecera(self) -> None:
        respuesta = client.post("/api/v1/solve", json={"latex": "x + 1"})

        assert "X-Tiempo-Proceso-ms" in respuesta.headers
        assert float(respuesta.headers["X-Tiempo-Proceso-ms"]) > 0


class TestRegistro:
    def test_descarta_las_muestras_mas_antiguas(self) -> None:
        """El registro es acotado: no puede crecer sin límite en un proceso vivo."""
        propio = RegistroMetricas(max_muestras=3)
        for n in range(10):
            propio.registrar("/api/v1/solve", "POST", 200, float(n))

        assert propio.resumen()["count"] == 3

    def test_reporta_cpu_y_memoria_del_proceso(self) -> None:
        recursos = RegistroMetricas().resumen()["recursos"]

        # La memoria residente de un proceso vivo nunca es cero.
        assert recursos["memory_mb"] > 0
        assert recursos["cpu_percent"] >= 0

    def test_sin_trafico_los_agregados_son_cero_y_no_fallan(self) -> None:
        resumen = RegistroMetricas().resumen()

        assert resumen["count"] == 0
        assert resumen["latency_ms"]["p95"] == 0.0
