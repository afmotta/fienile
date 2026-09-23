import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { PointerLockControls } from 'three/addons/controls/PointerLockControls.js';
import { Sky } from 'three/addons/objects/Sky.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { GTAOPass } from 'three/addons/postprocessing/GTAOPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

/* ==========================================================================
   PARAMETRI DI PROGETTO
   Fonte: CONTEXT.md (parete ovest, varianti PT/P1, cucina) + rilievo DWG
   "FIENILE_260430_post_rilievo" per il resto dell'edificio.
   Unità: metri. Posizioni lungo la parete misurate da nord (sinistra del prospetto).

   Assi della scena: +X = est (verso l'interno), -X = ovest (portico),
   +Z = sud, -Z = nord, +Y = alto. Filo esterno della parete ovest: x = 0.
   ========================================================================== */
const P = {
  sito: { lat: 45.51, lon: 9.33 },                 // Pioltello (MI)
  L: 13.47,            // lunghezza interna parete ovest
  tW: 0.45,            // spessore parete ovest
  hPiano: 2.70,        // altezza parete per piano
  solaio: 0.30,        // spessore solaio tra PT e P1
  hTesta: 2.50,        // filo superiore di tutte le finestre (architrave 20 cm)
  profSoggiorno: 4.64, // profondità open space: 2 × 31,23 m² / 13,47 m
  profEdificio: 10.50, // filo esterno ovest → filo esterno est (rilievo)
  tTestata: 0.60,      // muri di testata nord/sud
  tEst: 0.45,          // muro est
  // i pilastri della parete ovest (PT 3 × 30 cm, P1 2 × 30 cm) sono inglobati nella muratura:
  // restano nei vincoli delle varianti, ma non si vedono in facciata e non vengono disegnati
  arretramentoP1: 1.10, // il primo piano è arretrato di 110 cm rispetto al piano terra
  colonna: { z: [6.355, 7.115], x: [1.60, 2.36] }, // 76 cm, centrata; x dal filo interno
  varco: [8.50, 10.20],                            // passaggio verso ingresso/scala (rilievo)
  portico: { prof: 3.60, pilastri: [[-0.60, 0.10], [6.435, 7.035], [13.37, 14.07]] },
  // lati corti del portico chiusi da muri a gelosia in mattoni (vuoti regolari a corsi sfalsati)
  gelosia: { spessore: 0.25, zoccolo: 0.60, fasciaAlta: 0.25, spallaFacciata: 0.25 },
  // parapetto in ferro sul bordo del terrazzo: correnti piatti, bacchette verticali, montanti
  parapetto: { h: 1.00, arretramento: 0.06, passo: 0.114, bacchetta: 0.014, montante: 0.04, interasseMontanti: 1.50 },
  // tetto (dalla sezione di rilievo): quote dell'intradosso rispetto al pavimento PT
  tetto: { colmoX: 6.30, colmoH: 8.80, hOvest: 6.10, grondaOvestX: -4.80, hEst: 7.10, grondaEstX: 11.90 },
  cucina: { banco: { z: [0, 0.60], lungo: 3.60 }, isola: { z: [1.80, 2.80], x0: 1.20, lungo: 2.40 }, h: 0.90 },
};

// finestra = [posizione da nord, larghezza, altezza, davanzale]
const VAR_PT = {
  E:        { nome: 'E — F1/F4 174×150 (attuale)', rai: 0.260, f: [[1.000, 1.74, 1.5, 1], [3.5375, 2.9, 2.5, 0], [7.0325, 2.9, 2.5, 0], [10.730, 1.74, 1.5, 1]] },
  A:        { nome: 'A — tutte da terra',           rai: 0.292, f: [[1.045, 1.9, 2.5, 0], [3.538, 2.9, 2.5, 0], [7.033, 2.9, 2.5, 0], [10.525, 1.9, 2.5, 0]] },
  B:        { nome: 'B — F1/F4 190×150',            rai: 0.268, f: [[1.045, 1.9, 1.5, 1], [3.538, 2.9, 2.5, 0], [7.033, 2.9, 2.5, 0], [10.525, 1.9, 1.5, 1]] },
  C:        { nome: 'C — F1/F4 allargate',          rai: 0.311, f: [[0.1475, 2.795, 1.5, 1], [3.5375, 2.9, 2.5, 0], [7.0325, 2.9, 2.5, 0], [10.5275, 2.795, 1.5, 1]] },
  D:        { nome: 'D — F1/F4 160×150',            rai: 0.253, f: [[1.000, 1.6, 1.5, 1], [3.5375, 2.9, 2.5, 0], [7.0325, 2.9, 2.5, 0], [10.870, 1.6, 1.5, 1]] },
  attuale:  { nome: 'Progetto originale 200×250',   rai: 0.243, f: [[0.735, 2, 2.5, 0], [3.735, 2, 2.5, 0], [7.735, 2, 2.5, 0], [10.735, 2, 2.5, 0]] },
  regolare: { nome: 'Regolare 200×250',             rai: 0.243, f: [[0.735, 2, 2.5, 0], [3.9875, 2, 2.5, 0], [7.4825, 2, 2.5, 0], [10.735, 2, 2.5, 0]] },
};
const p1 = (w) => [[0.65, 0.6, 1.5, 1], [2.50, w, 2.5, 0], [P.L - 2.50 - w, w, 2.5, 0], [P.L - 0.65 - 0.6, 0.6, 1.5, 1]];
const VAR_P1 = {
  B: { nome: 'B — camere 174 (attuale)', f: p1(1.74) },
  A: { nome: 'A — camere 160', f: p1(1.60) },
  C: { nome: 'C — camere 180', f: p1(1.80) },
  D: { nome: 'D — camere 200', f: p1(2.00) },
};

/* ==========================================================================
   STATO E DOM
   ========================================================================== */
const $ = (id) => document.getElementById(id);
const state = {
  varPT: 'E', varP1: 'B',
  floor: 'cottoMilano', brick: 'naturale',
  showUpper: true, showKitchen: true, showFurniture: true, showLights: false, showAO: true,
  exposure: 0.9, hour: 16, date: null,
};
const today = new Date();
state.date = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;

