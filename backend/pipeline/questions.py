"""Las 3 preguntas fijas del cubo semántico — un solo lugar de verdad.

Cualquier otro módulo (el corpus semilla, el ajuste offline, la futura
app) debe importar de aquí en vez de repetir el texto.
"""
from __future__ import annotations

QUESTIONS: dict[int, str] = {
    1: "¿Qué es lo que más te apasiona de tu deporte favorito?",
    2: "Si pudieras cambiar una regla de tu deporte favorito, ¿cuál sería y por qué?",
    3: "¿Qué le dirías a alguien que piensa que tu deporte favorito no sirve para nada?",
}
