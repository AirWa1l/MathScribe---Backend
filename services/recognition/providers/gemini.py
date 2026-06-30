"""Proveedor de reconocimiento basado en Google Gemini (motor principal del MVP)."""

from app.schemas.recognition import RecognitionResponse
from services.recognition.base import RecognitionProvider


class GeminiProvider(RecognitionProvider):
    name = "gemini"

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key

    async def recognize(self, image_bytes: bytes, *, filename: str | None = None) -> RecognitionResponse:
        # TODO: enviar la imagen al modelo multimodal de Gemini y parsear el LaTeX.
        return RecognitionResponse(
            latex=r"\int_0^1 x^2\,dx = \frac{1}{3}",
            confidence=0.0,
            provider=self.name,
        )
