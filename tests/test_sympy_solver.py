"""Pruebas de la resolución simbólica.

Verifican que el resultado es matemáticamente correcto —no sólo que la función
devuelve algo—, porque SymPy es la fuente de verdad del sistema: si aquí se
cuela un error, ninguna capa posterior lo detecta.
"""

from __future__ import annotations

import pytest

from services.solver.sympy_solver import solve_expression


class TestIntegrales:
    def test_integral_definida_da_el_valor_exacto(self) -> None:
        resultado, pasos = solve_expression(r"\int_0^1 x^2\,dx")

        assert resultado == r"\frac{1}{3}"
        assert len(pasos) == 3
        # El paso intermedio debe mostrar la antiderivada, no sólo el resultado.
        assert pasos[1].latex == r"\frac{x^{3}}{3}"

    def test_integral_indefinida_incluye_la_constante(self) -> None:
        resultado, pasos = solve_expression(r"\int x^2\,dx")

        assert "C" in resultado
        assert r"\frac{x^{3}}{3}" in resultado
        assert "constante" in pasos[-1].description.lower()

    def test_integral_de_funcion_trigonometrica(self) -> None:
        resultado, _ = solve_expression(r"\int \sin(x)\,dx")
        assert r"\cos" in resultado


class TestDerivadas:
    def test_derivada_aplica_la_regla_de_la_potencia(self) -> None:
        resultado, pasos = solve_expression(r"\frac{d}{dx}(x^3)")

        assert resultado == "3 x^{2}"
        assert len(pasos) == 2

    def test_derivada_de_producto(self) -> None:
        resultado, _ = solve_expression(r"\frac{d}{dx}(x \cdot \sin(x))")
        assert r"\sin" in resultado and r"\cos" in resultado


class TestEcuaciones:
    def test_ecuacion_cuadratica_da_ambas_raices(self) -> None:
        resultado, pasos = solve_expression(r"x^2 - 4 = 0")

        assert "-2" in resultado and "2" in resultado
        assert len(pasos) >= 2

    def test_ecuacion_lineal_muestra_la_normalizacion(self) -> None:
        resultado, pasos = solve_expression(r"2x + 3 = 7")

        assert "2" in resultado
        # Al haber términos a ambos lados, el paso de normalización sí informa.
        assert any("un lado" in paso.description for paso in pasos)

    def test_ecuacion_ya_igualada_a_cero_omite_paso_redundante(self) -> None:
        _, pasos = solve_expression(r"x^2 - 4 = 0")

        assert not any("un lado" in paso.description for paso in pasos)

    def test_ecuacion_sin_solucion_real_no_rompe(self) -> None:
        resultado, pasos = solve_expression(r"x^2 + 1 = 0")

        assert resultado != ""
        assert len(pasos) >= 2


class TestSimplificacion:
    def test_simplifica_una_fraccion_algebraica(self) -> None:
        resultado, pasos = solve_expression(r"\frac{x^2-1}{x-1}")

        assert resultado == "x + 1"
        assert any("implifica" in paso.description for paso in pasos)

    def test_factoriza_un_trinomio_cuadrado_perfecto(self) -> None:
        resultado, pasos = solve_expression(r"x^2+2x+1")

        assert resultado == r"\left(x + 1\right)^{2}"
        assert any("actoriza" in paso.description for paso in pasos)

    def test_expresion_aritmetica_se_evalua(self) -> None:
        resultado, _ = solve_expression(r"2+2")
        assert resultado == "4"

    def test_expresion_ya_simplificada_deja_constancia(self) -> None:
        _, pasos = solve_expression(r"x + 1")
        assert len(pasos) >= 2


class TestEntradasInvalidas:
    @pytest.mark.parametrize("entrada", ["", "   ", "esto no es una expresión $$$", r"\frac{"])
    def test_latex_invalido_devuelve_resultado_vacio_sin_excepcion(self, entrada: str) -> None:
        resultado, pasos = solve_expression(entrada)

        assert resultado == ""
        assert pasos == []


def test_los_pasos_van_numerados_de_forma_consecutiva() -> None:
    """El frontend usa `order` como clave de render; no puede haber huecos."""
    for expresion in [r"\int_0^1 x^2\,dx", r"2x + 3 = 7", r"x^2+2x+1"]:
        _, pasos = solve_expression(expresion)
        assert [paso.order for paso in pasos] == list(range(1, len(pasos) + 1))
