#!/bin/zsh
# Render della sezione "Persiane" della galleria (src/render/render.html): terrazzo del primo piano, 21 giugno
# alle 19 (sole basso da ovest-nordovest, come le tende zip); entrambi i colori del Cotto Milano, che è anche
# il pavimento del terrazzo; senza divano, come il resto della galleria.
# Uso, dalla radice del repo:  zsh src/blender/render_persiane.sh [cartella_png] [altre opzioni di Blender]
# Poi:                         zsh src/render/aggiorna_render.sh render/persiane
set -e -o pipefail
DIR=${0:A:h}                                 # fuori da r(): dentro una funzione $0 è il suo nome
OUT=${1:-render/persiane}; shift $(( $# > 0 ? 1 : 0 ))
BLENDER=${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}
r() { $BLENDER -b -P $DIR/fienile_pt_render.py -- --out $OUT --gpu --preset terracotta --preset creta \
        --data 2026-06-21 --no-sofa "$@" | grep -E '^(SOLE|RENDER)' }

# dal terrazzo verso nord: persiane aperte contro la facciata, accostate (36°), chiuse
for ap in 100 20 0; do r --camera persiane --scene giorno --ora 19 --persiane $ap "$@"; done
