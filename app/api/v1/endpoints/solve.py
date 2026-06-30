"""Endpoint de resolución: resuelve y explica una expresión en LaTeX (PB-07, PB-08)."""

from fastapi import APIRouter

from app.schemas.solve import SolveRequest, SolveResponse
from services.solver.service import SolverService

router = APIRouter()
_service = SolverService()


@router.post("", response_model=SolveResponse)
async def solve(payload: SolveRequest) -> SolveResponse:
    """Resuelve la expresión y devuelve la solución con explicación paso a paso."""
    return await _service.solve(payload.latex)
