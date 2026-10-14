"""Import a Freerouting .ses into the board, add GND pours, refill zones."""
import re, sys, pcbnew
from design import *

MM = pcbnew.FromMM
pcbnew.KIID.SeedGenerator(504)   # deterministic UUIDs -> reproducible .kicad_pcb
ses = sys.argv[1] if len(sys.argv) > 1 else "nodo503.ses"
b = pcbnew.LoadBoard("nodo503.kicad_pcb")

def tokenize(s):
    return re.findall(r'\(|\)|"[^"]*"|[^\s()]+', s)
def parse(tokens):
    stack = [[]]
    for t in tokens:
        if t == '(':
            stack.append([])
        elif t == ')':
            x = stack.pop(); stack[-1].append(x)
        else:
            stack[-1].append(t.strip('"'))
    return stack[0][0]

tree = parse(tokenize(open(ses).read()))
def find(node, key):
    for c in node:
        if isinstance(c, list) and c and c[0] == key:
            yield c
routes = next(find(tree, "routes"))
res = next(find(routes, "resolution"))
scale = {"um": 1e-3, "mm": 1.0, "mil": 0.0254}[res[1]] / float(res[2])   # -> mm
def pt(x, y): return pcbnew.VECTOR2I(MM(float(x) * scale), MM(-float(y) * scale))
layers = {"F.Cu": pcbnew.F_Cu, "B.Cu": pcbnew.B_Cu}
ntr = nvia = 0
for net in find(next(find(routes, "network_out")), "net"):
    ni = b.FindNet(net[1])
    for w in find(net, "wire"):
        p = next(find(w, "path"))
        layer, width, coords = p[1], float(p[2]) * scale, p[3:]
        pts = [pt(coords[i], coords[i + 1]) for i in range(0, len(coords), 2)]
        for a, c in zip(pts, pts[1:]):
            if a == c:
                continue
            t = pcbnew.PCB_TRACK(b); t.SetStart(a); t.SetEnd(c); t.SetWidth(MM(width))
            t.SetLayer(layers[layer]); t.SetNet(ni); b.Add(t); ntr += 1
    for v in find(net, "via"):
        m = re.search(r'_(\d+):(\d+)_um', v[1])
        d, dr = (int(m.group(1)) / 1000, int(m.group(2)) / 1000) if m else (0.6, 0.3)
        via = pcbnew.PCB_VIA(b); via.SetPosition(pt(v[2], v[3])); via.SetWidth(MM(d)); via.SetDrill(MM(dr))
        via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); via.SetNet(ni); b.Add(via); nvia += 1

# drop vias duplicated by the router's echo of fixed wiring
_vs = set()
for v in [x for x in b.GetTracks() if x.GetClass() == "PCB_VIA"]:
    k = (v.GetPosition().x, v.GetPosition().y)
    if k in _vs:
        b.Remove(v)
    _vs.add(k)
# remove duplicate segments and dangling stubs left by the router
seen = set()
for t in list(b.GetTracks()):
    if t.GetClass() != "PCB_TRACK":
        continue
    k = (t.GetLayer(), t.GetNetCode(), *sorted([(t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)]))
    if k in seen:
        b.Remove(t)
    seen.add(k)
def dangling_tracks():
    tracks = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
    vias = [(v.GetPosition(), v.GetNetCode()) for v in b.GetTracks() if t_is_via(v)]
    pads = [p for fp in b.GetFootprints() for p in fp.Pads()]
    ends = {}
    for t in tracks:
        for p in (t.GetStart(), t.GetEnd()):
            k = (t.GetLayer(), p.x, p.y)
            ends[k] = ends.get(k, 0) + 1
    out = []
    for t in tracks:
        for p in (t.GetStart(), t.GetEnd()):
            if ends[(t.GetLayer(), p.x, p.y)] > 1:
                continue
            if any(vp.x == p.x and vp.y == p.y for vp, nc in vias):
                continue
            if any(pd.GetNetCode() == t.GetNetCode() and pd.IsOnLayer(t.GetLayer()) and pd.HitTest(p) for pd in pads):
                continue
            if any(o is not t and o.GetNetCode() == t.GetNetCode() and o.GetLayer() == t.GetLayer() and o.HitTest(p, 0)
                   for o in tracks):
                continue
            out.append(t); break
    return out
def t_is_via(x): return x.GetClass() == "PCB_VIA"
while True:
    d = dangling_tracks()
    if not d:
        break
    for t in d:
        b.Remove(t)
    print("removed dangling", len(d))
