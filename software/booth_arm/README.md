# Robot house booth: taught poses instead of recordings

`booth_arm.py` runs on the Windows laptop next to LeRobot 0.7.0 (`C:\robot\.venv`), with the white
arm (follower, COM11) and, for teaching only, the black arm (leader, COM12).

1. **Teach once** – blocks in storage, arm folded:
   `python booth_arm.py teach`
   Build the house slowly with the black arm. For every block press Enter four times:
   above it in storage (gripper open, about 5 cm above everything), jaws closed on its handle,
   above its spot in the house (still holding it), and seated in the house (still closed).
   Then open, lift, go to the next block. At the end fold the arm and press Enter (home), then raise it
   high above the middle of the board, well above every stack, and press Enter (travel).
   `b` redoes the last step, `q` stops (finished blocks are kept).
2. **Check** – `python booth_arm.py run --once`, or one block: `python booth_arm.py test 4`.
3. **Fix one pose** – `python booth_arm.py fix 4 place` (steps: pick_above, pick, place_above, place), `fix home` or `fix travel`.
4. **Booth** – `python booth_arm.py run` (Ctrl+C stops and folds the arm).

Between places the arm goes straight up to the travel height, turns, and comes down, so it never sweeps
through the stacks. Taking the house apart is the taught list backwards. The program checks the gripper position: if a grab
closes on nothing or a block falls on the way, the arm folds, beeps and waits for Enter.
Speeds, pauses and gripper margins are at the top of the file.

## Recordings instead: `booth_replay.py`

`python booth_replay.py --build <name> --unbuild <name>` plays two LeRobot recordings in a loop (build,
30 s, take apart, 90 s) and compares the arm with what it did while recording. If the gripper closes past
where it held a block, an arm joint stays 25 degrees away from the recording, or the connection drops, it
lets go, folds the arm, beeps, waits a minute for someone to put all blocks back in storage, and starts again
from the build. After five problems in a row it waits for Enter. Every event goes to `booth_log.txt`.
