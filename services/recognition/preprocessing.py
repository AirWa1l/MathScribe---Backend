"""Preprocesamiento de imagen con OpenCV (paso de visión open source).

Este módulo cumple el requisito del taller de usar una librería de visión
computacional *open source* dentro del flujo Cámara → Visión → LLM → Respuesta.
Se ejecuta antes de delegar en el proveedor multimodal (Gemini/GPT-4V/Mathpix)
para limpiar la foto tomada con el celular: escala de grises, reducción de ruido
y umbral adaptativo. Con esto el texto matemático queda con mejor contraste y el
modelo multimodal recibe una imagen más nítida.

El proveedor multimodal sigue siendo quien produce el LaTeX final; OpenCV solo
prepara la entrada. Si el preprocesamiento falla (imagen corrupta o vacía) se
registra el incidente y se continúa con los bytes originales, de modo que un
problema aquí nunca tumbe la petición de reconocimiento.
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


def preprocess(image_bytes: bytes) -> bytes:
    """Limpia la imagen antes del reconocimiento y devuelve los bytes procesados.

    Pasos: decodifica → escala de grises → reducción de ruido → umbral adaptativo
    → re-codifica a PNG. Ante cualquier fallo devuelve ``image_bytes`` sin tocar,
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
