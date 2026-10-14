"""Placement sanity check: courtyard overlaps and parts outside the board. Run from hardware/ after gen_pcb.py."""
import itertools, pcbnew
from design import W, H, OX, OY

b = pcbnew.LoadBoard("nodo503.kicad_pcb")
fps = list(b.GetFootprints())
bad = 0
for a, c in itertools.combinations(fps, 2):
    A, C = a.GetCourtyard(pcbnew.F_CrtYd), c.GetCourtyard(pcbnew.F_CrtYd)
    if A.OutlineCount() and C.OutlineCount() and A.Collide(C, 0):
        print("overlap", a.GetReference(), c.GetReference()); bad += 1
for fp in fps:
    cy = fp.GetCourtyard(pcbnew.F_CrtYd)
    bb = cy.BBox() if cy.OutlineCount() else fp.GetBoundingBox()
    x0, x1 = pcbnew.ToMM(bb.GetX()) - OX, pcbnew.ToMM(bb.GetRight()) - OX
    y0, y1 = pcbnew.ToMM(bb.GetY()) - OY, pcbnew.ToMM(bb.GetBottom()) - OY
    if x0 < -0.2 or y0 < -0.2 or x1 > W + 0.01 or y1 > H + 0.01:   # antenna keep-out may touch the edge
        print("outside", fp.GetReference(), round(x0, 2), round(y0, 2), round(x1, 2), round(y1, 2)); bad += 1
print("problems", bad)
