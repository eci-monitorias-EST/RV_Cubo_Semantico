"""Lista fija de deportes para el selector rápido, antes de las 3 preguntas.

El deporte es metadato puro: se guarda junto a cada uno de los 3 puntos
del visitante (para mostrarlo al pasar el mouse), pero nunca entra al
texto que se embebe ni se convierte en un canal visual nuevo -- eso ya
está resuelto por color (clúster) y forma (pregunta).

Se selecciona UNA sola vez por visitante, no una vez por pregunta: las 3
respuestas son sobre el mismo deporte.
"""
from __future__ import annotations

# Mismos 8 deportes del corpus semilla -- mantiene coherencia entre lo
# que ya calibramos y lo que el selector ofrece por defecto.
SPORTS: list[str] = [
    "Fútbol",
    "Baloncesto",
    "Voleibol",
    "Natación",
    "Atletismo",
    "Ciclismo",
    "Tenis",
    "Gimnasia",
]

OTHER_SPORT_LABEL = "Otro"
MAX_CUSTOM_SPORT_LENGTH = 40


def normalize_sport_name(name: str) -> str:
    """Limpia el nombre escrito a mano cuando el visitante elige 'Otro'.

    Si llega vacío (alguien elige "Otro" y no escribe nada), cae de
    vuelta a la etiqueta genérica en vez de guardar un campo vacío.
    """
    cleaned = name.strip()
    if not cleaned:
        return OTHER_SPORT_LABEL
    return cleaned[:MAX_CUSTOM_SPORT_LENGTH].strip().capitalize()