/* ==========================================================================
   RENDERER, SCENA, CAMERA
   ========================================================================== */
const stage = $('stage');
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = state.exposure;
stage.appendChild(renderer.domElement);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.05, 2000);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.maxPolarAngle = Math.PI * 0.495;
controls.minDistance = 0.5;
controls.maxDistance = 80;

const walk = new PointerLockControls(camera, renderer.domElement);

const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));
const ao = new GTAOPass(scene, camera, window.innerWidth, window.innerHeight);
ao.updateGtaoMaterial({ radius: 0.6, distanceExponent: 1.0, thickness: 1.0, scale: 1.0 });
ao.blendIntensity = 0.9;
composer.addPass(ao);
composer.addPass(new OutputPass());

/* ---------- cielo, sole, ambiente ---------- */
const sky = new Sky();
sky.scale.setScalar(4500);
Object.assign(sky.material.uniforms.turbidity, { value: 3.5 });
sky.material.uniforms.rayleigh.value = 1.6;
sky.material.uniforms.mieCoefficient.value = 0.004;
sky.material.uniforms.mieDirectionalG.value = 0.8;
scene.add(sky);

const sun = new THREE.DirectionalLight(0xfff1dd, 3);
sun.castShadow = true;
sun.shadow.mapSize.set(4096, 4096);
Object.assign(sun.shadow.camera, { left: -20, right: 20, top: 20, bottom: -20, near: 1, far: 120 });
sun.shadow.bias = -0.0004;
sun.shadow.normalBias = 0.03;
scene.add(sun, sun.target);
// rimbalzo caldo dal pavimento e dal portico: compensa l'assenza di illuminazione globale
const bounce = new THREE.HemisphereLight(0xf1ebe1, 0xb99a7a, 0.5);
scene.add(bounce);
sun.target.position.set(4, 2, P.L / 2);

const pmrem = new THREE.PMREMGenerator(renderer);
const envScene = new THREE.Scene();
let envRT = null;

/* ==========================================================================
   TEXTURE PROCEDURALI (canvas) — UV in metri, repeat = 1 / lato del tassello
   ========================================================================== */
function rand(seed) { let s = seed >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }

