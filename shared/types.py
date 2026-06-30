"""Tipos y enumeraciones compartidas."""

from enum import Enum


class RecognitionProviderName(str, Enum):
    GEMINI = "gemini"
    OPENAI = "openai"
    MATHPIX = "mathpix"


# Formatos de imagen aceptados en la captura/carga (PB-03).
ALLOWED_IMAGE_TYPES: frozenset[str] = frozenset(
    {"image/png", "image/jpeg", "image/webp"}
)

# Tamaño máximo de imagen aceptado (bytes).
MAX_IMAGE_BYTES: int = 8 * 1024 * 1024
