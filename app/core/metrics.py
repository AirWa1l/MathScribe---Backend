"""Registro en memoria de las métricas técnicas del servicio.

Mide latencia por petición y muestrea CPU y memoria del proceso, y consolida el
consumo de tokens que reporta la capa de inteligencia. Los agregados se exponen
en `GET /api/v1/metrics` y alimentan el análisis de desempeño y de costos.

El almacenamiento es en memoria y acotado a las últimas peticiones: el objetivo
es caracterizar el comportamiento del sistema durante una sesión de uso o una
demostración, no construir un histórico persistente, que exigiría una
infraestructura de observabilidad fuera del alcance del proyecto. Al reiniciar
el servicio los contadores vuelven a cero, y así se documenta.
"""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from dataclasses import dataclass

import psutil

logger = logging.getLogger(__name__)

# Número de peticiones recientes sobre las que se calculan los percentiles.
_MAX_MUESTRAS = 500

# Rutas que no representan trabajo del agente y distorsionarían la latencia:
# el healthcheck lo consulta la plataforma cada pocos segundos, y consultar las
# propias métricas no debería alterarlas.
_RUTAS_EXCLUIDAS = frozenset({"/health", "/api/v1/metrics"})


@dataclass(frozen=True)
class Muestra:
    """Una petición medida."""

    ruta: str
    metodo: str
    estado: int
    duracion_ms: float


def percentil(valores: list[float], porcentaje: float) -> float:
    """Percentil por interpolación lineal sobre una lista ya ordenada.

    Se implementa aquí para no añadir una dependencia sólo por esto. Con una
    sola muestra devuelve ese valor, en lugar de fallar.
    """
    if not valores:
        return 0.0
    if len(valores) == 1:
        return round(valores[0], 2)

    posicion = (len(valores) - 1) * porcentaje
    inferior = int(posicion)
    superior = min(inferior + 1, len(valores) - 1)
    peso = posicion - inferior
    return round(valores[inferior] * (1 - peso) + valores[superior] * peso, 2)


class RegistroMetricas:
    """Acumulador de métricas del proceso, seguro entre hilos."""

    def __init__(self, max_muestras: int = _MAX_MUESTRAS) -> None:
        self._muestras: deque[Muestra] = deque(maxlen=max_muestras)
        self._lock = threading.Lock()
        self._proceso = psutil.Process()
        self._inicio = time.time()
        # La primera llamada a cpu_percent siempre devuelve 0.0 porque necesita
        # un intervalo previo con el que comparar; se consume aquí para que las
        # lecturas posteriores sean reales.
        self._proceso.cpu_percent(interval=None)

    def registrar(self, ruta: str, metodo: str, estado: int, duracion_ms: float) -> None:
        with self._lock:
            self._muestras.append(Muestra(ruta, metodo, estado, duracion_ms))

    def reiniciar(self) -> None:
        """Vacía las muestras. Se usa para aislar las pruebas entre sí."""
        with self._lock:
            self._muestras.clear()

    def _recursos(self) -> dict[str, float]:
        """Lee CPU y memoria del proceso, tolerando que el sistema no lo permita."""
        try:
            memoria_mb = self._proceso.memory_info().rss / (1024 * 1024)
            cpu = self._proceso.cpu_percent(interval=None)
        except psutil.Error:  # pragma: no cover - depende del sistema operativo
            logger.warning("No se pudieron leer los recursos del proceso.")
            return {"cpu_percent": 0.0, "memory_mb": 0.0}
        return {"cpu_percent": round(cpu, 2), "memory_mb": round(memoria_mb, 2)}

    def resumen(self) -> dict[str, object]:
        """Agregados de las peticiones medidas y del consumo del modelo."""
        # Importación diferida: la capa de inteligencia importa la configuración,
        # y hacerlo en el arranque crearía un ciclo con el middleware.
        from services.llm.gemini_client import consumo

        with self._lock:
            muestras = list(self._muestras)

        duraciones = sorted(m.duracion_ms for m in muestras)
        errores = sum(1 for m in muestras if m.estado >= 500)

        return {
            "count": len(muestras),
            "errores": errores,
            "uptime_s": round(time.time() - self._inicio, 1),
            "latency_ms": {
                "p50": percentil(duraciones, 0.50),
                "p95": percentil(duraciones, 0.95),
                "max": round(duraciones[-1], 2) if duraciones else 0.0,
                "promedio": round(sum(duraciones) / len(duraciones), 2) if duraciones else 0.0,
            },
            "recursos": self._recursos(),
            "gemini": consumo.resumen(),
            "por_ruta": self._por_ruta(muestras),
        }

    def _por_ruta(self, muestras: list[Muestra]) -> dict[str, dict[str, float]]:
        """Latencia desglosada por endpoint.

        Es lo que permite comparar el costo temporal del reconocimiento —que
        incluye visión y una llamada al modelo— frente al de la resolución.
        """
        agrupadas: dict[str, list[float]] = {}
        for muestra in muestras:
            agrupadas.setdefault(muestra.ruta, []).append(muestra.duracion_ms)

        return {
            ruta: {
                "count": len(duraciones),
                "p50": percentil(sorted(duraciones), 0.50),
                "p95": percentil(sorted(duraciones), 0.95),
            }
            for ruta, duraciones in sorted(agrupadas.items())
        }


registro = RegistroMetricas()


async def middleware_metricas(request, call_next):
    """Mide cada petición y deja una línea de registro estructurada."""
    inicio = time.perf_counter()
    respuesta = await call_next(request)
    duracion_ms = (time.perf_counter() - inicio) * 1000

    ruta = request.url.path
    if ruta not in _RUTAS_EXCLUIDAS:
        registro.registrar(ruta, request.method, respuesta.status_code, duracion_ms)
        logger.info(
            "peticion metodo=%s ruta=%s estado=%d duracion_ms=%.2f",
            request.method,
            ruta,
            respuesta.status_code,
            duracion_ms,
        )

    # Expone la medición en la respuesta: permite verificar la latencia desde el
    # navegador sin depender del endpoint de métricas.
    respuesta.headers["X-Tiempo-Proceso-ms"] = f"{duracion_ms:.2f}"
    return respuesta
