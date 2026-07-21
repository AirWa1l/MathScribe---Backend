"""Pruebas del servicio de reconocimiento y de la selección de proveedor.

La interfaz `RecognitionProvider` es la pieza que permite cambiar de proveedor
de IA sin tocar la API ni el frontend, y es la mitigación declarada frente al
riesgo de depender de un servicio externo. Estas pruebas verifican que esa
sustitución realmente funciona, no sólo que la clase existe.
"""

from __future__ import annotations

import asyncio

import pytest

from app.schemas.recognition import RecognitionResponse
from services.recognition import service as modulo_servicio
from services.recognition.base import RecognitionProvider
from services.recognition.providers.gemini import GeminiProvider
from services.recognition.providers.mathpix import MathpixProvider
from services.recognition.providers.openai_vision import OpenAIVisionProvider
from services.recognition.service import RecognitionService, _build_provider


def ejecutar(corrutina):
    return asyncio.run(corrutina)


class ProveedorFalso(RecognitionProvider):
    """Proveedor de prueba que registra lo que recibe."""

    name = "falso"

    def __init__(self) -> None:
        self.recibido: bytes | None = None
        self.nombre_archivo: str | None = None

    async def recognize(
        self, image_bytes: bytes, *, filename: str | None = None
    ) -> RecognitionResponse:
        self.recibido = image_bytes
        self.nombre_archivo = filename
        return RecognitionResponse(latex="x^2", confidence=0.5, provider=self.name)


class TestSeleccionDeProveedor:
    @pytest.mark.parametrize(
        ("configurado", "esperado"),
        [
            ("gemini", GeminiProvider),
            ("openai", OpenAIVisionProvider),
            ("mathpix", MathpixProvider),
            ("GEMINI", GeminiProvider),
            ("OpenAI", OpenAIVisionProvider),
        ],
    )
    def test_construye_el_proveedor_configurado(
        self, monkeypatch: pytest.MonkeyPatch, configurado: str, esperado: type
    ) -> None:
        monkeypatch.setattr(modulo_servicio.settings, "recognition_provider", configurado)
        assert isinstance(_build_provider(), esperado)

    def test_un_proveedor_desconocido_recae_en_gemini(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Una configuración errónea no debe dejar el sistema sin proveedor."""
        monkeypatch.setattr(modulo_servicio.settings, "recognition_provider", "inexistente")
        assert isinstance(_build_provider(), GeminiProvider)


class TestServicioDeReconocimiento:
    def test_preprocesa_la_imagen_antes_de_delegar(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """El paso de visión open source debe ejecutarse siempre, no ser opcional."""
        llamadas: list[bytes] = []

        def _preprocesar_espia(datos: bytes) -> bytes:
            llamadas.append(datos)
            return b"imagen-procesada"

        monkeypatch.setattr(modulo_servicio, "preprocess", _preprocesar_espia)
        proveedor = ProveedorFalso()

        resultado = ejecutar(
            RecognitionService(provider=proveedor).recognize(b"imagen-original", filename="a.png")
        )

        assert llamadas == [b"imagen-original"]
        # Al proveedor multimodal llega la imagen ya limpiada por OpenCV.
        assert proveedor.recibido == b"imagen-procesada"
        assert resultado.latex == "x^2"

    def test_propaga_el_nombre_del_archivo(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(modulo_servicio, "preprocess", lambda datos: datos)
        proveedor = ProveedorFalso()

        ejecutar(RecognitionService(provider=proveedor).recognize(b"x", filename="captura.png"))

        assert proveedor.nombre_archivo == "captura.png"

    def test_sin_proveedor_explicito_usa_el_configurado(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(modulo_servicio.settings, "recognition_provider", "mathpix")
        assert isinstance(RecognitionService()._provider, MathpixProvider)


class TestProveedoresNoImplementados:
    """Los proveedores alternativos son andamiaje; deben degradar, no romper."""

    @pytest.mark.parametrize(
        "proveedor",
        [MathpixProvider(app_id="x", app_key="y"), OpenAIVisionProvider(api_key="z")],
    )
    def test_devuelven_respuesta_vacia_valida(self, proveedor: RecognitionProvider) -> None:
        resultado = ejecutar(proveedor.recognize(b"imagen"))

        assert resultado.latex == ""
        assert resultado.confidence == 0.0
        assert resultado.provider == proveedor.name


def test_la_interfaz_obliga_a_implementar_recognize() -> None:
    """Un proveedor incompleto debe fallar al instanciarse, no en producción."""
    with pytest.raises(TypeError):
        RecognitionProvider()  # type: ignore[abstract]
