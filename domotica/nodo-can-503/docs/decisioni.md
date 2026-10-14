# Decisioni e storia del progetto

Registro delle scelte fatte con Alberto, con il motivo. Le voci più recenti sono in fondo. Quando cambi qualcosa di sostanziale, aggiungi una voce datata.

## Requisiti di partenza (ottobre 2026)

- Nodo per la domotica CAN del fienile, montato **dietro i pulsanti in una scatola 503**: legge 6 pulsanti e comunica sul bus CAN (125 kbit/s nell'esempio ESPHome).
- Alimentazione dai **24 V del bus**, regolati a 5 V; transceiver **TJA1051** (Alberto aveva un modulo AliExpress; si è scelto il chip TJA1051T/3 in SOIC-8 con VIO a 3,3 V, che rende inutile la resistenza da 4,7 kΩ su RXD degli schemi ESPHome).
- **Niente terminazione 120 Ω** a bordo (il bus si termina agli estremi). **Un solo morsetto** per 24 V + CAN (la continuità verso i nodi successivi si fa fuori dalla scheda).
- Progetto in **KiCad**. Inizialmente al massimo 5 × 5 cm; poi esteso a 56 × 41 mm (vedi sotto).

## Evoluzione

1. **Rev A — XIAO ESP32-C6 (abbandonata).** Modulo Seeed XIAO su pin header, regolatore TRACO TSR 1-2450 scartato perché costoso → **MORNSUN K7805-500R3** (switching, pin 7805). Aggiunta porta **Qwiic**. Lo XIAO non è nel catalogo JLCPCB: va montato a mano.
2. **Rev B — ESP32-C6-MINI-1 (abbandonata).** Modulo saldato direttamente per l'assemblaggio completo JLCPCB, ma il MINI-1 non era a magazzino.
3. **Rev C — ESP32-C6-WROOM-1-N8 (attuale).** Modulo a magazzino (C5366877), più grande: scheda 48 × 44 mm con tutti i componenti su un lato. Aggiunti LDO AP2112K-3.3 e "OR" a diodi (D3, D5) per alimentare il modulo dal pettine USB senza 24 V; RC su EN e pull-up su GPIO8 come da Espressif; pettine di programmazione 1×6 con pin BOOT (ponticello 5–6 = download).
4. **Librerie JLCPCB.** Sostituzioni dirette verso parti Basic dove possibile; tutto in BOM con codice LCSC ("non voglio montare nulla a mano"), THT inclusi (saldatura a onda). Creata anche la variante solo SMD.
5. **ESP32-C3 valutato e scartato.** Zigbee non serve, ma il risparmio sarebbe ~0,50 €/scheda: non vale la perdita di capacità.
6. **Revisione di un esperto.** `cleanup.py` per micro-segmenti e sovrapposizioni, coordinate arrotondate a 1 µm, verifica dei pad dei ponticelli e dell'ingresso fili di J1.
7. **Solo rev C.** Rev A e B abbandonate: non vanno più mantenute.
8. **Morsetto del bus.** Il codice C42400616 (Kefa KF350) esiste solo nel catalogo JLCPCB e non su LCSC → **DORABO DB125-3.5-4P-GN-S (C2757925)**, stesso passo e footprint.
9. **56 × 41 mm con 4 fori M3.** Richiesta: fori agli angoli per un case stampato in 3D, senza superare la **CANBed RP2040 (56 × 41 mm)**. La vecchia 48 × 44 superava già i 41 mm in altezza, quindi la scheda è stata ridisposta: modulo in alto a sinistra, J1 sul bordo destro, pulsanti sul bordo inferiore. Fori a 3,5 mm dai bordi (interasse 49 × 34 mm), keepout piste/via di 3,3 mm.
10. **Tolti i pull-up I²C** opzionali (R + ponticelli a saldare): Alberto usa il **QwiicBus**, che li ha già.
11. **GPIO riassegnati** per sbrogliare meglio: pulsanti 1–3 sul lato sinistro del modulo, 4–6 sul destro, CAN TX/RX scambiati per allinearli ai pin 1 e 4 del TJA1051. Risultato: meno via, retro quasi tutto massa.
12. **Connettore dei pulsanti.** La scheda sta dietro i pulsanti, quindi servono fili che entrano **dall'alto** e un modo rapido per staccarla: scelto il **morsetto estraibile verticale** (presa KF2EDGV-3.5 + spina a vite KF2EDGK-3.5). Scartato il push-in KF141V-2.54 (alto 13,6 mm, footprint a due file non verificabile, fili solo sottili). Poi passati da 2 × 4 poli a **un 7 poli con un solo GND** (un'unica spina, niente rischio di scambiare le spine, 6 mm in meno). Rischio: magazzino basso (presa 485, spina 234 al 2026-10-14); riserva = due 4 poli, ma richiede di rifare il PCB.
13. **Filo consigliato per i pulsanti:** cordina 0,5 mm² (corrente ~0,3 mA); isolamento adatto ai 230 V se condivide scatola o tubi con la rete.
14. **Designatori rinumerati** senza buchi (J1 bus, J2 pulsanti, J3 Qwiic, J4 programmazione; R13 EN, R14 GPIO8) e riferimenti J1/J2 spostati lontano dalle etichette dei pin.

## Scelte tecniche che non vanno cambiate senza motivo

| Scelta | Perché |
|---|---|
| TJA1051T/3 con VIO a 3,3 V | Uscita RXD già a 3,3 V, niente partitore; pin S a GND (modalità normale). |
| K7805-500R3 + AP2112K | 5 V per il transceiver, 3,3 V puliti per il modulo; il K7805 regge fino a 36 V in ingresso. |
| PTC 0,5 A, SS34, SMBJ26CA, NUP2105L | Protezione da sovracorrente, inversione, sovratensione sul 24 V e ESD sulle linee CAN. |
| RC sui pulsanti (10k / 1k / 100 nF) | Filtro dei disturbi sulle linee lunghe verso i pulsanti; antirimbalzo fine in ESPHome (`delayed_on_off`). |
| Antenna a filo del bordo superiore, keepout Espressif | Prestazioni Wi-Fi; nessun rame e nessun componente davanti all'antenna. |
| Fori M3 non metallizzati | Case in plastica; la testa della vite poggia su massa coperta da solder mask. Vite in nylon consigliata nel foro vicino all'antenna. |
| Freerouting 1.9.0 | Unica versione che funziona headless in questo ambiente (vedi CLAUDE.md). |

## Punti aperti

- Verifiche nell'anteprima di assemblaggio JLCPCB: rotazioni (U3, U2, U4, J1, J2, J3, diodi, C1), orientamento del corpo di J1 (fili dal bordo destro), lato dell'incastro di J2, via-in-pad tappate sotto il modulo.
- J3 (JST SH, C160404) ha pochi pezzi: alternative C7430446, C2845363, C18077910 (da confrontare col footprint).
- Possibile J1 estraibile (proposto, non deciso).
- Firmware ESPHome da scrivere (c'è solo l'esempio nel README).
- Case stampato in 3D da progettare (interasse fori 49 × 34 mm, altezza massima componenti ≈ 11 mm per K7805 e morsetti; la spina di J2 sporge di più).
