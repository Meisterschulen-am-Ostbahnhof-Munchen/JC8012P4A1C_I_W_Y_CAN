# Frame for the JC8012P4A1C_I_W_Y display with the CAN addon board and the
# PCB back plate (../backplate).
#
# Based on "Guition 10.1" ESP32P4 / JC8012P4A1C wall mount" by 8bitmcu,
# https://www.thingiverse.com/thing:7208630, licensed CC BY-SA.
# This derived frame is licensed CC BY-SA as well (see LICENSE.md).
#
# Run:  freecadcmd make_frame.py      (FreeCAD 1.1)
# Output: frame.step, frame.stl
#
# Coordinates (as in the original STEP): x = long side, y = short side,
# +y = top of the display (landscape), -y = bottom (D-Sub).
# z = 0 is the back of the frame (back plate), the display back rests on the
# wall at z = 18. The bosses at z 9.3 .. 13.3 sit on the brass posts of the display.
#
# Changes to the original:
#  1. D-Sub 9 cutout in the bottom wall, shifted to -x so that the IDC body
#     clears the display boss at x = +16.4. Wall thinned locally for the
#     jackposts.
#  2. Bosses with holes for M3 heat-set inserts, for the back plate screws.
#  3. Keyhole plates for wall mounting removed (VESA 100 on the back plate).

import os
import FreeCAD as App
import Part
from FreeCAD import Vector as V

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "source", "guition_mount-landscape.step")

# ---- parameters [mm] ----------------------------------------------------
WALL_Y = 79.35          # outer wall, bottom at -WALL_Y
WALL_T = 3.0            # wall thickness (inner wall surface at -76.35)
RIM_IN = 73.35          # back rim reaches inward to |y| = 73.35
RIM_Z = 3.0             # back rim height (6 mm wide)

DSUB_X = -4.0           # D-Sub centre (x)
DSUB_Z = 10.5           # D-Sub centre (z), flange 12.5 high -> 4.25 .. 16.75
DSUB_CUT_W = 20.0       # cutout for the mating plug shell
DSUB_CUT_H = 11.0
DSUB_CUT_R = 1.5
DSUB_HOLE_PITCH = 25.0  # jackpost holes
DSUB_HOLE_D = 3.2
DSUB_FLANGE_W = 31.6    # flange 30.8 + clearance
DSUB_FLANGE_H = 13.0    # flange 12.5 + clearance
DSUB_WALL_LOCAL = 2.0   # local wall thickness at the D-Sub (jackpost thread)

INSERT_D = 4.0          # hole for M3 heat-set insert (e.g. M3 x 5.7, OD 4.6)
INSERT_DEPTH = 6.5
BOSS_D = 8.0
BOSS_H = 9.0            # from z = 0, stays below the display bosses (z 9.3)

# back plate screw positions (must match ../backplate)
SCREWS = [(-115.7, -73.6), (115.7, -73.6), (-115.7, 73.6), (115.7, 73.6),
          (-60.0, -76.35), (60.0, -76.35), (-60.0, 76.35), (60.0, 76.35)]

# keyhole plates of the original (top, x = +-76.2)
KEYHOLE_BOXES = [(-89.0, -63.0), (63.0, 89.0)]


def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def rounded_rect_y(cx, cz, w, h, r, y0, y1):
    """prism along y with a rounded rectangle cross section in the x-z plane"""
    core = box(cx - w / 2 + r, cx + w / 2 - r, y0, y1, cz - h / 2, cz + h / 2)
    core = core.fuse(box(cx - w / 2, cx + w / 2, y0, y1, cz - h / 2 + r, cz + h / 2 - r))
    for sx in (-1, 1):
        for sz in (-1, 1):
            c = Part.makeCylinder(r, y1 - y0, V(cx + sx * (w / 2 - r), y0, cz + sz * (h / 2 - r)), V(0, 1, 0))
            core = core.fuse(c)
    return core.removeSplitter()


frame = Part.Shape()
frame.read(SRC)
frame = Part.Solid(frame.Solids[0])
# outer envelope of the frame (used to trim the bosses)
env = frame.BoundBox
outer = Part.Face(Part.Wire(frame.slice(V(0, 0, 1), 9.0)[0])).extrude(V(0, 0, 18.0))
outer.translate(V(0, 0, -9.0))

# 1: D-Sub
inner_wall = -WALL_Y + WALL_T
pocket = box(DSUB_X - DSUB_FLANGE_W / 2, DSUB_X + DSUB_FLANGE_W / 2,
             -WALL_Y + DSUB_WALL_LOCAL, inner_wall + 0.01,
             DSUB_Z - DSUB_FLANGE_H / 2, DSUB_Z + DSUB_FLANGE_H / 2)
cut = rounded_rect_y(DSUB_X, DSUB_Z, DSUB_CUT_W, DSUB_CUT_H, DSUB_CUT_R, -WALL_Y - 1, inner_wall + 1)
frame = frame.cut(pocket).cut(cut)
for sx in (-1, 1):
    h = Part.makeCylinder(DSUB_HOLE_D / 2, 10, V(DSUB_X + sx * DSUB_HOLE_PITCH / 2, -WALL_Y - 2, DSUB_Z), V(0, 1, 0))
    frame = frame.cut(h)

# 3: keyhole plates (only below the rim top, outside the rim)
for x0, x1 in KEYHOLE_BOXES:
    frame = frame.cut(box(x0, x1, 50.0, RIM_IN - 0.01, -1.0, RIM_Z + 0.01))

# 2: bosses for the back plate screws
for x, y in SCREWS:
    boss = Part.makeCylinder(BOSS_D / 2, BOSS_H, V(x, y, 0)).common(outer)
    frame = frame.fuse(boss)
for x, y in SCREWS:
    frame = frame.cut(Part.makeCylinder(INSERT_D / 2, INSERT_DEPTH + 1, V(x, y, -1)))

frame = frame.removeSplitter()
print("valid", frame.isValid(), "solids", len(frame.Solids), "volume", round(frame.Volume))
frame.exportStep(os.path.join(HERE, "frame.step"))
import Mesh
m = Mesh.Mesh()
m.addFacets(frame.tessellate(0.05))
m.write(os.path.join(HERE, "frame.stl"))
print("written")
