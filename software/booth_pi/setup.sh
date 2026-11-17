#!/usr/bin/env bash
# One-time setup of the SO-101 booth on a Raspberry Pi (64-bit Raspberry Pi OS, Pi 4 or 5).
# Installs LeRobot 0.7.0 in ~/lerobot-venv, puts booth.sh in ~/booth and a booth.service that
# starts the replay loop at boot (enabled only when you ask, after the recordings are copied).
#
#   curl -fsSL https://raw.githubusercontent.com/anasshawish0-glitch/delta/refs/heads/claude/swaili-3d-thickness-ef5jeh/software/booth_pi/setup.sh | bash
set -euo pipefail
RAW="https://raw.githubusercontent.com/anasshawish0-glitch/delta/refs/heads/claude/swaili-3d-thickness-ef5jeh/software/booth_pi"
VENV="$HOME/lerobot-venv"
BOOTH="$HOME/booth"

echo "== 1/5 Checking the Pi"
if [ "$(uname -m)" != "aarch64" ]; then
  echo "This needs the 64-bit Raspberry Pi OS (uname -m should say aarch64, this one says $(uname -m))."
  exit 1
fi

echo "== 2/5 uv and Python 3.12"
if ! command -v uv >/dev/null 2>&1 && [ ! -x "$HOME/.local/bin/uv" ]; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
UV="$(command -v uv || echo "$HOME/.local/bin/uv")"
[ -x "$VENV/bin/python" ] || "$UV" venv -p 3.12 "$VENV"

echo "== 3/5 LeRobot 0.7.0 (this is the long part)"
"$UV" pip install --python "$VENV/bin/python" "lerobot[feetech,dataset]==0.7.0"

echo "== 4/5 Booth files in $BOOTH"
mkdir -p "$BOOTH"
curl -fsSL "$RAW/booth.sh" -o "$BOOTH/booth.sh"
chmod +x "$BOOTH/booth.sh"
[ -f "$BOOTH/booth.conf" ] || curl -fsSL "$RAW/booth.conf" -o "$BOOTH/booth.conf"
sudo usermod -aG dialout "$USER"

echo "== 5/5 Start at boot (booth.service)"
sudo tee /etc/systemd/system/booth.service >/dev/null <<UNIT
[Unit]
Description=SO-101 booth replay loop
After=multi-user.target

[Service]
User=$USER
Environment=HF_HUB_OFFLINE=1
ExecStart=$BOOTH/booth.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
UNIT
sudo systemctl daemon-reload

echo
echo "Done."
echo "Next: put the folder 'lerobot' on a USB stick in the Pi and run:  ~/booth/booth.sh import"
echo "Try one round:                                                   ~/booth/booth.sh once"
echo "Then start it at every boot:                                     sudo systemctl enable --now booth"
