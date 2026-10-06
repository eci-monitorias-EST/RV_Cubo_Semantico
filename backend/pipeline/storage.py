"""Persistencia local de las respuestas de los visitantes durante el evento.

Una fila por respuesta, no por visitante -- cada visitante genera 3 filas
(una por pregunta), agrupadas por visita_id para poder resaltar sus
puntos justo después de que los envía.

Nunca se guardan aquí los puntos semilla: esa separación es justo lo que
mantiene el cubo "vacío" para el aspirante aunque el modelo ya esté
calibrado por dentro (ver README, sección "Cómo funciona la actividad").
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "visitantes.sqlite"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS respuestas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    visita_id TEXT NOT NULL,
    pregunta_id INTEGER NOT NULL,
    deporte TEXT NOT NULL,
    texto TEXT NOT NULL,
    cluster_id INTEGER NOT NULL,
    x REAL NOT NULL,
    y REAL NOT NULL,
    z REAL NOT NULL,
    creado_en TEXT NOT NULL
)
"""


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(_SCHEMA)
    return conn


def save_answer(
    *,
    visita_id: str,
    pregunta_id: int,
    deporte: str,
    texto: str,
    cluster_id: int,
    x: float,
    y: float,
    z: float,
) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO respuestas
                (visita_id, pregunta_id, deporte, texto, cluster_id, x, y, z, creado_en)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                visita_id,
                pregunta_id,
                deporte,
                texto,
                cluster_id,
                x,
                y,
                z,
                datetime.now(timezone.utc).isoformat(),
            ),
        )


def load_all_points() -> list[dict]:
    with _connect() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM respuestas ORDER BY id ASC").fetchall()
        return [dict(row) for row in rows]
