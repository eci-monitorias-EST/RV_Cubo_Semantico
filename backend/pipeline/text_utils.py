"""Normalización mínima de una respuesta, solo para hash/deduplicación.

Ojo: esto NO se usa para limpiar el texto antes de meterlo al modelo de
embeddings. MiniLM funciona mejor con la oración natural completa, tal
como la escribió el visitante -- quitar tildes o palabras no ayuda aquí,
a diferencia de un pipeline de TF-IDF clásico.
"""
from __future__ import annotations

import hashlib
import re


def normalize_for_hash(text: str) -> str:
    normalized = text.strip().lower()
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def answer_hash(text: str) -> str:
    return hashlib.sha256(normalize_for_hash(text).encode("utf-8")).hexdigest()
