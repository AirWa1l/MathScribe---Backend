"""Agrega los routers de los endpoints de la versión 1 de la API."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, history, metrics, recognition, solve

api_router = APIRouter()
api_router.include_router(recognition.router, prefix="/recognition", tags=["recognition"])
api_router.include_router(solve.router, prefix="/solve", tags=["solve"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(history.router, prefix="/history", tags=["history"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["meta"])
