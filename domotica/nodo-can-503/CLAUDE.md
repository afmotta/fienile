# CLAUDE.md — Nodo CAN 503 (rev C)

Contesto per le sessioni di Claude Code che riprendono questo progetto. Il progetto vive nella cartella `domotica/nodo-can-503/` del repository `afmotta/fienile` (il resto del repository riguarda il progetto architettonico e ha il suo `CLAUDE.md` alla radice): tutti i percorsi qui sotto sono relativi a questa cartella. Leggi questo file per intero prima di toccare qualcosa; i dettagli sono in [docs/pipeline.md](docs/pipeline.md) (come funzionano gli script) e [docs/decisioni.md](docs/decisioni.md) (perché il progetto è fatto così).

## Cos'è

PCB di un nodo per la domotica CAN di un fienile ristrutturato, da montare dietro i pulsanti in una scatola elettrica italiana **503**. Una sola scheda, revisione **C** (le rev A e B sono state abbandonate: non ricrearle).

- ESP32-C6-WROOM-1-N8 (Wi-Fi, ESPHome/OTA), TJA1051T/3 per il CAN (VIO a 3,3 V), 24 V dal bus → K7805-500R3 (5 V) → AP2112K-3.3.
- 6 ingressi pulsante (pull-up 10k, serie 1k, 100 nF), porta Qwiic senza pull-up, pettine di programmazione USB non montato.
- 56 × 41 mm, 2 strati, componenti solo sul lato superiore, 4 fori M3 negli angoli.
- Pensata per l'assemblaggio completo da JLCPCB (SMD + THT a onda).

L'utente è **Alberto**, scrive in **italiano**: rispondi in italiano. Documentazione e README sono in italiano; codice e commenti degli script in inglese.

## Regola fondamentale: il progetto è generato da script

`hardware/nodo503.kicad_sch` e `hardware/nodo503.kicad_pcb` sono **file generati**. Non modificarli a mano e non modificarli in KiCad GUI: la prossima esecuzione degli script li sovrascrive. Ogni modifica va fatta in:

- `hardware/design.py` — **unica fonte di verità**: componenti, net di ogni pin, posizioni su schema e PCB, codici LCSC, netclass, piste pre-sbrogliate, fori.
- `hardware/gen_sch.py`, `gen_pcb.py`, `route_import.py`, `gen_bom.py` — logica di generazione (serigrafie e posizioni dei riferimenti sono in `gen_pcb.py`).

Se l'utente modifica il PCB in KiCad e vuole conservare le modifiche, vanno riportate in `design.py`/`gen_pcb.py` (oppure si smette di rigenerare: chiedi prima).

## Comandi

Prerequisiti (una volta, Ubuntu 24.04): `sudo tools/setup.sh` — KiCad 7.0.x con modulo Python `pcbnew`, `kicad-cli`, Freerouting **1.9.0** in `tools/`, xvfb, Java, cairosvg.

Da `hardware/`:

