# Progetto Fienile — Prospetti Parete Ovest

## Contesto

Progetto di distribuzione finestre sulla parete ovest di una casa in costruzione. Sono state sviluppate 5 varianti per il piano terra e 4 varianti per il primo piano, ciascuna con prospetto tecnico in HTML/SVG e tabella riepilogativa. È disponibile anche una pagina di confronto interattiva.

## Parametri fissi della parete — Piano Terra

- **Lunghezza parete**: 13,47 m
- **Altezza parete**: 2,70 m
- **3 pilastri** da 30 cm, che dividono la parete in 4 campate simmetriche:
  - Campata 1: 309 cm
  - Campata 2: 319,5 cm
  - Campata 3: 319,5 cm
  - Campata 4: 309 cm
- **Posizione pilastri** (bordo sinistro):
  - P1: da 3,09 m a 3,39 m
  - P2: da 6,585 m a 6,885 m
  - P3: da 10,08 m a 10,38 m
- **Colonna frontale**: larga 76 cm, centrata rispetto alla parete (da 635,5 cm a 711,5 cm). Visualizzata nei prospetti con contorno tratteggiato e tratteggiatura diagonale a 45° (opacità 60%).

## Parametri fissi della parete — Primo Piano

- **Lunghezza parete**: 13,47 m (identica al piano terra)
- **Altezza parete**: 2,70 m (identica al piano terra)
- **2 pilastri** da 30 cm, simmetrici, che dividono la parete in 3 campate:
  - Campata 1: 590 cm
  - Campata 2: 107 cm (centrale)
  - Campata 3: 590 cm
- **Posizione pilastri** (bordo sinistro):
  - P1: da 5,90 m a 6,20 m
  - P2: da 7,27 m a 7,57 m
- **Colonna frontale**: identica al piano terra (76 cm, centrata)
- **4 stanze** servite dalle finestre:
  - Bagno Nord (F1): 4,52 m²
  - Camera Nord (F2): 17,30 m²
  - Camera Sud (F3): 12,40 m²
  - Bagno Sud (F4): 4,10 m²

## Vincoli generali — Piano Terra

- Distanza minima dai pilastri: **10 cm** (alcune varianti usano margini maggiori)
- Distanza minima dal bordo parete: **73,5 cm** (in alcune varianti è 1 m, in altre questo vincolo è rilassato)
- Le finestre non possono sovrapporsi ai pilastri

## Vincoli generali — Primo Piano

- Le finestre non possono sovrapporsi ai pilastri
- Le finestre F1/F4 (bagni) sono fisse in tutte le varianti
- Le finestre F2/F3 (camere) variano in larghezza nelle diverse varianti
- Il layout è simmetrico

## Rapporto Aeroilluminante (RAI) — Piano Terra

- Il RAI si calcola come: superficie vetrata utile / superficie pavimento
- Superficie pavimento per stanza: **31,23 m²**
- La casa ha **due stanze identiche** al piano terra; per il calcolo si usano F1 e F2 (simmetria con F3 e F4)
- **Altezza utile limitata a 190 cm da terra** a causa del tetto spiovente in aggetto (le parti di finestra sopra 190 cm non contano)
- Minimo richiesto: **0,125**

## RAI — Primo Piano

- Il RAI si calcola **per stanza** (4 stanze indipendenti)
- **Regola altezza utile primo piano**:
  - 0–60 cm da terra: non conteggiata
  - 60–172 cm da terra: conteggiata al 100% (112 cm)
  - 172–250 cm da terra: conteggiata al 33% (78 cm × ⅓ = 26 cm)
- **Altezza utile effettiva**:
  - Porte finestre da terra (h 250): 112 + 26 = **138 cm**
  - Finestre con davanzale 100 cm (h 150): 72 + 26 = **98 cm**
- Minimo richiesto: **0,125**

## Le 5 varianti — Piano Terra

### 1. Attuale (di progetto) — `parete_attuale.html`
- **4 porte finestre identiche**: 200 × 250 cm, tutte da terra
- Distribuzione: distanze tra finestre di 1m / 2m / 1m
- Bordo: 73,5 cm per lato (simmetrica)
- **Posizioni**: F1 da 0,735m, F2 da 3,735m, F3 da 7,735m, F4 da 10,735m
- **RAI: 0,243** (F1: 2,00×1,90 = 3,80 m², F2: 2,00×1,90 = 3,80 m², totale 7,60 m²)

