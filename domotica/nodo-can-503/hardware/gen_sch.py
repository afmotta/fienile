"""Generate project lib, footprint, project file and schematic for nodo503."""
import json, re, uuid, os
from design import *

ROOT = os.path.dirname(os.path.abspath(__file__))
SYMDIR = os.environ.get("KICAD7_SYMBOL_DIR", "/usr/share/kicad/symbols")
# deterministic UUIDs: same design.py -> byte-identical schematic (clean git diffs)
_NS = uuid.UUID("6a1f3c2e-5b7d-4e8a-9c10-503503503503")
_counter = iter(range(10**9))
U = lambda: str(uuid.uuid5(_NS, f"item-{next(_counter)}"))
ROOT_UUID = "6a1f3c2e-5b7d-4e8a-9c10-503503503503"

# --------------------------------------------- ESP32-C6-WROOM-1 symbol (pins from Espressif lib)
F = '(effects (font (size 1.27 1.27)))'
FH = '(effects (font (size 1.27 1.27)) hide)'
MOD_PINS = [  # (number, name, type, x, y, angle) - ESP32-C6-WROOM-1
    ("1", "GND", "power_in", 0, -33.02, 90), ("28", "GND", "passive", 0, -33.02, 90), ("29", "GND", "passive", 0, -33.02, 90),
    ("2", "3V3", "power_in", 0, 33.02, 270),
    ("3", "EN/CHIP_PU", "input", -27.94, 27.94, 0),
    ("8", "GPIO0/XTAL_32K_P", "bidirectional", -27.94, 22.86, 0), ("9", "GPIO1/XTAL_32K_N", "bidirectional", -27.94, 20.32, 0),
    ("27", "GPIO2", "bidirectional", -27.94, 17.78, 0), ("26", "GPIO3", "bidirectional", -27.94, 15.24, 0),
    ("4", "MTMS/GPIO4", "bidirectional", -27.94, 7.62, 0), ("5", "MTDI/GPIO5", "bidirectional", -27.94, 5.08, 0),
    ("6", "MTCK/GPIO6", "bidirectional", -27.94, 2.54, 0), ("7", "MTDO/GPIO7", "bidirectional", -27.94, 0, 0),
    ("11", "GPIO10", "bidirectional", -27.94, -5.08, 0), ("12", "GPIO11", "bidirectional", -27.94, -7.62, 0),
    ("22", "NC", "no_connect", -27.94, -12.7, 0),
    ("25", "U0TXD/GPIO16", "bidirectional", 27.94, 27.94, 180), ("24", "U0RXD/GPIO17", "bidirectional", 27.94, 25.4, 180),
    ("14", "GPIO13/USB_D+", "bidirectional", 27.94, 20.32, 180), ("13", "GPIO12/USB_D-", "bidirectional", 27.94, 17.78, 180),
    ("10", "GPIO8", "bidirectional", 27.94, 7.62, 180), ("15", "GPIO9/BOOT", "bidirectional", 27.94, 5.08, 180),
    ("23", "GPIO15", "bidirectional", 27.94, 2.54, 180), ("16", "GPIO18", "bidirectional", 27.94, -2.54, 180),
    ("17", "GPIO19", "bidirectional", 27.94, -5.08, 180), ("18", "GPIO20", "bidirectional", 27.94, -7.62, 180),
    ("19", "GPIO21", "bidirectional", 27.94, -10.16, 180), ("20", "GPIO22", "bidirectional", 27.94, -12.7, 180),
    ("21", "GPIO23", "bidirectional", 27.94, -15.24, 180),
]

def mod_sym(name):
    pins = []
    for num, nm, typ, x, y, a in MOD_PINS:
        hide = " hide" if (nm == "GND" and num != "1") else ""
        pins.append(f'(pin {typ} line (at {x} {y} {a}) (length 2.54){hide} (name "{nm}" {F}) (number "{num}" {F}))')
    return f'''(symbol "{name}" (in_bom yes) (on_board yes)
    (property "Reference" "U" (at -25.4 31.75 0) (effects (font (size 1.27 1.27)) (justify left)))
    (property "Value" "ESP32-C6-WROOM-1" (at -25.4 -31.75 0) (effects (font (size 1.27 1.27)) (justify left)))
    (property "Footprint" "nodo503:ESP32-C6-WROOM-1" (at 0 -36 0) {FH})
    (property "Datasheet" "https://www.espressif.com/sites/default/files/documentation/esp32-c6-wroom-1_wroom-1u_datasheet_en.pdf" (at 0 -38 0) {FH})
    (symbol "{name}_0_1" (rectangle (start -25.4 30.48) (end 25.4 -30.48) (stroke (width 0.254) (type default)) (fill (type background))))
    (symbol "{name}_1_1" {" ".join(pins)}))'''

CUSTOM_SYMS = {"ESP32-C6-WROOM-1": mod_sym}
open(f"{ROOT}/nodo503.kicad_sym", "w").write(
    f'(kicad_symbol_lib (version 20220914) (generator nodo503_gen)\n  {mod_sym("ESP32-C6-WROOM-1")}\n)\n')

