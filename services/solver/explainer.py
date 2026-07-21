"""Generación de la explicación paso a paso en lenguaje natural mediante un LLM.

Toma los pasos ya calculados y verificados por SymPy y los redacta de forma
didáctica. El modelo **no participa en el cálculo**: recibe los pasos hechos y
sólo sustituye su descripción por una redacción más clara. Si su respuesta no
encaja con los pasos recibidos, se descarta y se conservan los originales.

Esa restricción es deliberada: es lo que impide que una alucinación del modelo
llegue al usuario como si fuera matemática verificada.
"""

from __future__ import annotations

import asyncio
import json
import logging

from app.core.config import settings
from app.schemas.solve import SolutionStep
from services.llm.gemini_client import (
    GeminiNoConfiguradoError,
    config_generacion,
    consumo,
    crear_cliente,
)

logger = logging.getLogger(__name__)

PROMPT_EXPLICACION = (
    "Eres un profesor de matemáticas que explica a un estudiante de secundaria.\n"
    "Te doy la expresión original y los pasos ya resueltos por un motor de álgebra "
    "simbólica.\n\n"
    "Reglas estrictas:\n"
    "1. NO recalcules nada. Los valores de los pasos son correctos y definitivos.\n"
    "2. Reescribe únicamente la descripción de cada paso, en español, con una o dos "
    "frases claras que expliquen QUÉ se hace y POR QUÉ.\n"
    "3. Mantén el mismo número de pasos y el mismo orden.\n"
    "4. No menciones el motor simbólico ni el proceso interno.\n"
    "5. Responde SÓLO con un arreglo JSON de cadenas, una por paso, sin ningún otro "
    "texto ni delimitadores de código.\n\n"
    "Ejemplo de respuesta para dos pasos:\n"
    '["Primera explicación.", "Segunda explicación."]'
)


def construir_entrada(latex: str, steps: list[SolutionStep]) -> str:
    """Arma el contexto que se envía al modelo, en texto plano y acotado."""
    lineas = [f"Expresión original: {latex}", "", "Pasos calculados:"]
    for paso in steps:
        detalle = f"{paso.order}. {paso.description}"
        if paso.latex:
            detalle += f"  ->  {paso.latex}"
        lineas.append(detalle)
    return "\n".join(lineas)


def extraer_descripciones(texto: str, esperadas: int) -> list[str] | None:
    """Interpreta la respuesta del modelo y valida que encaje con los pasos.

    Devuelve `None` si la respuesta no es un arreglo JSON de cadenas con
    exactamente la longitud esperada: ante cualquier desajuste se prefiere
    conservar las descripciones originales antes que emparejar mal las
    explicaciones con los pasos.
    """
    limpio = texto.strip()
    inicio, fin = limpio.find("["), limpio.rfind("]")
    if inicio == -1 or fin == -1 or fin < inicio:
        return None

    try:
        descripciones = json.loads(limpio[inicio : fin + 1])
    except json.JSONDecodeError:
        return None

    if not isinstance(descripciones, list) or len(descripciones) != esperadas:
        return None
    if not all(isinstance(d, str) and d.strip() for d in descripciones):
        return None

    return [d.strip() for d in descripciones]


async def _generar(cliente, latex: str, steps: list[SolutionStep]):
    """Realiza la llamada al modelo en un hilo aparte para no bloquear el bucle."""
    return await asyncio.to_thread(
        cliente.models.generate_content,
        model=settings.gemini_model,
        contents=[PROMPT_EXPLICACION, construir_entrada(latex, steps)],
        config=config_generacion(),
    )


async def explain(latex: str, steps: list[SolutionStep]) -> list[SolutionStep]:
    """Enriquece los pasos con descripciones en lenguaje natural.

    Devuelve siempre una lista utilizable: ante falta de clave, error de red o
    respuesta inconsistente, se devuelven los pasos originales de SymPy. Se
    pierde la redacción, nunca la corrección.
    """
    if not steps:
        return steps

    try:
        cliente = crear_cliente()
    except GeminiNoConfiguradoError:
        logger.warning("Explicación omitida: falta GEMINI_API_KEY; se usan los pasos de SymPy.")
        return steps

    try:
        respuesta = await _generar(cliente, latex, steps)
    except Exception:  # noqa: BLE001 - la causa concreta queda en el log
        logger.exception("Falló la llamada a Gemini durante la explicación.")
        return steps

    consumo.registrar(getattr(respuesta, "usage_metadata", None))

    descripciones = extraer_descripciones(getattr(respuesta, "text", "") or "", len(steps))
    if descripciones is None:
        logger.warning(
            "La explicación del modelo no encajó con los %d pasos; se conservan los originales.",
            len(steps),
        )
        return steps

    # Se sustituye sólo la descripción: `order` y `latex` provienen de SymPy y
    # son los que garantizan que el procedimiento mostrado sea correcto.
    return [
        SolutionStep(order=paso.order, description=descripcion, latex=paso.latex)
        for paso, descripcion in zip(steps, descripciones, strict=True)
    ]