### 2. Variante Regolare — `parete_regolare.html`
- **4 porte finestre identiche**: 200 × 250 cm, tutte da terra
- Ogni finestra centrata nella propria campata
- Bordo: 73,5 cm (F1/F4 non centrate, spostate per rispettare il vincolo bordo)
- Gap: 73,5 cm (bordo) / 35,5 cm (F1↔P1, P3↔F4) / 59,75 cm (F2/F3 ↔ pilastri)
- **Posizioni**: F1 da 0,735m, F2 da 3,9875m, F3 da 7,4825m, F4 da 10,735m
- **RAI: 0,243**

### 3. Variante A — `parete_variante_a.html`
- **F1/F4**: 190 × 250 cm (porte finestre da terra)
- **F2/F3**: 290 × 250 cm (porte finestre da terra)
- Finestre centrate in campata, margini ~4,5 cm (esterne) e ~4,75 cm (interne) oltre il vincolo minimo
- **Posizioni**: F1 da 1,045m, F2 da 3,538m, F3 da 7,033m, F4 da 10,525m
- **RAI: 0,292** (F1: 1,90×1,90 = 3,61 m², F2: 2,90×1,90 = 5,51 m², totale 9,12 m²)

### 4. Variante B — `parete_variante_b.html`
- **F1/F4**: 190 × 150 cm, **finestre con davanzale a 1 m** da terra
- **F2/F3**: 290 × 250 cm (porte finestre da terra)
- Filo superiore allineato a 2,50 m per tutte le finestre
- Stesse posizioni orizzontali della Variante A
- **RAI: 0,231** (F1: 1,90×0,90 = 1,71 m², F2: 2,90×1,90 = 5,51 m², totale 7,22 m²)

### 5. Variante C — `parete_variante_c.html`
- **F1/F4**: 279,5 × 150 cm, **finestre con davanzale a 1 m**, larghezza massimizzata
- **F2/F3**: 290 × 250 cm (porte finestre da terra)
- Margine uniforme di 14,75 cm (uguale per tutte, sia da bordo che da pilastro)
- Filo superiore allineato a 2,50 m
- **Posizioni**: F1 da 0,1475m, F2 da 3,5375m, F3 da 7,0325m, F4 da 10,5275m
- **RAI: 0,257** (F1: 2,795×0,90 = 2,52 m², F2: 2,90×1,90 = 5,51 m², totale 8,03 m²)

### 6. Variante D — `parete_variante_d.html`
- **F1/F4**: 160 × 150 cm, **finestre con davanzale a 1 m** da terra
- **F2/F3**: 290 × 250 cm (porte finestre da terra)
- F1/F4 spostate verso il centro della campata, con margine minimo 1 m dal bordo parete
- Filo superiore allineato a 2,50 m
- **Posizioni**: F1 da 1,000m, F2 da 3,5375m, F3 da 7,0325m, F4 da 10,870m
- **RAI: 0,223** (F1: 1,60×0,90 = 1,44 m², F2: 2,90×1,90 = 5,51 m², totale 6,95 m²)

### 7. Variante E — `parete_variante_e.html`
- **F1/F4**: 174 × 150 cm, **finestre con davanzale a 1 m** da terra
- **F2/F3**: 290 × 250 cm (porte finestre da terra)
- Larghezza F1/F4 calcolata con stesso rapporto L/H di F2/F3 (290/250 = 1,16 → 150×1,16 = 174)
- F1/F4 con margine minimo 1 m dal bordo parete
- Filo superiore allineato a 2,50 m
- **Posizioni**: F1 da 1,000m, F2 da 3,5375m, F3 da 7,0325m, F4 da 10,730m
- **RAI: 0,227** (F1: 1,74×0,90 = 1,57 m², F2: 2,90×1,90 = 5,51 m², totale 7,08 m²)

## Le 4 varianti — Primo Piano

Tutte le varianti hanno F1/F4 fissi (60×150 cm, davanzale a 100 cm, a 65 cm dai bordi).
Le varianti differiscono solo per la larghezza di F2/F3 (porte finestre da terra, a 250 cm dai bordi).