function canvasTex(px, py, meters, draw, srgb = true) {
  const c = document.createElement('canvas'); c.width = px; c.height = py;
  draw(c.getContext('2d'), px, py);
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(1 / meters[0], 1 / meters[1]);
  t.anisotropy = renderer.capabilities.getMaxAnisotropy();
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
function noiseTex(meters, amp, seed) {
  return canvasTex(256, 256, meters, (g, w, h) => {
    const r = rand(seed), img = g.createImageData(w, h);
    for (let i = 0; i < w * h; i++) {
      const v = 255 - r() * amp;
      img.data[i * 4] = img.data[i * 4 + 1] = img.data[i * 4 + 2] = v; img.data[i * 4 + 3] = 255;
    }
    g.putImageData(img, 0, 0);
  });
}
function woodTex(base, seed) {
  // doghe da 19 cm che corrono lungo Z (lunghezza del soggiorno)
  const [r0, g0, b0] = base;
  return canvasTex(1024, 1024, [1.9, 1.9], (g, w, h) => {
    const rnd = rand(seed), cols = 10, cw = w / cols;
    for (let c = 0; c < cols; c++) {
      let y = -rnd() * h;
      while (y < h) {
        const len = h * (0.45 + rnd() * 0.5), k = 0.85 + rnd() * 0.25;
        g.fillStyle = `rgb(${r0 * k | 0},${g0 * k | 0},${b0 * k | 0})`;
        g.fillRect(c * cw, y, cw, len);
        g.globalAlpha = 0.12;
        for (let i = 0; i < 26; i++) {
          const x = c * cw + rnd() * cw;
          g.strokeStyle = rnd() > 0.5 ? '#3b2616' : '#fff3dd';
          g.lineWidth = 0.6 + rnd() * 1.6;
          g.beginPath(); g.moveTo(x, y);
          g.bezierCurveTo(x + (rnd() - 0.5) * 8, y + len * 0.3, x + (rnd() - 0.5) * 8, y + len * 0.7, x, y + len);
          g.stroke();
        }
        g.globalAlpha = 1;
        g.fillStyle = 'rgba(40,25,15,0.55)'; g.fillRect(c * cw, y, cw, 1.5);
        y += len;
      }
      g.fillStyle = 'rgba(40,25,15,0.55)'; g.fillRect(c * cw, 0, 1.5, h);
    }
  });
}
function tileTex(size, c1, c2, joint, seed, tilesPerTex) {
  const m = size * tilesPerTex;
  return canvasTex(512, 512, [m, m], (g, w, h) => {
    const rnd = rand(seed), s = w / tilesPerTex;
    g.fillStyle = joint; g.fillRect(0, 0, w, h);
    for (let i = 0; i < tilesPerTex; i++) for (let j = 0; j < tilesPerTex; j++) {
      g.fillStyle = rnd() > 0.5 ? c1 : c2; g.fillRect(i * s + 1.5, j * s + 1.5, s - 3, s - 3);
      g.globalAlpha = 0.08;
      for (let k = 0; k < 40; k++) {
        g.fillStyle = rnd() > 0.5 ? '#000' : '#fff';
        g.fillRect(i * s + rnd() * s, j * s + rnd() * s, 2 + rnd() * 10, 2 + rnd() * 10);
      }
      g.globalAlpha = 1;
    }
  });
}
function brickTex(limewash, seed) {
  // mattone ~25 × 5,5 cm, fuga 1 cm: il tassello è 1,04 × 0,52 m (4 teste × 8 corsi)
  return canvasTex(512, 256, [1.04, 0.52], (g, w, h) => {
    const rnd = rand(seed), bw = w / 4, ch = h / 8, mortar = 5;
    g.fillStyle = '#9d9383'; g.fillRect(0, 0, w, h);
    for (let row = 0; row < 8; row++) {
      const off = row % 2 ? bw / 2 : 0;
      for (let i = -1; i < 5; i++) {
        const k = 0.78 + rnd() * 0.32, rr = 150 * k, gg = 78 * k * (0.9 + rnd() * 0.2), bb = 54 * k;
        g.fillStyle = `rgb(${rr | 0},${gg | 0},${bb | 0})`;
        g.fillRect(i * bw + off + mortar / 2, row * ch + mortar / 2, bw - mortar, ch - mortar);
      }
    }
    if (limewash) {
      for (let k = 0; k < 90; k++) {
        g.fillStyle = `rgba(236,231,221,${0.25 + rnd() * 0.45})`;
        g.beginPath(); g.ellipse(rnd() * w, rnd() * h, 20 + rnd() * 60, 10 + rnd() * 30, 0, 0, Math.PI * 2); g.fill();
      }
    }
  });
}

function latticeTex(limewash, seed) {
  // mattoni 25 × 5,5 cm con vuoti di 12,5 cm, corsi alterni sfalsati di mezzo passo.
  // Tassello: 0,75 m (2 mattoni + 2 vuoti) × 0,13 m (2 corsi). Il vuoto è trasparente.
  const pxm = 800, W = 0.75 * pxm, Hh = 0.13 * pxm;
  return canvasTex(W, Hh, [0.75, 0.13], (g, w, h) => {
    const rnd = rand(seed), bw = 0.25 * pxm, gap = 0.125 * pxm, ch = 0.065 * pxm, m = 0.01 * pxm;
    g.clearRect(0, 0, w, h);
    for (let row = 0; row < 2; row++) {
      const y = h - (row + 1) * ch, off = row ? (bw + gap) / 2 : 0;
      g.fillStyle = '#9d9383'; g.fillRect(0, y + ch - m, w, m);               // letto di malta continuo
      for (let i = -1; i < 3; i++) {
        const x = off + i * (bw + gap);
        const k = 0.78 + rnd() * 0.32;
        g.fillStyle = `rgb(${150 * k | 0},${78 * k * (0.9 + rnd() * 0.2) | 0},${54 * k | 0})`;
        g.fillRect(x, y, bw, ch - m);
        if (limewash) { g.fillStyle = `rgba(236,231,221,${0.3 + rnd() * 0.4})`; g.fillRect(x, y, bw * (0.4 + rnd() * 0.6), ch - m); }
      }
    }
  });
}

function cottoMilanoTex(seed) {
  // lastre 120×120 in gres effetto cotto lombardo: ogni lastra ha il suo tono, velature e
  // abrasioni morbide, fuga sottile (~3 mm). Tassello: 4×4 lastre = 4,8 m, per non far notare la ripetizione.
  const n = 4, size = 1.2;
  return canvasTex(2048, 2048, [n * size, n * size], (g, w, h) => {
    const rnd = rand(seed), sp = w / n;
    for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) {
      const x0 = i * sp, y0 = j * sp, k = 0.9 + rnd() * 0.16, warm = rnd() * 10;
      g.fillStyle = `rgb(${188 * k + warm | 0},${106 * k | 0},${68 * k - warm / 2 | 0})`;
      g.fillRect(x0, y0, sp, sp);
      g.save(); g.beginPath(); g.rect(x0, y0, sp, sp); g.clip();
      for (let m = 0; m < 70; m++) {                       // velature chiare e scure
        const cx = x0 + rnd() * sp, cy = y0 + rnd() * sp, r = 20 + rnd() * 140;
        const grd = g.createRadialGradient(cx, cy, 0, cx, cy, r);
        const light = rnd() > 0.45;
        grd.addColorStop(0, light ? 'rgba(222,160,120,0.16)' : 'rgba(110,52,30,0.14)');
        grd.addColorStop(1, 'rgba(0,0,0,0)');
        g.fillStyle = grd; g.fillRect(cx - r, cy - r, 2 * r, 2 * r);
      }
      for (let m = 0; m < 1400; m++) {                     // puntinatura fine della pasta
        g.fillStyle = rnd() > 0.5 ? 'rgba(90,40,22,0.18)' : 'rgba(235,190,150,0.16)';
        g.fillRect(x0 + rnd() * sp, y0 + rnd() * sp, 1 + rnd() * 2.5, 1 + rnd() * 2.5);
      }
      for (let m = 0; m < 6; m++) {                        // abrasioni tipiche del cotto
        g.fillStyle = 'rgba(214,168,132,0.22)';
        g.beginPath(); g.ellipse(x0 + rnd() * sp, y0 + rnd() * sp, 6 + rnd() * 24, 3 + rnd() * 10, rnd() * Math.PI, 0, Math.PI * 2); g.fill();
      }
      g.restore();
      g.fillStyle = '#8c7d70';                             // fughe
      g.fillRect(x0, y0, sp, 1.3); g.fillRect(x0, y0, 1.3, sp);
    }
  });
}

const TEX = {
  plaster: noiseTex([1, 1], 18, 7),
  rovere: woodTex([206, 158, 104], 11),
  rovereFume: woodTex([128, 102, 80], 12),
  cotto: tileTex(0.30, '#b4643e', '#9c5230', '#bdb4a6', 13, 4),
  gres: tileTex(0.60, '#a6a29b', '#9c9891', '#8f8b85', 14, 2),
  resina: noiseTex([2, 2], 26, 15),
  cottoMilano: cottoMilanoTex(41),
  mattoneNaturale: brickTex(false, 21),
  mattoneScialbato: brickTex(true, 21),
  gelosiaNaturale: latticeTex(false, 31),
  gelosiaScialbata: latticeTex(true, 31),
  portico: tileTex(0.50, '#9d968b', '#8f887d', '#6d675f', 16, 2),
};

