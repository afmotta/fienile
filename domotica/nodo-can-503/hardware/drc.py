import pcbnew, re, collections
b = pcbnew.LoadBoard("nodo503.kicad_pcb")
pcbnew.WriteDRCReport(b, "drc.rpt", pcbnew.EDA_UNITS_MILLIMETRES, True)
t = open("drc.rpt").read()
print(collections.Counter(re.findall(r'^\[(\w+)\]', t, re.M)))
for m in re.findall(r'\*\* Found .*', t): print(m)
