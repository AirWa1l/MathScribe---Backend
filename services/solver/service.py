"""Servicio de resolución: combina SymPy (cálculo) y LLM (explicación)."""

from app.schemas.solve import SolveResponse
from services.solver.explainer import explain
from services.solver.sympy_solver import solve_expression


class SolverService:
    """Orquesta el cálculo simbólico y la redacción de la explicación."""

    async def solve(self, latex: str) -> SolveResponse:
        result, steps = solve_expression(latex)
        steps = await explain(latex, steps)
        return SolveResponse(result=result, steps=steps)
