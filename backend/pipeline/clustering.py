"""Ajuste y asignación de clústeres para el cubo semántico.

Se probó HDBSCAN (detecta el número de grupos solo, a partir de los
datos -- el mensaje pedagógico que hubiéramos querido). Con el corpus
semilla real (48 opiniones, mismo idioma, mismo tema, estilo parecido)
se quedó consistentemente en 2 grupos reales y la mayoría de los puntos
como ruido, incluso normalizando los embeddings y aflojando sus
parámetros (min_samples, cluster_selection_method="leaf").

Se optó por KMeans con k fijo = 5, uno por cada tema transversal que se
escribió a mano en el corpus semilla (equipo, disciplina, estrategia,
pasión, reconocimiento). El trade-off: ya no es la IA la que decide
CUÁNTOS grupos hay, pero sigue siendo la IA la que decide QUÉ va en cada
uno. De regalo, KMeans nunca deja un punto sin asignar -- la regla de
"asignar siempre al más cercano" queda resuelta gratis, sin lógica
adicional.

Importante: el ajuste corre sobre las 3 COORDENADAS ya proyectadas
(x, y, z), no sobre los 384 números originales del embedding. Si
agrupara sobre el embedding completo, dos opiniones del mismo clúster
podrían caer lejos una de otra en el diagrama -- las 3 coordenadas solo
capturan una fracción de la varianza total. Agrupando sobre lo mismo que
se dibuja, "mismo color" siempre implica "cerca en el diagrama".
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import pickle

import numpy as np


N_CLUSTERS = 5
MAX_PALETTE_SLOTS = 8  # tantos como colores tiene la paleta categórica

ARTIFACTS_DIR = Path(__file__).resolve().parent.parent / "build_seed_space" / "artifacts"
CLUSTER_MODEL_PATH = ARTIFACTS_DIR / "cluster_model.pkl"


@dataclass
class ClusterModel:
    backend: object
    train_coordinates: np.ndarray
    train_labels: np.ndarray

    def predict_one(self, coordinates: np.ndarray) -> int:
        """Devuelve el cluster_id de unas coordenadas (x, y, z) nuevas.

        KMeans siempre asigna a alguno -- nunca deja nada sin asignar.
        """
        vector = np.asarray(coordinates, dtype=float).reshape(1, -1)
        return int(self.backend.predict(vector)[0])


def fit_cluster_model(coordinates: np.ndarray) -> ClusterModel:
    from sklearn.cluster import KMeans

    kmeans = KMeans(n_clusters=N_CLUSTERS, n_init="auto", random_state=42)
    labels = kmeans.fit_predict(coordinates)
    return ClusterModel(backend=kmeans, train_coordinates=coordinates, train_labels=labels)


@lru_cache(maxsize=1)
def _load_cluster_model() -> ClusterModel:
    if not CLUSTER_MODEL_PATH.exists():
        raise FileNotFoundError(
            "No existe cluster_model.pkl todavía. Corre primero "
            "build_seed_space/fit_projection.py para generar los artefactos."
        )
    with open(CLUSTER_MODEL_PATH, "rb") as f:
        return pickle.load(f)


def assign_cluster(coordinates: np.ndarray) -> int:
    """Punto de entrada para el uso en vivo: carga el modelo ya ajustado y clasifica.

    Recibe las coordenadas (x, y, z) YA proyectadas -- llamar después de
    projection.transform_to_3d(), no con el embedding crudo. Nunca
    reentrena -- solo consulta el modelo congelado por fit_projection.py.
    """
    return _load_cluster_model().predict_one(coordinates)


def assign_palette_slots(labels: np.ndarray, max_slots: int = MAX_PALETTE_SLOTS) -> dict[int, int]:
    """Asigna cada cluster_id a un slot fijo de la paleta categórica.

    Los clústeres más grandes se quedan con los primeros slots (los únicos
    que la paleta valida para comparaciones "todos contra todos" en un
    scatter 3D). Con KMeans no hay ruido (-1), así que no hace falta
    filtrar nada antes de ordenar.
    """
    ids, counts = np.unique(labels, return_counts=True)
    order = [cluster_id for cluster_id, _ in sorted(zip(ids, counts), key=lambda item: -item[1])]

    slots: dict[int, int] = {}
    for index, cluster_id in enumerate(order):
        slots[int(cluster_id)] = index if index < max_slots else -1
    return slots
