"""Pruebas del preprocesamiento y análisis con OpenCV (`services.recognition.preprocessing`).

Cubre el paso de visión open source del flujo: que una imagen válida se procese y
devuelva bytes no vacíos, que el análisis de ROI recorte al contenido, que una
imagen en blanco (sin contornos) no falle, y que una imagen corrupta caiga con
gracia a los bytes originales sin lanzar excepción (para no tumbar el endpoint).
"""

import cv2
import numpy as np

from services.recognition.preprocessing import _detectar_roi, preprocess


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


def test_preprocess_recorta_a_la_region_de_interes() -> None:
    """El análisis de ROI debe recortar el fondo sobrante alrededor del contenido."""
    lienzo = np.full((400, 400, 3), 255, dtype=np.uint8)
    # Trazo pequeño y centrado, rodeado de mucho blanco.
    cv2.rectangle(lienzo, (185, 185), (215, 215), (0, 0, 0), -1)
    ok, buffer = cv2.imencode(".png", lienzo)
    assert ok

    resultado = preprocess(buffer.tobytes())
    decodificada = cv2.imdecode(np.frombuffer(resultado, np.uint8), cv2.IMREAD_GRAYSCALE)
    assert decodificada is not None
    alto, ancho = decodificada.shape
    # La salida debe ser menor que el lienzo original: se recortó al ROI.
    assert alto < 400
    assert ancho < 400


def test_detectar_roi_localiza_el_contenido() -> None:
    """La detección de ROI devuelve una caja que contiene el trazo dibujado."""
    binaria = np.zeros((200, 200), dtype=np.uint8)
    cv2.rectangle(binaria, (60, 70), (140, 130), 255, -1)  # contenido en blanco

    roi = _detectar_roi(binaria)
    assert roi is not None
    (x0, y0, x1, y1), n_contornos = roi
    assert n_contornos >= 1
    # La caja (con padding) debe englobar el rectángulo dibujado.
    assert x0 <= 60 and y0 <= 70
    assert x1 >= 140 and y1 >= 130


def test_detectar_roi_sin_contenido_devuelve_none() -> None:
    """Una imagen sin contornos (toda negra) no produce ROI."""
    binaria = np.zeros((100, 100), dtype=np.uint8)
    assert _detectar_roi(binaria) is None


def test_preprocess_imagen_en_blanco_no_falla() -> None:
    """Sin contenido detectable, se usa la imagen completa sin lanzar excepción."""
    lienzo = np.full((100, 150, 3), 255, dtype=np.uint8)
    ok, buffer = cv2.imencode(".png", lienzo)
    assert ok
    resultado = preprocess(buffer.tobytes())
    assert isinstance(resultado, bytes)
    assert len(resultado) > 0


def test_preprocess_imagen_corrupta_cae_a_original() -> None:
    basura = b"esto-no-es-una-imagen"
    resultado = preprocess(basura)
    assert resultado == basura
