"""Pruebas del preprocesamiento con OpenCV (`services.recognition.preprocessing`).

Cubre el paso de visión open source del flujo: que una imagen válida se procese y
devuelva bytes no vacíos, y que una imagen corrupta caiga con gracia a los bytes
originales sin lanzar excepción (para no tumbar el endpoint de reconocimiento).
"""

import cv2
import numpy as np

from services.recognition.preprocessing import preprocess


def _imagen_sintetica() -> bytes:
    """Genera un PNG pequeño con 'texto' negro sobre fondo blanco."""
    img = np.full((120, 200, 3), 255, dtype=np.uint8)
    cv2.putText(img, "x^2", (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)
    ok, buffer = cv2.imencode(".png", img)
    assert ok
    return buffer.tobytes()


def test_preprocess_devuelve_bytes_no_vacios() -> None:
    resultado = preprocess(_imagen_sintetica())
    assert isinstance(resultado, bytes)
    assert len(resultado) > 0


def test_preprocess_salida_es_imagen_decodificable() -> None:
    resultado = preprocess(_imagen_sintetica())
    decodificada = cv2.imdecode(np.frombuffer(resultado, np.uint8), cv2.IMREAD_GRAYSCALE)
    assert decodificada is not None


def test_preprocess_imagen_corrupta_cae_a_original() -> None:
    basura = b"esto-no-es-una-imagen"
    resultado = preprocess(basura)
    assert resultado == basura
