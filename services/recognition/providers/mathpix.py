"""Proveedor de reconocimiento basado en Mathpix (respaldo de alta precisión)."""

from app.schemas.recognition import RecognitionResponse
from services.recognition.base import RecognitionProvider


class MathpixProvider(RecognitionProvider):
    name = "mathpix"

    def __init__(self, app_id: str | None = None, app_key: str | None = None) -> None:
        self._app_id = app_id
        self._app_key = app_key

    async def recognize(self, image_bytes: bytes, *, filename: str | None = None) -> RecognitionResponse:
        # TODO: llamar a la API de Mathpix (v3/text) y mapear la respuesta a LaTeX.
        return RecognitionResponse(latex="", confidence=0.0, provider=self.name)
