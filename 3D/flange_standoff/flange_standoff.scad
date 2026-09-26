// Flange standoff: solid column with a round flange at each end.
// All dimensions in mm.

L        = 55.40;  // total length, flange face to flange face
tube_d   = 12.44;  // column outer diameter
flange_d = 18.0;   // flange diameter
flange_t = 2.86;   // flange thickness
screw_d  = 2.6;    // 4 screw holes per flange; 2.6 lets an M3 screw tap its own thread (use 3.2 for a clearance hole)
pat      = 14.0;   // distance between opposite screw holes
$fn      = 128;

module holes() {
    for (a = [0, 90, 180, 270]) rotate(a) translate([pat/2, 0, -1])
        cylinder(d = screw_d, h = flange_t + 2);
}

difference() {
    union() {
        cylinder(d = tube_d, h = L);
        cylinder(d = flange_d, h = flange_t);
        translate([0, 0, L - flange_t]) cylinder(d = flange_d, h = flange_t);
    }
    holes();
    translate([0, 0, L - flange_t]) holes();
}
