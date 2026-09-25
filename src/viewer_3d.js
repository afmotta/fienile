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
  ribassamento: { h: 0.28, prof: 0.70 },           // soffitto ribassato lungo il lato est dell'open space, a tutta lunghezza
  portico: { prof: 3.60, pilastri: [[-0.60, 0.10], [6.435, 7.035], [13.37, 14.07]] },
  // lati corti del portico chiusi da muri a gelosia in mattoni (vuoti regolari a corsi sfalsati)
  gelosia: { spessore: 0.25, zoccolo: 0.60, fasciaAlta: 0.25, spallaFacciata: 0.25 },
  // parapetto in ferro sul bordo del terrazzo: correnti piatti, bacchette verticali, montanti
  parapetto: { h: 1.00, arretramento: 0.06, passo: 0.114, bacchetta: 0.014, montante: 0.04, interasseMontanti: 1.50 },
  // tetto (dalla sezione di rilievo): quote dell'intradosso rispetto al pavimento PT
  tetto: { colmoX: 6.30, colmoH: 8.80, hOvest: 6.10, grondaOvestX: -4.80, hEst: 7.10, grondaEstX: 11.90 },
};

// Cucina Veneta Cucine "Sakura Presa" (ordine del 28/07/2026), dai disegni esecutivi del rivenditore.
// u = lungo la parete, s = distanza dalla parete (metri). Parete nord: u dal filo interno ovest;
// parete ovest ed est: u dalla testata nord. Basi h 912 (zoccolo 120, top Caranto Ker 12 mm), colonne h 2420.
const CUCINA = {
  hZoccolo: 0.12, hScocca: 0.90, hTop: 0.012, pBase: 0.60, pTop: 0.63, hColonna: 2.42, pColonna: 0.78,
  schienale: 0.558, alzatina: 0.06,
  // basi: [u0, u1, tipo]; tipo = cassetti (2 cestoni con gola intermedia), anta, fianco, giorno (vano a giorno)
  nord:  { u: [0, 3.76], moduli: [[0.63, 0.76, 'fianco'], [0.76, 1.51, 'cassetti'], [1.51, 2.71, 'cassetti'], [2.71, 3.46, 'cassetti'], [3.46, 3.76, 'anta']] },
  ovest: { u: [0.63, 3.34], moduli: [[0.63, 1.30, 'anta'], [1.30, 2.50, 'cassetti'], [2.50, 3.10, 'anta'], [3.10, 3.34, 'giorno']] },
  // colonne laccate lungo la parete est: walk-in d'angolo, forno + micro, estraibile, fianchi
  colonne: [[0, 1.45, 'walkin'], [1.45, 2.05, 'forno'], [2.05, 2.08, 'fianco'], [2.08, 2.38, 'estraibile'], [2.38, 2.45, 'fianco']],
  frigo: { u: [2.45, 3.283], h: 1.793 },                       // frigo americano del cliente, libera installazione
  isola: { x: [1.75, 2.83], z: [1.64, 3.29], ante: 4 },        // 4 ante L 397 per lato
  piano: { u: 2.11, s: 0.315, w: 0.80, d: 0.52 },               // Bosch PVQ811H26E, induzione con cappa integrata
  lavello: { u: [1.53, 2.27], s: [0.12, 0.52], rubinetto: 1.90 }, // Franke MRG 110-72 Sahara, sotto la finestra F1
  presa: { x: 2.04, z: 2.18 },                                  // presa a scomparsa sul top dell'isola
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

// Tende zip esterne sulle finestre del piano terra, completamente incassate nel muro: cassonetto
// nell'architrave e guide nelle spallette, invisibili; il telo scende nella mazzetta, verso l'esterno.
// Tutte alzate non si vedono: il fondale in alluminio rientra nell'architrave.
// telo = distanza del telo dal filo di facciata; fondale = [altezza, profondità] della barra.
const ZIP = { telo: 0.06, fondale: [0.035, 0.03] };
// proposte di colore: telo + profili (cassonetto, guide, fondale) verniciati in tinta vicina.
// Le chiare si confondono con facciata e infissi; la testa di moro si abbina alle persiane del primo piano
const ZIP_COLORI = {
  avorio:  { nome: 'Avorio',         telo: 0xebe4d3, profili: 0xe8e0cd, nota: 'profili vicini al RAL 9001: la tenda si confonde con infissi bianchi e intonaco.' },
  paglia:  { nome: 'Paglia',         telo: 0xe2d4a8, profili: 0xe2d8bf, nota: 'profili vicini al RAL 1013: tono su tono con il giallo pallido della facciata.' },
  perla:   { nome: 'Perla',          telo: 0xd4cfc6, profili: 0xc9c4b5, nota: 'profili vicini al RAL 7044: grigio caldo e neutro, richiama il travertino.' },
  tortora: { nome: 'Tortora chiaro', telo: 0xc2b39f, profili: 0xab9d88, nota: 'profili vicini al RAL 1019: lega con mattoni e ferro, segna meno lo sporco e dall\'interno lascia vedere meglio fuori.' },
  testaDiMoro: { nome: 'Testa di moro', telo: 0x4a3b33, profili: 0x45322e, nota: 'profili vicini al RAL 8017, come le persiane del primo piano: da dentro si vede fuori meglio che con i teli chiari e abbaglia meno, ma il telo scalda di più al sole e da fuori la finestra si legge come un vano scuro.' },
};
// teli screen per fattore di apertura (quota di tessuto vuota tra i fili): da lì passano la vista e il
// sole diretto, quindi nel modello opacità del telo = 1 − fattore di apertura
const ZIP_TELI = {
  f5:  { nome: '5%',  fattore: 0.05 },
  f10: { nome: '10%', fattore: 0.10 },
  f15: { nome: '15%', fattore: 0.15 },
};

// Persiane alla genovese sulle finestre del primo piano, verniciate (colore in PERSIANE_COLORI).
// Incernierate sullo spigolo esterno delle spallette: chiuse stanno nel vano, quasi a filo facciata;
// aperte (180°) si appoggiano alla facciata accanto alla finestra. Porte finestre delle camere a 2 ante,
// finestre dei bagni ad anta unica che si apre verso la testata vicina (dall'altra parte c'è la porta finestra).
// Stecche inclinate a 45° con il bordo esterno più basso: fermano il sole alto, da dentro si vede in basso.
const PERSIANE = {
  sp: 0.045, montante: 0.065, traversoAlto: 0.08, traversoBasso: 0.11,  // telaio dell'anta
  stecca: [0.05, 0.008], passo: 0.036, inclinazione: Math.PI / 4,      // [larghezza, spessore], interasse
  luce: 0.004,     // gioco tra anta e vano, e tra le due ante
  scosto: 0.01,    // cerniera 1 cm fuori dal filo di facciata: aperte, le ante non toccano l'intonaco
  sottoPorta: 0.03, // le ante delle porte finestre restano sopra il pavimento del terrazzo (+2 cm)
};
const PERSIANE_COLORI = {
  testaDiMoro: { nome: 'Testa di moro', colore: 0x45322e, nota: 'vicino al RAL 8017: lega con i coppi, i mattoni della gelosia e il ferro del parapetto.' },
  verde:       { nome: 'Verde',         colore: 0x1f4a3a, nota: 'vicino al RAL 6005 (verde muschio), il verde classico delle persiane: stacca di più sul giallo pallido della facciata.' },
};

/* ==========================================================================
   STATO E DOM
   ========================================================================== */
const $ = (id) => document.getElementById(id);
const state = {
  varPT: 'E', varP1: 'B',
  floorPT: 'terracotta', floorP1: 'rovere',
  showUpper: true, showRoof: true, showKitchen: true, showFurniture: true, showLights: false, showAO: true,
  exposure: 0.9, hour: 16, date: null,
  // le tende zip partono avvolte, così le viste interne restano quelle di sempre
  showTende: true, tendeColore: 'avorio', tendeApertura: 1, tendeTelo: 'f5',
  showPersiane: true, persianeApertura: 1, persianeColore: 'testaDiMoro',
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
// foto di un materiale del produttore, ripetuta a specchio (niente giunte) alla scala reale
function photoTex(url, meters) {
  const t = new THREE.TextureLoader().load(url);
  t.wrapS = t.wrapT = THREE.MirroredRepeatWrapping;
  t.repeat.set(1 / meters[0], 1 / meters[1]);
  t.anisotropy = renderer.capabilities.getMaxAnisotropy();
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
function brickTex(seed) {
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
  });
}

function latticeTex(seed) {
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

/* ---------- Cotto Milano 120×120 ultramatt: texture del produttore, 5 facce per colore ---------- */
// Le facce vengono posate a caso su un campo di 8 × 12 lastre (9,6 × 14,4 m), più grande del soggiorno
// (9,6 × 13,47 m): nessuna ripetizione visibile. Il seme è lo stesso per tutti i colori, così cambiando
// colore la posa resta identica e il confronto è immediato.
const COTTO_MILANO = { facce: 5, nx: 8, nz: 12, lato: 1.2, seme: 57 };
const cottoImgs = {};
function loadImg(src) {
  return new Promise((ok, ko) => { const i = new Image(); i.onload = () => ok(i); i.onerror = () => ko(new Error(src)); i.src = src; });
}
function cottoMilanoPosa(colore) {
  const C = COTTO_MILANO;
  cottoImgs[colore] ??= Promise.all(Array.from({ length: C.facce },
    (_, k) => loadImg(`./texture/cottomilano/${colore}_${String(k + 1).padStart(2, '0')}.jpg`)));
  return cottoImgs[colore].then((imgs) => {
    const s = Math.min(384, Math.floor(renderer.capabilities.maxTextureSize / C.nz));   // px per lastra
    return canvasTex(C.nx * s, C.nz * s, [C.nx * C.lato, C.nz * C.lato], (g, w, h) => {
      const rnd = rand(C.seme), faccia = [];
      for (let j = 0; j < C.nz; j++) for (let i = 0; i < C.nx; i++) {
        // faccia a caso, diversa da quelle già posate a sinistra e sopra; rotazione a caso di 90°
        const vicine = [i ? faccia[j * C.nx + i - 1] : -1, j ? faccia[(j - 1) * C.nx + i] : -1];
        let k; do k = Math.floor(rnd() * C.facce); while (vicine.includes(k));
        faccia.push(k);
        g.save();
        g.translate((i + 0.5) * s, (j + 0.5) * s); g.rotate(Math.floor(rnd() * 4) * Math.PI / 2);
        g.drawImage(imgs[k], -s / 2, -s / 2, s, s);
        g.restore();
      }
      g.fillStyle = 'rgba(95,80,68,0.45)';                 // fughe da 2-3 mm
      for (let i = 0; i <= C.nx; i++) g.fillRect(i * s - 0.5, 0, 1, h);
      for (let j = 0; j <= C.nz; j++) g.fillRect(0, j * s - 0.5, w, 1);
    });
  });
}

const TEX = {
  plaster: noiseTex([1, 1], 18, 7),
  rovere: woodTex([206, 158, 104], 11),
  rovereFume: woodTex([128, 102, 80], 12),
  // rovere Ikebana della Sakura: campione Veneta Cucine ritagliato, circa 30 × 28 cm, fibra verticale
  anteRovere: photoTex('./texture/cucina/rovere_ikebana.jpg', [0.30, 0.283]),
  cotto: tileTex(0.30, '#b4643e', '#9c5230', '#bdb4a6', 13, 4),
  gres: tileTex(0.60, '#a6a29b', '#9c9891', '#8f8b85', 14, 2),
  resina: noiseTex([2, 2], 26, 15),
  cottoMilano: cottoMilanoTex(41),
  mattone: brickTex(21),
  gelosia: latticeTex(31),
  portico: tileTex(0.50, '#9d968b', '#8f887d', '#6d675f', 16, 2),
};

/* ---------- materiali ---------- */
const std = (o) => new THREE.MeshStandardMaterial(o);
const M = {
  facade:   std({ color: 0xefe2b4, map: TEX.plaster, roughness: 0.95 }),   // intonaco giallo molto pallido
  interno:  std({ color: 0xf2efe9, map: TEX.plaster, roughness: 0.95 }),
  soffitto: std({ color: 0xf4f2ee, map: TEX.plaster, roughness: 0.95 }),
  pavimento: std({ color: 0xcfa27c, roughness: 0.85 }),                   // Cotto Milano, texture caricata a parte
  mattone:  std({ map: TEX.mattone, roughness: 0.9 }),
  gelosia:  std({ map: TEX.gelosia, roughness: 0.9, alphaTest: 0.5, side: THREE.DoubleSide }),
  telaio:   std({ color: 0xf3f1ec, roughness: 0.5 }),                        // infissi bianchi
  vetro:    new THREE.MeshPhysicalMaterial({ color: 0xe4eef2, roughness: 0.03, metalness: 0, transparent: true, opacity: 0.16, envMapIntensity: 1.2, depthWrite: false }),
  davanzale: std({ color: 0xd8d2c6, roughness: 0.6 }),
  portico:  std({ color: 0xcfa27c, roughness: 0.92 }),   // stesso cotto del piano terra, versione strutturata R11
  pavimentoP1: std({ map: TEX.rovere, roughness: 0.55 }),
  ferro:    std({ color: 0x3a3936, roughness: 0.55, metalness: 0.7 }),       // ferro micaceo scuro
  coppi:    std({ color: 0x9f5638, roughness: 0.85 }),
  tavolato: std({ map: TEX.rovereFume, roughness: 0.8 }),
  prato:    std({ color: 0x66753f, roughness: 1 }),
  ante:     std({ map: TEX.anteRovere, roughness: 0.6 }),                    // rovere Ikebana
  laccato:  std({ color: 0x8c8a62, roughness: 0.7 }),                         // laccato verde avocado opaco
  travertino: std({ color: 0xdccab0, map: TEX.plaster, roughness: 0.55 }),    // Caranto Ker travertino opaco
  bronzo:   std({ color: 0x5f4b37, roughness: 0.45, metalness: 0.6 }),        // gola e zoccolo bronzo opaco
  vetroNero: std({ color: 0x111111, roughness: 0.15, metalness: 0.2 }),       // forno, micro, piano cottura
  lavello:  std({ color: 0xc9b393, roughness: 0.6 }),                         // Franke fragranite Sahara
  vasca:    std({ color: 0x9c8769, roughness: 0.7 }),                         // fondo della vasca, in ombra
  cromo:    std({ color: 0xd8d8d8, roughness: 0.15, metalness: 1 }),
  frigo:    std({ color: 0x2c2c2e, roughness: 0.35, metalness: 0.5 }),
  legno:    std({ map: TEX.rovere, color: 0xc9b39a, roughness: 0.6 }),
  tessuto:  std({ color: 0xc8baa3, roughness: 1 }),
  scuro:    std({ color: 0x222222, roughness: 0.5, metalness: 0.4 }),
  persiana: std({ roughness: 0.5 }),                                          // smalto satinato, colore da applyPersiane()
  led:      std({ color: 0x000000, emissive: 0xffc98a, emissiveIntensity: 0 }),
};
// telo e profili delle tende zip. L'ombra del telo usa un retino ordinato 8×8 sui texel della shadow
// map: il telo blocca una quota di sole pari all'opacità e il filtro PCF la sfuma in penombra
// (l'alphaHash di three.js lavora a celle di ~20 cm e sulle finestre dava tutto o niente)
M.telo = std({ roughness: 0.95, transparent: true, depthWrite: false, side: THREE.DoubleSide });
M.zipProfili = std({ roughness: 0.45, metalness: 0.2 });                     // alluminio verniciato
const teloOmbra = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking });
teloOmbra.userData.opacita = { value: 1 };
teloOmbra.onBeforeCompile = (s) => {
  s.uniforms.opacita = teloOmbra.userData.opacita;
  s.fragmentShader = 'uniform float opacita;\n' + s.fragmentShader.replace('#include <alphatest_fragment>', `#include <alphatest_fragment>
    ivec2 q = ivec2(mod(gl_FragCoord.xy, 8.0));
    int bayer = 0;                                   // soglia di Bayer 8×8 (64 livelli, passi dell'1,6%)
    for (int k = 0; k < 3; k++) {
      int xk = (q.x >> k) & 1, yk = (q.y >> k) & 1;
      bayer = (bayer << 2) | (((xk ^ yk) << 1) | yk);
    }
    if (opacita < (float(bayer) + 0.5) / 64.0) discard;`);
};
// pavimenti del primo piano (quelli del piano terra sono solo Cotto Milano, vedi COTTO_MILANO)
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
    // telaio a ~2/3 dello spessore, verso l'interno: traversi a tutta larghezza, montanti tra i traversi
    // e vetri solo nelle luci, senza pezzi che si compenetrano (in Blender davano pixel neri agli incroci)
    const fx0 = ox + t - 0.16, fx1 = ox + t - 0.09, fw = 0.055, yb = y0 + sill, mw = 0.03;
    box(fx0, yb, a, fx1, yb + fw, b, M.telaio, group);
    box(fx0, top - fw, a, fx1, top, b, M.telaio, group);
    box(fx0, yb + fw, a, fx1, top - fw, a + fw, M.telaio, group);
    box(fx0, yb + fw, b - fw, fx1, top - fw, b, M.telaio, group);
    // come nei prospetti: le finestre grandi sono divise in due (2 ante, o scorrevole + fisso), le strette hanno un'anta sola
    const zm = a + w / 2, luci = w > 1.1 ? [[a + fw, zm - mw], [zm + mw, b - fw]] : [[a + fw, b - fw]];
    if (w > 1.1) box(fx0, yb + fw, zm - mw, fx1, top - fw, zm + mw, M.telaio, group);
    for (const [za, zb] of luci) box(fx0 + 0.03, yb + fw, za, fx0 + 0.035, top - fw, zb, M.vetro, group, { cast: false });
  }
}

