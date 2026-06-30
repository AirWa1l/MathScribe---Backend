"""Esquemas de la respuesta de reconocimiento y del historial de conversiones."""

from datetime import datetime

from pydantic import BaseModel, Field


class RecognitionResponse(BaseModel):
    """Resultado de convertir una imagen a LaTeX."""

    latex: str = Field(..., description="Expresión reconocida en notación LaTeX.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confianza estimada del modelo.")
    provider: str = Field(..., description="Proveedor de IA que produjo el resultado.")


class ConversionRecord(BaseModel):
    """Entrada del historial de conversiones de un usuario."""

    id: int
    latex: str
    created_at: datetime
