"""Servicio de reconocimiento: selecciona el proveedor configurado y delega en él."""

from app.core.config import settings
from app.schemas.recognition import RecognitionResponse
from services.recognition.base import RecognitionProvider
from services.recognition.providers.gemini import GeminiProvider
from services.recognition.providers.mathpix import MathpixProvider
from services.recognition.providers.openai_vision import OpenAIVisionProvider


def _build_provider() -> RecognitionProvider:
    """Construye el proveedor según `RECOGNITION_PROVIDER`."""
    provider = settings.recognition_provider.lower()
    if provider == "openai":
        return OpenAIVisionProvider(api_key=settings.openai_api_key)
    if provider == "mathpix":
        return MathpixProvider(app_id=settings.mathpix_app_id, app_key=settings.mathpix_app_key)
    return GeminiProvider(api_key=settings.gemini_api_key)


class RecognitionService:
    """Fachada estable para la API; oculta qué proveedor está activo."""

    def __init__(self, provider: RecognitionProvider | None = None) -> None:
        self._provider = provider or _build_provider()

    async def recognize(
        self, image_bytes: bytes, *, filename: str | None = None
    ) -> RecognitionResponse:
        return await self._provider.recognize(image_bytes, filename=filename)
