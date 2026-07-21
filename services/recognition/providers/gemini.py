"""Proveedor de reconocimiento basado en Google Gemini (motor principal del MVP).

Recibe la imagen ya preprocesada y recortada por OpenCV y pide al modelo
multimodal la transcripción a LaTeX. El modelo se usa exclusivamente como OCR
matemático: no resuelve ni interpreta la expresión, porque de eso se encarga
SymPy más adelante en el flujo, donde el resultado sí es verificable.
"""

from __future__ import annotations

import asyncio
import logging
import re

from app.core.config import settings
from app.schemas.recognition import RecognitionResponse
from services.llm.gemini_client import (
    GeminiNoConfiguradoError,
    config_generacion,
    consumo,
    crear_cliente,
    parte_imagen,
)
from services.recognition.base import RecognitionProvider

logger = logging.getLogger(__name__)

# Instrucción deliberadamente restrictiva: sin ella el modelo tiende a saludar,
# explicar o resolver la expresión, y cualquier texto extra rompe el parseo de
# SymPy en el siguiente paso del flujo.
PROMPT_RECONOCIMIENTO = (
    "Eres un OCR matemático. Transcribe la expresión matemática de la imagen a "
    "LaTeX válido.\n"
    "Reglas estrictas:\n"
    "1. Devuelve ÚNICAMENTE la expresión en LaTeX, sin explicaciones ni comentarios.\n"
    "2. No uses delimitadores: nada de ```latex, ```, $, $$ ni \\[ \\].\n"
    "3. No resuelvas ni simplifiques la expresión: transcríbela tal como aparece.\n"
    "4. Si la imagen no contiene ninguna expresión matemática legible, devuelve "
    "una cadena vacía."
)

# Confianza asumida cuando el modelo no reporta probabilidades. Gemini no expone
# `avg_logprobs` de forma consistente, así que se declara un valor explícito en
# lugar de simular una precisión que no se está midiendo.
_CONFIANZA_POR_DEFECTO = 0.9

_PATRON_FENCE = re.compile(r"^```(?:latex|tex)?\s*|\s*```$", re.IGNORECASE)
_PATRON_DELIMITADORES = re.compile(r"^(\$\$|\$|\\\[|\\\()\s*|\s*(\$\$|\$|\\\]|\\\))$")


def limpiar_latex(texto: str) -> str:
    """Elimina los envoltorios con los que el modelo suele decorar la respuesta.

    Aunque el prompt los prohíbe, el modelo los añade de forma intermitente; se
    limpian aquí porque `sympy.parsing.latex` falla ante cualquier carácter que
    no forme parte de la expresión.
    """
    limpio = texto.strip()
    limpio = _PATRON_FENCE.sub("", limpio).strip()
    anterior = None
    while anterior != limpio:
        anterior = limpio
        limpio = _PATRON_DELIMITADORES.sub("", limpio).strip()
    return limpio


class GeminiProvider(RecognitionProvider):
    """Reconocimiento imagen → LaTeX mediante el modelo multimodal de Gemini."""

    name = "gemini"

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self._api_key = api_key
        self._model = model or settings.gemini_model

    async def recognize(
        self, image_bytes: bytes, *, filename: str | None = None
    ) -> RecognitionResponse:
        """Transcribe la imagen a LaTeX.

        Ante cualquier fallo (falta de clave, error de red, cuota agotada) se
        devuelve una respuesta degradada con `latex` vacío en lugar de propagar
        la excepción: la interfaz debe poder mostrar un mensaje útil y ofrecer
        reintentar, no una pantalla de error 500.
        """
        try:
            cliente = crear_cliente(self._api_key)
        except GeminiNoConfiguradoError:
            logger.warning(
                "Reconocimiento omitido: falta GEMINI_API_KEY; se devuelve resultado vacío."
            )
            return self._respuesta_degradada()

        try:
            respuesta = await asyncio.to_thread(
                cliente.models.generate_content,
                model=self._model,
                contents=[
                    parte_imagen(image_bytes),
                    PROMPT_RECONOCIMIENTO,
                ],
                config=config_generacion(),
            )
        except Exception:  # noqa: BLE001 - la causa concreta queda en el log
            logger.exception("Falló la llamada a Gemini durante el reconocimiento.")
            return self._respuesta_degradada()

        consumo.registrar(getattr(respuesta, "usage_metadata", None))

        latex = limpiar_latex(getattr(respuesta, "text", "") or "")
        if not latex:
            logger.info("Gemini no encontró una expresión matemática en la imagen.")
            return self._respuesta_degradada()

        logger.info("Expresión reconocida (%d caracteres).", len(latex))
        return RecognitionResponse(
            latex=latex,
            confidence=_CONFIANZA_POR_DEFECTO,
            provider=self.name,
        )

    def _respuesta_degradada(self) -> RecognitionResponse:
        """Respuesta vacía y explícita cuando no se pudo reconocer nada."""
        return RecognitionResponse(latex="", confidence=0.0, provider=self.name)
