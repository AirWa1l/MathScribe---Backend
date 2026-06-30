"""Esquemas de la petición y respuesta de resolución/explicación."""

from pydantic import BaseModel, Field


class SolveRequest(BaseModel):
    latex: str = Field(..., description="Expresión a resolver, en notación LaTeX.")


class SolutionStep(BaseModel):
    """Un paso del procedimiento de resolución."""

    order: int
    description: str
    latex: str | None = None


class SolveResponse(BaseModel):
    result: str = Field(..., description="Resultado final en LaTeX.")
    steps: list[SolutionStep] = Field(default_factory=list)
