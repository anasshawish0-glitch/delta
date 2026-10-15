# SO-101 digital twin (browser prototype)

A CAD-style page with the SO-101 follower arm in 3D. Drag the gizmo to move the gripper (IK),
preview the move as a ghost, run it, or let the arm pick an object into the tray. Simulation only
for now; a Python service on the Raspberry Pi will later stream real joint angles and camera frames.

- `index.html`: the page (three.js from jsDelivr)
- `kin.js`: forward kinematics + damped least-squares IK (also runs in Node)
- `robot.json`, `meshes.json`: built from the official URDF by `build_meshes.py`

Rebuild assets: `python3 build_meshes.py <path to SO-ARM100/Simulation/SO101>`
Preview locally: `python3 -m http.server` in this folder, then open http://localhost:8000

Website: the `gh-pages` branch holds a copy of `index.html`, `kin.js`, `robot.json` and `meshes.json`,
served by GitHub Pages at https://anasshawish0-glitch.github.io/delta/. After changing the page, copy
those four files onto `gh-pages` and push.
