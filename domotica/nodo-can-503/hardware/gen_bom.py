import csv, collections, json, os, pcbnew
THT_JLC = {"J1", "J2", "U1"}
DNP = {"J4"}
SMD_EXCL = THT_JLC | DNP   # excluded from BOM_SMD / CPL_SMD
LIB = json.load(open("jlc_library.json")) if os.path.exists("jlc_library.json") else {}
from design import *
b = pcbnew.LoadBoard("nodo503.kicad_pcb")
groups = collections.OrderedDict()
for ref in sorted(COMP, key=lambda r: (r.rstrip("0123456789"), int(''.join(c for c in r if c.isdigit())))):
    c = COMP[ref]
    if ref.startswith("JP"):
        continue
    k = (c["value"], c["fp"], c["mpn"], c["lcsc"])
    groups.setdefault(k, []).append(ref)
with open("out/BOM.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Comment", "Designator", "Footprint", "Quantita", "Descrizione / MPN", "LCSC", "Libreria JLCPCB"])
    for (val, fp, mpn, lcsc), refs in groups.items():
        lib = LIB.get(lcsc, "")
        if refs[0] in DNP: lib = "non montato (DNP)"
        elif not lcsc: lib = "codice da assegnare"
        elif refs[0] in THT_JLC: lib += " - THT (saldatura a onda/manuale JLCPCB)"
        w.writerow([val, ",".join(refs), fp.split(":")[1], len(refs), mpn, lcsc, lib])
tht = DNP
with open("out/CPL_JLCPCB.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
    for fp in sorted(b.GetFootprints(), key=lambda x: x.GetReference()):
        r = fp.GetReference()
        if r in tht or r.startswith("JP") or fp.GetAttributes() & pcbnew.FP_EXCLUDE_FROM_POS_FILES:
            continue
        p = fp.GetPosition()
        if r in THT_JLC:   # THT footprints have the origin on pin 1: use the centre of the pads
            xs = [pd.GetPosition().x for pd in fp.Pads()]; ys = [pd.GetPosition().y for pd in fp.Pads()]
            p = pcbnew.VECTOR2I(int((min(xs) + max(xs)) / 2), int((min(ys) + max(ys)) / 2))
        w.writerow([r, f"{pcbnew.ToMM(p.x) - OX:.3f}mm", f"{OY + H - pcbnew.ToMM(p.y):.3f}mm", "Top",
                    f"{fp.GetOrientationDegrees() % 360:.0f}"])
# SMD-only BOM/CPL (THT parts and DNP excluded)
rows = list(csv.reader(open("out/BOM.csv")))
csv.writer(open("out/BOM_SMD.csv", "w", newline="")).writerows(
    [rows[0]] + [r for r in rows[1:] if not set(r[1].split(",")) & SMD_EXCL])
cpl = list(csv.reader(open("out/CPL_JLCPCB.csv")))
csv.writer(open("out/CPL_SMD.csv", "w", newline="")).writerows(
    [cpl[0]] + [r for r in cpl[1:] if r[0] not in SMD_EXCL])
print("ok")
