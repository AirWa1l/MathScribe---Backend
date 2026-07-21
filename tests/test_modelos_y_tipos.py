"""Pruebas del modelo de datos y de los tipos compartidos.

Se ejercitan contra SQLite en memoria para no depender de PostgreSQL en el
pipeline. Verifican el esquema y las reglas que el resto del sistema da por
sentadas: unicidad del correo, relación usuario–conversiones y borrado en
cascada.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import Conversion, User
from shared.types import ALLOWED_IMAGE_TYPES, MAX_IMAGE_BYTES, RecognitionProviderName


@pytest.fixture
def sesion():
    """Base de datos temporal en memoria, aislada por prueba."""
    motor = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(motor)
    with Session(motor) as sesion:
        yield sesion
    Base.metadata.drop_all(motor)


class TestModelos:
    def test_persiste_un_usuario_con_sus_conversiones(self, sesion: Session) -> None:
        usuario = User(email="ana@example.com", name="Ana", hashed_password="hash")
        usuario.conversions.append(Conversion(latex="x^2", provider="gemini"))
        sesion.add(usuario)
        sesion.commit()

        recuperado = sesion.scalar(select(User).where(User.email == "ana@example.com"))

        assert recuperado is not None
        assert len(recuperado.conversions) == 1
        assert recuperado.conversions[0].latex == "x^2"

    def test_el_correo_es_unico(self, sesion: Session) -> None:
        """Dos cuentas con el mismo correo romperían el inicio de sesión."""
        sesion.add(User(email="dup@example.com", name="Uno", hashed_password="a"))
        sesion.commit()

        sesion.add(User(email="dup@example.com", name="Dos", hashed_password="b"))
        with pytest.raises(IntegrityError):
            sesion.commit()

    def test_borrar_el_usuario_arrastra_su_historial(self, sesion: Session) -> None:
        """Es un requisito de privacidad: no deben quedar conversiones huérfanas."""
        usuario = User(email="baja@example.com", name="Baja", hashed_password="h")
        usuario.conversions.append(Conversion(latex="x", provider="gemini"))
        sesion.add(usuario)
        sesion.commit()

        sesion.delete(usuario)
        sesion.commit()

        assert sesion.scalars(select(Conversion)).all() == []

    def test_la_imagen_es_opcional_en_una_conversion(self, sesion: Session) -> None:
        """Por omisión no se guarda la imagen; sólo el LaTeX resultante."""
        usuario = User(email="sin@example.com", name="Sin", hashed_password="h")
        usuario.conversions.append(Conversion(latex="y", provider="gemini"))
        sesion.add(usuario)
        sesion.commit()

        assert usuario.conversions[0].image_url is None


class TestTiposCompartidos:
    def test_los_nombres_de_proveedor_coinciden_con_los_implementados(self) -> None:
        assert {p.value for p in RecognitionProviderName} == {"gemini", "openai", "mathpix"}

    def test_se_comparan_como_cadenas(self) -> None:
        """El valor viaja como texto en la configuración y en las respuestas."""
        assert RecognitionProviderName.GEMINI == "gemini"

    def test_solo_se_aceptan_formatos_de_imagen_web(self) -> None:
        assert ALLOWED_IMAGE_TYPES == {"image/png", "image/jpeg", "image/webp"}
        assert "image/svg+xml" not in ALLOWED_IMAGE_TYPES

    def test_el_limite_de_tamano_es_razonable_para_una_foto(self) -> None:
        assert MAX_IMAGE_BYTES == 8 * 1024 * 1024
