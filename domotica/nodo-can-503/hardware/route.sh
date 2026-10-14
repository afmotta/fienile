#!/bin/bash
# Full re-route: placement -> Specctra DSN -> Freerouting 1.9 -> SES import + pours -> DRC
set -e
cd "$(dirname "$0")"
python3 gen_pcb.py 2>&1 | grep -v swig
python3 -c "import pcbnew; b=pcbnew.LoadBoard('nodo503.kicad_pcb'); print('dsn', pcbnew.ExportSpecctraDSN(b, 'nodo503.dsn'))" 2>&1 | grep -v swig
mkdir -p logs
timeout ${FR_TIMEOUT:-560} xvfb-run -a java -jar ${FREEROUTING:-../tools/freerouting-1.9.0.jar} -de nodo503.dsn -do nodo503.ses -mp ${FR_PASSES:-100} > logs/freerouting.log 2>&1 || true
grep -E "completed|unrouted|Saving" logs/freerouting.log | tail -5
python3 route_import.py nodo503.ses 2>&1 | grep -v swig
python3 drc.py 2>&1 | grep -v swig
