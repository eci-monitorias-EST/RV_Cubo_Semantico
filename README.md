# Cubo Semántico VR — Stand ConexIA 2026

Versión en realidad virtual del Cubo Semántico: cada respuesta de un visitante sobre su deporte favorito se convierte en un punto 3D, y las opiniones parecidas en significado quedan cerca.

## Estructura

```
backend/       Pipeline de NLP (embeddings, PCA congelado, KMeans congelado), API FastAPI y la app original de Streamlit
frontend-vr/   Escena WebXR (Three.js + Vite) para navegador y Meta Quest
```

## Cómo correrlo

Requisitos: Python 3.11+, Node.js LTS y Git. En PowerShell, permitir scripts una sola vez:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

**Primera vez (instala todo):**

```powershell
.\instalar.ps1
```

**Cada vez que se quiera usar:**

```powershell
.\iniciar.ps1
```

Se abren dos ventanas: la API (puerto 8000) y el frontend (puerto 5173). Para apagar, cerrar ambas ventanas.

Abrir `https://localhost:5173` en el navegador. El navegador avisa que el certificado no es seguro (es autofirmado para desarrollo): "Configuración avanzada" → "Continuar". La primera respuesta enviada tarda más porque descarga el modelo de embeddings (~470 MB).

### Arranque manual (alternativa)

Terminal 1:

```powershell
cd backend
.venv\Scripts\activate
uvicorn api:app --reload --port 8000
```

Terminal 2:

```powershell
cd frontend-vr
npm run dev
```

### Probar en Meta Quest

1. PC y gafas en la misma red Wi-Fi. Si la red de la universidad no deja conectar dispositivos entre sí, usar el hotspot de un celular para ambos.
2. La ventana de Vite muestra una dirección `Network: https://192.168.x.x:5173`.
3. En las gafas, abrir el **Navegador** de Meta Quest, ir a esa dirección, aceptar el certificado y pulsar **ENTER VR**.
4. Si no carga, revisar que el Firewall de Windows permita Node.js en redes privadas y públicas.

Para probar sin gafas: extensión **Immersive Web Emulator** (Chrome/Edge), activarla para `localhost` y recargar.

Controles en VR: apuntar con el rayo a un punto muestra su opinión; el gatillo la deja fija; el joystick derecho (izquierda/derecha) gira el cubo. Las respuestas se envían desde el formulario antes de entrar a VR.

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
