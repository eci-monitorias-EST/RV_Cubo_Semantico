"""API del cubo semántico para la experiencia en realidad virtual.

Expone el mismo pipeline que usa app.py (embeddings, PCA congelado,
KMeans congelado, SQLite) para que el frontend WebXR pueda pedir los
puntos y enviar respuestas nuevas. Nunca reentrena nada.

Si existe la carpeta frontend-dist (generada con `npm run build`), la
API también entrega la escena VR, para publicar todo con un solo servidor.

Corre con: uvicorn api:app --reload --port 8000
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from pipeline import storage
from pipeline.clustering import assign_cluster
from pipeline.embeddings import encode
from pipeline.projection import get_variance_explained, transform_to_3d
from pipeline.questions import QUESTIONS
from pipeline.sports import MAX_CUSTOM_SPORT_LENGTH, OTHER_SPORT_LABEL, SPORTS, normalize_sport_name
from pipeline.visual_encoding import get_color_for_cluster, get_shape_for_pregunta

MIN_ANSWER_LENGTH = 10
MAX_ANSWER_LENGTH = 500
FRONTEND_DIST = Path(os.environ.get("FRONTEND_DIST", Path(__file__).resolve().parent.parent / "frontend-dist"))

app = FastAPI(title="Cubo Semántico VR")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class VisitaIn(BaseModel):
    deporte: str = Field(..., min_length=1, max_length=MAX_CUSTOM_SPORT_LENGTH)
    respuestas: dict[int, str]


def _to_public_point(row: dict) -> dict:
    return {
        "id": row["id"],
        "visita_id": row["visita_id"],
        "pregunta_id": row["pregunta_id"],
        "pregunta": QUESTIONS.get(row["pregunta_id"], ""),
        "deporte": row["deporte"],
        "texto": row["texto"],
        "cluster_id": row["cluster_id"],
        "color": get_color_for_cluster(row["cluster_id"]),
        "forma": get_shape_for_pregunta(row["pregunta_id"]),
        "x": row["x"],
        "y": row["y"],
        "z": row["z"],
    }


@app.get("/api/salud")
def salud() -> dict:
    return {"ok": True}


@app.get("/api/config")
def config() -> dict:
    return {
        "preguntas": QUESTIONS,
        "deportes": SPORTS,
        "otro_deporte": OTHER_SPORT_LABEL,
        "min_caracteres": MIN_ANSWER_LENGTH,
        "varianza_explicada": get_variance_explained(),
    }


@app.get("/api/puntos")
def puntos() -> list[dict]:
    return [_to_public_point(row) for row in storage.load_all_points()]


@app.post("/api/visita")
def crear_visita(visita: VisitaIn) -> dict:
    faltantes = [pid for pid in QUESTIONS if pid not in visita.respuestas]
    if faltantes:
        raise HTTPException(status_code=422, detail=f"Faltan respuestas para las preguntas {faltantes}")

    textos: dict[int, str] = {}
    for pregunta_id in QUESTIONS:
        texto = visita.respuestas[pregunta_id].strip()
        if len(texto) < MIN_ANSWER_LENGTH:
            raise HTTPException(
                status_code=422,
                detail=f"La respuesta {pregunta_id} debe tener al menos {MIN_ANSWER_LENGTH} caracteres",
            )
        textos[pregunta_id] = texto[:MAX_ANSWER_LENGTH]

    deporte = normalize_sport_name(visita.deporte)
    visita_id = str(uuid.uuid4())

    for pregunta_id, texto in textos.items():
        x, y, z = transform_to_3d(encode(texto))
        cluster_id = assign_cluster([x, y, z])
        storage.save_answer(
            visita_id=visita_id,
            pregunta_id=pregunta_id,
            deporte=deporte,
            texto=texto,
            cluster_id=cluster_id,
            x=x,
            y=y,
            z=z,
        )

    nuevos = [p for p in puntos() if p["visita_id"] == visita_id]
    return {"visita_id": visita_id, "puntos": nuevos}


if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