open(f"{ROOT}/sym-lib-table", "w").write(
    '(sym_lib_table\n  (lib (name "nodo503")(type "KiCad")(uri "${KIPRJMOD}/nodo503.kicad_sym")(options "")(descr "Simboli progetto"))\n)\n')
open(f"{ROOT}/fp-lib-table", "w").write(
    '(fp_lib_table\n  (lib (name "nodo503")(type "KiCad")(uri "${KIPRJMOD}/nodo503.pretty")(options "")(descr "Footprint progetto"))\n)\n')

# ---------------------------------------------------------------- project file
def nc(name, track, clearance):
    return {"name": name, "clearance": clearance, "track_width": track, "via_diameter": 0.6,
            "via_drill": 0.3, "diff_pair_width": 0.2, "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25,
            "microvia_diameter": 0.3, "microvia_drill": 0.1, "wire_width": 6, "bus_width": 12,
            "line_style": 0, "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)"}
classes = [nc("Default", 0.25, 0.2)] + [nc(k, v["track"], v["clearance"]) for k, v in NETCLASSES.items()]
patterns = [{"netclass": k, "pattern": n} for k, v in NETCLASSES.items() for n in v["nets"]]
pro = {
    "board": {"design_settings": {
        "defaults": {"board_outline_line_width": 0.1, "copper_line_width": 0.2, "copper_text_size_h": 1.5,
                     "copper_text_size_v": 1.5, "copper_text_thickness": 0.3, "silk_line_width": 0.12,
                     "silk_text_size_h": 0.8, "silk_text_size_v": 0.8, "silk_text_thickness": 0.12},
        "rules": {"min_clearance": 0.15, "min_track_width": 0.15, "min_via_diameter": 0.5,
                  "min_through_hole_diameter": 0.3, "min_hole_clearance": 0.25, "min_hole_to_hole": 0.25,
                  "min_copper_edge_clearance": 0.3, "min_silk_clearance": 0.0, "min_text_height": 0.6,
                  "min_text_thickness": 0.1, "min_annular_ring": 0.13, "min_via_annular_width": 0.1,
                  "solder_mask_to_copper_clearance": 0.0},
        "track_widths": [0.0, 0.25, 0.4, 0.6, 1.0], "via_dimensions": [{"diameter": 0.0, "drill": 0.0}, {"diameter": 0.6, "drill": 0.3}],
        "rule_severities": {"silk_overlap": "ignore", "silk_over_copper": "ignore", "silk_edge_clearance": "ignore",
                            "lib_footprint_issues": "ignore", "lib_footprint_mismatch": "ignore",
                            "text_height": "ignore", "text_thickness": "ignore"},
    }},
    "meta": {"filename": f"{PROJECT}.kicad_pro", "version": 1},
    "net_settings": {"classes": classes, "meta": {"version": 3}, "net_colors": None,
                     "netclass_assignments": None, "netclass_patterns": patterns},
    "erc": {"rule_severities": {"lib_symbol_issues": "ignore", "footprint_link_issues": "ignore"}},
    "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
    "sheets": [[ROOT_UUID, "Root"]],
    "text_variables": {},
}
json.dump(pro, open(f"{ROOT}/{PROJECT}.kicad_pro", "w"), indent=2)

# ------------------------------------------------------------- symbol library
def extract(lib, sym):
    t = open(f"{SYMDIR}/{lib}.kicad_sym").read()
    i = t.find(f'\n  (symbol "{sym}"') + 1
    d, j = 0, i
    while True:
        c = t[j]
        if c == '(':
            d += 1
        elif c == ')':
            d -= 1
            if d == 0:
                break
        j += 1
    return t[i:j + 1]

libcache = {}
def libsym(lib_id):
    if lib_id not in libcache:
        lib, sym = lib_id.split(":")
        if lib == "nodo503":
            body = CUSTOM_SYMS[sym](sym)
        else:
            body = extract(lib, sym)
            m = re.search(r'\(extends "([^"]+)"\)', body[:400])
            if m:   # flatten derived symbol: base graphics/pins, renamed
                base = m.group(1)
                bb = extract(lib, base)
                body = bb.replace(f'(symbol "{base}"', f'(symbol "{sym}"', 1).replace(f'(symbol "{base}_', f'(symbol "{sym}_')
        body = body.replace(f'(symbol "{sym}"', f'(symbol "{lib_id}"', 1)
        pins = {}
        for m in re.finditer(r'\(pin (\w+) \w+\s*\(at ([-\d. ]+)\).*?\(number "([^"]*)"', body, re.S):
            x, y, a = m.group(2).split()
            pins.setdefault(m.group(3), (float(x), float(y), int(float(a))))
        libcache[lib_id] = (body, pins)
    return libcache[lib_id]