/* ---------- materiali ---------- */
const std = (o) => new THREE.MeshStandardMaterial(o);
const M = {
  facade:   std({ color: 0xefe2b4, map: TEX.plaster, roughness: 0.95 }),   // intonaco giallo molto pallido
  interno:  std({ color: 0xf2efe9, map: TEX.plaster, roughness: 0.95 }),
  soffitto: std({ color: 0xf4f2ee, map: TEX.plaster, roughness: 0.95 }),
  pavimento: std({ map: TEX.rovere, roughness: 0.55 }),
  mattone:  std({ map: TEX.mattoneNaturale, roughness: 0.9 }),
  gelosia:  std({ map: TEX.gelosiaNaturale, roughness: 0.9, alphaTest: 0.5, side: THREE.DoubleSide }),
  telaio:   std({ color: 0x2b2b2b, roughness: 0.45, metalness: 0.6 }),
  vetro:    new THREE.MeshPhysicalMaterial({ color: 0xe4eef2, roughness: 0.03, metalness: 0, transparent: true, opacity: 0.16, envMapIntensity: 1.2, depthWrite: false }),
  davanzale: std({ color: 0xd8d2c6, roughness: 0.6 }),
  portico:  std({ map: TEX.cottoMilano, roughness: 0.92 }),   // stesso cotto, versione strutturata R11
  pavimentoP1: std({ map: TEX.rovere, roughness: 0.55 }),
  ferro:    std({ color: 0x3a3936, roughness: 0.55, metalness: 0.7 }),       // ferro micaceo scuro
  coppi:    std({ color: 0x9f5638, roughness: 0.85 }),
  tavolato: std({ map: TEX.rovereFume, roughness: 0.8 }),
  prato:    std({ color: 0x66753f, roughness: 1 }),
  cucina:   std({ color: 0xf0eee9, roughness: 0.4 }),
  top:      std({ color: 0xd6d0c5, roughness: 0.35 }),
  legno:    std({ map: TEX.rovere, color: 0xc9b39a, roughness: 0.6 }),
  tessuto:  std({ color: 0xc8baa3, roughness: 1 }),
  scuro:    std({ color: 0x222222, roughness: 0.5, metalness: 0.4 }),
  led:      std({ color: 0x000000, emissive: 0xffc98a, emissiveIntensity: 0 }),
};
const FLOOR = {
  cottoMilano: { map: TEX.cottoMilano, color: 0xffffff, roughness: 0.85 },
  rovere:     { map: TEX.rovere, color: 0xffffff, roughness: 0.55 },
  rovereFume: { map: TEX.rovereFume, color: 0xffffff, roughness: 0.55 },
  resina:     { map: TEX.resina, color: 0x9d9a95, roughness: 0.3 },
  cotto:      { map: TEX.cotto, color: 0xffffff, roughness: 0.75 },
  gres:       { map: TEX.gres, color: 0xffffff, roughness: 0.6 },
};

/* ==========================================================================
   GEOMETRIA
   ========================================================================== */
