"""Proyección a 3D con PCA ya ajustado y congelado.

El modelo se ajusta una sola vez en build_seed_space/fit_projection.py.
Este módulo NUNCA reentrena: solo carga el modelo y proyecta puntos
nuevos, para que las posiciones ya existentes en el diagrama no se
muevan cuando llega un visitante nuevo.

Se eligió PCA (no UMAP) justamente por esto: PCA es una transformación
lineal fija, así que insertar un punto nuevo en un espacio ya congelado
es matemáticamente confiable -- dos respuestas distintas siempre caen en
coordenadas distintas. UMAP no garantiza eso al proyectar fuera de
muestra.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
import pickle

import numpy as np


ARTIFACTS_DIR = Path(__file__).resolve().parent.parent / "build_seed_space" / "artifacts"
PROJECTION_MODEL_PATH = ARTIFACTS_DIR / "projection_model.pkl"
PROJECTION_META_PATH = ARTIFACTS_DIR / "projection_meta.json"


@lru_cache(maxsize=1)
def _load_projection_model():
    if not PROJECTION_MODEL_PATH.exists():
        raise FileNotFoundError(
            "No existe projection_model.pkl todavía. Corre primero "
            "build_seed_space/fit_projection.py para generar los artefactos."
        )
    with open(PROJECTION_MODEL_PATH, "rb") as f:
        return pickle.load(f)


def transform_to_3d(embedding: np.ndarray) -> tuple[float, float, float]:
    reducer = _load_projection_model()
    vector = np.asarray(embedding, dtype=float).reshape(1, -1)
    coordinates = reducer.transform(vector)[0]
    return float(coordinates[0]), float(coordinates[1]), float(coordinates[2])


def get_variance_explained() -> float | None:
    """Qué tan fiel es el diagrama: cuánta variación real de los 384
    componentes originales del embedding quedó capturada en los 3 ejes
    que se dibujan. None si todavía no se corrió fit_projection.py."""
    if not PROJECTION_META_PATH.exists():
        return None
    with open(PROJECTION_META_PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("variance_explained")
