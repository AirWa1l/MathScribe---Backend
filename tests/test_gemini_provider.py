"""Pruebas del proveedor de reconocimiento con Gemini.

Todas las pruebas usan dobles de prueba: no se realiza ninguna llamada de red,
de modo que la suite corre en el pipeline sin clave de API ni cuota consumida.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from services.llm.gemini_client import ConsumoTokens, GeminiNoConfiguradoError
from services.recognition.providers import gemini as modulo_gemini
from services.recognition.providers.gemini import GeminiProvider, limpiar_latex


def ejecutar(corrutina):
    """Ejecuta una corrutina en las pruebas sin depender de un plugin externo."""
    return asyncio.run(corrutina)


class _RespuestaFalsa:
    """Imita la respuesta del SDK: texto generado y metadatos de consumo."""

    def __init__(self, text: str, usage: object | None = None) -> None:
        self.text = text
        self.usage_metadata = usage


class _UsoFalso:
    def __init__(self, entrada: int, salida: int, razonamiento: int, total: int) -> None:
        self.prompt_token_count = entrada
        self.candidates_token_count = salida
        self.thoughts_token_count = razonamiento
        self.total_token_count = total


class _ClienteFalso:
    """Cliente cuyo `generate_content` devuelve una respuesta fija."""

    def __init__(self, respuesta: _RespuestaFalsa) -> None:
        self.models = self
        self._respuesta = respuesta
        self.llamadas: list[dict[str, Any]] = []

    def generate_content(self, **kwargs: Any) -> _RespuestaFalsa:
        self.llamadas.append(kwargs)
        return self._respuesta


@pytest.fixture(autouse=True)
def _aislar_del_sdk(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sustituye las piezas que construyen tipos reales del SDK de Google."""
    monkeypatch.setattr(modulo_gemini, "config_generacion", lambda **_: None)
    monkeypatch.setattr(modulo_gemini, "parte_imagen", lambda data, *a, **k: data)


# --------------------------------------------------------------------------- #
# Limpieza del LaTeX devuelto por el modelo
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("```latex\n\\frac{1}{2}\n```", "\\frac{1}{2}"),
        ("```\nx^2 + 1\n```", "x^2 + 1"),
        ("$$\\int_0^1 x^2\\,dx$$", "\\int_0^1 x^2\\,dx"),
        ("$x + y$", "x + y"),
        ("\\[ a^2 \\]", "a^2"),
        ("   x = 5   ", "x = 5"),
        ("```latex\n$$\\sqrt{2}$$\n```", "\\sqrt{2}"),
        ("", ""),
    ],
)
def test_limpiar_latex_quita_envoltorios(entrada: str, esperado: str) -> None:
    assert limpiar_latex(entrada) == esperado


# --------------------------------------------------------------------------- #
# Comportamiento del proveedor
# --------------------------------------------------------------------------- #


def test_reconoce_y_limpia_la_respuesta_del_modelo(monkeypatch: pytest.MonkeyPatch) -> None:
    cliente = _ClienteFalso(_RespuestaFalsa("```latex\n\\int_0^1 x^2\\,dx\n```"))
    monkeypatch.setattr(modulo_gemini, "crear_cliente", lambda _=None: cliente)

    resultado = ejecutar(GeminiProvider(api_key="clave-de-prueba").recognize(b"png"))

    assert resultado.latex == "\\int_0^1 x^2\\,dx"
    assert resultado.provider == "gemini"
    assert resultado.confidence > 0


def test_usa_el_modelo_configurado(monkeypatch: pytest.MonkeyPatch) -> None:
    cliente = _ClienteFalso(_RespuestaFalsa("x"))
    monkeypatch.setattr(modulo_gemini, "crear_cliente", lambda _=None: cliente)

    ejecutar(GeminiProvider(api_key="clave", model="modelo-de-prueba").recognize(b"png"))

    assert cliente.llamadas[0]["model"] == "modelo-de-prueba"


def test_sin_clave_devuelve_respuesta_degradada(monkeypatch: pytest.MonkeyPatch) -> None:
    def _sin_clave(_: str | None = None) -> None:
        raise GeminiNoConfiguradoError("falta la clave")

    monkeypatch.setattr(modulo_gemini, "crear_cliente", _sin_clave)

    resultado = ejecutar(GeminiProvider().recognize(b"png"))

    assert resultado.latex == ""
    assert resultado.confidence == 0.0
    assert resultado.provider == "gemini"


def test_error_de_la_api_no_propaga_excepcion(monkeypatch: pytest.MonkeyPatch) -> None:
    class _ClienteQueFalla:
        def __init__(self) -> None:
            self.models = self

        def generate_content(self, **_: Any) -> None:
            raise RuntimeError("503 Service Unavailable")

    monkeypatch.setattr(modulo_gemini, "crear_cliente", lambda _=None: _ClienteQueFalla())

    resultado = ejecutar(GeminiProvider(api_key="clave").recognize(b"png"))

    assert resultado.latex == ""
    assert resultado.confidence == 0.0


def test_imagen_sin_expresion_devuelve_latex_vacio(monkeypatch: pytest.MonkeyPatch) -> None:
    cliente = _ClienteFalso(_RespuestaFalsa("   "))
    monkeypatch.setattr(modulo_gemini, "crear_cliente", lambda _=None: cliente)

    resultado = ejecutar(GeminiProvider(api_key="clave").recognize(b"png"))

    assert resultado.latex == ""
    assert resultado.confidence == 0.0


def test_registra_el_consumo_de_tokens(monkeypatch: pytest.MonkeyPatch) -> None:
    uso = _UsoFalso(entrada=260, salida=18, razonamiento=140, total=418)
    cliente = _ClienteFalso(_RespuestaFalsa("x^2", usage=uso))
    contador = ConsumoTokens()
    monkeypatch.setattr(modulo_gemini, "crear_cliente", lambda _=None: cliente)
    monkeypatch.setattr(modulo_gemini, "consumo", contador)

    ejecutar(GeminiProvider(api_key="clave").recognize(b"png"))

    resumen = contador.resumen()
    assert resumen["llamadas"] == 1
    assert resumen["tokens_totales"] == 418
    # El razonamiento se contabiliza aparte porque domina el costo en los
    # modelos 3.x y debe poder analizarse por separado.
    assert resumen["tokens_razonamiento"] == 140
    assert resumen["costo_usd_estimado"] > 0


def test_el_prompt_prohibe_resolver_y_delimitar() -> None:
    """El prompt es parte del contrato con SymPy: si cambia, algo se rompe aguas abajo."""
    prompt = modulo_gemini.PROMPT_RECONOCIMIENTO
    assert "ÚNICAMENTE" in prompt
    assert "No resuelvas" in prompt
    assert "```latex" in prompt


def test_consumo_tolera_metadatos_ausentes() -> None:
    contador = ConsumoTokens()
    contador.registrar(None)
    resumen = contador.resumen()
    assert resumen["llamadas"] == 1
    assert resumen["tokens_totales"] == 0
