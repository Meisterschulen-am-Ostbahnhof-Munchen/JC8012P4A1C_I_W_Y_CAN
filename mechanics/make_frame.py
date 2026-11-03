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
#     clears the display boss at x = +16.4. Wall 2.0 mm, 1.0 mm under the
#     jackpost hexes (counterbores) so the mating plug goes in deep enough.
#  2. Bosses for the back plate screws (Wuerth WUEPLAST WN 1451 3x10, thread
#     forming screw for thermoplastics), pilot hole through the whole boss.
#  3. Keyhole plates for wall mounting removed (VESA 100 on the back plate).
#
# Variant 2 (keypad): set FRAME_VARIANT=keypad or run make_frame_keypad.py.
# Output: frame_keypad.step, frame_keypad.stl. The frame gets a chamber on +x
# (right side seen from the FRONT, left side seen from behind) for the keypad
# sandwich ../keypad (PCB + plexiglass + PU foil, 5.5 mm). The sandwich lies in
# a pocket 2 mm behind the glass front of the display and is held by M2.5 x 8
# screws from behind through lugs into the SMD spacers of the keypad PCB.

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

DSUB_X = -7.0           # D-Sub centre (x); flange ends at +8.6, the web of the
                        # middle display boss (x = +16.4, r 7) starts at +9.4
DSUB_Z = 10.5           # D-Sub centre (z), flange 12.5 high -> 4.25 .. 16.75
DSUB_CUT_W = 20.0       # cutout for the mating plug shell
DSUB_CUT_H = 11.0
DSUB_CUT_R = 1.5
DSUB_HOLE_PITCH = 25.0  # jackpost holes
DSUB_HOLE_D = 3.2
DSUB_FLANGE_W = 31.6    # flange 30.8 + clearance
DSUB_FLANGE_H = 13.0    # flange 12.5 + clearance
DSUB_WALL_LOCAL = 2.0   # local wall thickness at the D-Sub (jackpost thread)
DSUB_NUT_D = 5.8        # recess for the 4-40 nuts of 618009227221 (hex 5.42 across
DSUB_NUT_DEPTH = 0.4    # corners), they stand 0.3 mm in front of the flange
# counterbores for the jackpost hexes on the outside: the mating plug rests on
# the hex (5.0 mm), so every mm of wall under the hex costs mating depth.
# Wall under the hex = DSUB_WALL_LOCAL - HEX_CB_DEPTH = 1.0 mm (0.6 mm at the
# bush recess); the rest of the wall stays 2.0 mm.
HEX_CB_D = 6.0          # hex 4.5 AF, 5.2 across corners
HEX_CB_DEPTH = 1.0

# EJOT PT / WUEPLAST design rules (d1 = 3): boss 2 x d1, pilot 0.7..0.8 x d1,
# relief bore 1.05 x d1 x (0.3..0.5 x d1), engagement 2 x d1
SCREW_PILOT_D = 2.4     # pilot hole (0.8 x d1), proven in our prints for 3 mm plastic screws
RELIEF_D = 3.2          # relief bore at the entry (>= 1.05 x d1 = 3.15)
RELIEF_DEPTH = 1.2      # 0.3..0.5 x d1
BOSS_D = 8.0            # >= 2.5 x d
BOSS_H = 9.0            # from z = 0, stays below the display bosses (z 9.3);
                        # 3x10 screw - 1.6 mm plate - 1.2 relief = 7.2 mm thread (>= 2 x d1)

# back plate screw positions (must match ../backplate)
SCREWS = [(-115.7, -73.6), (115.7, -73.6), (-115.7, 73.6), (115.7, 73.6),
          (-60.0, -76.35), (60.0, -76.35), (-60.0, 76.35), (60.0, 76.35)]

VARIANT = os.environ.get("FRAME_VARIANT", "")
KEYPAD = VARIANT == "keypad"

