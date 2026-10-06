import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { VRButton } from 'three/addons/webxr/VRButton.js';
import { XRControllerModelFactory } from 'three/addons/webxr/XRControllerModelFactory.js';

const DATA_BOUND = 12.5;
const CUBE_HALF = 0.6;
const DATA_SCALE = CUBE_HALF / DATA_BOUND;
const CUBE_CENTER = new THREE.Vector3(0, 1.3, -1.4);
const POINT_RADIUS = 0.028;
const HIGHLIGHT_SCALE = 1.9;
const HIT_RADIUS = 0.06;

const GEOMETRIES = {
  circle: new THREE.SphereGeometry(POINT_RADIUS, 20, 14),
  square: new THREE.BoxGeometry(POINT_RADIUS * 1.6, POINT_RADIUS * 1.6, POINT_RADIUS * 1.6),
  diamond: new THREE.OctahedronGeometry(POINT_RADIUS * 1.25),
};
const HIT_GEOMETRY = new THREE.SphereGeometry(HIT_RADIUS, 8, 6);
const HIT_MATERIAL = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0, depthWrite: false });

export function createCubeScene(container) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#eaf2fb');

  const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.05, 50);
  camera.position.set(0.5, 1.6, 0.9);

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.xr.enabled = true;
  container.appendChild(renderer.domElement);
  document.body.appendChild(VRButton.createButton(renderer));

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.target.copy(CUBE_CENTER);
  controls.enableDamping = true;
  controls.update();

  scene.add(new THREE.HemisphereLight('#ffffff', '#b8c7d9', 2.2));
  const sun = new THREE.DirectionalLight('#ffffff', 1.4);
  sun.position.set(2, 4, 1);
  scene.add(sun);

  const grid = new THREE.GridHelper(10, 40, '#a9bdd4', '#cfdbea');
  scene.add(grid);

  const cube = new THREE.Group();
  cube.position.copy(CUBE_CENTER);
  scene.add(cube);

  const frame = new THREE.LineSegments(
    new THREE.EdgesGeometry(new THREE.BoxGeometry(CUBE_HALF * 2, CUBE_HALF * 2, CUBE_HALF * 2)),
    new THREE.LineBasicMaterial({ color: '#7a95b5' }),
  );
  cube.add(frame);
  cube.add(createAxes());

  const pointsGroup = new THREE.Group();
  cube.add(pointsGroup);

  const infoPanel = createInfoPanel();
  infoPanel.mesh.position.copy(CUBE_CENTER).add(new THREE.Vector3(CUBE_HALF + 0.75, 0.1, 0.25));
  scene.add(infoPanel.mesh);

  const meshesById = new Map();
  let highlightedVisita = null;
  let selectedMesh = null;
  let hoveredMesh = null;
  let shownMesh;

  function upsertPoints(points) {
    for (const p of points) {
      if (meshesById.has(p.id)) continue;
      const geometry = GEOMETRIES[p.forma] ?? GEOMETRIES.circle;
      const material = new THREE.MeshStandardMaterial({ color: p.color, roughness: 0.45, metalness: 0.05 });
      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.set(p.x * DATA_SCALE, p.y * DATA_SCALE, p.z * DATA_SCALE);
      mesh.userData = { point: p, baseScale: 1, appear: 0 };
      mesh.scale.setScalar(0.001);
      const hitArea = new THREE.Mesh(HIT_GEOMETRY, HIT_MATERIAL);
      hitArea.userData.owner = mesh;
      mesh.add(hitArea);
      pointsGroup.add(mesh);
      meshesById.set(p.id, mesh);
    }
    applyHighlight();
    return meshesById.size;
  }

  function highlightVisita(visitaId) {
    highlightedVisita = visitaId;
    applyHighlight();
    const first = [...meshesById.values()].find((m) => m.userData.point.visita_id === visitaId);
    if (first) select(first);
  }

  function applyHighlight() {
    for (const mesh of meshesById.values()) {
      const mine = highlightedVisita && mesh.userData.point.visita_id === highlightedVisita;
      mesh.userData.baseScale = mine ? HIGHLIGHT_SCALE : 1;
      mesh.material.emissive.set(mine ? '#333333' : '#000000');
    }
  }

  function select(mesh) {
    selectedMesh = mesh;
  }

  function updatePanel() {
    const target = hoveredMesh ?? selectedMesh;
    if (target === shownMesh) return;
    shownMesh = target;
    infoPanel.show(target ? target.userData.point : null);
  }

  function firstPoint(hits) {
    for (const h of hits) {
      const owner = h.object.userData.owner ?? h.object;
      if (owner.userData.point) return owner;
    }
    return null;
  }

  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();
  let pointerInside = false;

  renderer.domElement.addEventListener('pointermove', (e) => {
    pointer.x = (e.clientX / window.innerWidth) * 2 - 1;
    pointer.y = -(e.clientY / window.innerHeight) * 2 + 1;
    pointerInside = true;
  });
  renderer.domElement.addEventListener('pointerleave', () => {
    pointerInside = false;
  });
  renderer.domElement.addEventListener('click', () => {
    if (hoveredMesh) select(hoveredMesh);
  });

  const controllers = setupControllers(renderer, scene, (controller) => {
    const hit = intersectFromController(controller);
    if (hit) select(hit);
  });

  const tempMatrix = new THREE.Matrix4();

  function intersectFromController(controller) {
    tempMatrix.identity().extractRotation(controller.matrixWorld);
    raycaster.ray.origin.setFromMatrixPosition(controller.matrixWorld);
    raycaster.ray.direction.set(0, 0, -1).applyMatrix4(tempMatrix);
    return firstPoint(raycaster.intersectObjects(pointsGroup.children, true));
  }

  function updateHover() {
    let hit = null;
    if (renderer.xr.isPresenting) {
      for (const c of controllers) {
        hit = intersectFromController(c);
        const line = c.getObjectByName('rayo');
        if (line) line.scale.z = hit ? raycaster.ray.origin.distanceTo(hit.getWorldPosition(new THREE.Vector3())) : 5;
        if (hit) break;
      }
    } else if (pointerInside) {
      raycaster.setFromCamera(pointer, camera);
      hit = firstPoint(raycaster.intersectObjects(pointsGroup.children, true));
    }
    hoveredMesh = hit;
    updatePanel();
    renderer.domElement.style.cursor = hit && !renderer.xr.isPresenting ? 'pointer' : 'default';
  }

  function rotateWithThumbsticks(delta) {
    const session = renderer.xr.getSession();
    if (!session) return;
    for (const source of session.inputSources) {
      const axes = source.gamepad?.axes;
      if (!axes || axes.length < 4) continue;
      const x = axes[2];
      if (Math.abs(x) > 0.15) cube.rotation.y += x * delta * 1.5;
    }
  }

  const clock = new THREE.Clock();

  renderer.setAnimationLoop(() => {
    const delta = clock.getDelta();
    const t = clock.elapsedTime;

    updateHover();
    rotateWithThumbsticks(delta);

    for (const mesh of meshesById.values()) {
      const d = mesh.userData;
      d.appear = Math.min(1, d.appear + delta * 2.5);
      const ease = 1 - Math.pow(1 - d.appear, 3);
      let s = d.baseScale * ease;
      if (d.baseScale > 1) s *= 1 + 0.08 * Math.sin(t * 4);
      if (mesh === hoveredMesh || mesh === selectedMesh) s *= 1.35;
      mesh.scale.setScalar(Math.max(s, 0.001));
    }

    if (!renderer.xr.isPresenting) controls.update();
    infoPanel.mesh.lookAt(camera.position);
    renderer.render(scene, camera);
  });

  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });

  return { upsertPoints, highlightVisita };
}

