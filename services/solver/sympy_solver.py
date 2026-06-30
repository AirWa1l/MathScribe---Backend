"""Resolución simbólica con SymPy.

Convierte la expresión LaTeX a una expresión de SymPy y la resuelve/simplifica.
Es la base verificable del resultado; el LLM se encarga de la narración en lenguaje natural.
"""

from app.schemas.solve import SolutionStep


def solve_expression(latex: str) -> tuple[str, list[SolutionStep]]:
    """Resuelve la expresión y devuelve (resultado_latex, pasos).

    TODO: usar `sympy.parsing.latex.parse_latex` y elegir la operación adecuada
    (resolver ecuación, derivar, integrar, simplificar) según la expresión.
    """
    result = ""
    steps: list[SolutionStep] = []
    return result, steps
