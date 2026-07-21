"""Cliente compartido de Gemini y utilidades de uso de tokens.

Centraliza la creación del cliente para que el reconocimiento (imagen → LaTeX) y
la explicación paso a paso reutilicen la misma configuración y el mismo registro
de consumo, en lugar de instanciar el SDK por separado en cada servicio.

El consumo de tokens se registra aquí porque es el único punto por el que pasan
todas las llamadas al modelo; la capa de métricas lo consulta para calcular el
costo estimado.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field

from app.core.config import settings

logger = logging.getLogger(__name__)


class GeminiNoConfiguradoError(RuntimeError):
    """Se intentó usar Gemini sin haber definido `GEMINI_API_KEY`."""


@dataclass
class ConsumoTokens:
    """Acumulado de tokens consumidos por las llamadas al modelo."""

    llamadas: int = 0
    tokens_entrada: int = 0
    tokens_salida: int = 0
    tokens_razonamiento: int = 0
    tokens_totales: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def registrar(self, usage: object | None) -> None:
        """Suma el consumo de una respuesta del modelo.

        `usage` es el `usage_metadata` que devuelve el SDK. Se lee de forma
        defensiva: si el modelo no reporta algún campo, se cuenta como cero en
        lugar de propagar un error hacia la petición del usuario.
        """
        entrada = int(getattr(usage, "prompt_token_count", 0) or 0)
        salida = int(getattr(usage, "candidates_token_count", 0) or 0)
        razonamiento = int(getattr(usage, "thoughts_token_count", 0) or 0)
        total = int(getattr(usage, "total_token_count", 0) or 0) or (
            entrada + salida + razonamiento
        )

        with self._lock:
            self.llamadas += 1
            self.tokens_entrada += entrada
            self.tokens_salida += salida
            self.tokens_razonamiento += razonamiento
            self.tokens_totales += total

        logger.info(
            "gemini: tokens entrada=%d salida=%d razonamiento=%d total=%d",
            entrada,
            salida,
            razonamiento,
            total,
        )

    def costo_estimado_usd(self) -> float:
        """Costo estimado según la tarifa configurada por cada 1000 tokens."""
        return round(self.tokens_totales / 1000 * settings.gemini_cost_per_1k_tokens, 6)

    def resumen(self) -> dict[str, float | int]:
        """Instantánea del consumo, apta para exponer en el endpoint de métricas."""
        with self._lock:
            return {
                "llamadas": self.llamadas,
                "tokens_entrada": self.tokens_entrada,
                "tokens_salida": self.tokens_salida,
                "tokens_razonamiento": self.tokens_razonamiento,
                "tokens_totales": self.tokens_totales,
                "costo_usd_estimado": self.costo_estimado_usd(),
            }


# Acumulador de proceso. La capa de métricas (BE-4) lo consulta.
consumo = ConsumoTokens()


def crear_cliente(api_key: str | None = None):
    """Devuelve un cliente de Gemini listo para usar.

    Lanza `GeminiNoConfiguradoError` si no hay clave: los servicios que lo usan
    capturan esa excepción y degradan a una respuesta vacía, de modo que la API
    siga respondiendo aunque la capa de inteligencia no esté disponible.
    """
    clave = api_key or settings.gemini_api_key
    if not clave:
        raise GeminiNoConfiguradoError("No se configuró GEMINI_API_KEY.")

    from google import genai

    return genai.Client(api_key=clave)


def parte_imagen(data: bytes, mime_type: str = "image/png"):
    """Envuelve los bytes de una imagen en el tipo que espera el SDK."""
    from google.genai import types

    return types.Part.from_bytes(data=data, mime_type=mime_type)


def _config_razonamiento(types, presupuesto: int):
    """Traduce el presupuesto de razonamiento al campo que soporte el SDK.

    El SDK ha cambiado de forma de expresarlo: unas versiones aceptan un número
    de tokens (`thinking_budget`) y otras un nivel cualitativo
    (`thinking_level`). Se consulta el modelo en tiempo de ejecución en lugar de
    fijar uno, porque enviar el campo equivocado no falla al importar sino al
    llamar al modelo, es decir, en producción y no en el arranque.

    Devuelve `None` si la versión instalada no admite ninguno de los dos, para
    que la petición salga con la configuración por defecto en lugar de romper.
    """
    campos = getattr(types.ThinkingConfig, "model_fields", {})

    if "thinking_budget" in campos:
        return types.ThinkingConfig(thinking_budget=presupuesto)

    if "thinking_level" in campos:
        # Equivalencia aproximada entre presupuesto y nivel: sin presupuesto se
        # pide el mínimo razonamiento posible, y a partir de ahí se escala.
        if presupuesto <= 0:
            nivel = "MINIMAL"
        elif presupuesto <= 2048:
            nivel = "LOW"
        else:
            nivel = "HIGH"
        return types.ThinkingConfig(thinking_level=nivel)

    logger.warning(
        "La versión instalada del SDK no permite ajustar el razonamiento; "
        "se usa la configuración por defecto del modelo."
    )
    return None


def config_generacion(**extra: object):
    """Construye la configuración de generación con el presupuesto de razonamiento.

    Los modelos de la familia 3.x razonan antes de responder y esos tokens se
    cobran a tarifa de salida. Para tareas mecánicas —transcribir una expresión—
    ese razonamiento encarece y ralentiza sin mejorar el resultado, así que el
    presupuesto es configurable y se envía sólo cuando está definido.
    """
    from google.genai import types

    presupuesto = settings.gemini_thinking_budget
    if presupuesto is not None:
        configuracion = _config_razonamiento(types, presupuesto)
        if configuracion is not None:
            extra["thinking_config"] = configuracion

    return types.GenerateContentConfig(**extra)
