"""Punto de entrada de la API de MathScribe.

Configura la aplicación FastAPI, el middleware de CORS y registra el router de la v1.
Este módulo representa la *capa de aplicación* descrita en la arquitectura preliminar:
orquesta las llamadas a la capa de inteligencia y centraliza autenticación y trazabilidad.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Agente visual multimodal: imagen → LaTeX, resolución y explicación paso a paso.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    """Sonda de salud para orquestadores y balanceadores."""
    return {"status": "ok", "environment": settings.environment}
