"""Carga del modelo de embeddings multilingüe, una sola vez por proceso.

Mismo modelo que ya usa app_monitorias_2026-1 para su cubo 3D de
comentarios: funciona bien en español y no depende de ningún servicio
externo (corre 100% local, importante para el stand).
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np


MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


@lru_cache(maxsize=1)
def _load_model():
    from sentence_transformers import SentenceTransformer  # type: ignore

    return SentenceTransformer(MODEL_NAME)


def encode(text: str) -> np.ndarray:
    """Convierte una sola respuesta en su vector de embedding."""
    return encode_many([text])[0]


def encode_many(texts: list[str]) -> np.ndarray:
    """Convierte varias respuestas de una vez (más eficiente para el ajuste offline).

    normalize_embeddings=True es importante: HDBSCAN/KMeans comparan por
    distancia Euclidiana, pero los embeddings de sentence-transformers están
    pensados para compararse por similitud coseno (dirección, no magnitud).
    Normalizando a longitud 1, la distancia Euclidiana queda directamente
    relacionada con el coseno -- sin esto, el clustering pierde casi toda
    la estructura semántica real.
    """
    model = _load_model()
    matrix = model.encode(
        texts,
        convert_to_numpy=True,
        show_progress_bar=False,
        normalize_embeddings=True,
    )
    return np.asarray(matrix, dtype=float)
