"""Single source of truth for nodo503: components, nets, schematic and PCB placement."""

PROJECT = "nodo503"

# Board size (mm)
W, H = 56.0, 41.0
OX, OY = 100.0, 100.0   # board origin in KiCad page coordinates

# ---------------------------------------------------------------------------
# Components
#   ref: (lib_id, value, footprint, {pin: net}, sch(x,y), pcb(x,y,rot), extra)
#   pcb coordinates are relative to the board's top-left corner.
# ---------------------------------------------------------------------------
R0603 = "Resistor_SMD:R_0603_1608Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
C1206 = "Capacitor_SMD:C_1206_3216Metric"
R0402 = "Resistor_SMD:R_0402_1005Metric"
C0402 = "Capacitor_SMD:C_0402_1005Metric"
TB4 = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5-4-3.5-H_1x04_P3.50mm_Horizontal"
PLUG7V = "Connector_Phoenix_MC:PhoenixContact_MCV_1,5_7-G-3.5_1x07_P3.50mm_Vertical"   # pluggable header, wires from the top

COMP = {}

def add(ref, lib, value, fp, pins, sch, pcb, mpn="", lcsc="", note=""):
    COMP[ref] = dict(lib=lib, value=value, fp=fp, pins=pins, sch=sch, pcb=pcb,
                     mpn=mpn, lcsc=lcsc, note=note)

# --- Bus terminal -----------------------------------
bus = {"4": "VBUS24", "3": "GND", "2": "CANH", "1": "CANL"}
add("J1", "Connector:Screw_Terminal_01x04", "BUS 24V CAN", TB4, bus, (25.4, 45.72), (51.0, 29.0, 90),
    mpn="Morsetto a vite 4 poli passo 3,5 mm, DORABO DB125-3.5-4P-GN-S (THT)", lcsc="C2757925")

# --- Power input protection + 5 V regulator --------------------------------
add("F1", "Device:Polyfuse", "PTC 0.5A 30V", "Fuse:Fuse_1812_4532Metric",
    {"1": "VBUS24", "2": "V24F"}, (55.88, 45.72), (42.6, 18.5, 180),
    mpn="PTC 1812 RUILON SMD1812P050TF/30 (0,5 A hold, 30 V)", lcsc="C12559")
add("D1", "Device:D_Schottky", "SS34", "Diode_SMD:D_SMA",
    {"1": "V24P", "2": "V24F"}, (76.2, 45.72), (35.0, 18.5, 0),
    mpn="SS34 (40 V 3 A) - protezione inversione polarita'", lcsc="C8678")
add("D2", "Device:D_TVS", "SMBJ26CA", "Diode_SMD:D_SMB",
    {"1": "V24P", "2": "GND"}, (96.52, 45.72), (31.4, 12.2, 0),
    mpn="SMBJ26CA TVS bidirezionale 26 V, SMB (hongjiacheng)", lcsc="C19077581")
add("C1", "Device:C_Polarized", "22uF 50V", "Capacitor_SMD:CP_Elec_6.3x5.4",
    {"1": "V24P", "2": "GND"}, (109.22, 45.72), (42.8, 36.5, 0),
    mpn="Panasonic EEE-FK1H220P, elettrolitico SMD 22 uF 50 V, D6.3x5.8 mm, 105 C", lcsc="C128458")
add("C2", "Device:C", "10uF 50V", C1206,
    {"1": "V24P", "2": "GND"}, (121.92, 45.72), (30.0, 15.6, 0),
    mpn="MLCC 10 uF 50 V X5R 1206 (Samsung CL31A106KBHNNNE)", lcsc="C13585")
add("U1", "Regulator_Switching:TSR_1-2450", "K7805-500R3", "Converter_DCDC:Converter_DCDC_TRACO_TSR-1_THT",
    {"1": "V24P", "2": "GND", "3": "+5V"}, (142.24, 45.72), (31.0, 6.6, 0),
    mpn="MORNSUN K7805-500R3 (6,5-36 V -> 5 V 0,5 A, SIP-3, pin 78xx)", lcsc="C86735")
add("C3", "Device:C", "10uF", C0805, {"1": "+5V", "2": "GND"}, (167.64, 45.72), (38.0, 10.6, 0),
    mpn="MLCC 10 uF 25 V 0805", lcsc="C15850")
