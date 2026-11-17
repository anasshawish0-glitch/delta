# SO-101 booth on a Raspberry Pi

Plays the house recordings with the white arm, one after another, forever, and starts by itself
when the Pi boots: plug in the arm power and the Pi, and it runs.

1. On a 64-bit Raspberry Pi OS (Pi 4 or 5), with internet, run once:

       curl -fsSL https://raw.githubusercontent.com/anasshawish0-glitch/delta/refs/heads/claude/swaili-3d-thickness-ef5jeh/software/booth_pi/setup.sh | bash

2. Copy the folder `C:\Users\<you>\.cache\huggingface\lerobot` from the laptop to a USB stick
   (it holds `local\` with the recordings and `calibration\` with `white_arm.json`), plug the
   stick into the Pi and run `~/booth/booth.sh import`.
3. Set the recording names and pauses in `~/booth/booth.conf`.
4. Try one round with `~/booth/booth.sh once`, then `sudo systemctl enable --now booth`.

Stop it: `sudo systemctl stop booth` (until the next boot) or `sudo systemctl disable --now booth`.
Watch it: `journalctl -u booth -f`.

A step that fails (arm power off, cable out) is tried again every 15 s; the loop never skips a
step or starts over, so blocks are never placed on top of ones already there.
