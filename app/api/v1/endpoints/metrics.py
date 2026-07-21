"""Endpoint de métricas técnicas del servicio.

Expone latencia, uso de recursos y consumo del modelo, que sustentan el análisis
de desempeño y de costos, y alimentan el panel de métricas del frontend.
"""

from fastapi import APIRouter

from app.core.metrics import registro

router = APIRouter()


@router.get("")
async def metricas() -> dict[str, object]:
    """Devuelve los agregados de desempeño y consumo acumulados en el proceso."""
    return registro.resumen()
