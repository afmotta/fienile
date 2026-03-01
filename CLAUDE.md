# Progetto Fienile — Prospetti Parete Ovest

## Panoramica

Progetto architettonico per la distribuzione finestre sulla parete ovest di una casa in costruzione. Contiene prospetti tecnici HTML/SVG con tabelle RAI (Rapporto Aeroilluminante). Ogni file HTML e' autonomo (inline CSS + SVG + tabelle).

Prima di qualsiasi modifica, leggi sempre `CONTEXT.md` per i parametri completi.

## Struttura file

```
index.html              — Indice con link a tutte le varianti
confronto.html          — Confronto interattivo PT + P1 con selettori dropdown
parete_attuale.html     — Piano Terra: Attuale (4×200×250)
parete_regolare.html    — Piano Terra: Regolare (centrate in campata)
parete_variante_a.html  — Piano Terra: Variante A (F1/F4 190, F2/F3 290)
parete_variante_b.html  — Piano Terra: Variante B (F1/F4 finestre h150, F2/F3 porte h250)
parete_variante_c.html  — Piano Terra: Variante C (F1/F4 allargate, margine uniforme)
parete_variante_d.html  — Piano Terra: Variante D (F1/F4 160×150, bordo 1m)
parete_variante_e.html  — Piano Terra: Variante E (F1/F4 174×150, stesso rapporto L/H)
primo_piano_a.html      — Primo Piano: P1-A (F2/F3=160cm)
primo_piano_b.html      — Primo Piano: P1-B (F2/F3=170cm)
primo_piano_c.html      — Primo Piano: P1-C (F2/F3=180cm)
primo_piano_d.html      — Primo Piano: P1-D (F2/F3=200cm)
CONTEXT.md              — Parametri tecnici completi, vincoli, formule
```

## Convenzioni SVG — Piano Terra

Tutti i prospetti PT usano lo stesso sistema di coordinate:

- **ViewBox**: `0 0 980 370`
- **Scala orizzontale**: `0.6385 px/cm` (860 px per 1347 cm di parete)
- **Scala verticale**: `0.8 px/cm` (216 px per 270 cm di altezza)
- **Offset orizzontale**: `xOff = 70 px`
- **Formula posizione X**: `x = 70 + posizione_cm × 0.6385`
- **Formula larghezza**: `w = larghezza_cm × 0.6385`
- **Muro**: top `y=40`, bottom `y=256`
- **Finestre da terra (h 250)**: `y=56` (top) a `y=256` (bottom)
- **Architrave**: `y=40` a `y=56` (h 200mm = 16px)
- **Finestre h 150 con davanzale 1m**: `y=56` (top) a `y=176` (bottom)

### Pilastri Piano Terra (3 pilastri da 30 cm)

| Pilastro | Posizione (cm) | x (px) | w (px) |
|----------|---------------|--------|--------|
| P1 | 309–339 | 267.3 | 19.16 |
| P2 | 658.5–688.5 | 490.44 | 19.16 |
| P3 | 1008–1038 | 713.58 | 19.16 |

### Colonna frontale (76 cm, centrata)

- Da 635.5 a 711.5 cm → `x=475.77`, `w=48.52`
- Pattern diagonale 45° con `stroke="#b0453a"`, `stroke-dasharray="6,4"`

## Convenzioni SVG — Primo Piano

Stesso sistema di coordinate del PT, ma con 2 pilastri:

| Pilastro | Posizione (cm) | x (px) | w (px) |
|----------|---------------|--------|--------|
| P1 | 590–620 | 446.73 | 19.16 |
| P2 | 727–757 | 534.20 | 19.16 |

## Classi CSS condivise (inline in ogni file)

```css
.wall-fill { fill: #e8e2d9; }
.wall-stroke { stroke: #2a2520; stroke-width: 1.5; fill: none; }
.pillar-fill { fill: #6b5e52; }
.window-fill { fill: #c8dce8; }
.window-stroke { stroke: #5a8199; stroke-width: 1.2; fill: none; }
.window-frame { stroke: #5a8199; stroke-width: 0.8; fill: none; }
.architrave-zone { fill: #ddd5cb; }
.dim-line { stroke: #b0453a; stroke-width: 0.8; }         /* quote rosse principali */
.dim-line-light { stroke: #c9a07a; stroke-width: 0.6; stroke-dasharray: 3,3; }  /* margini */
.dim-text { fill: #b0453a; font-size: 9px; }              /* testo quote */
.dim-text-light { fill: #9a8d7f; font-size: 7.5px; }      /* testo margini */
.label-text { fill: #5a8199; font-size: 10px; }            /* etichette finestre */
.label-room { fill: #8a7e72; font-size: 8px; }             /* nomi stanze */
.margin-zone { fill: #f0ccc8; opacity: 0.3; }              /* zone margine */
.align-line { stroke: #b0453a; stroke-dasharray: 6,3; opacity: 0.5; } /* filo allineamento */
```

