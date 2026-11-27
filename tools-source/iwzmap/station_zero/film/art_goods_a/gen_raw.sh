#!/bin/sh
# generate the wordless art of the sleeves and tape boxes (4 at a time); words are added by make_goods_pictures.py
D=$(dirname "$0")/prompts
OUT=${1:-/c/studio-data/sz/film/art/arcade/goods_a/raw}
mkdir -p "$OUT"
run(){ n=$(basename "$1" .txt); [ -f "$OUT/$n.png" ] && return; python ~/.claude/skills/imagegen/scripts/codex_imagegen.py --prompt-file "$1" --out "$OUT/$n.png" > "$OUT/$n.json" 2>&1; echo "$n $?"; }
i=0
for f in "$D"/*.txt; do run "$f" & i=$((i+1)); [ $((i % 4)) -eq 0 ] && wait; done
wait
