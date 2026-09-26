// L-shaped motor mount bracket (قاعدة ماتور على شكل L)
// All dimensions in mm. Edit the parameters below then export STL from OpenSCAD.

t        = 2.60;   // sheet thickness (السمك)
W        = 25;     // bracket width
L        = 32;     // leg length measured from the outer corner
ri       = 2;      // inner bend radius
center_d = 8.0;    // center (shaft) hole diameter
screw_d  = 3.0;    // screw holes
pat_a    = 14;     // motor hole spacing A
pat_b    = 14;     // motor hole spacing B
$fn      = 96;

R  = ri + t;       // outer bend radius
hc = L - W/2;      // hole center distance from outer corner

module leg_profile() {
    difference() {
        hull() {
            translate([R, -W/2]) square([hc - R, W]);
            translate([hc, 0]) circle(d = W);
        }
        translate([hc, 0]) {
            circle(d = center_d);
            {
                for (s = [-1, 1]) translate([s * pat_a/2, 0]) circle(d = screw_d);
                for (s = [-1, 1]) translate([0, s * pat_b/2]) circle(d = screw_d);
            }
        }
    }
}

// horizontal leg (XY plane)
linear_extrude(t) leg_profile();

// vertical leg (YZ plane)
translate([t, 0, 0]) rotate([0, -90, 0]) linear_extrude(t) leg_profile();

// bend
translate([R, W/2, R]) rotate([90, 0, 0])
    linear_extrude(W)
        intersection() {
            difference() { circle(r = R); circle(r = ri); }
            translate([-R, -R]) square(R);
        }
