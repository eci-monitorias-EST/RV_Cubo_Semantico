"""Configuración puramente visual: qué color y qué forma le corresponde a un punto.

No hay modelos aquí — solo mapeos fijos y la carga del slot de paleta que
build_seed_space/fit_projection.py calculó una sola vez. Lo que decide
"dónde va" un punto vive en projection.py/clustering.py; lo que decide
"cómo se ve" vive aquí.

Paleta categórica tomada tal cual del skill de dataviz (orden fijo,
validada contra ceguera al color). En un scatter 3D solo los primeros 3
slots son seguros comparados "todos contra todos" -- de ahí en adelante,
la forma del marcador (fija por pregunta) y el texto al pasar el mouse
son el respaldo de accesibilidad, no el color.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


ARTIFACTS_DIR = Path(__file__).resolve().parent.parent / "build_seed_space" / "artifacts"
PALETTE_FILE = ARTIFACTS_DIR / "cluster_palette.json"

CATEGORICAL_PALETTE = [
    {"light": "#2a78d6", "dark": "#3987e5"},  # 1 blue
    {"light": "#eb6834", "dark": "#d95926"},  # 2 orange
    {"light": "#1baf7a", "dark": "#199e70"},  # 3 aqua
    {"light": "#eda100", "dark": "#c98500"},  # 4 yellow
    {"light": "#e87ba4", "dark": "#d55181"},  # 5 magenta
    {"light": "#008300", "dark": "#008300"},  # 6 green
    {"light": "#4a3aa7", "dark": "#9085e9"},  # 7 violet
    {"light": "#e34948", "dark": "#e66767"},  # 8 red
]
OTHER_COLOR = {"light": "#898781", "dark": "#898781"}  # clústeres 9+, "Other"

PREGUNTA_TO_SHAPE: dict[int, str] = {
    1: "circle",
    2: "square",
    3: "diamond",
}


@lru_cache(maxsize=1)
def _load_palette_slots() -> dict[int, int]:
    if not PALETTE_FILE.exists():
        return {}
    with open(PALETTE_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return {int(k): v for k, v in raw.items()}


def get_color_for_cluster(cluster_id: int, mode: str = "light") -> str:
    slots = _load_palette_slots()
    slot = slots.get(cluster_id, -1)
    if slot == -1 or slot >= len(CATEGORICAL_PALETTE):
        return OTHER_COLOR[mode]
    return CATEGORICAL_PALETTE[slot][mode]


def get_shape_for_pregunta(pregunta_id: int) -> str:
    return PREGUNTA_TO_SHAPE.get(pregunta_id, "circle")
