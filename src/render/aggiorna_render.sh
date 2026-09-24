#!/bin/zsh
# Copia i render di Blender (PNG in ./render, vedi src/blender/fienile_pt_render.py) nella galleria del sito:
# JPEG 1920 px in src/render/img e miniature 640 px in src/render/img/mini, senza la variante nel nome.
# Uso, dalla radice del repo:  zsh src/render/aggiorna_render.sh [cartella_png]
set -e
SRC=${1:-render}
DST=${0:A:h}/img
mkdir -p $DST/mini
for f in $SRC/*__PT-*__*__*.png; do
  n=${f:t:r}                                   # vista__PT-E__colore__scena
  out=$(print -r -- $n | sed -E 's/__PT-[^_]+__/__/').jpg   # vista__colore__scena.jpg
  sips -s format jpeg -s formatOptions 82 $f --out $DST/$out >/dev/null
  sips -Z 640 -s format jpeg -s formatOptions 78 $f --out $DST/mini/$out >/dev/null
  echo $out
done
