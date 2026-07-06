"""Proveedor de reconocimiento basado en GPT-4 Vision."""

from app.schemas.recognition import RecognitionResponse
from services.recognition.base import RecognitionProvider


class OpenAIVisionProvider(RecognitionProvider):
    name = "openai"

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key

    async def recognize(
        self, image_bytes: bytes, *, filename: str | None = None
    ) -> RecognitionResponse:
        # TODO: enviar la imagen al endpoint de visión de OpenAI y parsear el LaTeX.
        return RecognitionResponse(latex="", confidence=0.0, provider=self.name)
