"""Endpoint de historial de conversiones por usuario (PB-10)."""

from fastapi import APIRouter

from app.schemas.recognition import ConversionRecord

router = APIRouter()


@router.get("", response_model=list[ConversionRecord])
async def list_history() -> list[ConversionRecord]:
    """Devuelve el historial de conversiones del usuario autenticado.

    TODO: filtrar por el usuario del token y paginar desde PostgreSQL.
    """
    return []