| Quando | Comando | Cosa fa |
|---|---|---|
| Cambiano componenti, net, valori, testi dello schema | `python3 gen_sch.py` | Riscrive simbolo del modulo, lib-table, `.kicad_pro` (netclass/regole) e `.kicad_sch`. Va eseguito **prima** di `gen_pcb.py` se aggiungi componenti (crea l'UUID in `.comp_uuid.json`). |
| Cambiano piazzamento, footprint, net, contorno, keepout | `./route.sh` | Piazza da zero, esporta DSN, sbroglia con Freerouting (≈1 min, timeout 560 s), importa, versa le masse, DRC. Sovrascrive `nodo503.ses`. |
| Cambiano solo serigrafie/testi/attributi | `./build_pcb.sh` | Piazza da zero e reimporta lo sbroglio salvato `nodo503.ses` (riproducibile), DRC. **Non usarlo** se hai spostato componenti o cambiato net: lo sbroglio salvato non corrisponderebbe. |
| Sempre, alla fine | `./export.sh` | Controllo parità schema↔PCB, Gerber+foratura zip, BOM/CPL (completo e solo SMD), PDF dello schema, anteprime PNG in `out/`. |

Criteri di accettazione prima di consegnare o fare commit — tutti obbligatori:

1. `drc.py` (chiamato da `route.sh`/`build_pcb.sh`) stampa `Found 0 DRC violations` e `Found 0 unconnected pads`.
2. `export.sh` stampa `parita schema/PCB, discrepanze: 0`.
3. Guarda le anteprime `out/anteprima_lato_top.png` e `_bottom.png` (strumento Read sull'immagine): niente piste assurde, serigrafie leggibili e non sovrapposte alle etichette dei connettori.
4. `out/` è versionato: rigeneralo e committalo insieme alle modifiche agli script.

## Stato attuale (2026-10-14)

- DRC pulito, parità 0, pronto per l'ordine dopo le verifiche nell'anteprima JLCPCB (vedi README, "Da verificare prima dell'ordine").
- Connettori: J1 bus (morsetto a vite laterale, bordo destro, dall'alto 24V-GND-H-L), J2 pulsanti (presa estraibile verticale 7 poli KF2EDGV-3.5-7P, pin 1–6 + GND, bordo inferiore; la spina KF2EDGK-3.5-7P si ordina a parte, non è in BOM), J3 Qwiic (JST SH, bordo superiore), J4 pettine di programmazione (DNP).
- Pinout GPIO: vedi tabella nel README. Pulsanti 1–3 su GPIO7/0/1 (lato sinistro del modulo), 4–6 su GPIO20/19/18 (lato destro); CAN TX GPIO23, RX GPIO22; I²C SDA GPIO3, SCL GPIO2.
- Aperti / da fare: verifiche nell'anteprima JLCPCB; scarsa disponibilità di J3 (C160404) e delle spine 7 poli; firmware ESPHome non ancora scritto (c'è solo l'esempio nel README); proposta non ancora decisa di rendere estraibile anche J1.

## Mappa del PCB (mm, origine in alto a sinistra, y verso il basso)

- Modulo U3 in alto a sinistra (`MODX, MODY = 17.3, 15.9`), antenna a filo del bordo superiore: **nessun rame** davanti all'antenna (keepout nel footprint Espressif). Non spostare parti o piste in quella zona.
- Striscia sinistra (x 0–7.5): J4, disaccoppiamento 3V3 (C15, C16), RC su EN (R13, C17), pull-up GPIO8 (R14).
- Sotto il modulo (y 27–32): due gruppi RC dei pulsanti (`btn_xy`), poi J2 sul bordo inferiore (x 7–34).
- Destra del modulo: U1 K7805 in alto, J3 Qwiic in alto a destra, D2/C2/C3/C4, gruppo LDO (D3, D5, C13, C14, U4), F1/D1 sulla riga di J1, U2 TJA1051 + C5/C6/D4, C1 in basso a destra.
- Fori M3 a 3,5 mm dai bordi (`HOLES`), keepout piste/via di raggio 3,3 mm (`HOLE_KEEPOUT_R`). Il foro in alto a sinistra è a ~4 mm dall'antenna: consigliata vite in nylon.

## Vincoli e preferenze dell'utente (non violarli senza chiedere)

- Dimensione massima: **56 × 41 mm** (quella della CANBed RP2040). Fori M3 negli angoli per un case stampato in 3D.
- Assemblaggio **completo** da JLCPCB ("non voglio montare nulla a mano"): ogni parte montata ha un codice LCSC; preferire Basic, poi Preferred, poi Extended. Esiste anche la variante solo SMD (BOM_SMD/CPL_SMD).
- Resta su **ESP32-C6** (scartato il C3: risparmio irrilevante). Zigbee non usato per ora.
- Nessuna terminazione 120 Ω a bordo. Un solo morsetto per il bus. Niente pull-up I²C (usa QwiicBus). Ingressi pulsante con un solo GND comune.
- Lavora solo sulla rev C. Prima di rifare piazzamento/sbroglio per richieste ambigue o che toccano i vincoli, fai una domanda breve con le opzioni (l'utente risponde in fretta).
- Quando cerchi componenti, verifica stock e libreria su lcsc.com e jlcpcb.com/partdetail/Cxxxx e cita le fonti.

## Insidie note (risparmiano ore)

- **Freerouting**: usa la **1.9.0** con `xvfb-run` (senza display va in HeadlessException). La 2.x in headless produce percorsi a un solo punto. Non lanciare mai `pkill -f freerouting`: uccide anche la shell che lo invoca. Per la stessa DSN il risultato è deterministico; piccoli spostamenti cambiano molto l'esito. Se restano collegamenti aperti: sposta di poco i componenti coinvolti o aggiungi piste fisse in `PREROUTE` (esempio: bus +3V3 sulle colonne dei pull-up).
- **API pcbnew (KiCad 7)**: `board.Zones()` non è iterabile → `GetAreaCount()`/`GetArea(i)`. `ImportSpecctraSES` non è usabile → c'è un parser SES in `route_import.py`. L'angolo dei testi dei footprint è **relativo** alla rotazione del footprint (per un riferimento orizzontale su un footprint ruotato di `rot` usa `-rot`). Rotazione positiva = antioraria sullo schermo (y verso il basso).
- **Morsetto PT-1,5-H** (J1): a rotazione 0 il lato d'ingresso dei fili è verso +y; a 90° verso +x (bordo destro). La numerazione dei pin di J1 è invertita apposta (pin 4 = 24V in alto).
- **Starved thermal** su pad GND: aggiungi il riferimento a `SOLID_GND` in `design.py`.
- Fori di montaggio: footprint board-only, esclusi da BOM e CPL; le rule area attorno ai fori vengono esportate nella DSN come keepout.
- `gen_sch.py` è deterministico (UUID derivati con uuid5): a parità di `design.py` lo schema è identico byte per byte; lo stesso vale per il PCB prodotto da `build_pcb.sh` (generatore di UUID KiCad inizializzato con un seme). Un diff su `.kicad_sch`/`.kicad_pcb` quindi indica modifiche reali. Gli UUID dei simboli stanno in `.comp_uuid.json`: non cancellarlo, collega i simboli dello schema ai footprint del PCB.
- Lo sbroglio salvato (`nodo503.ses`) è stato prodotto prima della rinumerazione dei designatori: rilanciando `route.sh` sullo stato attuale Freerouting produce uno sbroglio diverso (anch'esso con DRC pulito, verificato). Va bene: dopo ogni modifica che richiede `route.sh` controlla DRC e anteprime come al solito.
- Rete del sandbox cloud: datasheet LCSC e API EasyEDA sono bloccati; le pagine prodotto di lcsc.com e jlcpcb.com/partdetail funzionano con WebFetch. Le pagine JLCPCB mostrano "Extended" anche per i Preferred. Alcuni codici esistono solo nel catalogo JLCPCB e non su LCSC (es. C42400616): verifica sempre entrambi.
- Elenco ufficiale Basic/Preferred: `scraped/assembly-details.csv` del repo GitHub CDFER/jlcpcb-parts-database (`base` = Basic, `expand` = Preferred). La classificazione usata è in `hardware/jlc_library.json` (aggiungi lì ogni nuovo codice).

## Git

- Il progetto è nel repository `afmotta/fienile`, cartella `domotica/nodo-can-503/`. È stata importata solo l'ultima iterazione; la storia precedente è riassunta in `docs/decisioni.md`.
- Lavora su un branch dedicato e apri una pull request verso `main`; i commit devono toccare solo `domotica/nodo-can-503/` (e, se serve, la riga che la descrive nel `CLAUDE.md` alla radice).
- Committa script, file KiCad generati e `hardware/out/` insieme, dopo aver soddisfatto i criteri di accettazione. Messaggi di commit in italiano, brevi, che dicano cosa cambia sulla scheda.
- Aggiorna `docs/decisioni.md` (nuova voce datata) e, se cambia qualcosa per l'utente, il README.
