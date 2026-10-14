#!/bin/bash
# Toolchain for the nodo503 PCB pipeline (tested on Ubuntu 24.04, headless).
#   - KiCad 7.0.x with its Python module (pcbnew) and kicad-cli
#   - Freerouting 1.9.0 (Java) run under xvfb   -> tools/freerouting-1.9.0.jar
#   - cairosvg for the PNG previews
# Usage: sudo tools/setup.sh      (re-runnable)
set -e
cd "$(dirname "$0")"

if ! command -v kicad-cli >/dev/null || ! kicad-cli version | grep -q '^7\.'; then
    apt-get update
    # Ubuntu 24.04 ships KiCad 7.0.11 in universe. KiCad 8/9 also work for opening the
    # project, but the scripts use the KiCad 7 pcbnew API: keep 7.x for the pipeline.
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        kicad kicad-footprints kicad-symbols
fi
command -v xvfb-run >/dev/null || DEBIAN_FRONTEND=noninteractive apt-get install -y xvfb
command -v java >/dev/null || DEBIAN_FRONTEND=noninteractive apt-get install -y openjdk-21-jre-headless
python3 -c "import cairosvg" 2>/dev/null || pip install --break-system-packages cairosvg

JAR=freerouting-1.9.0.jar
SHA=9084a4888937a7f31f857ecc12aa7a37407f51160e4d2892dff9c9bb47ae3102
if [ ! -f "$JAR" ]; then
    curl -sSL -o "$JAR" "https://github.com/freerouting/freerouting/releases/download/v1.9.0/$JAR"
fi
echo "$SHA  $JAR" | sha256sum -c -

python3 -c "import pcbnew; print('pcbnew', pcbnew.Version())"
echo "toolchain ok"
