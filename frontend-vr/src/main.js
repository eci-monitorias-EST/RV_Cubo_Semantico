import { createCubeScene } from './scene.js';

const POLL_MS = 4000;

const cubo = createCubeScene(document.body);

const form = document.getElementById('form-visita');
const selectDeporte = document.getElementById('deporte');
const inputOtro = document.getElementById('deporte-otro');
const contPreguntas = document.getElementById('preguntas');
const btnEnviar = document.getElementById('btn-enviar');
const estado = document.getElementById('estado');
const total = document.getElementById('total');

let config = null;

async function api(path, options) {
  const res = await fetch(path, options);
  if (!res.ok) {
    let detail = `Error ${res.status}`;
    try {
      const body = await res.json();
      if (body.detail) detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
    } catch {
      return Promise.reject(new Error(detail));
    }
    throw new Error(detail);
  }
  return res.json();
}

function setEstado(texto, esError = false) {
  estado.textContent = texto;
  estado.classList.toggle('error', esError);
}

function renderFormulario() {
  selectDeporte.innerHTML = '<option value="" disabled selected>Elige uno…</option>';
  for (const d of [...config.deportes, config.otro_deporte]) {
    const opt = document.createElement('option');
    opt.value = d;
    opt.textContent = d;
    selectDeporte.appendChild(opt);
  }

  contPreguntas.innerHTML = '';
  for (const [id, texto] of Object.entries(config.preguntas)) {
    const label = document.createElement('label');
    label.htmlFor = `p${id}`;
    label.textContent = `${id}. ${texto}`;
    const area = document.createElement('textarea');
    area.id = `p${id}`;
    area.name = id;
    area.required = true;
    area.minLength = config.min_caracteres;
    area.maxLength = 500;
    contPreguntas.append(label, area);
  }
}

selectDeporte.addEventListener('change', () => {
  const esOtro = selectDeporte.value === config.otro_deporte;
  inputOtro.hidden = !esOtro;
  inputOtro.required = esOtro;
  if (esOtro) inputOtro.focus();
});

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const deporte = selectDeporte.value === config.otro_deporte ? inputOtro.value.trim() || config.otro_deporte : selectDeporte.value;
  const respuestas = {};
  for (const id of Object.keys(config.preguntas)) {
    respuestas[id] = document.getElementById(`p${id}`).value.trim();
  }

  btnEnviar.disabled = true;
  setEstado('Ubicando tus opiniones en el cubo…');
  try {
    const res = await api('/api/visita', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ deporte, respuestas }),
    });
    total.textContent = cubo.upsertPoints(res.puntos);
    cubo.highlightVisita(res.visita_id);
    form.reset();
    inputOtro.hidden = true;
    setEstado('¡Listo! Tus 3 opiniones ya están en el cubo. Entra a VR para recorrerlo.');
  } catch (err) {
    setEstado(err.message, true);
  } finally {
    btnEnviar.disabled = false;
  }
});

async function refrescarPuntos() {
  try {
    const puntos = await api('/api/puntos');
    total.textContent = cubo.upsertPoints(puntos);
  } catch {
    setEstado('No hay conexión con el servidor. Intenta de nuevo en un momento.', true);
  }
}

async function iniciar() {
  try {
    config = await api('/api/config');
    renderFormulario();
  } catch {
    setEstado('No hay conexión con el servidor. Intenta de nuevo en un momento.', true);
    btnEnviar.disabled = true;
    return;
  }
  await refrescarPuntos();
  setInterval(refrescarPuntos, POLL_MS);
}

iniciar();