# Cubo Semántico — Stand ConexIA 2026

Actividad de stand de Ingeniería Estadística para **ConexIA – Encuentro de Colegios 2026** (Escuela Colombiana de Ingeniería Julio Garavito), bajo el eje temático de Inteligencia Artificial.

## Qué es esto

Un cubo 3D interactivo donde cada punto es la opinión de un visitante sobre su deporte favorito. El objetivo pedagógico: mostrar, sin fórmulas, cómo la IA convierte texto en números y agrupa opiniones parecidas por su significado — no por reglas escritas a mano.

## Cómo funciona la actividad

Cada visitante responde 3 preguntas de opinión sobre deporte:

1. ¿Qué es lo que más te apasiona de tu deporte favorito?
2. Si pudieras cambiar una regla de tu deporte favorito, ¿cuál sería y por qué?
3. ¿Qué le dirías a alguien que piensa que tu deporte favorito no sirve para nada?

Cada respuesta se convierte en su propio punto en el cubo (un visitante genera 3 puntos, uno por pregunta). La codificación visual de cada punto:

| Canal visual | Qué representa | Cómo se determina |
|---|---|---|
| Color | Clúster de opinión (grupo semántico) | Automático — clustering sobre las 3 coordenadas ya proyectadas (no sobre el embedding completo), ajustado una sola vez; así "mismo color" siempre implica "cerca en el diagrama" |
| Forma del marcador | A cuál de las 3 preguntas responde | Fijo — mapeo directo pregunta → forma |
| Tamaño / borde | Si es el punto del visitante actual | Dinámico, solo en el último punto agregado |
| Posición (x, y, z) | Qué tan parecida es la opinión en significado | UMAP ajustado una sola vez sobre un corpus semilla; los puntos nuevos se proyectan sin mover a los demás |

Las posiciones quedan fijas una vez ubicadas — nada se reacomoda durante el evento, para que la experiencia sea legible para quien mira la pantalla varias horas. Se descartó reentrenar el mapa con cada respuesta nueva (como hace `app_monitorias_2026-1`): con cientos de visitantes esperados, eso se vuelve más lento justo cuando hay más fila, y además un punto podría cambiar de color solo porque HDBSCAN reasignó los clústeres, sin que nadie lo haya tocado.

**Antes de las 3 preguntas, el visitante elige su deporte** de una lista corta (los mismos 8 del corpus semilla) o escribe el suyo si elige "Otro". El deporte es metadato puro: se guarda junto a los 3 puntos de ese visitante y aparece en el texto que se muestra **al pasar el mouse sobre un punto** (hover del gráfico 3D, junto a la pregunta y la respuesta) — nunca se convierte en un color o forma nuevos, ni entra al texto que se embebe para calcular la posición.

**El cubo se ve vacío para el aspirante, aunque por dentro no lo esté.** Las 48 respuestas semilla sirven únicamente para calibrar el mapa (para que UMAP y el clustering tengan suficiente variedad antes de que exista un solo visitante real) — pero nunca se dibujan en pantalla. Lo único que se muestra es lo que hay en `data/visitantes.sqlite`: el cubo arranca vacío a los ojos de quien llega y se va llenando solo con opiniones reales. **Regla para cuando se construya `app.py`: nunca renderizar puntos de `seed_points.json`, solo usarlo por dentro para el ajuste offline.**

## Estructura del repositorio

```
stand-cubo-deporte/
├── app.py                        # la app de Streamlit
├── pipeline/
│   ├── questions.py               # las 3 preguntas fijas, un solo lugar de verdad
│   ├── sports.py                  # lista fija de deportes + normalización de "Otro"
│   ├── embeddings.py
│   ├── projection.py
│   ├── clustering.py
│   ├── visual_encoding.py
│   ├── text_utils.py
│   └── storage.py                 # guarda/lee respuestas en data/visitantes.sqlite
├── build_seed_space/
│   ├── seed_answers.json          # 48 respuestas semilla (16 por pregunta, 8 deportes)
│   ├── fit_projection.py
│   └── artifacts/                  # se generan al correr fit_projection.py
│       ├── umap_model.pkl
│       ├── cluster_model.pkl
│       ├── cluster_palette.json
│       └── seed_points.json
├── data/
│   └── visitantes.sqlite          # se crea en el evento, no se versiona
├── scripts/
│   └── probar_pipeline_en_vivo.py # prueba de humo del pipeline en vivo, sin la UI
├── mockups/
│   └── cubo_deporte_mockup.html   # referencia visual aprobada para app.py
├── requirements.txt
├── .gitignore
└── README.md
```

