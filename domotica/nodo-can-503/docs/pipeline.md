# Pipeline di generazione

Tutto il progetto KiCad è prodotto da script Python che usano il modulo `pcbnew` di KiCad 7. Gli script stanno in `hardware/` e vanno eseguiti da lì (gli shell script fanno `cd` nella propria cartella).

```
design.py ──► gen_sch.py ──► nodo503.kicad_sch, .kicad_pro, .kicad_sym, *-lib-table, .comp_uuid.json
    │
    └──────► gen_pcb.py ──► nodo503.kicad_pcb (non sbrogliato)
                               │
          route.sh:  ExportSpecctraDSN ─► Freerouting 1.9 ─► nodo503.ses
                               │
                     route_import.py (+ cleanup.py) ─► piste, masse, via di cucitura
                               │
                     drc.py ─► drc.rpt (0 violazioni, 0 non collegati)
                               │
          export.sh: parità schema↔PCB, Gerber, gen_bom.py, PDF, PNG ─► out/
```

## Strumenti

| Strumento | Versione usata | Note |
|---|---|---|
| KiCad (`pcbnew`, `kicad-cli`) | 7.0.11 (Ubuntu 24.04, pacchetto `kicad`) | Le librerie standard sono lette da `/usr/share/kicad/{footprints,symbols}`; sovrascrivibili con `KICAD7_FOOTPRINT_DIR` e `KICAD7_SYMBOL_DIR`. |
| Freerouting | 1.9.0 (`tools/freerouting-1.9.0.jar`, SHA-256 in `tools/setup.sh`) | Richiede Java e `xvfb-run`. Percorso sovrascrivibile con `FREEROUTING`. |
| Python | 3.12 + `cairosvg` | Solo per le anteprime PNG. |

`tools/setup.sh` installa tutto.

## `design.py` — fonte di verità

- `W, H` dimensioni della scheda (mm); `OX, OY = 100, 100` posizione dell'origine della scheda nella pagina KiCad.
- `add(ref, lib_id, value, footprint, pins, sch, pcb, mpn, lcsc)` aggiunge un componente a `COMP`:
  - `pins`: dizionario `{numero_pin: net}`; `None` = non collegato (lo schema mette una croce di no-connect).
  - `sch`: posizione `(x, y)` del simbolo nello schema (mm, pagina A3).
  - `pcb`: `(x, y, rotazione)` del footprint, in mm **relativi all'angolo in alto a sinistra della scheda**. Le coordinate vengono arrotondate a 1 µm.
  - `mpn`: descrizione/MPN che finisce in BOM; `lcsc`: codice LCSC (vuoto = da assegnare).
- `MODX, MODY`: origine del modulo ESP32 (le piste fisse della griglia di massa sotto il modulo dipendono da qui).
- `btn_xy`: posizione dei 6 gruppi RC dei pulsanti (R pull-up a x, R serie a x+2,2, C a x+4,4).
- `NETCLASSES`: larghezze e clearance (Bus/Power 0,6 mm, CAN 0,4 mm, Default 0,25 mm). Finiscono nel `.kicad_pro` e quindi nella DSN.
- `PREROUTE`: rame fisso piazzato prima dello sbroglio. Tipi: `("trk", x1, y1, x2, y2, net)` pista 0,3 mm su F.Cu, `"trkn"` 0,2 mm su F.Cu, `"trkb"` 0,25 mm su B.Cu, `("via", x, y, net)`. Oggi contiene: griglia 3×3 del pad di massa del modulo con 5 via, anello EN–VIN dell'AP2112K, bus +3V3 lungo le colonne dei pull-up dei pulsanti.
- `SOLID_GND`: componenti i cui pad GND si collegano al piano senza razze termiche (evita gli starved thermal).
- `HOLES`, `HOLE_KEEPOUT_R`: centri dei fori M3 e raggio dell'area senza piste/via.
- `FLAGS`, `SCH_TEXT`: power flag e testi dello schema.

## Script