## Struttura SVG di una finestra

Ogni finestra ha questi elementi nell'ordine:

1. **Architrave**: `<rect>` con classe `architrave-zone`, stessa x/w della finestra, y=40, h=16
2. **Vetro**: `<rect>` con `window-fill`, poi stessa rect con `window-stroke`
3. **Montanti/traversi**: `<line>` con `window-frame` (dividono la finestra in pannelli)
4. **Linea architrave**: `<line>` tratteggiata a `y=56`
5. **Davanzale** (solo finestre non da terra): `<line>` spessa a `y=176`
6. **Etichetta**: `<text>` con `label-text` (es. "F1 — 190 × 150") sopra la finestra
7. **Nome stanza**: `<text>` con `label-room` sotto l'etichetta

## Calcolo RAI — Piano Terra

```
RAI = superficie_vetrata_utile / superficie_pavimento
superficie_pavimento = 31.23 m² per stanza
altezza_utile = min(altezza_finestra, 190cm_da_terra)
```

Per finestre da terra (h 250): altezza utile = 190 cm
Per finestre con davanzale 100 cm (h 150): altezza utile = 90 cm (da 100 a 190)
Minimo RAI richiesto: 0.125

## Calcolo RAI — Primo Piano

```
RAI per stanza, 4 stanze indipendenti
Regola altezza utile:
  0–60 cm: non conteggiata
  60–172 cm: 100% (112 cm)
  172–250 cm: 33% (78 cm × 1/3 = 26 cm)
```

Altezza utile effettiva:
- Porte finestre da terra (h 250): 112 + 26 = 138 cm
- Finestre con davanzale 100 cm (h 150): 72 + 26 = 98 cm

## Toggle visibilita'

Ogni variante ha toggle per pilastri, colonna e cucina. I gruppi SVG hanno id:
- `id="pillars-group"` — contiene tutti i pilastri
- `id="column-group"` — contiene la colonna frontale
- `id="kitchen-group"` — contiene banco e isola cucina (solo PT)

## Cucina (solo Piano Terra)

Elementi cucina visualizzati con contorno tratteggiato `#6b5e52` e pattern diagonale 45°:
- **Banco**: 60 cm lungo parete × 90 cm alto, attaccato al bordo sinistro (pos. 0–60 cm)
- **Isola**: 100 cm lungo parete × 90 cm alto, a 120 cm dal banco (pos. 180–280 cm)
- SVG: banco x=70 w=38.31, isola x=184.93 w=63.85, entrambi y=184 h=72
- Pattern: `id="kitchenHatch"` (in confronto.html: `id="kitH${uid}"`)

## Come creare una nuova variante Piano Terra

1. Copia una variante esistente simile (es. `parete_variante_b.html`)
2. Aggiorna il `<title>` e l'`<h1>`
3. Per ogni finestra, ricalcola:
   - `x = 70 + posizione_cm × 0.6385`
   - `w = larghezza_cm × 0.6385`
   - Centro finestra: `x_centro = x + w/2`
   - Montanti: equidistanti nel vetro
   - Traversi: equidistanti in altezza
4. Aggiorna le quote orizzontali (margini, larghezze)
5. Aggiorna la tabella posizioni
6. Ricalcola il RAI e aggiorna la tabella RAI
7. Aggiorna `index.html` per aggiungere il link
8. Aggiorna `confronto.html` per aggiungere l'opzione nel selettore

## Come modificare una variante esistente

1. Leggi il file HTML della variante
2. Identifica la finestra da modificare (F1, F2, F3, F4)
3. Ricalcola le coordinate SVG con le formule sopra
4. Aggiorna: rect architrave, rect vetro, montanti, traversi, davanzale, etichetta
5. Aggiorna le linee di quota orizzontali (posizioni e testo)
6. Ricalcola e aggiorna il RAI nella tabella
7. Se la variante e' nel confronto, aggiorna anche `confronto.html`

## Palette colori

| Uso | Colore |
|-----|--------|
| Background | `#f5f2ed` |
| Muro fill | `#e8e2d9` |
| Muro stroke | `#2a2520` |
| Pilastri | `#6b5e52` |
| Finestre fill | `#c8dce8` |
| Finestre stroke | `#5a8199` |
| Architrave | `#ddd5cb` |
| Quote principali | `#b0453a` |
| Quote secondarie | `#c9a07a` |
| Testo quote secondarie | `#9a8d7f` |
| Etichette finestre | `#5a8199` |
| Nomi stanze | `#8a7e72` |
| Colonna frontale | `#b0453a` |
| Zone margine | `#f0ccc8` (opacity 0.3) |

## Font

- **Titoli/etichette**: DM Sans (Google Fonts)
- **Quote/dati/monospace**: JetBrains Mono (Google Fonts)
- Import: `@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');`

## Lingua

L'interfaccia e' in italiano. Usa termini tecnici italiani: "porta finestra", "davanzale", "architrave", "campata", "pilastro", "rapporto aeroilluminante".
