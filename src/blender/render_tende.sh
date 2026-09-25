#!/bin/zsh
# Render della sezione "Tende zip" della galleria (src/render/render.html): 21 giugno, sole basso da
# ovest-nordovest che entra sotto il portico; telo avorio; entrambi i colori del Cotto Milano; senza divano, come il resto della galleria.
# Uso, dalla radice del repo:  zsh src/blender/render_tende.sh [cartella_png] [altre opzioni di Blender]
# Poi:                         zsh src/render/aggiorna_render.sh render/tende
set -e -o pipefail
DIR=${0:A:h}                                 # fuori da r(): dentro una funzione $0 è il suo nome
OUT=${1:-render/tende}; shift $(( $# > 0 ? 1 : 0 ))
BLENDER=${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}
r() { $BLENDER -b -P $DIR/fienile_pt_render.py -- --out $OUT --gpu --preset terracotta --preset creta \
        --data 2026-06-21 --colore-tende avorio --no-sofa "$@" | grep -E '^(SOLE|RENDER)' }

# controluce in soggiorno alle 19: tende alzate, poi giù con i tre teli
r --camera controluce --scene giorno --ora 19 --tende 100 "$@"
for telo in 5 10 15; do r --camera controluce --scene giorno --ora 19 --tende 0 --telo $telo "$@"; done
# dettaglio dell'incasso dal portico, tende a metà, luce radente
r --camera incasso --scene giorno --ora 18.5 --tende 50 "$@"
# ora blu, luci accese, tende giù: i teli fanno da lanterne
r --camera portico --scene sera --ora-sera 21.15 --exposure 1.2 --tende 0 "$@"
