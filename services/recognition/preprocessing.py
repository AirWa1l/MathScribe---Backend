"""Preprocesamiento y análisis de imagen con OpenCV (paso de visión open source).

Este módulo cumple el requisito del taller de usar una librería de visión
computacional *open source* dentro del flujo Cámara → Visión → LLM → Respuesta.
Se ejecuta antes de delegar en el proveedor multimodal (Gemini/GPT-4V/Mathpix) y
hace dos cosas con OpenCV:

1. **Limpieza** de la foto tomada con el celular: escala de grises, reducción de
   ruido y umbral adaptativo, para mejorar el contraste del texto matemático.
2. **Análisis / localización de la región de interés (ROI):** detecta los
   contornos del contenido (símbolos, trazos) con ``cv2.findContours``, descarta
   el ruido pequeño y calcula el rectángulo que engloba la expresión. Con eso
   recorta el fondo sobrante y envía al modelo multimodal solo la zona útil.

El proveedor multimodal sigue siendo quien produce el LaTeX final; OpenCV percibe
y localiza el contenido, y prepara la entrada. Si algo falla (imagen corrupta o
vacía) se registra el incidente y se continúa con los bytes originales, de modo
que un problema aquí nunca tumbe la petición de reconocimiento.
"""

from __future__ import annotations

import logging

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Tamaño de vecindad para el umbral adaptativo (debe ser impar).
_ADAPTIVE_BLOCK_SIZE = 31
# Constante que se resta de la media local en el umbral adaptativo.
_ADAPTIVE_C = 10
# Fracción del área total por debajo de la cual un contorno se considera ruido.
_MIN_CONTOUR_AREA_RATIO = 0.0002
# Margen (px) que se deja alrededor de la ROI para no cortar los símbolos.
_ROI_PADDING = 12


def _detectar_roi(binary_inv: np.ndarray) -> tuple[tuple[int, int, int, int], int] | None:
    """Localiza la región de interés analizando los contornos del contenido.

    Recibe una imagen binaria invertida (contenido en blanco sobre fondo negro),
    detecta los contornos externos, descarta los muy pequeños (ruido) y devuelve
    el rectángulo ``(x0, y0, x1, y1)`` que engloba a los relevantes junto con el
    número de contornos considerados. Devuelve ``None`` si no hay contenido útil.
    """
    contours, _ = cv2.findContours(binary_inv, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    alto, ancho = binary_inv.shape
    area_minima = max(20.0, alto * ancho * _MIN_CONTOUR_AREA_RATIO)
    cajas = [cv2.boundingRect(c) for c in contours if cv2.contourArea(c) >= area_minima]
    if not cajas:
        return None

    x0 = min(x for x, _, _, _ in cajas)
    y0 = min(y for _, y, _, _ in cajas)
    x1 = max(x + w for x, _, w, _ in cajas)
    y1 = max(y + h for _, y, _, h in cajas)

    # Padding acotado a los límites de la imagen.
    x0 = max(0, x0 - _ROI_PADDING)
    y0 = max(0, y0 - _ROI_PADDING)
    x1 = min(ancho, x1 + _ROI_PADDING)
    y1 = min(alto, y1 + _ROI_PADDING)
    return (x0, y0, x1, y1), len(cajas)


def preprocess(image_bytes: bytes) -> bytes:
    """Limpia y localiza el contenido de la imagen antes del reconocimiento.

    Pasos: decodifica → escala de grises → reducción de ruido → detección de la
    ROI por contornos (análisis) → recorte al contenido → umbral adaptativo →
    re-codifica a PNG. Ante cualquier fallo devuelve ``image_bytes`` sin tocar,
    para no romper el endpoint de reconocimiento.

    :param image_bytes: Bytes de la imagen original (JPEG/PNG, etc.).
    :return: Bytes de la imagen preprocesada, o los originales si algo falla.
    """
    try:
        buffer = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("cv2.imdecode no pudo decodificar la imagen")

        logger.info(
            "preprocess: entrada shape=%s bytes=%d",
            image.shape,
            len(image_bytes),
        )

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        denoised = cv2.fastNlMeansDenoising(gray, h=10)

        # Análisis: binariza (contenido en blanco) y localiza la ROI del contenido.
        binary_inv = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            _ADAPTIVE_BLOCK_SIZE,
            _ADAPTIVE_C,
        )
        roi = _detectar_roi(binary_inv)
        if roi is not None:
            (x0, y0, x1, y1), n_contornos = roi
            logger.info(
                "preprocess: ROI detectada bbox=(%d,%d,%d,%d) contornos=%d",
                x0,
                y0,
                x1,
                y1,
                n_contornos,
            )
            denoised = denoised[y0:y1, x0:x1]
        else:
            logger.info("preprocess: sin ROI detectable; se usa la imagen completa")

        # Salida limpia (texto oscuro sobre fondo claro) para el modelo multimodal.
        threshold = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            _ADAPTIVE_BLOCK_SIZE,
            _ADAPTIVE_C,
        )

        ok, encoded = cv2.imencode(".png", threshold)
        if not ok:
            raise ValueError("cv2.imencode no pudo re-codificar la imagen")

        result = encoded.tobytes()
        logger.info(
            "preprocess: salida shape=%s bytes=%d",
            threshold.shape,
            len(result),
        )
        return result
    except Exception as exc:
        logger.warning("preprocess falló (%s); se usa la imagen original", exc)
        return image_bytes
