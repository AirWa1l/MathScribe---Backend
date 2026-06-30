"""Contrato del proveedor de reconocimiento (imagen → LaTeX).

Desacoplar la capa de inteligencia detrás de esta interfaz permite cambiar de proveedor
de IA o añadir un modelo open source sin tocar la API ni el frontend.
"""

from abc import ABC, abstractmethod

from app.schemas.recognition import RecognitionResponse


class RecognitionProvider(ABC):
    """Interfaz que todo proveedor de reconocimiento debe implementar."""

    name: str = "base"

    @abstractmethod
    async def recognize(self, image_bytes: bytes, *, filename: str | None = None) -> RecognitionResponse:
        """Convierte los bytes de una imagen en una expresión LaTeX."""
        raise NotImplementedError