- **`gen_sch.py`** — scrive il simbolo del modulo (`nodo503.kicad_sym`, pin dalla libreria Espressif), le lib-table, il `.kicad_pro` (netclass, regole DRC, severità) e lo schema: ogni simbolo con etichette di net sui pin. Gli UUID dei simboli sono in `.comp_uuid.json` (conservati tra un'esecuzione e l'altra; i nuovi riferimenti ricevono un UUID derivato dal nome); tutti gli altri UUID sono deterministici, quindi lo schema generato è identico byte per byte a parità di `design.py`. Anche `gen_pcb.py` e `route_import.py` inizializzano il generatore di UUID di KiCad (`KIID.SeedGenerator`): a parità di input `build_pcb.sh` produce un `.kicad_pcb` identico. Gerber, PDF e PNG contengono invece date di generazione e cambiano a ogni esportazione.
- **`gen_pcb.py`** — crea la scheda da zero: net, footprint (librerie KiCad o `nodo503.pretty`), contorno con raggio 1,5 mm, fori M3 board-only + rule area, serigrafie (etichette dei pin dei connettori, testo sul retro), posizioni dei riferimenti (`REF_POS`), rame di `PREROUTE`. I riferimenti dei passivi 0402 sono nascosti.
- **`route.sh`** — `gen_pcb.py` → `ExportSpecctraDSN` → `xvfb-run java -jar freerouting-1.9.0.jar -de nodo503.dsn -do nodo503.ses -mp 100` (timeout `FR_TIMEOUT`, default 560 s; log in `logs/freerouting.log`) → `route_import.py` → `drc.py`.
- **`build_pcb.sh`** — come `route.sh` ma senza Freerouting: reimporta `nodo503.ses` salvato. Usalo solo se piazzamento e net non sono cambiati.
- **`route_import.py`** — parser SES fatto in casa; rimuove via e segmenti duplicati, monconi pendenti e via orfane; chiama `cleanup.run`; crea le zone GND su entrambi gli strati (clearance 0,3 mm, razze 0,3/0,4 mm, spessore minimo 0,25 mm); aggiunge via di cucitura su griglia 2 mm dove entrambe le masse coprono il punto (lontano da via, pad THT e fori di montaggio); rimuove le isole e aggancia con una via quelle rimaste senza collegamento all'altro strato.
- **`cleanup.py`** — elimina micro-segmenti (< 10 µm), unisce segmenti collineari sovrapposti, elimina segmenti stretti coperti da uno più largo.
- **`drc.py`** — `WriteDRCReport` → `drc.rpt`; stampa il conteggio per tipo e le righe `Found …`.
- **`gen_bom.py`** — `out/BOM.csv` (raggruppata per valore/footprint/MPN/LCSC, colonna libreria JLCPCB da `jlc_library.json`), `out/CPL_JLCPCB.csv` (THT al centro dei pad, esclusi DNP e componenti board-only), `out/BOM_SMD.csv` e `out/CPL_SMD.csv` (senza THT e DNP). `THT_JLC` = THT montati da JLCPCB, `DNP` = non montati.
- **`export.sh`** — netlist dallo schema e confronto pin per pin con il PCB (deve stampare 0 discrepanze), Gerber (F/B Cu, Paste, SilkS, Mask, Edge) + foratura Excellon in `out/gerber_JLCPCB.zip`, `gen_bom.py`, PDF dello schema, anteprime PNG dei due lati.

## Ricette

**Spostare un componente o cambiarne il footprint.** Modifica `pcb`/`fp` in `design.py` → `./route.sh` → controlla DRC e anteprima → `./export.sh`. Se il DRC segnala collegamenti mancanti, prova piccoli spostamenti (0,5–2 mm) dei componenti vicini al collegamento mancante o una pista fissa in `PREROUTE`, poi rilancia.

**Aggiungere un componente.** `add(...)` in `design.py` (con LCSC, e la libreria in `jlc_library.json`) → `python3 gen_sch.py` → `./route.sh` → `./export.sh`.

**Cambiare un codice LCSC o una descrizione.** Modifica `design.py` (e `jlc_library.json`) → `python3 gen_sch.py` → `./export.sh` (il PCB non cambia).

**Cambiare una serigrafia.** `gen_pcb.py` → `./build_pcb.sh` → `./export.sh`.

**Rinumerare i riferimenti.** Rinomina in `design.py`, `gen_pcb.py`, `gen_bom.py` e le chiavi di `.comp_uuid.json` (così il collegamento schema↔PCB resta) → `gen_sch.py` → `build_pcb.sh` → `export.sh` → README.

## Controlli utili

- `python3 check_placement.py` — sovrapposizioni dei courtyard e componenti fuori scheda (esegui dopo `gen_pcb.py`, prima di sbrogliare: fa risparmiare un giro di Freerouting).
- `python3 drc.py` — DRC completo (deve dare 0 e 0).
- `python3 metrics.py` — lunghezza piste per strato, via, copertura delle masse, lunghezza delle net principali: utile per confrontare due varianti di piazzamento.
