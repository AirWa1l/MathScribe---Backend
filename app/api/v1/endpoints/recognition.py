"""Endpoint de reconocimiento: recibe una imagen y devuelve su LaTeX (PB-04).

El endpoint delega en `services.recognition`, que abstrae al proveedor de IA
configurado (Gemini, GPT-4 Vision o Mathpix).
"""

from fastapi import APIRouter, File, UploadFile

from app.schemas.recognition import RecognitionResponse
from services.recognition.service import RecognitionService

router = APIRouter()
_service = RecognitionService()


@router.post("", response_model=RecognitionResponse)
async def recognize(image: UploadFile = File(...)) -> RecognitionResponse:
    """Convierte la imagen de una expresión matemática a LaTeX.

    TODO: validar formato/tamaño (PB-03), persistir la imagen en S3 y registrar la
    conversión en el historial del usuario autenticado.
    """
    content = await image.read()
    return await _service.recognize(content, filename=image.filename)