add("C4", "Device:C", "100nF", C0603, {"1": "+5V", "2": "GND"}, (180.34, 45.72), (38.0, 12.6, 0),
    mpn="MLCC 100 nF 50 V 0603", lcsc="C14663")
add("D3", "Device:D_Schottky", "B5819W", "Diode_SMD:D_SOD-123",
    {"1": "5V_LDO", "2": "+5V"}, (205.74, 45.72), (43.7, 8.5, 0),
    mpn="B5819W - OR alimentazione LDO (da 5 V bus)", lcsc="C8598")
add("D5", "Device:D_Schottky", "B5819W", "Diode_SMD:D_SOD-123",
    {"1": "5V_LDO", "2": "VBUS_PROG"}, (205.74, 60.96), (43.7, 10.8, 0),
    mpn="B5819W - OR alimentazione LDO (da USB di programmazione)", lcsc="C8598")
add("C13", "Device:C", "1uF", C0603, {"1": "5V_LDO", "2": "GND"}, (220.98, 45.72), (42.0, 13.0, 0),
    mpn="MLCC 1 uF 50 V X5R 0603 (Samsung CL10A105KB8NNNC)", lcsc="C15849")
add("U4", "Regulator_Linear:AP2112K-3.3", "AP2112K-3.3", "Package_TO_SOT_SMD:SOT-23-5",
    {"1": "5V_LDO", "2": "GND", "3": "5V_LDO", "4": None, "5": "+3V3"}, (246.38, 45.72), (45.6, 13.75, 180),
    mpn="Diodes AP2112K-3.3TRG1 (LDO 600 mA)", lcsc="C51118")
add("C14", "Device:C", "1uF", C0603, {"1": "+3V3", "2": "GND"}, (271.78, 45.72), (42.0, 14.8, 0),
    mpn="MLCC 1 uF 50 V X5R 0603 (Samsung CL10A105KB8NNNC)", lcsc="C15849")
add("C15", "Device:C", "10uF", C0603, {"1": "+3V3", "2": "GND"}, (284.48, 45.72), (6.4, 9.6, 90),
    mpn="MLCC 10 uF 10 V X5R 0603 (Samsung CL10A106KP8NNNC), vicino al modulo", lcsc="C19702")
add("C16", "Device:C", "100nF", C0603, {"1": "+3V3", "2": "GND"}, (297.18, 45.72), (4.6, 9.6, 90),
    mpn="MLCC 100 nF 50 V 0603", lcsc="C14663")

# --- CAN transceiver ---------------------------------------------------------
add("U2", "Interface_CAN_LIN:TJA1051T-3", "TJA1051T/3", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
    {"1": "CAN_TX", "2": "GND", "3": "+5V", "4": "CAN_RX", "5": "+3V3",
     "6": "CANL", "7": "CANH", "8": "GND"}, (76.2, 96.52), (35.0, 24.0, 0),
    mpn="NXP TJA1051T/3/1J", lcsc="C38695")
add("C5", "Device:C", "100nF", C0603, {"1": "+5V", "2": "GND"}, (106.68, 96.52), (30.3, 24.0, 90),
    mpn="MLCC 100 nF 50 V 0603", lcsc="C14663")
add("C6", "Device:C", "100nF", C0603, {"1": "+3V3", "2": "GND"}, (119.38, 96.52), (40.3, 25.5, 90),
    mpn="MLCC 100 nF 50 V 0603", lcsc="C14663")
add("D4", "Power_Protection:NUP2105L", "NUP2105L", "Package_TO_SOT_SMD:SOT-23",
    {"1": "CANH", "2": "CANL", "3": "GND"}, (139.7, 96.52), (43.8, 27.3, 0),
    mpn="onsemi NUP2105LT1G - ESD bus CAN 24 V", lcsc="C14486")

# --- MCU ---------------------------------------------------------------------
mod = {"1": "GND", "28": "GND", "29": "GND", "2": "+3V3", "3": "EN",
       # buttons 1-3 on the left pins, 4-6 on the right pins (both towards J2)
       "7": "BTN1", "8": "BTN2", "9": "BTN3", "18": "BTN4", "17": "BTN5", "16": "BTN6",
       "13": "USB_DN", "14": "USB_DP", "10": "STRAP8", "15": "BOOT",
       "26": "I2C_SDA", "27": "I2C_SCL", "21": "CAN_TX", "20": "CAN_RX"}   # TX above RX, like TJA1051 pins 1 and 4
