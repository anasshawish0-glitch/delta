#!/usr/bin/env bash
# SO-101 booth: replays the recordings listed in booth.conf, one after another, forever.
# booth.service starts it at boot.
#   booth.sh          loop forever
#   booth.sh once     one round, then stop
#   booth.sh import   copy the recordings and the calibration from a USB stick
#                     (the stick holds the folder "lerobot" copied from
#                     C:\Users\<you>\.cache\huggingface\lerobot on the laptop)
DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=/dev/null
source "$DIR/booth.conf"
LR="$HOME/.cache/huggingface/lerobot"
export HF_HUB_OFFLINE=1
export PATH="$HOME/lerobot-venv/bin:$PATH"

find_port() {
  if [ "$PORT" != "auto" ]; then echo "$PORT"; return; fi
  local p
  for p in /dev/serial/by-id/*; do
    [ -e "$p" ] || continue
    case "$p" in *[Aa]rduino*) continue ;; esac
    echo "$p"; return
  done
  for p in /dev/ttyACM* /dev/ttyUSB*; do
    [ -e "$p" ] && { echo "$p"; return; }
  done
}

import_usb() {
  local src=""
  for d in /media/"$USER"/*/lerobot /media/*/lerobot /mnt/*/lerobot; do
    [ -d "$d" ] && { src="$d"; break; }
  done
  if [ -z "$src" ]; then echo "No folder 'lerobot' found on a USB stick (looked in /media and /mnt)."; exit 1; fi
  mkdir -p "$LR"
  for sub in local calibration; do
    if [ -d "$src/$sub" ]; then cp -r "$src/$sub" "$LR/"; echo "Copied $sub from $src"; fi
  done
  echo "Recordings now on the Pi:"; ls "$LR/local" 2>/dev/null
  [ -f "$LR/calibration/robots/so_follower/$ROBOT_ID.json" ] && echo "Calibration: $ROBOT_ID.json OK" \
    || echo "WARNING: calibration/robots/so_follower/$ROBOT_ID.json is missing"
}

play() {   # play <recording name>; returns non-zero when the replay failed
  local port; port="$(find_port)"
  if [ -z "$port" ]; then echo "$(date +%T) no arm on USB"; return 1; fi
  echo "$(date +%T) playing $1 on $port"
  lerobot-replay --robot.type=so101_follower --robot.port="$port" --robot.id="$ROBOT_ID" \
    --robot.max_relative_target=10 --dataset.repo_id="local/$1" --dataset.episode=0 --play_sounds=false
}

run() {   # run once|loop. A step that fails is tried again (it never skips ahead or starts over),
          # so the blocks are never put where the last step already put some.
  local steps=($STEPS) i=0 name pause
  while true; do
    name="${steps[$i]%%:*}"; pause="${steps[$i]##*:}"
    if play "$name"; then
      sleep "$pause"
      i=$(( (i + 1) % ${#steps[@]} ))
      [ "$1" = once ] && [ "$i" -eq 0 ] && return 0
    else
      echo "$(date +%T) $name failed (arm power off or unplugged?), trying $name again in 15 s"
      sleep 15
    fi
  done
}

case "${1:-loop}" in
  import) import_usb ;;
  once)   run once ;;
  loop)   run loop ;;
  *)      echo "usage: booth.sh [loop|once|import]"; exit 1 ;;
esac
