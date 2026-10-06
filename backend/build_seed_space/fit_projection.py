"""Ajusta el espacio 3D y el modelo de clústeres una sola vez, offline.

Se corre manualmente antes del evento:

    python build_seed_space/fit_projection.py

Nunca se ejecuta durante el stand: las posiciones y los clústeres que
resultan de aquí quedan congelados en build_seed_space/artifacts/, y el
pipeline en vivo (pipeline/projection.py, pipeline/clustering.py) solo
proyecta puntos nuevos sobre ese espacio ya fijo.
"""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from pipeline.clustering import assign_palette_slots, fit_cluster_model  # noqa: E402
from pipeline.embeddings import encode_many  # noqa: E402

BASE_DIR = Path(__file__).resolve().parent
SEED_FILE = BASE_DIR / "seed_answers.json"
ARTIFACTS_DIR = BASE_DIR / "artifacts"


def main() -> None:
    with open(SEED_FILE, "r", encoding="utf-8") as f:
        respuestas = json.load(f)

    textos = [r["texto"] for r in respuestas]
    print(f"Calculando embeddings de {len(textos)} respuestas semilla...")
    embeddings = encode_many(textos)

    print("Ajustando PCA (una sola vez, este modelo queda congelado)...")
    # PCA en vez de UMAP: necesitamos insertar puntos nuevos en un espacio ya
    # fijo (ver pipeline/projection.py) y UMAP no tiene una forma confiable de
    # proyectar puntos fuera de muestra -- su .transform() interpola por
    # vecinos y puede colapsar respuestas distintas casi en el mismo lugar,
    # sobre todo con un corpus semilla chico. PCA es una transformación
    # lineal fija: dos vectores distintos siempre caen en coordenadas
    # distintas.
    #
    # StandardScaler antes de PCA: sin esto, PCA le da más peso a las
    # dimensiones del embedding que por casualidad tienen más varianza, sin
    # que eso signifique que sean semánticamente más importantes. Se
    # empaquetan juntos en un Pipeline para que projection.py no tenga que
    # saber que hay dos pasos -- sigue llamando solo a .transform().
    from sklearn.decomposition import PCA
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    reducer = make_pipeline(StandardScaler(), PCA(n_components=3, random_state=42))
    coordinates = reducer.fit_transform(embeddings)

    variance_explained = float(sum(reducer.named_steps["pca"].explained_variance_ratio_))
    print(f"Varianza explicada por los 3 componentes: {variance_explained:.1%}")

    print("Ajustando el modelo de clústeres...")
    # Sobre `coordinates` (las 3 dimensiones que se dibujan), no sobre
    # `embeddings` (los 384 originales). Si el clustering corriera sobre los
    # embeddings completos, dos opiniones del mismo clúster podrían caer
    # lejos una de otra en el diagrama -- esas 3 dimensiones solo capturan
    # una fracción de lo que las hace parecidas (ver variance_explained más
    # abajo). Agrupando sobre las mismas coordenadas que se ven, "mismo
    # color" siempre implica "cerca en el diagrama", por construcción.
    cluster_model = fit_cluster_model(coordinates)
    palette_slots = assign_palette_slots(cluster_model.train_labels)

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    with open(ARTIFACTS_DIR / "projection_model.pkl", "wb") as f:
        pickle.dump(reducer, f)

    with open(ARTIFACTS_DIR / "cluster_model.pkl", "wb") as f:
        pickle.dump(cluster_model, f)

    with open(ARTIFACTS_DIR / "cluster_palette.json", "w", encoding="utf-8") as f:
        json.dump({str(k): v for k, v in palette_slots.items()}, f, ensure_ascii=False, indent=2)

    with open(ARTIFACTS_DIR / "projection_meta.json", "w", encoding="utf-8") as f:
        json.dump({"variance_explained": variance_explained}, f, ensure_ascii=False, indent=2)

    seed_points = []
    for respuesta, coordinate, cluster_id in zip(respuestas, coordinates, cluster_model.train_labels):
        seed_points.append(
            {
                "deporte": respuesta["deporte"],
                "pregunta_id": respuesta["pregunta_id"],
                "texto": respuesta["texto"],
                "cluster_id": int(cluster_id),
                "x": float(coordinate[0]),
                "y": float(coordinate[1]),
                "z": float(coordinate[2]),
            }
        )

    with open(ARTIFACTS_DIR / "seed_points.json", "w", encoding="utf-8") as f:
        json.dump(seed_points, f, ensure_ascii=False, indent=2)

    n_clusters = len(set(cluster_model.train_labels))
    print(f"\nListo. {len(seed_points)} puntos semilla, {n_clusters} clústeres (KMeans).")
    print(f"Artefactos guardados en: {ARTIFACTS_DIR}")


if __name__ == "__main__":
    main()