# vias that connect to nothing on one side are harmless; drop vias with no track at all
for v in [x for x in b.GetTracks() if t_is_via(x)]:
    p = v.GetPosition()
    if not any(t.GetClass() == "PCB_TRACK" and (t.GetStart() == p or t.GetEnd() == p) for t in b.GetTracks()):
        b.Remove(v); print("removed orphan via")

import cleanup
cleanup.run(b)

for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(b.FindNet("GND"))
    z.SetZoneName("GND"); z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_NEVER); z.SetLocalClearance(MM(0.3)); z.SetMinThickness(MM(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(MM(0.3)); z.SetThermalReliefSpokeWidth(MM(0.4))
    o = z.Outline(); o.NewOutline()
    for x, y in [(0, 0), (W, 0), (W, H), (0, H)]:
        o.Append(MM(OX + x), MM(OY + y))
    b.Add(z)
b.BuildConnectivity()
pcbnew.ZONE_FILLER(b).Fill(b.Zones())

# GND stitching vias wherever both pours fully cover a via (+margin)
import math
gz = [b.GetArea(i) for i in range(b.GetAreaCount())]
gz = [z for z in gz if hasattr(z, "GetNetname") and z.GetNetname() == "GND"]
def covered(x, y):
    for z in gz:
        lay = z.GetLayer()
        for k in range(8):
            a = k * math.pi / 4
            p = pcbnew.VECTOR2I(int(x + MM(0.75) * math.cos(a)), int(y + MM(0.75) * math.sin(a)))
            if not z.HitTestFilledArea(lay, p):
                return False
        if not z.HitTestFilledArea(lay, pcbnew.VECTOR2I(int(x), int(y))):
            return False
    return True
def near_hole(x, y):
    return any(math.hypot(pcbnew.ToMM(x) - OX - hx, pcbnew.ToMM(y) - OY - hy) < HOLE_KEEPOUT_R + 0.5 for hx, hy in HOLES)
nst = 0
placed = []
step = 2.0
yy = 1.5
while yy < H - 1.0:
    xx = 1.5
    while xx < W - 1.0:
        x, y = MM(OX + xx), MM(OY + yy)
        exist = [(t.GetPosition().x, t.GetPosition().y) for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
        exist += [(p.GetPosition().x, p.GetPosition().y) for f in b.GetFootprints() for p in f.Pads()
                  if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and math.hypot(p.GetPosition().x - x, p.GetPosition().y - y) < MM(2.5)]
        if covered(x, y) and not near_hole(x, y) and all(math.hypot(x - px, y - py) > MM(3.0) for px, py in placed) \
                and all(math.hypot(x - px, y - py) > MM(2.2) for px, py in exist):
            v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(x, y)); v.SetWidth(MM(0.6)); v.SetDrill(MM(0.3))
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(b.FindNet("GND")); b.Add(v)
            placed.append((x, y)); nst += 1
        xx += step
    yy += step
print("stitching vias", nst)
for z in gz:
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
b.BuildConnectivity()
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
# make sure every pour island is tied to the other layer
tht = [p.GetPosition() for fp in b.GetFootprints() for p in fp.Pads()
       if p.GetNetname() == "GND" and p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
for z in gz:
    lay = z.GetLayer(); fp = z.GetFilledPolysList(lay)
    for k in range(fp.OutlineCount()):
        o = fp.Outline(k)
        anchors = placed + [(p.x, p.y) for p in tht]
        anchors += [(t.GetPosition().x, t.GetPosition().y) for t in b.GetTracks() if t.GetClass() == "PCB_VIA" and t.GetNetname() == "GND"]
        if any(o.PointInside(pcbnew.VECTOR2I(int(x), int(y))) for x, y in anchors):
            continue
        bb = o.BBox(); done = False
        y = bb.GetY()
        while y < bb.GetBottom() and not done:
            x = bb.GetX()
            while x < bb.GetRight():
                if o.PointInside(pcbnew.VECTOR2I(x, y)) and covered(x, y) and not near_hole(x, y):
                    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(x, y)); v.SetWidth(MM(0.6)); v.SetDrill(MM(0.3))
                    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(b.FindNet("GND")); b.Add(v)
                    placed.append((x, y)); done = True; print("island via at", pcbnew.ToMM(x) - OX, pcbnew.ToMM(y) - OY)
                    break
                x += MM(0.2)
            y += MM(0.2)
        if not done:
            print("WARNING: could not tie island", b.GetLayerName(lay), k)
b.BuildConnectivity()
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard("nodo503.kicad_pcb", b)
print(f"tracks {ntr} vias {nvia}")
