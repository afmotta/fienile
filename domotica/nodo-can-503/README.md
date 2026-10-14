# Nodo CAN 503 – ESP32-C6-WROOM-1 (rev C)

Nodo per la domotica CAN del fienile, da montare in scatola 503: un morsetto per 24 V e bus CAN, transceiver TJA1051T/3, 6 ingressi pulsante, porta Qwiic (I²C) e modulo **ESP32-C6-WROOM-1-N8** (LCSC C5366877) con Wi-Fi per ESPHome e aggiornamenti OTA. È pensato per il montaggio completo da JLCPCB, con tutti i componenti su un solo lato.

- **Dimensioni:** 56 × 41 mm (come la CANBed RP2040), 2 strati, spessore 1,6 mm, rame 1 oz
- **Fissaggio:** 4 fori M3 non metallizzati (Ø 3,2 mm) negli angoli, con il centro a 3,5 mm dai bordi: interasse **49 × 34 mm**. Entro 3,3 mm dal centro di ogni foro non passano piste né via, così la testa della vite (fino a Ø 6 mm) appoggia solo su piano di massa coperto da solder mask. Il foro in alto a sinistra è a circa 4 mm dall'antenna: lì usa una vite in nylon o un perno di plastica.
- **Progetto:** KiCad 7 (si apre anche in KiCad 8/9)
- **Simbolo e footprint del modulo:** dalla libreria ufficiale [espressif/kicad-libraries](https://github.com/espressif/kicad-libraries), licenza CC-BY-SA 4.0. Il footprint comprende anche l'area dell'antenna senza rame.

## Contenuto della cartella

Questa cartella (`domotica/nodo-can-503/` nel repository `afmotta/fienile`) contiene tutto il progetto della scheda; i percorsi sono relativi a qui.

| Percorso | Cosa contiene |
|---|---|
| `hardware/nodo503.kicad_pro / .kicad_sch / .kicad_pcb` | Progetto KiCad 7 completo (si apre con KiCad 7, 8 o 9) |
| `hardware/nodo503.kicad_sym`, `hardware/nodo503.pretty/` | Simbolo e footprint del modulo ESP32-C6-WROOM-1 (libreria di progetto) |
| `hardware/out/gerber_JLCPCB.zip` | Gerber + foratura, da caricare così com'è su JLCPCB |
| `hardware/out/BOM.csv`, `CPL_JLCPCB.csv` | Distinta e piazzamento per il montaggio completo (SMD + THT) |
| `hardware/out/BOM_SMD.csv`, `CPL_SMD.csv` | Distinta e piazzamento solo SMD |
| `hardware/out/nodo503_schema.pdf`, `anteprima_lato_*.png` | Schema elettrico e anteprime rame + serigrafia |
| `hardware/jlc_library.json` | Libreria JLCPCB (Basic / Preferred / Extended) di ogni codice LCSC |
| `hardware/*.py`, `hardware/*.sh` | Script che generano schema, PCB, sbroglio e file di produzione (vedi [docs/pipeline.md](docs/pipeline.md)) |
| `docs/decisioni.md` | Storia del progetto e motivazioni delle scelte |
| `docs/pipeline.md` | Come rigenerare tutto, struttura degli script, problemi noti |
| `CLAUDE.md` | Contesto per le sessioni di Claude Code che lavoreranno sul progetto |
| `tools/setup.sh` | Installa KiCad 7, Freerouting 1.9.0 e le dipendenze Python |

Per rigenerare i file di produzione dopo una modifica: `sudo tools/setup.sh` (una volta), poi `hardware/route.sh` se cambiano piazzamento o collegamenti, `hardware/build_pcb.sh` se basta lo sbroglio salvato, e infine `hardware/export.sh`.

## Circuito

- **Ingresso 24 V:** PTC da 0,5 A (F1), diodo SS34 contro l'inversione di polarità (D1), TVS SMBJ26CA (D2), elettrolitico da 22 µF e MLCC da 10 µF 50 V in ingresso.
- **5 V:** MORNSUN K7805-500R3 (U1), switching con pin compatibili 7805. Alimenta il TJA1051.
- **3,3 V:** LDO AP2112K-3.3 (U4, 600 mA). Due diodi B5819W (D3, D5) in "OR" lo alimentano dai 5 V del K7805 oppure dai 5 V del pettine di programmazione: il modulo si programma anche senza i 24 V, e la tensione dell'USB non risale verso il K7805.
- **CAN:** TJA1051T/3 con VIO a 3,3 V (nessun partitore sulle linee logiche), pin S a GND, protezione ESD NUP2105L sulle linee del bus. **Nessuna terminazione da 120 Ω** a bordo: il bus va terminato agli estremi della linea.
- **Microcontrollore:** modulo ESP32-C6-WROOM-1-N8 (flash 8 MB, antenna su PCB), con l'antenna a filo del bordo superiore della scheda. Rete RC su EN (10 kΩ + 1 µF) e pull-up da 10 kΩ su GPIO8, come raccomanda Espressif.
- **Ingressi pulsante:** per ciascuno pull-up da 10 kΩ a 3,3 V, resistenza in serie da 1 kΩ e condensatore da 100 nF verso GND (τ ≈ 100 µs). Il pulsante chiude verso GND (logica attiva bassa). Componenti 0402, sotto il bordo inferiore del modulo.

## Pinout

| Funzione | GPIO | Pin modulo WROOM |
|---|---|---|
| CAN TXD | GPIO23 | 21 |
| CAN RXD | GPIO22 | 20 |
| Pulsante 1 | GPIO7 | 7 |
| Pulsante 2 | GPIO0 | 8 |
| Pulsante 3 | GPIO1 | 9 |
| Pulsante 4 | GPIO20 | 18 |
| Pulsante 5 | GPIO19 | 17 |
| Pulsante 6 | GPIO18 | 16 |
| Qwiic SDA | GPIO3 | 26 |
| Qwiic SCL | GPIO2 | 27 |
| USB D− / D+ (programmazione) | GPIO12 / GPIO13 | 13 / 14 |
| BOOT (pin 5 di J4) | GPIO9 | 15 |
| Pull-up di boot | GPIO8 | 10 |
| Liberi | GPIO4, 5, 6, 10, 11, 15, 16, 17, 21 | – |

Rispetto alla versione 48 × 44 mm i GPIO di pulsanti, Qwiic e CAN sono cambiati: i pulsanti 1–3 usano i pin del lato sinistro del modulo, i pulsanti 4–6 quelli del lato destro, così le piste non si incrociano. GPIO4, GPIO5, GPIO8, GPIO9 e GPIO15 sono pin di strapping: se in futuro ne usi uno, tieni conto del livello che deve avere all'avvio.

## Connettori

- **J1 BUS:** morsetto passo 3,5 mm sul bordo destro, fili che entrano da destra. Dall'alto in basso: 24V – GND – CAN-H – CAN-L.
- **J2 PULSANTI:** morsetto estraibile verticale a 7 poli, passo 3,5 mm, sul bordo inferiore. Sulla scheda c'è la presa (Kefa KF2EDGV-3.5-7P); i fili vanno nella spina a vite (KF2EDGK-3.5-7P), che si innesta dall'alto, quindi i fili escono perpendicolari alla scheda. Cabli la spina sui pulsanti e poi la innesti: per staccare la scheda basta sfilarla. Pin da sinistra: pulsanti 1, 2, 3, 4, 5, 6, GND.
- **Comune dei pulsanti:** c'è un solo morsetto GND. Fai i ponticelli del comune tra i pulsanti sulla placca e porta un solo filo alla spina. Se preferisci due fili fino alla spina, il morsetto da 1,5 mm² ne accetta due da 0,5 mm², meglio con un puntale doppio.
- **Filo per i pulsanti:** la corrente è di circa 0,3 mA, quindi la sezione conta solo per la meccanica. Consigliata cordina da **0,5 mm²** (la spina accetta da 0,2 a 1,5 mm²). Se nella scatola o nei tubi passano anche conduttori a 230 V, il filo deve avere un isolamento adatto a quella tensione (ad esempio FS17 o H05V-K da 0,5 mm²).
- **J3 Qwiic:** JST SH a 4 pin, passo 1 mm, sul bordo superiore a destra con l'imbocco verso l'alto. GND, 3,3 V, SDA, SCL. **Nessun pull-up I²C sulla scheda:** li forniscono il QwiicBus e le schede dei sensori.
- **J4 PROG:** pettine verticale 1×6 a passo 2,54 mm sul lato sinistro, da non montare. Pin: 5V, D−, D+, GND, BOOT, GND. I pin 1–4 vanno al cavo USB (USB nativo del C6). Un ponticello sui pin 5–6 porta GPIO9 a massa e fa partire il modulo in modalità download.

Nessuna terminazione da 120 Ω sulla scheda: il bus va terminato agli estremi della linea.

## Prima programmazione

1. Collega un cavo USB al pettine J4: rosso al 5V, bianco a D−, verde a D+, nero a GND. Puoi usare un connettore a pettine o delle punte a molla (pogo pin).
2. Con il flash vuoto il modulo di solito entra da solo in modalità download. Se non succede, o se un firmware difettoso ha bloccato l'USB:
   - metti un ponticello sui pin 5–6 di J4 (BOOT–GND);
   - collega l'USB, oppure accendi la scheda;
   - programma, poi **togli il ponticello**. Se lo lasci, il modulo resta in modalità download a ogni riavvio e il firmware non parte.
3. Programma con ESPHome (o esptool) via USB. Dal flash successivo puoi usare l'OTA via Wi-Fi.

## Da verificare prima dell'ordine

1. **Codici LCSC e magazzino.** Tutti i componenti montati hanno un codice LCSC. Al caricamento della BOM controlla la disponibilità, soprattutto di J3 (vedi sotto).
2. **Rotazioni nel file CPL.** Controllale nell'anteprima di assemblaggio JLCPCB, soprattutto per il modulo U3 (l'antenna deve stare a filo del bordo superiore, sopra l'area senza rame), U2, U4 (ruotato di 180°), J3 (ruotato di 180°, imbocco verso l'alto), J1 (ruotato di 90°), J2 (il lato con l'incastro della spina deve coincidere con quello del footprint), i diodi e C1.
3. **Via nel pad di massa del modulo.** Il pad di massa sotto il WROOM è una griglia 3×3 con 5 via verso la massa sul retro. Su JLCPCB conviene chiedere che le via siano tappate ("via-in-pad" o "epoxy filled"), così lo stagno non cola nei fori. Se non lo fai, di solito funziona comunque.
4. **Piste sotto il modulo.** La pista di BOOT passa sullo strato superiore sotto il bordo inferiore del modulo, lontano dall'antenna; altre piste passano sul retro sotto il modulo. È ammesso, ma se in KiCad vuoi un piano di massa più pulito sotto il modulo puoi spostarle sul retro.

## Montaggio

- **Montaggio completo:** carica `BOM.csv` e `CPL_JLCPCB.csv`. JLCPCB monta anche i THT (K7805-500R3, J1 e la presa J2) a onda o a mano. Non resta nulla da saldare, J4 resta senza componente. La spina KF2EDGK-3.5-7P si ordina a parte.
- **Solo SMD:** carica `BOM_SMD.csv` e `CPL_SMD.csv`. Il K7805, J1 e la presa J2 restano da saldare a mano.

## Esempio ESPHome (indicativo)

```yaml
esp32:
  board: esp32-c6-devkitc-1
  variant: esp32c6
  framework:
    type: esp-idf

canbus:
  - platform: esp32_can
    tx_pin: GPIO23
    rx_pin: GPIO22
    can_id: 0x101
    bit_rate: 125kbps

i2c:
  sda: GPIO3
  scl: GPIO2
  scan: true

binary_sensor:
  - platform: gpio
    name: "Pulsante 1"
    pin:
      number: GPIO7
      inverted: true
      mode: { input: true, pullup: false }   # pull-up esterno da 10k
    filters:
      - delayed_on_off: 20ms
  # Pulsanti 2–6: GPIO0, GPIO1, GPIO20, GPIO19, GPIO18
```

## BOM e librerie JLCPCB (aggiornata il 2026-10-14)

Tutti i componenti hanno un codice LCSC e sono pensati per il montaggio completo da JLCPCB, compresi i THT (J1, J2 e K7805 U1, saldati da JLCPCB a onda o a mano). La colonna **Libreria JLCPCB** della BOM indica Basic / Preferred / Extended; l'elenco usato è in `hardware/jlc_library.json`.

- **Non montati:** solo **J4** (pettine di programmazione, DNP). Per programmare si usano pin a pressione o un pettine inserito al momento.
- **C2** è passato da 2,2 µF a **10 µF 50 V 1206** (C13585, Basic): più capacità in ingresso al K7805 e un componente Extended in meno.
- **C1:** Panasonic EEE-FK1H220P (C128458), 6,3 × 5,8 mm. È compatibile con il footprint 6,3 × 5,4 mm.
- **J1:** DORABO DB125-3.5-4P-GN-S (C2757925, Extended, saldatura a onda, disponibile anche in PCBA Economic), passo 3,5 mm, ingresso fili laterale, vite M2, filo fino a 1 mm². Il passo coincide con il footprint Phoenix PT 1,5/4-3,5-H. Prima dell'ordine verifica nell'anteprima JLCPCB che il corpo e il lato d'ingresso dei fili coincidano.
- **J2:** presa Kefa KF2EDGV-3.5-7P (C441326, Extended, saldatura a onda, PCBA Economic e Standard), footprint Phoenix MCV 1,5/7-G-3,5 verticale. A magazzino LCSC ce n'erano 485 il 2026-10-14.
- **Spina per J2 da ordinare a parte:** Kefa KF2EDGK-3.5-7P (LCSC C440852, circa 0,52 $ da 10 pezzi). Non è nella BOM di montaggio perché non si salda: si aggiunge all'ordine LCSC. Il 2026-10-14 ce n'erano solo 234: comprale con il primo ordine, con qualcuna di scorta. Se finissero, la soluzione di riserva sono due 4 poli (KF2EDGV/KF2EDGK-3.5-4P, C441323/C440849, molto disponibili), ma servirebbe rifare il PCB. 
- **CPL:** per i THT la posizione è il centro dei pin (non il pin 1). Controlla nell'anteprima di assemblaggio le rotazioni dei morsetti e del K7805.
- **J3 (C160404) ha pochissimi pezzi a magazzino.** Alternative compatibili Qwiic (Extended, da confrontare con il footprint): ZX-SH1.0-4PWT C7430446, HC-1.0-4PWT C2845363, BX-SH1.0-4PWT C18077910.
- Le pagine JLCPCB dei componenti Preferred mostrano solo "Extended": al caricamento della BOM verifica che abbiano il badge "Preferred".

## Storia e decisioni

La storia del progetto (rev A con XIAO, rev B con MINI-1, revisione di un esperto, passaggio a 56 × 41 mm, scelta dei connettori) e il motivo di ogni scelta sono in [docs/decisioni.md](docs/decisioni.md).