# ---- variant 2: keypad chamber on +x --------------------------------------
Z_GLASS = 25.0          # glass front of the display: rests on z = 18, module 7 mm
KP_STEP = 2.0           # foil surface behind the glass plane
KP_T = 5.5              # sandwich: PCB 1.6 + 300LSE + plexiglass 3 + 468MP + PU foil (flat part)
KP_W, KP_H = 48.0, 150.0  # sandwich outline (= ../keypad PCB)
KP_CLR = 0.3            # clearance sandwich to pocket
KP_SHELL_GAP = 0.5      # display shell (242.8 +-0.3) to partition
KP_PART_T = 2.0         # partition between display shell and keypad pocket (z 18 .. 25)
KP_WALL_T = 3.0         # outer wall of the chamber
KP_R = 10.0             # outer corner radius (as the back plate)
KP_DISP_R = 10.1        # corner radius of the display (JC8012P4A1.dwg), the frame front follows it
KP_LEDGE_W = 3.0        # ledge behind the PCB
KP_LEDGE_T = 2.0
KP_LUG_T = 4.0          # lugs for the M2.5 x 8 screws: lug 4 + PCB 1.6 + 2.4 in the spacer
KP_LUG_W = 7.0
KP_SCREW_D = 2.8        # M2.5 clearance
KP_SPACERS = [(-12.0, -70.0), (12.0, -70.0), (-12.0, 70.0), (12.0, 70.0)]  # from the keypad centre
KP_J1 = (0.0, 70.0)     # FFC connector J1 on the back of the keypad PCB (top)
KP_J1_W = 17.0          # ledge cut for J1 (courtyard 14.5 mm)
# cable slot from the main frame into the chamber (FFC from FPC4 EXTEND2)
KP_SLOT_Y = (48.0, 69.0)
KP_SLOT_Z = (3.5, 16.0)

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
    nut = Part.makeCylinder(DSUB_NUT_D / 2, DSUB_NUT_DEPTH + 0.1,
                            V(DSUB_X + sx * DSUB_HOLE_PITCH / 2, -WALL_Y + DSUB_WALL_LOCAL - DSUB_NUT_DEPTH, DSUB_Z), V(0, 1, 0))
    frame = frame.cut(nut)
    cb = Part.makeCylinder(HEX_CB_D / 2, HEX_CB_DEPTH + 1,
                           V(DSUB_X + sx * DSUB_HOLE_PITCH / 2, -WALL_Y - 1, DSUB_Z), V(0, 1, 0))
    frame = frame.cut(cb)

# 3: keyhole plates (only below the rim top, outside the rim)
for x0, x1 in KEYHOLE_BOXES:
    frame = frame.cut(box(x0, x1, 50.0, RIM_IN - 0.01, -1.0, RIM_Z + 0.01))

# 2: bosses for the back plate screws
for x, y in SCREWS:
    boss = Part.makeCylinder(BOSS_D / 2, BOSS_H, V(x, y, 0)).common(outer)
    frame = frame.fuse(boss)
for x, y in SCREWS:
    frame = frame.cut(Part.makeCylinder(SCREW_PILOT_D / 2, BOSS_H + 1, V(x, y, -1)))
    frame = frame.cut(Part.makeCylinder(RELIEF_D / 2, RELIEF_DEPTH + 1, V(x, y, -1)))

# 4: close the cable notch of the original (rim z 0..3, wall up to z 5)
NOTCH_X = (94.5, 102.5)
frame = frame.fuse(box(NOTCH_X[0], NOTCH_X[1], -WALL_Y, -RIM_IN, 0.0, RIM_Z))
frame = frame.fuse(box(NOTCH_X[0], NOTCH_X[1], -WALL_Y, -WALL_Y + WALL_T, 0.0, 6.0))



def rounded_slab(x0, x1, y0, y1, z0, z1, r, right_only=False):
    """box with rounded vertical edges (all four, or only the two at x1)"""
    xl = x0 if right_only else x0 + r
    s = box(xl, x1 - r, y0, y1, z0, z1).fuse(box(x0, x1, y0 + r, y1 - r, z0, z1))
    for yc in (y0 + r, y1 - r):
        s = s.fuse(Part.makeCylinder(r, z1 - z0, V(x1 - r, yc, z0)))
        if not right_only:
            s = s.fuse(Part.makeCylinder(r, z1 - z0, V(x0 + r, yc, z0)))
    return s.removeSplitter()