function createAxes() {
  const group = new THREE.Group();
  const material = new THREE.LineBasicMaterial({ color: '#b5c6da' });
  const h = CUBE_HALF;
  const axes = [
    [new THREE.Vector3(-h, 0, 0), new THREE.Vector3(h, 0, 0)],
    [new THREE.Vector3(0, -h, 0), new THREE.Vector3(0, h, 0)],
    [new THREE.Vector3(0, 0, -h), new THREE.Vector3(0, 0, h)],
  ];
  for (const [a, b] of axes) {
    group.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([a, b]), material));
  }
  return group;
}

function setupControllers(renderer, scene, onSelect) {
  const factory = new XRControllerModelFactory();
  const rayGeometry = new THREE.BufferGeometry().setFromPoints([
    new THREE.Vector3(0, 0, 0),
    new THREE.Vector3(0, 0, -1),
  ]);
  const controllers = [];

  for (let i = 0; i < 2; i++) {
    const controller = renderer.xr.getController(i);
    const ray = new THREE.Line(rayGeometry, new THREE.LineBasicMaterial({ color: '#1976d2' }));
    ray.name = 'rayo';
    ray.scale.z = 5;
    controller.add(ray);
    controller.addEventListener('selectstart', () => onSelect(controller));
    scene.add(controller);
    controllers.push(controller);

    const grip = renderer.xr.getControllerGrip(i);
    grip.add(factory.createControllerModel(grip));
    scene.add(grip);
  }
  return controllers;
}