- **`app.py`** — la app de Streamlit: selector de deporte, las 3 preguntas, y el Diagrama de Opiniones. Al terminar la 3ra pregunta corre el pipeline en vivo para las 3 respuestas y las guarda.
- **`pipeline/embeddings.py`** — carga el modelo de embeddings multilingüe una sola vez (cacheado) y expone `encode(texto) → vector`.
- **`pipeline/projection.py`** — carga el UMAP ya congelado y expone `transform_to_3d(vector) → (x, y, z)`. Nunca reentrena, solo proyecta.
- **`pipeline/clustering.py`** — carga el modelo de clustering y expone `assign_cluster(vector) → cluster_id`, con la regla de asignar al más cercano si no encaja bien en ninguno. Este `cluster_id` es lo que decide el color.
- **`pipeline/visual_encoding.py`** — config puramente visual: el mapeo fijo `pregunta → forma`, y la paleta `cluster_id → color`.
- **`pipeline/text_utils.py`** — normaliza cada respuesta individual (para hash/deduplicación); cada pregunta se procesa por separado.
- **`pipeline/sports.py`** — los 8 deportes del selector + normalización del texto libre cuando alguien elige "Otro".
- **`pipeline/storage.py`** — guarda cada respuesta en `data/visitantes.sqlite` y carga todos los puntos reales para dibujar el cubo. Nunca toca los puntos semilla.
- **`build_seed_space/seed_answers.json`** — corpus semilla: ~30-50 respuestas de ejemplo por cada una de las 3 preguntas (90-150 en total), escritas por el equipo antes del evento.
- **`build_seed_space/fit_projection.py`** — se corre UNA sola vez, offline: calcula embeddings del corpus semilla, ajusta UMAP y el clustering, guarda los artefactos congelados. Nunca se vuelve a correr durante el stand.
- **`build_seed_space/artifacts/`** — salidas congeladas de ese ajuste (modelo UMAP, modelo de clustering, puntos semilla). `seed_points.json` es solo para calibrar y depurar — nunca se muestra en el cubo real.
- **`data/visitantes.sqlite`** — se llena durante el evento; una fila por respuesta (texto, pregunta, coordenadas, cluster_id, hora).

## Cómo correr localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Estado actual

- [x] Estructura del proyecto definida
- [x] Preguntas y codificación visual definidas
- [x] Corpus semilla (`seed_answers.json`) — 48 respuestas, reescrito una vez para evitar que agrupara por pregunta en vez de por tema
- [x] Pipeline en vivo (`pipeline/`) — embeddings, proyección, clustering, codificación visual y almacenamiento (`storage.py`)
- [x] Artefactos congelados generados (`fit_projection.py` ya corrido, con 5 clústeres que agrupan por tema real)
- [x] Mockup de UI/UX aprobado (`mockups/cubo_deporte_mockup.html`)
- [x] App de Streamlit (`app.py`) — primera versión funcional, conectada al pipeline real
- [ ] Probar `app.py` en el hardware real del stand antes del evento
- [ ] Revisar visualmente el resultado y ajustar estilos si hace falta

**Nota sobre `app.py` vs. el mockup:** Streamlit no permite replicar el HTML pixel por pixel (sin glassmorphism ni control fino de layout). Se priorizó que funcione correctamente conectado al pipeline real, manteniendo el espíritu visual del mockup (colores, tipografía) sin ser una copia exacta. El nombre de la sección también cambió: ya no es "Constelación" (fondo oscuro estilo espacio), sino "Diagrama de Opiniones" (ejes claros, como un gráfico de dispersión real).
