"""Base declarativa de SQLAlchemy compartida por todos los modelos."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Clase base para los modelos ORM de MathScribe."""