function createInfoPanel() {
  const canvas = document.createElement('canvas');
  canvas.width = 1024;
  canvas.height = 420;
  const ctx = canvas.getContext('2d');
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;

  const mesh = new THREE.Mesh(
    new THREE.PlaneGeometry(1.05, 1.05 * (canvas.height / canvas.width)),
    new THREE.MeshBasicMaterial({ map: texture, transparent: true }),
  );

  function roundRect(x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  function wrap(text, x, y, maxWidth, lineHeight, maxLines) {
    const words = text.split(/\s+/);
    let line = '';
    let lines = 0;
    for (let i = 0; i < words.length; i++) {
      const test = line ? `${line} ${words[i]}` : words[i];
      if (ctx.measureText(test).width > maxWidth && line) {
        if (lines === maxLines - 1) {
          ctx.fillText(`${line}…`, x, y);
          return y + lineHeight;
        }
        ctx.fillText(line, x, y);
        line = words[i];
        y += lineHeight;
        lines++;
      } else {
        line = test;
      }
    }
    if (line) ctx.fillText(line, x, y);
    return y + lineHeight;
  }

  function show(point) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    roundRect(8, 8, canvas.width - 16, canvas.height - 16, 28);
    ctx.fillStyle = 'rgba(255,255,255,0.96)';
    ctx.fill();
    ctx.lineWidth = 4;
    ctx.strokeStyle = point ? point.color : '#d4deea';
    ctx.stroke();

    ctx.textBaseline = 'top';
    if (!point) {
      ctx.fillStyle = '#5d6470';
      ctx.font = '600 40px system-ui, sans-serif';
      ctx.fillText('Apunta a un punto para leer la opinión', 48, 180);
      texture.needsUpdate = true;
      return;
    }

    ctx.fillStyle = point.color;
    ctx.beginPath();
    ctx.arc(64, 70, 16, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = '#1c1b1b';
    ctx.font = '700 46px system-ui, sans-serif';
    ctx.fillText(point.deporte, 96, 48);

    ctx.fillStyle = '#5d6470';
    ctx.font = '500 30px system-ui, sans-serif';
    let y = wrap(`P${point.pregunta_id}. ${point.pregunta}`, 48, 112, canvas.width - 96, 38, 2);

    ctx.fillStyle = '#1c1b1b';
    ctx.font = '400 38px system-ui, sans-serif';
    wrap(`“${point.texto}”`, 48, y + 14, canvas.width - 96, 48, 4);

    texture.needsUpdate = true;
  }

  show(null);
  return { mesh, show };
}