// tende zip incassate del piano terra: si disegnano solo telo e fondale, che applyTende() sposta
// senza ricostruire la casa (cassonetto e guide stanno dentro il muro)
const tende = [];
function zipScreens(windows, group) {
  tende.length = 0;
  const [, fd] = ZIP.fondale, x = ZIP.telo;
  for (const [p, w, h, sill] of windows) {
    const a = p, b = p + w, top = sill + h, base = sill;     // il telo scende fino al davanzale o alla soglia
    const telo = new THREE.Mesh(new THREE.PlaneGeometry(w, 1).rotateY(-Math.PI / 2), M.telo);
    telo.position.set(x, 0, (a + b) / 2);
    telo.customDepthMaterial = teloOmbra;
    telo.castShadow = telo.receiveShadow = true;
    group.add(telo);
    const fondale = box(x - fd / 2, 0, a + 0.002, x + fd / 2, ZIP.fondale[0], b - 0.002, M.zipProfili, group);
    tende.push({ telo, fondale, top, base });
  }
}

// persiane del primo piano: ogni anta è un gruppo con l'origine sulla cerniera, che applyPersiane()
// ruota senza ricostruire la casa. dir = +1 se l'anta chiusa va verso sud dalla cerniera, -1 verso nord
const ante = [];
function shutters(y0, windows, group, ox) {
  ante.length = 0;
  const S = PERSIANE;
  for (const [p, w, h, sill] of windows) {
    const a = p, b = p + w, due = w > 1.1;
    const yb = y0 + sill + (sill === 0 ? S.sottoPorta : S.luce), yt = y0 + sill + h - S.luce;
    const cerniere = due ? [[a, 1], [b, -1]] : a + w / 2 < P.L / 2 ? [[a, 1]] : [[b, -1]];
    const lw = (due ? w / 2 : w) - S.luce;
    for (const [zc, dir] of cerniere) {
      const g = new THREE.Group();
      g.position.set(ox - S.scosto, 0, zc);
      group.add(g);
      shutterLeaf(g, Math.min(0, dir * lw), Math.max(0, dir * lw), yb, yt);
      ante.push({ g, dir });
    }
  }
}
// un'anta in coordinate della cerniera: x = spessore verso l'interno del vano, z = larghezza
function shutterLeaf(g, z0, z1, yb, yt) {
  const S = PERSIANE, t = S.sp, m = S.montante;
  box(0, yb, z0, t, yt, z0 + m, M.persiana, g);                          // montanti
  box(0, yb, z1 - m, t, yt, z1, M.persiana, g);
  box(0, yb, z0 + m, t, yb + S.traversoBasso, z1 - m, M.persiana, g);    // traversi
  box(0, yt - S.traversoAlto, z0 + m, t, yt, z1 - m, M.persiana, g);
  // stecche equidistanti tra i traversi, senza entrarci: e = mezzo ingombro verticale della stecca inclinata
  const [sw, ss] = S.stecca, e = (sw * Math.sin(S.inclinazione) + ss * Math.cos(S.inclinazione)) / 2;
  const s0 = yb + S.traversoBasso + e, s1 = yt - S.traversoAlto - e, n = Math.floor((s1 - s0) / S.passo) + 1;
  const stecche = new THREE.InstancedMesh(new THREE.BoxGeometry(sw, ss, z1 - z0 - 2 * m), M.persiana, n);
  const q = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 0, 1), S.inclinazione);  // bordo interno in alto
  const m4 = new THREE.Matrix4(), pos = new THREE.Vector3(), one = new THREE.Vector3(1, 1, 1);
  for (let i = 0; i < n; i++) {
    stecche.setMatrixAt(i, m4.compose(pos.set(t / 2, s0 + (s1 - s0) * i / (n - 1), (z0 + z1) / 2), q, one));
  }
  stecche.castShadow = stecche.receiveShadow = true;
  g.add(stecche);
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
  for (const k of ['pt', 'upper', 'roof', 'kitchen', 'furniture', 'lights', 'ground']) {
    G[k] = new THREE.Group(); house.add(G[k]);
  }
  G.tende = new THREE.Group(); G.pt.add(G.tende);
  G.persiane = new THREE.Group(); G.upper.add(G.persiane);
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
  zipScreens(VAR_PT[state.varPT].f, G.tende);
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
  // (nel gruppo del primo piano, così la vista in pianta lo toglie insieme al tetto).
  // Sotto il pavimento del P1 si ferma 2 cm più in basso: due facce alla stessa quota sfarfallano
  const xp = P.arretramentoP1 + t;                  // filo interno della parete ovest del P1
  box(xi, H, 0, xp, y1, L, M.soffitto, G.upper);
  box(xp, H, 0, D - P.tEst, y1 - 0.02, L, M.soffitto, G.upper);
  box(0, H, 0, xi, y1, L, M.facade, G.upper);
  // ribassamento sul lato est, opposto alle finestre: passa sopra il varco (h 2,20) senza interromperlo
  const rb = P.ribassamento, xr = xs - rb.prof;
  box(xr, H - rb.h, 0.01, xs, H, L - 0.01, M.soffitto, G.upper);

  // --- primo piano (involucro) + tetto
  const ox = P.arretramentoP1;
  westWall(y1, VAR_P1[state.varP1].f, G.upper, ox);
  shutters(y1, VAR_P1[state.varP1].f, G.persiane, ox);
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
  extrude(lay(under, 0, 0.12), -tt - 0.5, L + tt + 0.5, M.tavolato, G.roof);
  extrude(lay(under, 0.12, 0.32), -tt - 0.6, L + tt + 0.6, M.coppi, G.roof);

  kitchen(xi, xs);

  // --- arredo indicativo: tavolo 200 × 80 centrato tra cucina e colonna (lungo z) e nella larghezza
  // dell'open space (lungo x), divano e tappeto nella metà sud
  const tzc = (Math.max(CUCINA.ovest.u[1], CUCINA.isola.z[1]) + P.colonna.z[0]) / 2, txc = (xi + xs) / 2;
  const tz0 = tzc - 0.40, tz1 = tzc + 0.40, tx0 = txc - 1.00, tx1 = txc + 1.00;
  box(tx0, 0.72, tz0, tx1, 0.76, tz1, M.legno, G.furniture);
  for (const [x, z] of [[tx0 + 0.06, tz0 + 0.06], [tx1 - 0.11, tz0 + 0.06], [tx0 + 0.06, tz1 - 0.11], [tx1 - 0.11, tz1 - 0.11]])
    box(x, 0, z, x + 0.05, 0.72, z + 0.05, M.scuro, G.furniture);
  for (let i = 0; i < 3; i++) for (const side of [-1, 1]) {
    const x = tx0 + 0.13 + i * 0.65, z = side < 0 ? tz0 - 0.5 : tz1 + 0.08;
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
  // sul lato est il profilo corre davanti al ribassamento, continuo anche sopra il varco
  const zc = H - 0.2;
  box(xi + 0.08, zc, 0.12, xr - 0.08, zc + 0.012, 0.17, M.led, G.lights, { cast: false });
  box(xi + 0.08, zc, L - 0.17, xr - 0.08, zc + 0.012, L - 0.12, M.led, G.lights, { cast: false });
  box(xr - 0.17, zc, 0.12, xr - 0.12, zc + 0.012, L - 0.12, M.led, G.lights, { cast: false });
  for (const [x, z] of [[xi + 1.8, 1.9], [xi + 1.8, 4.6], [xi + 2.4, 10.0], [xi + 3.2, 7.3]]) {
    const pl = new THREE.PointLight(0xffc68c, 6, 7, 1.6); pl.position.set(x, 2.1, z); G.lights.add(pl);
  }

  scene.add(house);
  applyTende();
  applyPersiane();
  applyVisibility();
}

