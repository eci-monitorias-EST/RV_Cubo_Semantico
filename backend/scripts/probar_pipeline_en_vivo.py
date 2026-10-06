"""Simula lo que pasa cuando un visitante real responde las 3 preguntas.

No es parte de la app -- es una prueba de humo para confirmar que el
pipeline en vivo completo (embeddings -> proyección -> clúster -> color
y forma) funciona de punta a punta antes de construir la interfaz.

Requiere haber corrido antes build_seed_space/fit_projection.py (necesita
los artefactos ya generados). Se corre manualmente:

    python scripts\\probar_pipeline_en_vivo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from pipeline.clustering import assign_cluster  # noqa: E402
from pipeline.embeddings import encode  # noqa: E402
from pipeline.projection import transform_to_3d  # noqa: E402
from pipeline.questions import QUESTIONS  # noqa: E402
from pipeline.visual_encoding import get_color_for_cluster, get_shape_for_pregunta  # noqa: E402


# Respuestas de ejemplo -- a propósito NO son ninguna de las 48 semilla,
# para probar que el pipeline generaliza a texto que nunca vio.
RESPUESTAS_DE_PRUEBA = {
    1: "Lo que más me gusta del baloncesto es sentir que todo el equipo respira al mismo tiempo cuando el partido se pone difícil.",
    2: "Cambiaría que los árbitros expliquen sus decisiones en vivo, así todos entenderíamos mejor la estrategia detrás de cada jugada.",
    3: "Le diría que detrás de cada tiro libre hay años de práctica silenciosa que nadie ve desde las gradas.",
}


def main() -> None:
    print("Simulando un visitante respondiendo las 3 preguntas...\n")
    for pregunta_id, texto in RESPUESTAS_DE_PRUEBA.items():
        vector = encode(texto)
        x, y, z = transform_to_3d(vector)
        cluster_id = assign_cluster([x, y, z])
        color = get_color_for_cluster(cluster_id)
        shape = get_shape_for_pregunta(pregunta_id)

        print(f"Pregunta {pregunta_id}: {QUESTIONS[pregunta_id]}")
        print(f"  Respuesta: {texto}")
        print(f"  Coordenadas: ({x:.2f}, {y:.2f}, {z:.2f})")
        print(f"  Clúster: {cluster_id}  ->  Color: {color}")
        print(f"  Forma (fija por pregunta): {shape}\n")

    print("Si no hubo errores arriba, el pipeline en vivo funciona de punta a punta.")


if __name__ == "__main__":
    main()
