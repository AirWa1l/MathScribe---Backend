"""Resolución simbólica con SymPy.

Convierte la expresión LaTeX a una expresión de SymPy y la resuelve o simplifica
según el tipo de operación que representa. Es la base verificable del resultado:
el modelo de lenguaje sólo redacta después los pasos que aquí se calculan, y no
puede alterar sus valores.

Ante una expresión que no se puede interpretar se devuelve un resultado vacío en
lugar de una excepción, porque el LaTeX proviene del reconocimiento de una
imagen y equivocarse es un caso esperado, no un fallo del sistema.
"""

from __future__ import annotations

import logging

import sympy
from sympy.parsing.latex import parse_latex

from app.schemas.solve import SolutionStep

logger = logging.getLogger(__name__)


def _paso(orden: int, descripcion: str, expresion: object | None = None) -> SolutionStep:
    """Construye un paso, convirtiendo la expresión de SymPy a LaTeX si la hay."""
    latex = sympy.latex(expresion) if expresion is not None else None
    return SolutionStep(order=orden, description=descripcion, latex=latex)


def _resolver_integral(expr: sympy.Integral) -> tuple[object, list[SolutionStep]]:
    """Resuelve una integral mostrando la antiderivada antes del resultado."""
    pasos = [_paso(1, "Planteamos la integral que se debe calcular.", expr)]

    integrando = expr.function
    variable = expr.variables[0] if expr.variables else sympy.Symbol("x")
    antiderivada = sympy.integrate(integrando, variable)
    pasos.append(
        _paso(
            2,
            f"Calculamos la antiderivada de {sympy.latex(integrando)} respecto de "
            f"{sympy.latex(variable)}.",
            antiderivada,
        )
    )

    resultado = expr.doit()
    es_definida = bool(expr.limits and len(expr.limits[0]) == 3)
    if es_definida:
        _, inferior, superior = expr.limits[0]
        pasos.append(
            _paso(
                3,
                f"Evaluamos la antiderivada entre {sympy.latex(inferior)} y "
                f"{sympy.latex(superior)}.",
                resultado,
            )
        )
    else:
        # SymPy omite la constante de integración; se añade explícitamente
        # porque sin ella la primitiva estaría incompleta.
        resultado = resultado + sympy.Symbol("C")
        pasos.append(
            _paso(
                3, "Añadimos la constante de integración al ser una integral indefinida.", resultado
            )
        )

    return resultado, pasos


def _resolver_derivada(expr: sympy.Derivative) -> tuple[object, list[SolutionStep]]:
    """Deriva la expresión mostrando el planteamiento y el resultado."""
    pasos = [_paso(1, "Planteamos la derivada que se debe calcular.", expr)]
    resultado = expr.doit()
    variables = ", ".join(sympy.latex(v) for v in expr.variables)
    pasos.append(
        _paso(2, f"Aplicamos las reglas de derivación respecto de {variables}.", resultado)
    )
    return resultado, pasos


def _resolver_ecuacion(expr: sympy.Eq) -> tuple[object, list[SolutionStep]]:
    """Despeja las incógnitas de una ecuación."""
    pasos = [_paso(1, "Planteamos la ecuación que se debe resolver.", expr)]

    incognitas = sorted(expr.free_symbols, key=lambda s: s.name)
    if not incognitas:
        # Sin incógnitas la igualdad es una afirmación: sólo cabe verificarla.
        es_cierta = sympy.simplify(expr.lhs - expr.rhs) == 0
        resultado = sympy.true if es_cierta else sympy.false
        pasos.append(
            _paso(
                2,
                "La igualdad no tiene incógnitas, así que comprobamos si es verdadera.",
                resultado,
            )
        )
        return resultado, pasos

    incognita = incognitas[0]
    # El paso de normalización sólo informa cuando hay términos al otro lado;
    # si la ecuación ya está igualada a cero, repetiría la línea anterior.
    if expr.rhs != 0:
        normalizada = sympy.simplify(expr.lhs - expr.rhs)
        pasos.append(
            _paso(
                2,
                "Pasamos todos los términos a un lado de la igualdad.",
                sympy.Eq(normalizada, 0),
            )
        )

    soluciones = sympy.solve(expr, incognita)
    resultado = sympy.FiniteSet(*soluciones) if soluciones else sympy.EmptySet
    pasos.append(
        _paso(
            len(pasos) + 1,
            f"Resolvemos para {sympy.latex(incognita)} y obtenemos las soluciones.",
            resultado,
        )
    )
    return resultado, pasos


def _simplificar(expr: object) -> tuple[object, list[SolutionStep]]:
    """Simplifica y, si aporta, factoriza la expresión."""
    pasos = [_paso(1, "Partimos de la expresión reconocida.", expr)]

    simplificada = sympy.simplify(expr)
    if simplificada != expr:
        pasos.append(_paso(2, "Simplificamos la expresión.", simplificada))

    try:
        factorizada = sympy.factor(simplificada)
    except sympy.PolynomialError:  # pragma: no cover - depende de la expresión
        factorizada = simplificada

    if factorizada != simplificada:
        pasos.append(_paso(len(pasos) + 1, "Factorizamos el resultado.", factorizada))
        return factorizada, pasos

    if len(pasos) == 1:
        # Sin transformaciones, un único paso repetiría la entrada sin explicar
        # nada; se deja constancia explícita de que ya estaba simplificada.
        pasos.append(_paso(2, "La expresión ya está en su forma más simple.", simplificada))

    return simplificada, pasos


def solve_expression(latex: str) -> tuple[str, list[SolutionStep]]:
    """Resuelve la expresión y devuelve `(resultado_latex, pasos)`.

    Detecta el tipo de operación a partir de la expresión ya interpretada por
    SymPy —integral, derivada, ecuación o expresión a simplificar— en lugar de
    inspeccionar el texto LaTeX, que admite muchas grafías para lo mismo.
    """
    if not latex or not latex.strip():
        return "", []

    try:
        expr = parse_latex(latex)
    except Exception:  # noqa: BLE001 - cualquier fallo de parseo se trata igual
        logger.warning("No se pudo interpretar el LaTeX recibido: %r", latex[:120])
        return "", []

    try:
        if isinstance(expr, sympy.Integral):
            resultado, pasos = _resolver_integral(expr)
        elif isinstance(expr, sympy.Derivative):
            resultado, pasos = _resolver_derivada(expr)
        elif isinstance(expr, sympy.Eq):
            resultado, pasos = _resolver_ecuacion(expr)
        else:
            resultado, pasos = _simplificar(expr)
    except Exception:  # noqa: BLE001 - la causa concreta queda en el log
        logger.exception("Falló la resolución simbólica de %r", latex[:120])
        return "", []

    return sympy.latex(resultado), pasos