### 1. P1-A — `primo_piano_a.html` (F2/F3 = 160 cm, minimo RAI)

- **RAI**: Bagno Nord 0,130 / Camera Nord **0,128** / Camera Sud 0,178 / Bagno Sud 0,143

### 2. P1-B — `primo_piano_b.html` (F2/F3 = 174 cm)

- **RAI**: Bagno Nord 0,130 / Camera Nord 0,139 / Camera Sud 0,194 / Bagno Sud 0,143

### 3. P1-C — `primo_piano_c.html` (F2/F3 = 180 cm)

- **RAI**: Bagno Nord 0,130 / Camera Nord 0,144 / Camera Sud 0,200 / Bagno Sud 0,143

### 4. P1-D — `primo_piano_d.html` (F2/F3 = 200 cm, base)

- **RAI**: Bagno Nord 0,130 / Camera Nord 0,160 / Camera Sud 0,223 / Bagno Sud 0,143

## Struttura dei file

```
index.html              ← Indice con link a tutte le varianti PT + P1 + confronto
parete_attuale.html     ← PT: Attuale (di progetto)
parete_regolare.html    ← PT: Variante Regolare
parete_variante_a.html  ← PT: Variante A
parete_variante_b.html  ← PT: Variante B
parete_variante_c.html  ← PT: Variante C
parete_variante_d.html  ← PT: Variante D
parete_variante_e.html  ← PT: Variante E
primo_piano_a.html      ← P1: Variante P1-A (F2/F3 = 160 cm)
primo_piano_b.html      ← P1: Variante P1-B (F2/F3 = 170 cm)
primo_piano_c.html      ← P1: Variante P1-C (F2/F3 = 180 cm)
primo_piano_d.html      ← P1: Variante P1-D (F2/F3 = 200 cm)
confronto.html          ← Confronto interattivo PT + P1 con selettori
```

## Stile grafico dei prospetti

Tutti i prospetti HTML condividono lo stesso stile:
- **Font**: DM Sans (titoli/label) + JetBrains Mono (quote/dati) da Google Fonts
- **Background**: `#f5f2ed` (beige caldo)
- **Muro**: `#e8e2d9` con bordo `#2a2520`
- **Pilastri**: `#6b5e52` con tratteggiatura diagonale interna, altezza leggermente maggiore del muro
- **Finestre**: `#c8dce8` (azzurro chiaro) con cornice `#5a8199`, suddivisioni interne (montanti e traversi)
- **Architrave**: `#ddd5cb`, 200 mm sopra le finestre, con linea tratteggiata di separazione
- **Davanzale** (var. B e C): linea `#6b5e52` spessa
- **Colonna frontale**: contorno tratteggiato `#b0453a` con pattern diagonale 45° (opacità 60%), etichetta sotto
- **Quote rosse** (`#b0453a`): dimensioni principali (campate, larghezze finestre, totale parete)
- **Quote chiare** (`#c9a07a`, tratteggiato): margini e gap secondari
- **Quote verticali**: altezza parete (sinistra), altezza finestre, architrave, davanzale (destra dove applicabile)
- **Linea di terra**: con trattini inclinati sotto
- **Legenda**: in basso, con swatch colorati
- **Tabella riepilogativa**: posizioni, dimensioni, margini
- **Tabella RAI**: calcolo dettagliato superficie vetrata utile e rapporto
- **Link "Torna al menu"**: in fondo a ogni variante

### Coordinate SVG

- **ViewBox**: `0 0 980 370`
- **Offset orizzontale**: xOff = 70 px
- **Scala orizzontale**: 0,6385 px/cm (860 px per 1347 cm)
- **Posizione verticale muro**: top y=40, bottom y=256 (216 px per 270 cm, scala 0,8 px/cm)
- **Finestre da terra**: y=56 (top) a y=256 (bottom) per h 250 cm
- **Finestre h 150 con davanzale 1m**: y=56 (top) a y=176 (bottom)
- **Formula posizione**: `x = 70 + posizione_cm × 0,6385`

## Render di riferimento

Esiste un render 3D della facciata (`VISTA_OVEST.jpg`, 2000×1333 px) che mostra la configurazione attuale. I prospetti si riferiscono al piano terra visibile nel render.
