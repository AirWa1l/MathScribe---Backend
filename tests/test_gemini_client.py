"""Pruebas del cliente compartido de Gemini.

Cubren la construcción del cliente y la configuración de generación, que son el
único punto por el que pasan todas las llamadas al modelo: un fallo aquí afecta
al reconocimiento y a la explicación por igual.
"""

from __future__ import annotations

import pytest

from services.llm import gemini_client
from services.llm.gemini_client import (
    ConsumoTokens,
    GeminiNoConfiguradoError,
    config_generacion,
    crear_cliente,
    parte_imagen,
)


class TestCreacionDelCliente:
    def test_sin_clave_lanza_un_error_especifico(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Los servicios distinguen esta causa para degradar en lugar de fallar."""
        monkeypatch.setattr(gemini_client.settings, "gemini_api_key", None)

        with pytest.raises(GeminiNoConfiguradoError):
            crear_cliente()

    def test_una_clave_vacia_equivale_a_no_tenerla(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(gemini_client.settings, "gemini_api_key", "")

        with pytest.raises(GeminiNoConfiguradoError):
            crear_cliente()

    def test_la_clave_explicita_tiene_prioridad(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Permite inyectar una clave distinta sin tocar la configuración global."""
        monkeypatch.setattr(gemini_client.settings, "gemini_api_key", None)
        creado: dict[str, str] = {}

        class _ClienteFalso:
            def __init__(self, api_key: str) -> None:
                creado["api_key"] = api_key

        monkeypatch.setattr(gemini_client, "crear_cliente", crear_cliente)
        import sys
        import types as tipos_modulo

        modulo = tipos_modulo.ModuleType("google")
        submodulo = tipos_modulo.ModuleType("google.genai")
        submodulo.Client = _ClienteFalso  # type: ignore[attr-defined]
        modulo.genai = submodulo  # type: ignore[attr-defined]
        monkeypatch.setitem(sys.modules, "google", modulo)
        monkeypatch.setitem(sys.modules, "google.genai", submodulo)

        crear_cliente(api_key="clave-explicita")

        assert creado["api_key"] == "clave-explicita"


class TestConfiguracionDeGeneracion:
    def test_sin_presupuesto_no_envia_configuracion_de_razonamiento(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Omitirlo deja el comportamiento por defecto del modelo."""
        monkeypatch.setattr(gemini_client.settings, "gemini_thinking_budget", None)

        configuracion = config_generacion()

        assert getattr(configuracion, "thinking_config", None) is None

    def test_con_presupuesto_definido_se_envia_configuracion_de_razonamiento(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Es la palanca para abaratar la transcripción, que no lo necesita.

        Se comprueba que la configuración viaja, sin exigir un campo concreto:
        el SDK expresa el razonamiento como número de tokens o como nivel según
        la versión, y el código se adapta a la que esté instalada.
        """
        monkeypatch.setattr(gemini_client.settings, "gemini_thinking_budget", 0)

        configuracion = config_generacion()

        assert configuracion.thinking_config is not None

    @pytest.mark.parametrize("presupuesto", [0, 512, 8192])
    def test_cualquier_presupuesto_produce_una_configuracion_valida(
        self, monkeypatch: pytest.MonkeyPatch, presupuesto: int
    ) -> None:
        """Ningún valor razonable debe hacer fallar la construcción."""
        monkeypatch.setattr(gemini_client.settings, "gemini_thinking_budget", presupuesto)

        assert config_generacion() is not None

    def test_si_el_sdk_no_soporta_el_ajuste_no_se_rompe(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Ante una versión que no lo permita, se sigue con el valor por defecto."""

        class _ThinkingConfigSinCampos:
            model_fields: dict[str, object] = {}

        class _TiposFalsos:
            ThinkingConfig = _ThinkingConfigSinCampos

        assert gemini_client._config_razonamiento(_TiposFalsos, 0) is None


def test_envuelve_la_imagen_con_el_tipo_declarado() -> None:
    parte = parte_imagen(b"contenido-png")

    assert parte.inline_data is not None
    assert parte.inline_data.mime_type == "image/png"


class TestContabilidadDeConsumo:
    def test_acumula_varias_llamadas(self) -> None:
        class _Uso:
            prompt_token_count = 100
            candidates_token_count = 20
            thoughts_token_count = 300
            total_token_count = 420

        contador = ConsumoTokens()
        contador.registrar(_Uso())
        contador.registrar(_Uso())

        resumen = contador.resumen()
        assert resumen["llamadas"] == 2
        assert resumen["tokens_totales"] == 840
        assert resumen["tokens_razonamiento"] == 600

    def test_calcula_el_total_si_el_modelo_no_lo_reporta(self) -> None:
        class _UsoSinTotal:
            prompt_token_count = 10
            candidates_token_count = 5
            thoughts_token_count = 20
            total_token_count = 0

        contador = ConsumoTokens()
        contador.registrar(_UsoSinTotal())

        assert contador.resumen()["tokens_totales"] == 35

    def test_el_costo_es_proporcional_a_la_tarifa(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(gemini_client.settings, "gemini_cost_per_1k_tokens", 0.001)

        class _Uso:
            prompt_token_count = 0
            candidates_token_count = 0
            thoughts_token_count = 0
            total_token_count = 2000

        contador = ConsumoTokens()
        contador.registrar(_Uso())

        assert contador.costo_estimado_usd() == pytest.approx(0.002)