// box con UV in metri: la texture si ripete a scala reale su ogni faccia
function box(x0, y0, z0, x1, y1, z1, mat, group, opts = {}) {
  const w = Math.abs(x1 - x0), h = Math.abs(y1 - y0), d = Math.abs(z1 - z0);
  if (w < 1e-4 || h < 1e-4 || d < 1e-4) return null;
  const geo = new THREE.BoxGeometry(w, h, d);
  const uv = geo.attributes.uv;
  const dims = [[d, h], [d, h], [w, d], [w, d], [w, h], [w, h]];
  for (let f = 0; f < 6; f++) for (let k = 0; k < 4; k++) {
    const i = f * 4 + k; uv.setXY(i, uv.getX(i) * dims[f][0], uv.getY(i) * dims[f][1]);
  }
  const m = new THREE.Mesh(geo, mat);
  m.position.set((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2);
  m.castShadow = opts.cast !== false; m.receiveShadow = true;
  group.add(m);
  return m;
}
// profilo nel piano X/Y estruso lungo Z (tetto, timpani)
function extrude(points, z0, z1, mat, group) {
  const s = new THREE.Shape(points.map(([x, y]) => new THREE.Vector2(x, y)));
  const geo = new THREE.ExtrudeGeometry(s, { depth: z1 - z0, bevelEnabled: false });
  const m = new THREE.Mesh(geo, mat);
  m.position.z = z0; m.castShadow = m.receiveShadow = true;
  group.add(m); return m;
}
const T = P.tetto;
const roofH = (x) => x <= T.colmoX
  ? T.colmoH - (T.colmoH - T.hOvest) * (T.colmoX - x) / T.colmoX
  : T.colmoH - (T.colmoH - T.hEst) * (x - T.colmoX) / (P.profEdificio - T.colmoX);

let house = null;
const WALL = () => [M.interno, M.facade, M.facade, M.facade, M.facade, M.facade]; // +x = lato interno
const G = {};

// parete ovest di un piano: tratti pieni, finestre con telaio, davanzali, architravi.
// ox = filo esterno della parete (0 al piano terra, arretrato al primo piano)
function westWall(y0, windows, group, ox = 0) {
  const H = P.hPiano, t = P.tW;
  const cuts = windows.map(([p, w]) => [p, p + w]).sort((a, b) => a[0] - b[0]);
  let z = 0;
  for (const [a, b] of cuts) { if (a > z) box(ox, y0, z, ox + t, y0 + H, a, WALL(), group); z = Math.max(z, b); }
  if (z < P.L) box(ox, y0, z, ox + t, y0 + H, P.L, WALL(), group);
  for (const [p, w, h, sill] of windows) {
    const a = p, b = p + w, top = y0 + sill + h;
    if (sill > 0) {
      box(ox, y0, a, ox + t, y0 + sill - 0.03, b, WALL(), group);
      box(ox - 0.04, y0 + sill - 0.03, a - 0.03, ox + t - 0.1, y0 + sill, b + 0.03, M.davanzale, group); // soglia/davanzale
    }
    box(ox, top, a, ox + t, y0 + H, b, WALL(), group);                       // architrave
    if (sill === 0) box(ox - 0.02, y0 - 0.02, a, ox + t, y0, b, M.davanzale, group, { cast: false }); // soglia
    // telaio a ~2/3 dello spessore, verso l'interno
    const fx0 = ox + t - 0.16, fx1 = ox + t - 0.09, fw = 0.055, yb = y0 + sill;
    box(fx0, yb, a, fx1, yb + fw, b, M.telaio, group);
    box(fx0, top - fw, a, fx1, top, b, M.telaio, group);
    box(fx0, yb, a, fx1, top, a + fw, M.telaio, group);
    box(fx0, yb, b - fw, fx1, top, b, M.telaio, group);
    const leaves = w > 2.2 ? 3 : w > 1.1 ? 2 : 1;
    for (let i = 1; i < leaves; i++) {
      const zm = a + (w * i) / leaves;
      box(fx0, yb, zm - 0.03, fx1, top, zm + 0.03, M.telaio, group);
    }
    box(fx0 + 0.03, yb, a, fx0 + 0.035, top, b, M.vetro, group, { cast: false });
  }
}

// parapetto in ferro: corrente superiore e inferiore piatti, montanti, bacchette verticali (instanced)
function railing(yb, z0, z1, group) {
  const R = P.parapetto, x0 = R.arretramento, x1 = x0 + 0.05, ytop = yb + R.h;
  box(x0 - 0.005, ytop - 0.01, z0, x1 + 0.005, ytop, z1, M.ferro, group);        // corrimano piatto 60×10
  box(x0, yb + 0.07, z0, x1 - 0.02, yb + 0.08, z1, M.ferro, group);             // corrente inferiore
  const nPost = Math.max(2, Math.round((z1 - z0) / R.interasseMontanti) + 1);
  for (let i = 0; i < nPost; i++) {
    const z = z0 + (z1 - z0) * i / (nPost - 1);
    const za = Math.min(Math.max(z - R.montante / 2, z0), z1 - R.montante);
    box(x0, yb, za, x0 + R.montante, ytop - 0.01, za + R.montante, M.ferro, group);
  }
  const n = Math.floor((z1 - z0) / R.passo);
  const geo = new THREE.BoxGeometry(R.bacchetta, ytop - 0.01 - (yb + 0.08), R.bacchetta);
  const bars = new THREE.InstancedMesh(geo, M.ferro, n);
  const m4 = new THREE.Matrix4();
  for (let i = 0; i < n; i++) {
    m4.makeTranslation(x0 + 0.02, (ytop - 0.01 + yb + 0.08) / 2, z0 + R.passo * (i + 0.5));
    bars.setMatrixAt(i, m4);
  }
  bars.castShadow = bars.receiveShadow = true;
  group.add(bars);
}

function build() {
  if (house) {
    house.traverse((o) => { if (o.isMesh) o.geometry.dispose(); });
    scene.remove(house);
  }
  house = new THREE.Group();
  for (const k of ['pt', 'upper', 'kitchen', 'furniture', 'lights', 'ground']) {
    G[k] = new THREE.Group(); house.add(G[k]);
  }
  const L = P.L, D = P.profEdificio, t = P.tW, H = P.hPiano, S = P.solaio;
  const xi = t, xs = t + P.profSoggiorno;          // filo interno ovest, fine open space
  const y1 = H + S;                                 // quota pavimento P1
  const tt = P.tTestata;

  // --- terreno e portico
  box(-60, -0.06, -60, 60, -0.04, 60, M.prato, G.ground, { cast: false });
  box(-P.portico.prof, -0.04, -tt, 0, -0.01, L + tt, M.portico, G.ground, { cast: false });
  for (const [a, b] of P.portico.pilastri)
    box(-P.portico.prof, 0, a, -P.portico.prof + 0.6, roofH(-P.portico.prof + 0.6) + 0.05, b, M.mattone, G.pt);
  // muri a gelosia sui due lati corti: portico al piano terra e, sopra il solaio, i lati del terrazzo
  // davanti al primo piano arretrato. Zoccolo pieno, traforo continuo, fascia piena sotto la falda.
  const gz = P.gelosia, xa = -P.portico.prof + 0.6, xb = 0, xt = P.arretramentoP1;
  const xl0 = xa, xl1 = xb - gz.spallaFacciata, yt = H + S;
  const hTop = (x) => roofH(x) - gz.fasciaAlta;
  for (const zOut of [-tt + 0.05, L + tt - 0.05 - gz.spessore]) {
    const z0 = zOut, z1 = zOut + gz.spessore;
    box(xa, 0, z0, xb, gz.zoccolo, z1, M.mattone, G.pt);                                   // zoccolo
    box(xl1, gz.zoccolo, z0, xb, yt, z1, M.mattone, G.pt);                                 // spalla fino al solaio
    extrude([[xl0, gz.zoccolo], [xl1, gz.zoccolo], [xl1, hTop(xl1)], [xl0, hTop(xl0)]],
            z0, z1, M.gelosia, G.pt);                                                      // traforo del portico
    extrude([[xl1, yt], [xt, yt], [xt, hTop(xt)], [xl1, hTop(xl1)]],
            z0, z1, M.gelosia, G.upper);                                                   // traforo del terrazzo
    extrude([[xa, hTop(xa)], [xt, hTop(xt)], [xt, roofH(xt) + 0.05], [xa, roofH(xa) + 0.05]],
            z0, z1, M.mattone, G.upper);                                                   // fascia alta continua
  }

  // --- piano terra
  box(xi, -0.02, 0, D - P.tEst, 0, L, M.pavimento, G.pt, { cast: false });
  westWall(0, VAR_PT[state.varPT].f, G.pt);
  // testate nord/sud e muro est fino al solaio
  box(0, 0, -tt, D, y1, 0, M.facade, G.pt);
  box(0, 0, L, D, y1, L + tt, M.facade, G.pt);
  box(D - P.tEst, 0, 0, D, y1, L, M.facade, G.pt);
  // pelli interne bianche dell'open space
  box(xi, 0, 0, xs, H, 0.01, M.interno, G.pt, { cast: false });
  box(xi, 0, L - 0.01, xs, H, L, M.interno, G.pt, { cast: false });
  // muro interno est dell'open space, con varco
  const [va, vb] = P.varco;
  box(xs, 0, 0, xs + 0.3, H, va, M.interno, G.pt);
  box(xs, 0, vb, xs + 0.3, H, L, M.interno, G.pt);
  box(xs, 2.2, va, xs + 0.3, H, vb, M.interno, G.pt);
  // colonna in mattoni
  box(xi + P.colonna.x[0], 0, P.colonna.z[0], xi + P.colonna.x[1], H, P.colonna.z[1], M.mattone, G.pt);
  // solaio: intradosso bianco, fascia di facciata gialla
  // (nel gruppo del primo piano, così la vista in pianta lo toglie insieme al tetto)
  box(xi, H, 0, D - P.tEst, y1, L, M.soffitto, G.upper);
  box(0, H, 0, xi, y1, L, M.facade, G.upper);

  // --- primo piano (involucro) + tetto
  const ox = P.arretramentoP1;
  westWall(y1, VAR_P1[state.varP1].f, G.upper, ox);
  box(ox, y1 + H, 0, ox + t, roofH(ox) + 0.05, L, WALL(), G.upper);
  box(ox + t, y1 - 0.02, 0, D - P.tEst, y1, L, M.pavimentoP1, G.upper, { cast: false });
  box(0, y1, 0, ox, y1 + 0.02, L, M.portico, G.upper, { cast: false });   // terrazzo davanti al P1
  railing(y1 + 0.02, -tt + 0.05 + P.gelosia.spessore, L + tt - 0.05 - P.gelosia.spessore, G.upper);
  box(D - P.tEst, y1, 0, D, roofH(D) + 0.05, L, M.facade, G.upper);
  const gable = [[ox, y1], [D, y1], [D, roofH(D)], [T.colmoX, T.colmoH], [ox, roofH(ox)]];
  extrude(gable, -tt, 0, M.facade, G.upper);
  extrude(gable, L, L + tt, M.facade, G.upper);
  // falde: tavolato sotto (visibile dal portico), coppi sopra
  const xw = T.grondaOvestX, xe = T.grondaEstX;
  const hwE = roofH(0) + (xw / T.colmoX) * (T.colmoH - T.hOvest);            // prolungamento falda ovest
  const heE = roofH(D) - ((xe - D) / (D - T.colmoX)) * (T.colmoH - T.hEst);  // prolungamento falda est
  const under = [[xw, hwE], [T.colmoX, T.colmoH], [xe, heE]];
  const lay = (pts, dy0, dy1) => [...pts.map(([x, y]) => [x, y + dy0]), ...pts.slice().reverse().map(([x, y]) => [x, y + dy1])];
  extrude(lay(under, 0, 0.12), -tt - 0.5, L + tt + 0.5, M.tavolato, G.upper);
  extrude(lay(under, 0.12, 0.32), -tt - 0.6, L + tt + 0.6, M.coppi, G.upper);

  // --- cucina di progetto (banco lungo la testata nord, isola)
  const C = P.cucina;
  box(xi, 0.1, C.banco.z[0], xi + C.banco.lungo, C.h - 0.04, C.banco.z[1], M.cucina, G.kitchen);
  box(xi, C.h - 0.04, C.banco.z[0], xi + C.banco.lungo, C.h, C.banco.z[1] + 0.02, M.top, G.kitchen);
  box(xi, 0, C.banco.z[0], xi + C.banco.lungo, 0.1, C.banco.z[1] - 0.05, M.scuro, G.kitchen);
  const ix0 = xi + C.isola.x0;
  box(ix0, 0.1, C.isola.z[0], ix0 + C.isola.lungo, C.h - 0.04, C.isola.z[1], M.cucina, G.kitchen);
  box(ix0 - 0.02, C.h - 0.04, C.isola.z[0] - 0.02, ix0 + C.isola.lungo + 0.02, C.h, C.isola.z[1] + 0.02, M.top, G.kitchen);
  box(ix0 + 0.05, 0, C.isola.z[0] + 0.05, ix0 + C.isola.lungo - 0.05, 0.1, C.isola.z[1] - 0.05, M.scuro, G.kitchen);

  // --- arredo indicativo: tavolo tra cucina e colonna, divano e tappeto nella metà sud
  const tz0 = 4.15, tz1 = 5.15, tx0 = xi + 0.70, tx1 = xi + 2.90;
  box(tx0, 0.72, tz0, tx1, 0.76, tz1, M.legno, G.furniture);
  for (const [x, z] of [[tx0 + 0.06, tz0 + 0.06], [tx1 - 0.11, tz0 + 0.06], [tx0 + 0.06, tz1 - 0.11], [tx1 - 0.11, tz1 - 0.11]])
    box(x, 0, z, x + 0.05, 0.72, z + 0.05, M.scuro, G.furniture);
  for (let i = 0; i < 3; i++) for (const side of [-1, 1]) {
    const x = tx0 + 0.3 + i * 0.7, z = side < 0 ? tz0 - 0.5 : tz1 + 0.08;
    box(x, 0.44, z, x + 0.44, 0.48, z + 0.42, M.scuro, G.furniture);
    const bz = side < 0 ? z : z + 0.38;
    box(x, 0.48, bz, x + 0.44, 0.85, bz + 0.04, M.scuro, G.furniture);
  }
  box(xi + 0.9, 0, 8.3, xi + 3.7, 0.012, 11.6, M.tessuto, G.furniture, { cast: false });
  const sx = xi + 3.3;
  box(sx, 0.1, 8.5, sx + 0.95, 0.42, 11.4, M.tessuto, G.furniture);
  box(sx + 0.72, 0.42, 8.5, sx + 0.95, 0.82, 11.4, M.tessuto, G.furniture);
  box(xi + 1.6, 0, 9.4, xi + 2.4, 0.36, 10.4, M.legno, G.furniture);

  // --- luci interne: profili LED a sguscio + punti luce caldi (nessuna ombra, per restare fluidi)
  const zc = H - 0.2;
  box(xi + 0.08, zc, 0.12, xs - 0.08, zc + 0.012, 0.17, M.led, G.lights, { cast: false });
  box(xi + 0.08, zc, L - 0.17, xs - 0.08, zc + 0.012, L - 0.12, M.led, G.lights, { cast: false });
  box(xs - 0.17, zc, 0.12, xs - 0.12, zc + 0.012, va - 0.1, M.led, G.lights, { cast: false });
  box(xs - 0.17, zc, vb + 0.1, xs - 0.12, zc + 0.012, L - 0.12, M.led, G.lights, { cast: false });
  for (const [x, z] of [[xi + 1.8, 1.9], [xi + 1.8, 4.6], [xi + 2.4, 10.0], [xi + 3.2, 7.3]]) {
    const pl = new THREE.PointLight(0xffc68c, 6, 7, 1.6); pl.position.set(x, 2.1, z); G.lights.add(pl);
  }

  scene.add(house);
  applyVisibility();
}

/* ==========================================================================
   SOLE (algoritmo NOAA semplificato) + ora legale italiana
   ========================================================================== */
function lastSunday(y, m) { const d = new Date(Date.UTC(y, m + 1, 0)); d.setUTCDate(d.getUTCDate() - d.getUTCDay()); return d.getUTCDate(); }
function localToUTC(dateStr, hour) {
  const [y, m, d] = dateStr.split('-').map(Number);
  const hh = Math.floor(hour), mm = Math.round((hour - hh) * 60);
  const dstStart = Date.UTC(y, 2, lastSunday(y, 2), 1), dstEnd = Date.UTC(y, 9, lastSunday(y, 9), 1);
  let utc = Date.UTC(y, m - 1, d, hh - 1, mm);
  if (utc >= dstStart && utc < dstEnd) utc -= 3600e3;
  return new Date(utc);
}
function sunPosition(date, lat, lon) {
  const rad = Math.PI / 180;
  const d = date.getTime() / 86400000 + 2440587.5 - 2451545.0;
  const g = (357.529 + 0.98560028 * d) * rad;
  const q = 280.459 + 0.98564736 * d;
  const Lm = (q + 1.915 * Math.sin(g) + 0.020 * Math.sin(2 * g)) * rad;
  const e = (23.439 - 0.00000036 * d) * rad;
  const ra = Math.atan2(Math.cos(e) * Math.sin(Lm), Math.cos(Lm));
  const dec = Math.asin(Math.sin(e) * Math.sin(Lm));
  const gmst = ((18.697374558 + 24.06570982441908 * d) % 24 + 24) % 24;
  const H = (gmst * 15 + lon) * rad - ra, phi = lat * rad;
  const el = Math.asin(Math.sin(phi) * Math.sin(dec) + Math.cos(phi) * Math.cos(dec) * Math.cos(H));
  let az = Math.atan2(-Math.sin(H), Math.tan(dec) * Math.cos(phi) - Math.sin(phi) * Math.cos(H));
  if (az < 0) az += 2 * Math.PI;
  return { az, el };
}
const DIRS = ['N', 'NE', 'E', 'SE', 'S', 'SO', 'O', 'NO'];

let envDirty = true;
function updateSun() {
  const { az, el } = sunPosition(localToUTC(state.date, state.hour), P.sito.lat, P.sito.lon);
  // verso il sole in coordinate scena: est = +X, nord = -Z
  const v = new THREE.Vector3(Math.sin(az) * Math.cos(el), Math.sin(el), -Math.cos(az) * Math.cos(el));
  sky.material.uniforms.sunPosition.value.copy(v);
  sun.position.copy(sun.target.position).addScaledVector(v, 60);
  const day = THREE.MathUtils.smoothstep(el * 180 / Math.PI, -1, 8);
  sun.intensity = 3.2 * day;
  sun.color.setHSL(0.09, 0.9, 0.62 + 0.3 * THREE.MathUtils.smoothstep(el * 180 / Math.PI, 2, 30));
  scene.environmentIntensity = 0.06 + 0.32 * day;
  bounce.intensity = 0.05 + 0.75 * day;
  const hh = Math.floor(state.hour), mm = Math.round((state.hour - hh) * 60);
  $('timeRead').textContent = `${String(hh).padStart(2, '0')}:${String(mm).padStart(2, '0')}`;
  const deg = (r) => (r * 180 / Math.PI).toFixed(0);
  $('sunRead').innerHTML = el > 0
    ? `az ${deg(az)}° ${DIRS[Math.round(az / (Math.PI / 4)) % 8]}<br>el ${deg(el)}°`
    : 'sole sotto<br>l\'orizzonte';
  envDirty = true;
}
function refreshEnvironment() {
  // la mappa d'ambiente viene dal cielo: più calda al tramonto, scura di notte
  envScene.add(sky);
  if (envRT) envRT.dispose();
  envRT = pmrem.fromScene(envScene, 0, 1, 3000);
  scene.add(sky);
  scene.environment = envRT.texture;
  envDirty = false;
}

/* ==========================================================================
   INTERFACCIA
   ========================================================================== */
function fillSelect(sel, data, value) {
  sel.innerHTML = Object.entries(data).map(([k, v]) => `<option value="${k}">${v.nome}</option>`).join('');
  sel.value = value;
}
fillSelect($('varPT'), VAR_PT, state.varPT);
fillSelect($('varP1'), VAR_P1, state.varP1);
function raiHint() {
  const v = VAR_PT[state.varPT];
  $('raiPT').textContent = `RAI piano terra ${v.rai.toFixed(3).replace('.', ',')} (minimo 0,125).`;
}
raiHint();

function applyMaterials() {
  const f = FLOOR[state.floor];
  M.pavimento.map = f.map; M.pavimento.color.set(f.color); M.pavimento.roughness = f.roughness;
  M.pavimento.needsUpdate = true;
  M.mattone.map = state.brick === 'scialbato' ? TEX.mattoneScialbato : TEX.mattoneNaturale;
  M.mattone.needsUpdate = true;
  M.gelosia.map = state.brick === 'scialbato' ? TEX.gelosiaScialbata : TEX.gelosiaNaturale;
  M.gelosia.needsUpdate = true;
}
function applyVisibility() {
  if (!house) return;
  G.upper.visible = state.showUpper;
  G.kitchen.visible = state.showKitchen;
  G.furniture.visible = state.showFurniture;
  G.lights.visible = state.showLights;
  M.led.emissiveIntensity = state.showLights ? 4 : 0;
  ao.enabled = state.showAO;
}

const on = (id, ev, fn) => $(id).addEventListener(ev, fn);
on('varPT', 'change', (e) => { state.varPT = e.target.value; raiHint(); build(); });
on('varP1', 'change', (e) => { state.varP1 = e.target.value; build(); });
on('hour', 'input', (e) => { state.hour = +e.target.value; updateSun(); });
$('date').value = state.date;
on('date', 'change', (e) => { if (e.target.value) { state.date = e.target.value; updateSun(); } });
document.querySelectorAll('.chips button').forEach((b) => b.addEventListener('click', () => {
  state.date = `${state.date.slice(0, 4)}-${b.dataset.date}`; $('date').value = state.date; updateSun();
}));
on('floor', 'change', (e) => { state.floor = e.target.value; applyMaterials(); });
on('brick', 'change', (e) => { state.brick = e.target.value; applyMaterials(); });
for (const k of ['showUpper', 'showKitchen', 'showFurniture', 'showLights', 'showAO'])
  on(k, 'change', (e) => { state[k] = e.target.checked; applyVisibility(); });
on('exposure', 'input', (e) => { state.exposure = +e.target.value; renderer.toneMappingExposure = state.exposure; });

/* ---------- punti di vista ---------- */
const VIEWS = {
  ovest:   { pos: [-19, 4.5, P.L / 2 - 4], tgt: [0, 3.2, P.L / 2], far: true },
  portico: { pos: [-3.0, 1.6, 0.9], tgt: [0.3, 1.4, 9.5] },
  nord:    { pos: [4.7, 1.65, 3.15], tgt: [0.9, 1.15, 13] },
  sud:     { pos: [4.4, 1.6, P.L - 0.6], tgt: [0.9, 1.1, 2] },
  pianta:  { pos: [P.profEdificio / 2 - 0.5, 21, P.L / 2 + 0.01], tgt: [P.profEdificio / 2 - 0.5, 0, P.L / 2], upper: false, far: true },
};
function setView(name) {
  if (walk.isLocked) walk.unlock();
  const v = VIEWS[name];
  controls.target.set(...v.tgt);
  camera.position.set(...v.pos);
  // in verticale (telefono) le viste d'insieme si allontanano per contenere tutto l'edificio
  if (v.far && innerWidth < innerHeight) camera.position.sub(controls.target).multiplyScalar(1.9).add(controls.target);
  controls.update();
  const wantUpper = v.upper !== false;
  if (state.showUpper !== wantUpper) { state.showUpper = wantUpper; $('showUpper').checked = wantUpper; applyVisibility(); }
}
document.querySelectorAll('.views button').forEach((b) => b.addEventListener('click', () => setView(b.dataset.view)));

/* ---------- camminata (desktop) ---------- */
const keys = {};
addEventListener('keydown', (e) => { keys[e.code] = true; });
addEventListener('keyup', (e) => { keys[e.code] = false; });
on('walkbtn', 'click', () => {
  if (!state.showUpper) { state.showUpper = true; $('showUpper').checked = true; applyVisibility(); }
  camera.position.set(4.2, 1.6, 1.2); camera.lookAt(1, 1.5, 8);
  walk.lock();
});
walk.addEventListener('lock', () => { controls.enabled = false; $('walkhint').style.display = 'block'; });
walk.addEventListener('unlock', () => {
  controls.enabled = true; $('walkhint').style.display = 'none';
  const dir = new THREE.Vector3(); camera.getWorldDirection(dir);
  controls.target.copy(camera.position).addScaledVector(dir, 2); controls.update();
});
function walkStep(dt) {
  const sp = (keys.ShiftLeft ? 3 : 1.4) * dt;
  if (keys.KeyW || keys.ArrowUp) walk.moveForward(sp);
  if (keys.KeyS || keys.ArrowDown) walk.moveForward(-sp);
  if (keys.KeyA || keys.ArrowLeft) walk.moveRight(-sp);
  if (keys.KeyD || keys.ArrowRight) walk.moveRight(sp);
  // resta nell'open space e nel portico
  camera.position.x = THREE.MathUtils.clamp(camera.position.x, -P.portico.prof + 0.8, P.tW + P.profSoggiorno - 0.25);
  camera.position.z = THREE.MathUtils.clamp(camera.position.z, 0.25, P.L - 0.25);
  camera.position.y = 1.6;
}

/* ---------- screenshot ---------- */
let wantShot = false;
on('shot', 'click', () => { wantShot = true; });
function saveShot() {
  const a = document.createElement('a');
  a.download = `fienile_PT-${state.varPT}_P1-${state.varP1}_${state.date}_${$('timeRead').textContent.replace(':', '')}.png`;
  a.href = renderer.domElement.toDataURL('image/png');
  a.click();
}

/* ---------- pannello su mobile ---------- */
const panel = $('panel');
if (matchMedia('(max-width: 720px)').matches) panel.classList.add('closed');
on('panelhead', 'click', () => {
  if (!matchMedia('(max-width: 720px)').matches) return;
  panel.classList.toggle('closed');
  $('toggle').textContent = panel.classList.contains('closed') ? 'Mostra controlli' : 'Nascondi';
});

/* ---------- resize e ciclo ---------- */
function frameCamera() {
  // su desktop il pannello occupa ~330 px a sinistra: spostiamo il centro ottico a destra
  const side = innerWidth > 720 ? 332 : 0;
  camera.aspect = innerWidth / innerHeight;
  if (side) camera.setViewOffset(innerWidth + side, innerHeight, 0, 0, innerWidth, innerHeight);
  else camera.clearViewOffset();
  camera.updateProjectionMatrix();
}
frameCamera();
addEventListener('resize', () => {
  frameCamera();
  renderer.setSize(innerWidth, innerHeight); composer.setSize(innerWidth, innerHeight);
  ao.setSize(innerWidth, innerHeight);
});

applyMaterials();
build();
updateSun();
setView('ovest');

const clock = new THREE.Clock();
renderer.setAnimationLoop(() => {
  const dt = Math.min(clock.getDelta(), 0.05);
  if (walk.isLocked) walkStep(dt); else controls.update();
  if (envDirty) refreshEnvironment();
  composer.render();
  if (wantShot) { saveShot(); wantShot = false; }
});

window.__viewer = { state, setView, build, updateSun, VIEWS, P };
window.__viewerReady = true;
$('status').style.display = 'none';
