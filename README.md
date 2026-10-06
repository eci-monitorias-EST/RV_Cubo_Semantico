# Cubo Semántico VR — Stand ConexIA 2026

Versión en realidad virtual del Cubo Semántico: cada respuesta de un visitante sobre su deporte favorito se convierte en un punto 3D, y las opiniones parecidas en significado quedan cerca.

## Estructura

```
backend/       Pipeline de NLP (embeddings, PCA congelado, KMeans congelado), API FastAPI y la app original de Streamlit
frontend-vr/   Escena WebXR (Three.js + Vite) para navegador y Meta Quest
```

## Cómo correrlo

Se necesitan dos terminales.

**Terminal 1 — backend (API)**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn api:app --reload --port 8000
```

La primera vez descarga el modelo de embeddings (~470 MB), así que tarda un poco.

**Terminal 2 — frontend VR**

```bash
cd frontend-vr
npm install
npm run dev
```

Abrir `https://localhost:5173` en el navegador. El navegador avisa que el certificado no es seguro (es autofirmado para desarrollo): "Configuración avanzada" → "Continuar".

### Probar en Meta Quest

1. PC y gafas en la misma red Wi-Fi.
2. `npm run dev` muestra una dirección `Network: https://192.168.x.x:5173`.
3. Abrir esa dirección en el navegador de las Quest, aceptar el certificado y pulsar **ENTER VR**.

Controles en VR: apuntar con el rayo a un punto y presionar el gatillo para leer la opinión; el joystick derecho (izquierda/derecha) gira el cubo.

## API

| Método | Ruta | Qué hace |
|---|---|---|
| GET | `/api/config` | Preguntas, deportes y varianza explicada |
| GET | `/api/puntos` | Todos los puntos guardados con color y forma |
| POST | `/api/visita` | Recibe `{deporte, respuestas: {1, 2, 3}}`, calcula posiciones y guarda |

Documentación interactiva en `http://localhost:8000/docs`.

## App original (Streamlit)

```bash
cd backend
streamlit run app.py
```

Detalle del pipeline en `backend/README.md`.

## Datos de prueba

`backend/data/visitantes_prueba.sqlite` trae 12 respuestas de prueba. Para restaurarlas, copiarlo como `backend/data/visitantes.sqlite`.

## Hoja de ruta

- [x] API (FastAPI) sobre `backend/pipeline`
- [x] Escena WebXR con el cubo, puntos por clúster y forma por pregunta
- [x] Selección de puntos con mouse y con controles de Quest
- [ ] Responder las preguntas dentro de VR (teclado del sistema / voz)
- [ ] Prueba en Meta Quest
