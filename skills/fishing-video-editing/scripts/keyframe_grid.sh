#!/bin/bash
# keyframe_grid.sh SRC.MP4 OUTDIR t1 t2 [t3 ...]
# Tiles 2-up frames (each 960x540) with a yellow grid every 80 px (= 160 px of 1920-space) and the
# source time stamped in the corner. Read tracker keyframe boxes [t, x, y, w, h] off it:
# x/y in a tile × 2 = 1920x1080 coordinates (what fishtrack2.py and build_edit.py use), whatever
# the source resolution. Needs at least 2 times. Output: OUTDIR/grid_<SRC>_<t1>.jpg
set -e
SRC=$1; OUT=$2; shift 2
[ $# -lt 2 ] && { echo "need at least two times"; exit 1; }
mkdir -p "$OUT"
ins=(); f=""; st=""; n=0
for t in "$@"; do ins+=(-ss "$t" -i "$SRC"); n=$((n+1)); done
i=0
for t in "$@"; do
  f+="[$i:v]scale=960:540,drawgrid=w=80:h=80:t=1:c=yellow@0.5,drawtext=text='$t':x=6:y=6:fontsize=22:fontcolor=white:box=1:boxcolor=black[v$i];"
  st+="[v$i]"; i=$((i+1))
done
layout=$(python3 -c "n=$n; print('|'.join(f'{(i%2)*960}_{(i//2)*540}' for i in range(n)))")
dst="$OUT/grid_$(basename "$SRC" | sed 's/\.[^.]*$//')_$1.jpg"
ffmpeg -v error -y "${ins[@]}" -filter_complex "${f}${st}xstack=inputs=$n:layout=$layout:fill=black" -frames:v 1 "$dst"
echo "$dst"
