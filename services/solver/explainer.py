"""Generación de la explicación paso a paso en lenguaje natural mediante un LLM.

Toma los pasos verificados por SymPy y los redacta de forma didáctica (PB-08).
"""

from app.schemas.solve import SolutionStep


async def explain(latex: str, steps: list[SolutionStep]) -> list[SolutionStep]:
    """Enriquece los pasos con descripciones en lenguaje natural.

    TODO: construir el prompt con el LLM configurado y devolver los pasos redactados.
    """
    return steps
