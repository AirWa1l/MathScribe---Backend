"""Pruebas de la explicación en lenguaje natural.

El foco está en la garantía central del diseño: el modelo puede mejorar la
redacción, pero nunca puede alterar la matemática ni desalinear las
explicaciones respecto de los pasos calculados por SymPy.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest

from app.schemas.solve import SolutionStep
from services.llm.gemini_client import GeminiNoConfiguradoError
from services.solver import explainer as modulo_explainer
from services.solver.explainer import (
    construir_entrada,
    explain,
    extraer_descripciones,
)


def ejecutar(corrutina):
    """Ejecuta una corrutina en las pruebas sin depender de un plugin externo."""
    return asyncio.run(corrutina)


PASOS = [
    SolutionStep(order=1, description="Planteamos la integral.", latex=r"\int x^2 dx"),
    SolutionStep(order=2, description="Calculamos la antiderivada.", latex=r"\frac{x^3}{3}"),
]


class _RespuestaFalsa:
    def __init__(self, text: str, usage: object | None = None) -> None:
        self.text = text
        self.usage_metadata = usage


class _ClienteFalso:
    def __init__(self, respuesta: _RespuestaFalsa) -> None:
        self.models = self
        self._respuesta = respuesta
        self.llamadas: list[dict[str, Any]] = []

    def generate_content(self, **kwargs: Any) -> _RespuestaFalsa:
        self.llamadas.append(kwargs)
        return self._respuesta


@pytest.fixture(autouse=True)
def _aislar_del_sdk(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(modulo_explainer, "config_generacion", lambda **_: None)


# --------------------------------------------------------------------------- #
# Validación de la respuesta del modelo
# --------------------------------------------------------------------------- #


def test_extrae_un_arreglo_json_limpio() -> None:
    assert extraer_descripciones('["Uno.", "Dos."]', 2) == ["Uno.", "Dos."]


def test_extrae_aunque_el_modelo_agregue_texto_alrededor() -> None:
    texto = 'Claro, aquí tienes:\n```json\n["Uno.", "Dos."]\n```'
    assert extraer_descripciones(texto, 2) == ["Uno.", "Dos."]


@pytest.mark.parametrize(
    "texto",
    [
        '["Sólo una."]',  # menos elementos de los esperados
        '["Uno.", "Dos.", "Tres."]',  # más elementos
        "no es json",
        "",
        '["Uno.", ""]',  # una descripción vacía
        '["Uno.", 42]',  # un elemento que no es cadena
        '{"paso": "Uno."}',  # objeto en lugar de arreglo
    ],
)
def test_respuestas_inconsistentes_se_rechazan(texto: str) -> None:
    """Ante el mínimo desajuste se rechaza: emparejar mal sería peor que no explicar."""
    assert extraer_descripciones(texto, 2) is None


# --------------------------------------------------------------------------- #
# Comportamiento de explain
# --------------------------------------------------------------------------- #


def test_enriquece_las_descripciones_conservando_la_matematica(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    nuevas = ["Primero identificamos qué se integra.", "Luego subimos el exponente y dividimos."]
    cliente = _ClienteFalso(_RespuestaFalsa(json.dumps(nuevas)))
    monkeypatch.setattr(modulo_explainer, "crear_cliente", lambda: cliente)

    resultado = ejecutar(explain(r"\int x^2 dx", PASOS))

    assert [p.description for p in resultado] == nuevas
    # Lo que garantiza la corrección no se toca.
    assert [p.latex for p in resultado] == [p.latex for p in PASOS]
    assert [p.order for p in resultado] == [1, 2]


def test_sin_clave_devuelve_los_pasos_de_sympy(monkeypatch: pytest.MonkeyPatch) -> None:
    def _sin_clave():
        raise GeminiNoConfiguradoError("falta la clave")

    monkeypatch.setattr(modulo_explainer, "crear_cliente", _sin_clave)

    resultado = ejecutar(explain(r"\int x^2 dx", PASOS))

    assert resultado == PASOS


def test_error_de_la_api_devuelve_los_pasos_de_sympy(monkeypatch: pytest.MonkeyPatch) -> None:
    class _ClienteQueFalla:
        def __init__(self) -> None:
            self.models = self

        def generate_content(self, **_: Any) -> None:
            raise RuntimeError("429 Too Many Requests")

    monkeypatch.setattr(modulo_explainer, "crear_cliente", lambda: _ClienteQueFalla())

    resultado = ejecutar(explain(r"\int x^2 dx", PASOS))

    assert resultado == PASOS


def test_respuesta_con_numero_distinto_de_pasos_se_descarta(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Si el modelo inventa o pierde pasos, se conservan los originales."""
    cliente = _ClienteFalso(_RespuestaFalsa('["Uno.", "Dos.", "Tres inventado."]'))
    monkeypatch.setattr(modulo_explainer, "crear_cliente", lambda: cliente)

    resultado = ejecutar(explain(r"\int x^2 dx", PASOS))

    assert resultado == PASOS


def test_sin_pasos_no_llama_al_modelo(monkeypatch: pytest.MonkeyPatch) -> None:
    def _no_deberia_llamarse():
        raise AssertionError("no debe crearse el cliente si no hay pasos")

    monkeypatch.setattr(modulo_explainer, "crear_cliente", _no_deberia_llamarse)

    assert ejecutar(explain("", [])) == []


def test_el_contexto_enviado_incluye_los_pasos_y_su_latex() -> None:
    entrada = construir_entrada(r"\int x^2 dx", PASOS)

    assert r"\int x^2 dx" in entrada
    assert "1. Planteamos la integral." in entrada
    assert r"\frac{x^3}{3}" in entrada


def test_el_prompt_prohibe_recalcular() -> None:
    """Es la instrucción que sostiene la garantía de corrección del sistema."""
    assert "NO recalcules" in modulo_explainer.PROMPT_EXPLICACION
    assert "mismo número de pasos" in modulo_explainer.PROMPT_EXPLICACION
