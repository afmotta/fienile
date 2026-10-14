"""Routing metrics: track length per layer, vias, GND pour coverage, length of the main nets. Run from hardware/."""
import collections, pcbnew
from design import W, H

b = pcbnew.LoadBoard("nodo503.kicad_pcb")
tr = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
vi = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
L = lambda lay: sum(t.GetLength() for t in tr if t.GetLayer() == lay) / 1e6
print(f"board {W}x{H} mm, tracks F.Cu {L(pcbnew.F_Cu):.0f} mm, B.Cu {L(pcbnew.B_Cu):.0f} mm, "
      f"vias {len(vi)} (signal {sum(v.GetNetname() != 'GND' for v in vi)})")
for i in range(b.GetAreaCount()):
    z = b.GetArea(i)
    if z.GetIsRuleArea():
        continue
    a = z.GetFilledPolysList(z.GetLayer()).Area() / 1e12
    print(f"GND pour {b.GetLayerName(z.GetLayer())}: {a:.0f} mm2 ({100 * a / (W * H):.0f}%)")
nl = collections.Counter()
for t in tr:
    nl[t.GetNetname()] += t.GetLength() / 1e6
print(", ".join(f"{n}={l:.0f}" for n, l in sorted(nl.items()) if n != "GND"))
