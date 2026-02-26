# Progetto Fienile — Prospetti Parete Ovest

## Contesto

Progetto di distribuzione finestre sulla parete ovest di una casa in costruzione. La parete è al piano terra. Sono state sviluppate 5 varianti di distribuzione, ciascuna con prospetto tecnico in HTML/SVG e tabella riepilogativa.

## Parametri fissi della parete

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

## Vincoli generali

- Distanza minima dai pilastri: **10 cm** (alcune varianti usano margini maggiori)
- Distanza minima dal bordo parete: **73,5 cm** (in alcune varianti è 1 m, in altre questo vincolo è rilassato)
- Le finestre non possono sovrapporsi ai pilastri

## Rapporto Aeroilluminante (RAI)

- Il RAI si calcola come: superficie vetrata utile / superficie pavimento
- Superficie pavimento per stanza: **31,23 m²**
- La casa ha **due stanze identiche** al piano terra; per il calcolo si usano F1 e F2 (simmetria con F3 e F4)
- **Altezza utile limitata a 190 cm da terra** a causa del tetto spiovente in aggetto (le parti di finestra sopra 190 cm non contano)
- Minimo richiesto: **0,125**

## Le 5 varianti

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

## Struttura dei file

```
index.html              ← Indice con link a tutte le varianti (con RAI in descrizione)
parete_attuale.html     ← Attuale (di progetto)
parete_regolare.html    ← Variante Regolare
parete_variante_a.html  ← Variante A
parete_variante_b.html  ← Variante B
parete_variante_c.html  ← Variante C
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