NAME = "frame"
if KEYPAD:
    NAME = "frame_keypad"
    XS = env.XMax                                   # outer wall of the original frame (+x)
    PX0 = XS + KP_SHELL_GAP + KP_PART_T             # pocket, display side
    XK = PX0 + KP_CLR + KP_W / 2                    # keypad centre
    PX1 = XK + KP_W / 2 + KP_CLR                    # pocket, outer side
    XO = PX1 + KP_WALL_T                            # new outer wall
    PY = KP_H / 2 + KP_CLR
    Z_PCB = Z_GLASS - KP_STEP - KP_T                # back of the keypad PCB
    print("keypad centre x %.2f, outer x %.2f, width %.2f, PCB back z %.2f" % (XK, XO, XO + env.XMax, Z_PCB))
    lower = rounded_slab(XS - 1.0, XO, -WALL_Y, WALL_Y, 0.0, 18.0, KP_R, True)
    upper = rounded_slab(XS + KP_SHELL_GAP, XO, -WALL_Y, WALL_Y, 18.0, Z_GLASS, KP_R, True)
    frame = frame.fuse(lower).fuse(upper)
    # fill the notch between the rounded +x corners of the original and the chamber
    for sy in (-1, 1):
        y0, y1 = sorted((sy * (WALL_Y - 12.0), sy * WALL_Y))
        frame = frame.fuse(box(XS - 12.0, XS, y0, y1, 0.0, 18.0).cut(outer))
    # front part (z 18 .. glass) hugs the rounded corners of the display ("ploughshare"): the
    # corner between the display (242.8 x 158.7, R 10.1, + gap) and the straight partition is filled
    disp_gap = rounded_slab(-XS - KP_SHELL_GAP, XS + KP_SHELL_GAP, -WALL_Y - KP_SHELL_GAP, WALL_Y + KP_SHELL_GAP,
                            18.0 - 0.01, Z_GLASS + 0.01, KP_DISP_R + KP_SHELL_GAP)
    for sy in (-1, 1):
        y0, y1 = sorted((sy * (WALL_Y - KP_DISP_R - 1.0), sy * WALL_Y))
        fill = box(XS - KP_DISP_R - 1.0, XS + KP_SHELL_GAP + 0.01, y0, y1, 18.0, Z_GLASS).cut(disp_gap)
        print("display corner fill", round(fill.Volume, 1))
        frame = frame.fuse(fill)
    # chamber behind the PCB, back rim (6 mm as the original) and ledge
    frame = frame.cut(box(PX0, PX1, -(WALL_Y - WALL_T), WALL_Y - WALL_T, RIM_Z, Z_PCB - KP_LEDGE_T))
    frame = frame.cut(box(PX0, XO - 6.0, -RIM_IN, RIM_IN, -1.0, RIM_Z + 0.01))
    frame = frame.cut(box(PX0 + KP_LEDGE_W, PX1 - KP_LEDGE_W, -(PY - KP_LEDGE_W), PY - KP_LEDGE_W,
                          Z_PCB - KP_LEDGE_T - 0.1, Z_PCB + 0.1))
    frame = frame.cut(rounded_slab(PX0, PX1, -PY, PY, Z_PCB, Z_GLASS + 1.0, 1.5 + KP_CLR))
    # lugs for the spacers of the keypad
    for sx, sy in KP_SPACERS:
        yin = sy - 4.0 if sy > 0 else sy + 4.0
        y0, y1 = sorted((yin, (WALL_Y - WALL_T) * (1 if sy > 0 else -1)))
        frame = frame.fuse(box(XK + sx - KP_LUG_W / 2, XK + sx + KP_LUG_W / 2, y0, y1, Z_PCB - KP_LUG_T, Z_PCB))
    for sx, sy in KP_SPACERS:
        frame = frame.cut(Part.makeCylinder(KP_SCREW_D / 2, KP_LUG_T + 1, V(XK + sx, sy, Z_PCB - KP_LUG_T - 0.5)))
    # ledge cut for the FFC connector J1 and the cable
    jx, jy = XK + KP_J1[0], KP_J1[1]
    frame = frame.cut(box(jx - KP_J1_W / 2, jx + KP_J1_W / 2, jy - 4.0, WALL_Y - WALL_T + 0.01,
                          Z_PCB - KP_LUG_T - 0.5, Z_PCB + 0.01))
    # cable slot through the old side wall and the partition
    frame = frame.cut(box(XS - WALL_T - 1.0, PX0 + 0.1, KP_SLOT_Y[0], KP_SLOT_Y[1], KP_SLOT_Z[0], KP_SLOT_Z[1]))
    # back plate screws in the new corners
    kp_env = rounded_slab(XS - 1.0, XO, -WALL_Y, WALL_Y, 0.0, 18.0, KP_R, True)
    for y in (-73.6, 73.6):
        frame = frame.fuse(Part.makeCylinder(BOSS_D / 2, BOSS_H, V(XO - 5.7, y, 0)).common(kp_env))
    for y in (-73.6, 73.6):
        frame = frame.cut(Part.makeCylinder(SCREW_PILOT_D / 2, BOSS_H + 1, V(XO - 5.7, y, -1)))
        frame = frame.cut(Part.makeCylinder(RELIEF_D / 2, RELIEF_DEPTH + 1, V(XO - 5.7, y, -1)))
    print("back plate screws added at x %.2f" % (XO - 5.7))

frame = frame.removeSplitter()
print("valid", frame.isValid(), "solids", len(frame.Solids), "volume", round(frame.Volume))
frame.exportStep(os.path.join(HERE, NAME + ".step"))
import Mesh
m = Mesh.Mesh()
m.addFacets(frame.tessellate(0.05))
m.write(os.path.join(HERE, NAME + ".stl"))
print("written")