for n in ["4", "5", "6", "11", "12", "19", "22", "23", "24", "25"]:
    mod[n] = None
MODX, MODY = 17.3, 15.9      # module origin; antenna keep-out flush with the top edge
add("U3", "nodo503:ESP32-C6-WROOM-1", "ESP32-C6-WROOM-1-N8", "nodo503:ESP32-C6-WROOM-1", mod,
    (345.44, 106.68), (MODX, MODY, 0), mpn="Espressif ESP32-C6-WROOM-1-N8", lcsc="C5366877")
add("R13", "Device:R", "10k", R0402, {"1": "+3V3", "2": "EN"}, (289.56, 86.36), (6.4, 12.4, 90),
    mpn="10 kOhm 1% 0402", lcsc="C25744")
add("C17", "Device:C", "1uF", C0402, {"1": "EN", "2": "GND"}, (302.26, 86.36), (4.9, 12.4, 90),
    mpn="MLCC 1 uF 25 V X5R 0402 (Samsung CL05A105KA5NQNC) - RC su EN", lcsc="C52923")
add("R14", "Device:R", "10k", R0402, {"1": "+3V3", "2": "STRAP8"}, (289.56, 111.76), (6.9, 19.1, 90),
    mpn="10 kOhm 1% 0402 (GPIO8 alto al boot)", lcsc="C25744")
add("J4", "Connector_Generic:Conn_01x06", "PROG USB", "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical",
    {"1": "VBUS_PROG", "2": "USB_DN", "3": "USB_DP", "4": "GND", "5": "BOOT", "6": "GND"}, (325.12, 185.42), (2.6, 18.0, 0),
    mpn="Pettine 1x6 2,54 mm (non montato): 5V, D-, D+, GND, BOOT, GND - ponticello 5-6 = download")

# --- Button inputs (0402, under the module's lower edge) -----------------------------------
btn_xy = {1: (9.0, 28.2), 2: (9.0, 29.6), 3: (9.0, 31.0), 4: (21.0, 28.2), 5: (21.0, 29.6), 6: (21.0, 31.0)}
for i in range(1, 7):
    sx = 25.4 + ((i - 1) % 3) * 40.64
    sy = 127.0 if i <= 3 else 154.94
    x, y = btn_xy[i]
    add(f"R{i}", "Device:R", "10k", R0402, {"1": "+3V3", "2": f"BTN{i}_EXT"},
        (sx, sy), (x, y, 0), mpn="10 kOhm 1% 0402", lcsc="C25744")
    add(f"R{i+6}", "Device:R", "1k", R0402, {"1": f"BTN{i}_EXT", "2": f"BTN{i}"},
        (sx + 10.16, sy), (x + 2.2, y, 0), mpn="1 kOhm 1% 0402", lcsc="C11702")
    add(f"C{i+6}", "Device:C", "100nF", C0402, {"1": f"BTN{i}", "2": "GND"},
        (sx + 20.32, sy), (x + 4.4, y, 0), mpn="MLCC 100 nF 0402", lcsc="C1525")

add("J2", "Connector:Screw_Terminal_01x07", "PULSANTI 1-6", PLUG7V,
    {"1": "BTN1_EXT", "2": "BTN2_EXT", "3": "BTN3_EXT", "4": "BTN4_EXT", "5": "BTN5_EXT", "6": "BTN6_EXT", "7": "GND"},
    (157.48, 127.0), (9.95, 37.3, 0),
    mpn="Presa per morsetto estraibile verticale 7 poli passo 3,5 mm, Kefa KF2EDGV-3.5-7P (THT); spina KF2EDGK-3.5-7P C440852 da ordinare a parte", lcsc="C441326")

# --- Qwiic / I2C (SDA = GPIO20, SCL = GPIO21) ---------------------------
add("J3", "Connector_Generic:Conn_01x04", "QWIIC", "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal",
    {"1": "GND", "2": "+3V3", "3": "I2C_SDA", "4": "I2C_SCL"}, (259.08, 129.54), (44.7, 3.3, 180),
    mpn="JST SM04B-SRSS-TB(LF)(SN) (Qwiic, SH 1 mm, orizzontale)", lcsc="C160404")
