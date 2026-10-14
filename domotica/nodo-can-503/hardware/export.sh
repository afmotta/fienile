#!/bin/bash
# Production outputs: schematic/PCB parity check, Gerber + drill, BOM/CPL, PDF schematic, previews.
set -e
cd "$(dirname "$0")"
kicad-cli sch export netlist -o nodo503.net nodo503.kicad_sch >/dev/null 2>&1
python3 - <<'PY' 2>&1 | grep -v swig
import pcbnew, re
b=pcbnew.LoadBoard("nodo503.kicad_pcb")
t=open("nodo503.net").read(); sch={}
for m in re.finditer(r'\(net \(code "\d+"\) \(name "([^"]*)"\)(.*?)\)\s*(?=\(net |\)\s*\)\s*$)',t,re.S):
    for r,p in re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"',m.group(2)): sch[(r,p)]=m.group(1).lstrip("/")
bad=0
for fp in b.GetFootprints():
    for pd in fp.Pads():
        k=(fp.GetReference(),pd.GetNumber()); n=pd.GetNetname(); s=sch.get(k)
        if pd.GetNumber() in ("MP",""): continue
        if (s and not s.startswith("unconnected") and s!=n) or ((not s or s.startswith("unconnected")) and n): bad+=1
print("parita schema/PCB, discrepanze:", bad)
PY
rm -rf out/gerber && mkdir -p out/gerber
kicad-cli pcb export gerbers --layers F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts -o out/gerber/ nodo503.kicad_pcb >/dev/null 2>&1
kicad-cli pcb export drill --format excellon --drill-origin absolute --excellon-units mm -o out/gerber/ nodo503.kicad_pcb >/dev/null 2>&1
rm -f out/gerber_JLCPCB.zip; (cd out/gerber && zip -q ../gerber_JLCPCB.zip *)
python3 gen_bom.py 2>&1 | grep -v swig
kicad-cli sch export pdf -o out/nodo503_schema.pdf nodo503.kicad_sch >/dev/null 2>&1
for L in F B; do kicad-cli pcb export svg --layers $L.Cu,$L.SilkS,Edge_Cuts --page-size-mode 2 --exclude-drawing-sheet $( [ $L = B ] && echo --mirror ) -o out/_$L.svg nodo503.kicad_pcb >/dev/null 2>&1; done
python3 -c "
import cairosvg
cairosvg.svg2png(url='out/_F.svg', write_to='out/anteprima_lato_top.png', output_width=1400, background_color='white')
cairosvg.svg2png(url='out/_B.svg', write_to='out/anteprima_lato_bottom.png', output_width=1400, background_color='white')"
rm -f out/_F.svg out/_B.svg nodo503.net
echo "esportazione completata"
