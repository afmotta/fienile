"""Place footprints for nodo503 (unrouted board)."""
import json, os, pcbnew
from design import *

ROOT = os.path.dirname(os.path.abspath(__file__))
FPROOT = os.environ.get("KICAD7_FOOTPRINT_DIR", "/usr/share/kicad/footprints")
MM = pcbnew.FromMM
pcbnew.KIID.SeedGenerator(503)   # deterministic UUIDs -> reproducible .kicad_pcb
def P(x, y): return pcbnew.VECTOR2I(int(round((OX + x) * 1000)) * 1000, int(round((OY + y) * 1000)) * 1000)

REF_POS = {"J1": (51.5, 14.6), "J2": (35.9, 37.3)}
comp_uuid = json.load(open(f"{ROOT}/.comp_uuid.json"))
path = f"{ROOT}/{PROJECT}.kicad_pcb"
if os.path.exists(path):
    os.remove(path)
board = pcbnew.NewBoard(path)

# nets
nets = {}
for c in COMP.values():
    for n in c["pins"].values():
        if n and n not in nets:
            ni = pcbnew.NETINFO_ITEM(board, n)
            board.Add(ni)
            nets[n] = ni

for ref, c in COMP.items():
    lib, name = c["fp"].split(":")
    libpath = f"{ROOT}/nodo503.pretty" if lib == "nodo503" else f"{FPROOT}/{lib}.pretty"
    fp = pcbnew.FootprintLoad(libpath, name)
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    fp.SetReference(ref)
    fp.SetValue(c["value"])
    fp.SetPath(pcbnew.KIID_PATH(f"/{comp_uuid[ref]}"))
    x, y, rot = c["pcb"]
    fp.SetPosition(P(x, y))
    fp.SetOrientationDegrees(rot)
    for pad in fp.Pads():
        if ref in SOLID_GND and c['pins'].get(pad.GetNumber()) == 'GND':
            pad.SetZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
        n = c["pins"].get(pad.GetNumber())
        if n:
            pad.SetNet(nets[n])
    r = fp.Reference()
    if (ref[0] in 'RC' and c['fp'].endswith('0402_1005Metric')):
        r.SetVisible(False)
    r.SetTextSize(pcbnew.VECTOR2I(MM(0.7), MM(0.7)))
    r.SetTextThickness(MM(0.12))
    if ref in REF_POS:      # keep the designator away from the pin legends
        rx, ry = REF_POS[ref]
        r.SetPosition(P(rx, ry)); r.SetTextAngleDegrees(-rot)   # FP text angle is relative to the footprint
    board.Add(fp)

# outline with rounded corners
R = 1.5
def seg(x1, y1, x2, y2):
    s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(P(x1, y1)); s.SetEnd(P(x2, y2)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.1)); board.Add(s)
def arc(cx, cy, sx, sy, ang):
    s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_ARC)
    s.SetCenter(P(cx, cy)); s.SetStart(P(sx, sy)); s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(ang, pcbnew.DEGREES_T))
    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.1)); board.Add(s)
seg(R, 0, W - R, 0); seg(W, R, W, H - R); seg(W - R, H, R, H); seg(0, H - R, 0, R)
arc(R, R, 0, R, 90); arc(W - R, R, W - R, 0, 90); arc(W - R, H - R, W, H - R, 90); arc(R, H - R, R, H, 90)

# antenna keep-out comes with the Espressif module footprint

# M3 mounting holes (NPTH, board-only) + no-track/no-via area under the screw head
import math
for k, (hx, hy) in enumerate(HOLES, 1):
    fp = pcbnew.FootprintLoad(f"{FPROOT}/MountingHole.pretty", "MountingHole_3.2mm_M3")
    fp.SetFPID(pcbnew.LIB_ID("MountingHole", "MountingHole_3.2mm_M3"))
    fp.SetReference(f"H{k}"); fp.SetValue("M3"); fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
    fp.SetAttributes(pcbnew.FP_BOARD_ONLY | pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_EXCLUDE_FROM_BOM)
    fp.SetPosition(P(hx, hy)); board.Add(fp)
    z = pcbnew.ZONE(board); z.SetIsRuleArea(True); ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu); z.SetLayerSet(ls)
    z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True); z.SetDoNotAllowPads(False)
    z.SetDoNotAllowCopperPour(False); z.SetDoNotAllowFootprints(False); z.SetZoneName(f"VITE_H{k}")
    o = z.Outline(); o.NewOutline()
    for a in range(0, 360, 15):
        o.Append(P(hx + HOLE_KEEPOUT_R * math.cos(math.radians(a)), hy + HOLE_KEEPOUT_R * math.sin(math.radians(a))))
    board.Add(z)

# silkscreen legends
def text(t, x, y, size=0.8, rot=0, layer=pcbnew.F_SilkS, mirror=False):
    tx = pcbnew.PCB_TEXT(board); tx.SetText(t); tx.SetPosition(P(x, y)); tx.SetLayer(layer)
    tx.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size))); tx.SetTextThickness(MM(size * 0.15))
    tx.SetTextAngleDegrees(rot)
    if mirror: tx.SetMirrored(True)
    board.Add(tx)
x0, y0, _ = COMP["J1"]["pcb"]
for k, t in enumerate(["24V", "GND", "H", "L"]):      # J1 on the right edge, top to bottom
    text(t, 46.5, y0 - 10.5 + 3.5 * k, 0.6)
for ref, names in (("J2", ["1", "2", "3", "4", "5", "6", "G"]),):
    x0, y0, _ = COMP[ref]["pcb"]
    for k, t in enumerate(names):
        text(t, x0 + 3.5 * k, y0 - 5.3, 0.6)
text("QWIIC", 44.7, 7.0, 0.6)
x0, y0, _ = COMP["J4"]["pcb"]
for k, t in enumerate(["5V", "D-", "D+", "G", "BT", "G"]):
    text(t, x0 + 2.4, y0 + 2.54 * k, 0.55)
text("NODO CAN 503", 41.0, 33.8, 1.0, layer=pcbnew.B_SilkS, mirror=True)
text("ESP32-C6 + TJA1051T/3", 41.0, 35.6, 0.7, layer=pcbnew.B_SilkS, mirror=True)
text("rev C - 56 x 41 mm", 41.0, 37.2, 0.7, layer=pcbnew.B_SilkS, mirror=True)

# pre-routed GND tie for the TJA1051 / C5 pocket (too tight for the pour to reach a via)
def trk(x1, y1, x2, y2, net, w=0.3, layer=pcbnew.F_Cu):
    t = pcbnew.PCB_TRACK(board); t.SetStart(P(x1, y1)); t.SetEnd(P(x2, y2)); t.SetWidth(MM(w))
    t.SetLayer(layer); t.SetNet(nets[net]); board.Add(t)
def via(x, y, net):
    v = pcbnew.PCB_VIA(board); v.SetPosition(P(x, y)); v.SetWidth(MM(0.6)); v.SetDrill(MM(0.3))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(nets[net]); board.Add(v)
for pre in PREROUTE:
    if pre[0] == "via":
        via(*pre[1:])
    elif pre[0] == "trkn":
        trk(*pre[1:], w=0.2)
    elif pre[0] == "trkb":
        trk(*pre[1:], w=0.25, layer=pcbnew.B_Cu)
    else:
        trk(*pre[1:])

pcbnew.SaveBoard(path, board)
print("saved", path)