# no I2C pull-ups on board: the QwiicBus / sensor boards provide them

# power flags (schematic only)
FLAGS = [("#FLG01", "VBUS24", (200.66, 25.4)), ("#FLG02", "GND", (220.98, 25.4)),
         ("#FLG03", "V24P", (241.3, 25.4)), ("#FLG04", "5V_LDO", (261.62, 25.4)),
         ("#FLG05", "VBUS_PROG", (281.94, 25.4))]

NETCLASSES = {
    "Bus":   dict(track=0.6, clearance=0.25, nets=["VBUS24", "GND"]),
    "CAN":   dict(track=0.4, clearance=0.2, nets=["CANH", "CANL"]),
    "Power": dict(track=0.6, clearance=0.2, nets=["V24F", "V24P", "+5V", "5V_LDO", "VBUS_PROG", "+3V3"]),
}

SCH_TEXT = [
    ("BUS: 24 V + CAN (un solo morsetto)", (17.78, 30.48)),
    ("ALIMENTAZIONE 24 V -> 5 V -> 3,3 V", (78.74, 30.48)),
    ("Nessuna terminazione 120 ohm a bordo", (17.78, 80.01)),
    ("TRANSCEIVER CAN (logica 3,3 V via VIO)", (17.78, 87.63)),
    ("MCU ESP32-C6-WROOM-1: EN RC 10k/1uF, GPIO8 pull-up, BOOT=GPIO9 su J4", (284.48, 71.12)),
    ("PROGRAMMAZIONE: USB nativo (GPIO12/13) su J4, ponticello 5-6 = BOOT", (284.48, 175.26)),
    ("QWIIC I2C (SDA=GPIO20, SCL=GPIO21), pull-up esterni (QwiicBus)", (200.66, 120.65)),
    ("INGRESSI PULSANTI: pull-up 10k, serie 1k, filtro 100 nF (tau 100 us)", (17.78, 113.03)),
]

# fixed copper placed before autorouting: (kind, ...)
# GND for the module's exposed pad (3x3 grid of pads "29"): tie the grid, via to the bottom plane
PREROUTE = []
_ex = [MODX - 2.75, MODX - 1.5, MODX - 0.26]
_ey = [MODY - 3.79, MODY - 2.54, MODY - 1.29]
for x in _ex:
    PREROUTE.append(("trk", x, _ey[0], x, _ey[2], "GND"))
for y in _ey:
    PREROUTE.append(("trk", _ex[0], y, _ex[2], y, "GND"))
PREROUTE += [("via", _ex[0], _ey[0], "GND"), ("via", _ex[2], _ey[0], "GND"),
             ("via", _ex[0], _ey[2], "GND"), ("via", _ex[2], _ey[2], "GND"), ("via", _ex[1], _ey[1], "GND")]

# decoupling caps whose GND pad gets a solid (non-thermal) pour connection
SOLID_GND = {"C9", "C10", "J2", "J4", "U1"}

# AP2112K: EN (pin 3) tied to VIN (pin 1) around the GND pin
_ux, _uy = 45.6, 13.75
PREROUTE += [("trk", _ux + 1.1375, _uy + 0.95, _ux + 2.35, _uy + 0.95, "5V_LDO"),
             ("trk", _ux + 2.35, _uy + 0.95, _ux + 2.35, _uy - 0.95, "5V_LDO"),
             ("trk", _ux + 2.35, _uy - 0.95, _ux + 1.1375, _uy - 0.95, "5V_LDO")]


# M3 mounting holes (board only, no schematic symbol): centre 3.5 mm from each edge
HOLES = [(3.5, 3.5), (W - 3.5, 3.5), (3.5, H - 3.5), (W - 3.5, H - 3.5)]
HOLE_KEEPOUT_R = 3.3   # no tracks/vias under the screw head (M3 head ~5.5 mm)

# +3V3 bus along the pull-up column of each RC group (R1-R3 and R4-R6, pin 1)
for _gx in (btn_xy[1][0] - 0.51, btn_xy[4][0] - 0.51):
    PREROUTE.append(("trk", _gx, btn_xy[1][1], _gx, btn_xy[3][1], "+3V3"))