// cucina reale (CUCINA): basi a L su pareti nord e ovest, colonne sulla parete est, isola
function kitchen(xi, xs) {
  const C = CUCINA, g = G.kitchen, gap = 0.0015, tf = 0.02;
  const yz = C.hZoccolo, yb = C.hScocca, yt = yb + C.hTop;
  // un "lato" traduce (u lungo la parete, s dalla parete, y) in coordinate di scena
  const lato = {
    nord:  (u0, u1, s0, s1, y0, y1, m) => box(xi + u0, y0, s0, xi + u1, y1, s1, m, g),
    ovest: (u0, u1, s0, s1, y0, y1, m) => box(xi + s0, y0, u0, xi + s1, y1, u1, m, g),
    est:   (u0, u1, s0, s1, y0, y1, m) => box(xs - s1, y0, u0, xs - s0, y1, u1, m, g),
  };
  // frontale di un modulo alto s = sp; ante con fughe da 3 mm, cestoni con gola intermedia bronzo
  function fronte(L, u0, u1, sp, tipo, y0, y1, mat) {
    const a = u0 + gap, b = u1 - gap, f = (ya, yb2) => L(a, b, sp - tf, sp, ya + gap, yb2 - gap, mat);
    if (tipo === 'cassetti') { const ym = (y0 + y1) / 2; f(y0, ym - 0.0125); f(ym + 0.0125, y1); }
    else if (tipo === 'giorno') {                                       // vano a giorno: fianchi, ripiano, schienale
      L(u0, u0 + tf, 0, sp, y0, y1, M.ante); L(u1 - tf, u1, 0, sp, y0, y1, M.ante);
      L(u0, u1, 0, sp, y0, y0 + tf, M.ante); L(u0, u1, 0, sp, (y0 + y1) / 2 - tf / 2, (y0 + y1) / 2 + tf / 2, M.ante);
      L(u0, u1, 0, tf, y0, y1, M.ante);
    } else f(y0, y1);
  }
  function basi(L, run, u1Top) {
    const [u0, u1] = run.u;
    L(u0, u1, 0, C.pBase - 0.06, 0, yz, M.bronzo);                     // zoccolo arretrato
    for (const [a, b, tipo] of run.moduli)                              // scocca: si vede solo nelle fughe
      if (tipo !== 'giorno') L(a === run.moduli[0][0] ? u0 : a, b, 0, C.pBase - tf, yz, yb, M.bronzo);
    for (const [a, b, tipo] of run.moduli) fronte(L, a, b, C.pBase, tipo, yz, yb, M.ante);
    L(u0, u1Top ?? u1, 0, C.pTop, yb, yt, M.travertino);               // top
  }
  // le basi nord arrivano fino alla walk-in; l'eventuale differenza con la parete est è un tamponamento
  const uCol = xs - xi - C.pColonna;
  basi(lato.nord, C.nord, uCol);
  if (uCol - C.nord.u[1] > 0.005) {
    lato.nord(C.nord.u[1], uCol, 0, C.pBase - 0.06, 0, yz, M.bronzo);
    fronte(lato.nord, C.nord.u[1], uCol, C.pBase, 'anta', yz, yb, M.ante);
  }
  basi(lato.ovest, C.ovest);
  // schienale sulla parete nord e fino alla finestra F1 sulla ovest, alzatina sotto la finestra
  const uF1 = Math.min(VAR_PT[state.varPT].f[0][0] - 0.03, C.ovest.u[1]);
  lato.nord(0, uCol, 0, 0.012, yt, yt + C.schienale, M.travertino);
  lato.ovest(0.012, uF1, 0, 0.012, yt, yt + C.schienale, M.travertino);
  lato.ovest(uF1, C.ovest.u[1], 0, 0.012, yt, yt + C.alzatina, M.travertino);
  // piano cottura a filo top, lavello sottotop con rubinetto
  const pc = C.piano;
  lato.nord(pc.u - pc.w / 2, pc.u + pc.w / 2, pc.s - pc.d / 2, pc.s + pc.d / 2, yt, yt + 0.003, M.vetroNero);
  const lv = C.lavello;
  lato.ovest(lv.u[0], lv.u[1], lv.s[0], lv.s[1], yt, yt + 0.002, M.lavello);
  lato.ovest(lv.u[0] + 0.03, lv.u[1] - 0.03, lv.s[0] + 0.03, lv.s[1] - 0.03, yt + 0.002, yt + 0.003, M.vasca);
  lato.ovest(lv.rubinetto - 0.015, lv.rubinetto + 0.015, 0.05, 0.08, yt, yt + 0.42, M.cromo);
  lato.ovest(lv.rubinetto - 0.012, lv.rubinetto + 0.012, 0.05, 0.30, yt + 0.40, yt + 0.42, M.cromo);

  // colonne laccate sulla parete est
  const pc2 = C.pColonna, yc = C.hColonna;
  for (const [a, b, tipo] of C.colonne) {
    lato.est(a, b, 0, pc2 - 0.06, 0, yz, M.bronzo);
    lato.est(a, b, 0, pc2 - tf, yz, yc, tipo === 'fianco' ? M.laccato : M.bronzo);
    if (tipo === 'fianco') { lato.est(a, b, pc2 - tf, pc2, 0, yc, M.laccato); continue; }
    if (tipo === 'walkin') { fronte(lato.est, a, a + 0.46, pc2, 'anta', yz, yc, M.laccato); fronte(lato.est, a + 0.46, b, pc2, 'anta', yz, yc, M.laccato); }
    else if (tipo === 'forno') {                                         // anta, forno, micro, anta
      fronte(lato.est, a, b, pc2, 'anta', yz, 0.68, M.laccato);
      fronte(lato.est, a, b, pc2, 'anta', 0.68, 1.28, M.vetroNero);
      fronte(lato.est, a, b, pc2, 'anta', 1.28, 1.665, M.vetroNero);
      fronte(lato.est, a, b, pc2, 'anta', 1.665, yc, M.laccato);
    } else fronte(lato.est, a, b, pc2, 'anta', yz, yc, M.laccato);
  }
  // frigo americano a due ante + due cassetti
  const fr = C.frigo, fu0 = fr.u[0] + 0.005, fu1 = fr.u[1] - 0.005, fm = (fu0 + fu1) / 2;
  lato.est(fu0, fu1, 0.04, 0.74, 0.02, fr.h, M.frigo);
  for (const [ya, yb2] of [[0.02, 0.5], [0.52, 0.93], [0.95, fr.h]]) {
    if (ya < 0.9) lato.est(fu0, fu1, 0.74, 0.76, ya, yb2, M.frigo);
    else { lato.est(fu0, fm - 0.003, 0.74, 0.76, ya, yb2, M.frigo); lato.est(fm + 0.003, fu1, 0.74, 0.76, ya, yb2, M.frigo); }
  }

  // isola: ante sui due lati lunghi, fianchi in rovere sulle testate, presa a scomparsa sul top
  const I = C.isola, [ix0, ix1] = I.x.map((v) => xi + v), [iz0, iz1] = I.z;
  box(ix0 + 0.06, 0, iz0 + 0.06, ix1 - 0.06, yz, iz1 - 0.06, M.bronzo, g);
  box(ix0 + 0.02 + tf, yz, iz0 + tf, ix1 - 0.02 - tf, yb, iz1 - tf, M.bronzo, g);
  box(ix0 + 0.02, yz, iz0, ix1 - 0.02, yb, iz0 + tf, M.ante, g);
  box(ix0 + 0.02, yz, iz1 - tf, ix1 - 0.02, yb, iz1, M.ante, g);
  const dz = (iz1 - iz0 - 2 * tf) / I.ante;
  for (let i = 0; i < I.ante; i++) {
    const za = iz0 + tf + i * dz + gap, zb = za + dz - 2 * gap;
    box(ix0 + 0.02, yz + gap, za, ix0 + 0.02 + tf, yb - gap, zb, M.ante, g);
    box(ix1 - 0.02 - tf, yz + gap, za, ix1 - 0.02, yb - gap, zb, M.ante, g);
  }
  box(ix0, yb, iz0, ix1, yt, iz1, M.travertino, g);
  box(xi + C.presa.x - 0.03, yt, C.presa.z - 0.03, xi + C.presa.x + 0.03, yt + 0.01, C.presa.z + 0.03, M.vetroNero, g);
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
  const md = state.date.slice(5);
  document.querySelectorAll('.seasons button').forEach((b) => b.setAttribute('aria-pressed', b.dataset.date === md));
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
// gruppo di radio (campioni di colore o segmenti): `swatch` è la chiave del colore nei dati, se c'è
function fillChoices(box, data, value, onPick, swatch) {
  box.innerHTML = Object.entries(data).map(([k, v]) => {
    const dot = swatch ? `<i style="--c:#${v[swatch].toString(16).padStart(6, '0')}"></i>` : '';
    return `<label title="${v.nome}"><input type="radio" name="${box.id}" value="${k}"${k === value ? ' checked' : ''}>${dot}<span>${v.nome}</span></label>`;
  }).join('');
  box.addEventListener('change', (e) => onPick(e.target.value));
}
fillSelect($('varPT'), VAR_PT, state.varPT);
fillSelect($('varP1'), VAR_P1, state.varP1);
function raiHint() {
  const r = VAR_PT[state.varPT].rai;
  $('raiPT').innerHTML = `<b class="${r >= 0.125 ? 'ok' : 'ko'}">RAI ${r.toFixed(3).replace('.', ',')}</b> piano terra · minimo 0,125`;
}
raiHint();

let floorPTTex = null, floorPTReq = 0;
function applyFloorPT() {
  const req = ++floorPTReq;
  cottoMilanoPosa(state.floorPT).then((tex) => {
    if (req !== floorPTReq) { tex.dispose(); return; }    // nel frattempo è stato scelto un altro colore
    floorPTTex?.dispose();
    floorPTTex = tex;
    for (const m of [M.pavimento, M.portico]) { m.map = tex; m.color.set(0xffffff); m.needsUpdate = true; }
  }).catch((e) => console.error('Texture Cotto Milano non caricata:', e));
}
function applyMaterials() {
  const f = FLOOR[state.floorP1];
  M.pavimentoP1.map = f.map; M.pavimentoP1.color.set(f.color); M.pavimentoP1.roughness = f.roughness;
  M.pavimentoP1.needsUpdate = true;
}
// apertura 1 = telo tutto avvolto (fondale rientrato nell'architrave), 0 = telo giù fino al davanzale o a terra
function applyTende() {
  const c = ZIP_COLORI[state.tendeColore];
  M.telo.color.set(c.telo); M.zipProfili.color.set(c.profili);
  M.telo.opacity = teloOmbra.userData.opacita.value = 1 - ZIP_TELI[state.tendeTelo].fattore;
  const fh = ZIP.fondale[0];
  for (const t of tende) {
    const yb = t.base + (t.top - t.base) * state.tendeApertura;   // fondo del fondale
    const len = t.top - yb - fh;
    t.fondale.position.y = yb + fh / 2;
    t.fondale.visible = yb < t.top - 0.001;                       // tutto alzato: dentro l'architrave
    t.telo.visible = len > 0.005;
    t.telo.scale.y = Math.max(len, 0.001); t.telo.position.y = t.top - len / 2;
  }
  $('tendeAperturaRead').textContent = `${Math.round(state.tendeApertura * 100)}%`;
  $('tendeNota').textContent = `${c.nome}: ${c.nota}`;
}
// apertura 1 = ante aperte a 180° contro la facciata, 0 = chiuse nel vano
function applyPersiane() {
  const ap = state.persianeApertura, c = PERSIANE_COLORI[state.persianeColore];
  M.persiana.color.set(c.colore);
  $('persianeNota').textContent = `${c.nome}: ${c.nota}`;
  for (const { g, dir } of ante) g.rotation.y = -dir * Math.PI * ap;
  $('persianeAperturaRead').textContent = ap === 0 ? 'chiuse' : ap === 1 ? 'aperte' : `${Math.round(ap * 180)}°`;
}
function applyVisibility() {
  if (!house) return;
  G.tende.visible = state.showTende;
  G.persiane.visible = state.showPersiane;
  G.upper.visible = state.showUpper;
  G.roof.visible = state.showRoof;
  G.kitchen.visible = state.showKitchen;
  G.furniture.visible = state.showFurniture;
  G.lights.visible = state.showLights;
  M.led.emissiveIntensity = state.showLights ? 4 : 0;
  ao.enabled = state.showAO;
}

const on = (id, ev, fn) => $(id).addEventListener(ev, fn);
// imposta un toggle da codice (viste, camminata) tenendo allineata la checkbox
function setToggle(k, v) {
  if (state[k] === v) return;
  state[k] = v; $(k).checked = v; applyVisibility();
}
on('varPT', 'change', (e) => { state.varPT = e.target.value; raiHint(); build(); });
on('varP1', 'change', (e) => { state.varP1 = e.target.value; build(); });
on('hour', 'input', (e) => { state.hour = +e.target.value; updateSun(); });
$('date').value = state.date;
on('date', 'change', (e) => { if (e.target.value) { state.date = e.target.value; updateSun(); } });
document.querySelectorAll('.seasons button').forEach((b) => b.addEventListener('click', () => {
  state.date = `${state.date.slice(0, 4)}-${b.dataset.date}`; $('date').value = state.date; updateSun();
}));
// colore medio delle facce Cotto Milano, per il pallino del selettore
const PAV_PT = { terracotta: { nome: 'Terracotta', colore: 0xcfa27c }, creta: { nome: 'Creta', colore: 0xdbc1a2 } };
fillChoices($('floorPT'), PAV_PT, state.floorPT, (k) => { state.floorPT = k; applyFloorPT(); }, 'colore');
$('floorP1').value = state.floorP1;
on('floorP1', 'change', (e) => { state.floorP1 = e.target.value; applyMaterials(); });
// con tende o persiane nascoste i loro controlli restano visibili ma spenti
const syncBlocks = () => document.querySelectorAll('[data-for]').forEach((b) => { b.inert = !state[b.dataset.for]; });
for (const k of ['showUpper', 'showRoof', 'showKitchen', 'showFurniture', 'showLights', 'showAO', 'showTende', 'showPersiane'])
  on(k, 'change', (e) => { state[k] = e.target.checked; applyVisibility(); syncBlocks(); });
syncBlocks();
fillChoices($('tendeColore'), ZIP_COLORI, state.tendeColore, (k) => { state.tendeColore = k; applyTende(); }, 'telo');
fillChoices($('tendeTelo'), ZIP_TELI, state.tendeTelo, (k) => { state.tendeTelo = k; applyTende(); });
$('tendeApertura').value = state.tendeApertura;
on('tendeApertura', 'input', (e) => { state.tendeApertura = +e.target.value; applyTende(); });
$('persianeApertura').value = state.persianeApertura;
fillChoices($('persianeColore'), PERSIANE_COLORI, state.persianeColore, (k) => { state.persianeColore = k; applyPersiane(); }, 'colore');
on('persianeApertura', 'input', (e) => { state.persianeApertura = +e.target.value; applyPersiane(); });
const exposureRead = () => { $('exposureRead').textContent = state.exposure.toFixed(2).replace('.', ','); };
exposureRead();
on('exposure', 'input', (e) => { state.exposure = +e.target.value; renderer.toneMappingExposure = state.exposure; exposureRead(); });

/* ---------- punti di vista ---------- */
const VIEWS = {
  ovest:   { pos: [-19, 4.5, P.L / 2 - 4], tgt: [0, 3.2, P.L / 2], far: true },
  portico: { pos: [-3.0, 1.6, 0.9], tgt: [0.3, 1.4, 9.5] },
  nord:    { pos: [4.6, 1.65, 3.45], tgt: [0.9, 1.15, 13] },   // appena a sud del frigo
  sud:     { pos: [4.4, 1.6, P.L - 0.6], tgt: [0.9, 1.1, 2] },
  // cucina: panoramica da sud-est, colonne e frigo dal lato finestra, isola e piano cottura
  cucina:  { pos: [4.4, 1.75, 4.2], tgt: [1.4, 0.9, 1.4] },
  colonne: { pos: [1.3, 1.65, 4.3], tgt: [4.6, 1.2, 1.2] },
  isola:   { pos: [2.75, 1.75, 3.8], tgt: [2.3, 1.1, 0.3] },
  // tende zip: soggiorno verso le vetrate, dettaglio dell'incasso dal portico (se sono alzate, le abbassa a metà)
  controluce: { pos: [4.6, 1.5, 12.6], tgt: [0.4, 1.15, 8.2] },
  incasso:    { pos: [-1.5, 1.45, 7.6], tgt: [0.1, 1.55, 5.6], tende: 0.5 },
  // persiane del primo piano: dal terrazzo, lungo la facciata verso nord (F2 e, in fondo, F1)
  persiane:   { pos: [0.12, 4.5, 6.2], tgt: [1.1, 4.0, 1.8] },
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
  if (v.tende !== undefined && state.tendeApertura === 1) {
    state.tendeApertura = v.tende; $('tendeApertura').value = v.tende; applyTende();
  }
  const wantUpper = v.upper !== false;
  setToggle('showUpper', wantUpper);
  setToggle('showRoof', wantUpper);
  markView(name);
}
// la vista scelta resta evidenziata finché non si muove la camera a mano
const markView = (name) => document.querySelectorAll('.views button').forEach((b) => b.classList.toggle('on', b.dataset.view === name));
controls.addEventListener('start', () => markView(null));
document.querySelectorAll('.views button').forEach((b) => b.addEventListener('click', () => setView(b.dataset.view)));

/* ---------- camminata (desktop) ---------- */
const keys = {};
addEventListener('keydown', (e) => { keys[e.code] = true; });
addEventListener('keyup', (e) => { keys[e.code] = false; });
on('walkbtn', 'click', () => {
  setToggle('showUpper', true);
  setToggle('showRoof', true);
  camera.position.set(4.2, 1.6, 1.2); camera.lookAt(1, 1.5, 8);
  markView(null);
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

/* ---------- pannello a schede ---------- */
const panel = $('panel');
const mobile = () => matchMedia('(max-width: 720px)').matches;
function setPanelOpen(open) {
  panel.classList.toggle('closed', !open);
  const t = $('toggle'), lbl = open ? 'Riduci pannello' : 'Apri pannello';
  t.setAttribute('aria-expanded', open); t.title = lbl; t.setAttribute('aria-label', lbl);
  frameCamera();
}
const tabs = [...document.querySelectorAll('[role=tab]')];
function selectTab(tab, focus) {
  for (const t of tabs) {
    const sel = t === tab;
    t.setAttribute('aria-selected', sel); t.tabIndex = sel ? 0 : -1;
    $(t.getAttribute('aria-controls')).hidden = !sel;
  }
  if (focus) tab.focus();
  try { localStorage.setItem('viewer3d.tab', tab.id); } catch { /* storage non disponibile */ }
}
tabs.forEach((t, i) => {
  t.addEventListener('click', () => {
    const open = !panel.classList.contains('closed');
    // su telefono toccare la scheda già aperta richiude il foglio
    if (mobile() && open && t.getAttribute('aria-selected') === 'true') { setPanelOpen(false); return; }
    selectTab(t);
    if (!open) setPanelOpen(true);
  });
  t.addEventListener('keydown', (e) => {
    const d = { ArrowRight: 1, ArrowLeft: -1 }[e.key];
    if (d) { e.preventDefault(); selectTab(tabs[(i + d + tabs.length) % tabs.length], true); }
  });
});
on('toggle', 'click', () => setPanelOpen(panel.classList.contains('closed')));
try {
  const saved = $(localStorage.getItem('viewer3d.tab') || '');
  if (saved && tabs.includes(saved)) selectTab(saved);
} catch { /* storage non disponibile */ }
if (mobile()) panel.classList.add('closed');

/* ---------- resize e ciclo ---------- */
function frameCamera() {
  // su telefono il foglio dei controlli sta sopra la barra del sole
  document.documentElement.style.setProperty('--sunbar-h', `${$('sunbar').offsetHeight}px`);
  // su desktop il pannello aperto occupa la sinistra: spostiamo il centro ottico a destra
  const side = !mobile() && !panel.classList.contains('closed') ? panel.offsetWidth + 32 : 0;
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

applyFloorPT();
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