# ------------------------------------------------------------------ schematic
out = []
def eff(just=None, hide=False, size=1.27):
    j = f" (justify {just})" if just else ""
    h = " hide" if hide else ""
    return f"(effects (font (size {size} {size})){j}{h})"

def label(net, x, y, ang):
    just = "left bottom" if ang in (0, 90) else "right bottom"
    out.append(f'(label "{net}" (at {x:.2f} {y:.2f} {ang}) (fields_autoplaced) {eff(just)} (uuid {U()}))')

def place(ref, lib_id, value, fp, pinnets, x, y, extra_props=()):
    body, lpins = libsym(lib_id)
    is_pwr = ref.startswith("#")
    pin_uuids = " ".join(f'(pin "{p}" (uuid {U()}))' for p in lpins)
    xs = [p[0] for p in lpins.values()]; ys = [p[1] for p in lpins.values()]
    if all(abs(v) < 0.01 for v in xs) and len(lpins) == 2:     # vertical 2-pin part
        rp, vp, j = (x + 2.54, y - 1.27), (x + 2.54, y + 1.27), "left"
    else:
        top, bot = y - max(ys + [2.54]) - 1.27, y - min(ys + [-2.54]) + 1.27
        rp, vp, j = (x + 3.81, top - 1.27), (x + 3.81, bot + 2.54), "left"
    props = [
        f'(property "Reference" "{ref}" (at {rp[0]:.2f} {rp[1]:.2f} 0) {eff(j, hide=is_pwr)})',
        f'(property "Value" "{value}" (at {vp[0]:.2f} {vp[1]:.2f} 0) {eff(j)})',
        f'(property "Footprint" "{fp}" (at {x:.2f} {y:.2f} 0) {eff(hide=True)})',
        f'(property "Datasheet" "" (at {x:.2f} {y:.2f} 0) {eff(hide=True)})',
    ]
    for k, v in extra_props:
        props.append(f'(property "{k}" "{v}" (at {x:.2f} {y:.2f} 0) {eff(hide=True)})')
    out.append(f'''(symbol (lib_id "{lib_id}") (at {x:.2f} {y:.2f} 0) (unit 1)
    (in_bom {"no" if is_pwr else "yes"}) (on_board {"no" if is_pwr else "yes"}) (dnp no)
    (uuid {COMP_UUID.setdefault(ref, U())})
    {" ".join(props)}
    {pin_uuids}
    (instances (project "{PROJECT}" (path "/{ROOT_UUID}" (reference "{ref}") (unit 1)))))''')
    for p, (px, py, pa) in lpins.items():
        ex, ey = x + px, y - py
        net = pinnets.get(p, "__nc__")
        if net is None or net == "__nc__":
            out.append(f'(no_connect (at {ex:.2f} {ey:.2f}) (uuid {U()}))')
        else:
            label(net, ex, ey, (pa + 180) % 360)

# symbol UUIDs link schematic and PCB footprints: keep the existing ones, add new refs, drop removed ones
_path = f"{ROOT}/.comp_uuid.json"
_old = json.load(open(_path)) if os.path.exists(_path) else {}
COMP_UUID = {r: u for r, u in _old.items() if r in COMP or r.startswith("#FLG")}
for _r in list(COMP) + [f[0] for f in FLAGS]:
    COMP_UUID.setdefault(_r, str(uuid.uuid5(_NS, "comp-" + _r)))
for ref, c in COMP.items():
    x, y = c["sch"]
    extra = [("MPN", c["mpn"])] + ([("LCSC", c["lcsc"])] if c["lcsc"] else [])
    place(ref, c["lib"], c["value"], c["fp"], c["pins"], x, y, extra)
for ref, net, (x, y) in FLAGS:
    place(ref, "power:PWR_FLAG", "PWR_FLAG", "", {"1": net}, x, y)
for txt, (x, y) in SCH_TEXT:
    out.append(f'(text "{txt}" (at {x:.2f} {y:.2f} 0) {eff("left bottom", size=1.8)} (uuid {U()}))')

libs = "\n".join(libsym(l)[0] for l in sorted({c["lib"] for c in COMP.values()} | {"power:PWR_FLAG"}))
sch = f'''(kicad_sch (version 20230121) (generator eeschema)
  (uuid {ROOT_UUID})
  (paper "A3")
  (title_block (title "Nodo CAN 503 - ESP32-C6-WROOM-1") (date "2026-10-14") (rev "C") (company "Fienile - domotica CAN")
    (comment 1 "24 V -> K7805 5 V -> AP2112K 3,3 V; TJA1051T/3; 6 pulsanti; Qwiic; prog. USB su pettine"))
  (lib_symbols
{libs}
  )
{chr(10).join(out)}
  (sheet_instances (path "/" (page "1")))
)
'''
open(f"{ROOT}/{PROJECT}.kicad_sch", "w").write(sch)
json.dump(COMP_UUID, open(f"{ROOT}/.comp_uuid.json", "w"))
print("schematic written,", len(COMP), "components")
