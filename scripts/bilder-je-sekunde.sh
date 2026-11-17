#!/bin/bash
# Zählt verschiedene Bilder je voller Sekunde eines Videos (ffmpeg mpdecimate, Zeilen „keep pts“).
# Aufruf: scripts/bilder-je-sekunde.sh clip.mp4   → je Zeile „Sekunde  verschiedene Bilder“
set -euo pipefail
FFMPEG=$(command -v ffmpeg || echo /opt/homebrew/bin/ffmpeg)
"$FFMPEG" -hide_banner -nostats -loglevel debug -i "$1" -vf mpdecimate -f null - 2>&1 \
  | awk '/keep pts:/ { for (i=1;i<=NF;i++) if ($i ~ /^pts_time:/) { sub("pts_time:","",$i); s=int($i+1e-6) } n[s]++; if (s>m) m=s }
     END { for (s=0;s<=m;s++) printf "%2d  %d\n", s, n[s]+0 }'
