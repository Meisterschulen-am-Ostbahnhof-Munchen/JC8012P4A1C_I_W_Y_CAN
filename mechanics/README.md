# Frame

3D printed frame between the display and the back plate (`../backplate`).

![frame and back plate, exploded, seen from the inside](docs/assembly_exploded_inside.png)

| | |
|---|---|
| ![from behind](docs/assembly_exploded.png) | ![frame](docs/frame_iso.png) |
| ![D-Sub from outside](docs/frame_dsub_outside.png) | ![D-Sub from inside](docs/frame_dsub_inside.png) |

Based on **"Guition 10.1" ESP32P4 / JC8012P4A1C wall mount" by 8bitmcu**,
<https://www.thingiverse.com/thing:7208630>, licensed
[CC BY-SA](https://creativecommons.org/licenses/by-sa/4.0/). The original
files are in `source/`. The modified frame in this folder is licensed CC BY-SA
as well (see [LICENSE.md](LICENSE.md)), not GPL like the rest of the repository.

## Files

| File | Content |
|---|---|
| `make_frame.py` | FreeCAD script, all dimensions as parameters at the top |
| `frame.step`, `frame.stl` | result (STL for the slicer) |
| `make_frame_keypad.py`, `frame_keypad.step`, `frame_keypad.stl` | variant 2 with the keypad chamber (see below) |
| `source/` | original landscape frame (STEP), licence and readme of the original |
| `docs/` | renderings (FreeCAD), with the back plate from `../backplate` |
| `assembly/` | assembly drawings of both variants (PDF) and their scripts, see [assembly/README.md](assembly/README.md) |

Make the frame again: `freecadcmd make_frame.py` (FreeCAD 1.1).

## Changes to the original

1. **D-Sub 9** (Würth 618009227221) in the bottom wall, centre 7 mm off the
   middle, on the side away from the middle display boss (x = -7, the boss is
   at x = +16.4), so that the flange clears the web of the boss. Cutout 20 × 11 mm for the mating plug,
   jackpost holes 3.2 mm with 25 mm pitch. The flange (12.5 mm) sits in a
   pocket on the inside between the back rim (z 0–3) and the display (z 18),
   and the wall there is 2.0 mm. The mating plug rests on the jackpost hex,
   so every mm of wall under the hex costs mating depth: the hexes sit in
   **Ø 6.0 × 1.0 mm counterbores**, 1.0 mm wall under them (1 mm less mating
   depth than a D-Sub without a panel). The
   threaded bushes of the 618009227221 stand 0.3 mm in front of the flange and
   get a 5.8 × 0.4 mm recess (0.6 mm wall left under the hex). Jackposts:
   Würth 94510000 (UNC 4-40, hex 5.0, thread 5.0), 4.2 mm thread in the
   4.6 mm bush. Checked against the Würth STEP models of 618009227221,
   618009221923 and 94510000: no collision.
2. **8 bosses** (Ø 8 mm, 9 mm high) for the screws of the back plate:
   Würth WÜPLAST WN 1451 3 × 10 (art. 4234 3 10), thread forming screws for
   thermoplastics. Designed to the EJOT PT rules (same thread form): pilot
   hole 2.4 mm through the whole boss, relief bore 3.2 × 1.2 mm at the entry,
   7.2 mm thread engagement (≥ 2 × d). If the screws go in too hard in the
   printed frame, increase `SCREW_PILOT_D` to 2.5. The positions match the holes H5–H12 of the back plate.
3. **Keyhole tabs** for wall mounting removed: the back plate carries a
   VESA 100 mount.
4. **Cable notch** at the bottom closed: power and CAN come through the
   D-Sub.

The 6 bosses to the display (M2.5 × 8, onto the brass posts of the display)
are unchanged.

## Coordinates

As in the original STEP: x = long side, y = short side, +y = top of the
display (landscape), -y = bottom (D-Sub). z = 0 is the back (back plate),
the display back rests on the wall at z = 18, the glass front of the display
is at z = 25 (display module 7 mm). +x is on the right seen from the front,
on the left seen from behind.

## Variant 2: frame with keypad chamber

`make_frame_keypad.py` (FreeCAD 1.1) makes `frame_keypad.step` and
`frame_keypad.stl`: the same frame with a chamber on +x for the keypad
`../keypad` (12 keys). Close it with the wide back plate `../backplate_keypad`.
All dimensions are parameters `KP_*` in `make_frame.py`.

| front (foil hidden) | from behind, keypad mounted |
|---|---|
| ![front](docs/frame_keypad_front.png) | ![back](docs/frame_keypad_back.png) |

![J1, lugs and cable slot from behind](docs/frame_keypad_j1.png)

- Total width 296.9 mm (chamber 54.1 mm). The frame no longer fits a printer
  with a 256 mm bed.
- Partition 2 mm between the display shell (0.5 mm gap) and the keypad pocket,
  from z = 18 to the glass plane z = 25. Outer wall 3 mm.
- At the top and bottom the front part (z 18 .. 25) follows the rounded corners
  of the display (R 10.1 + 0.5 mm gap), so there is no notch between display
  and keypad chamber. The fill runs out thin at the tangent points.
- Pocket corners R 1.8 (sandwich R 1.5 + 0.3 mm clearance).
- Pocket 48.6 x 150.6 mm (0.3 mm clearance around the 48 x 150 mm sandwich). The
  foil lies 2 mm behind the glass plane, the frame edge is level with the glass.
- Ledge 3 mm wide, 2 mm thick behind the PCB (z = 15.5 .. 17.5); the key forces
  go into it.
- 4 lugs 4 mm thick with 2.8 mm holes for the M2.5 x 8 screws into the spacers
  of the keypad (keypad centre +-12, +-70 mm). Do not use longer screws.
- The ledge is cut at the top for the FFC connector J1 on the back of the
  keypad and for the cable.
- Cable slot 21 x 12.5 mm (y 48 .. 69, z 3.5 .. 16) through the old side wall and
  the partition, for the FFC from FPC4 EXTEND2.
- 2 more bosses for the back plate screws in the new corners (x = 169.8).
- Checked in FreeCAD with the KiCad STEP of the keypad and a model of the
  plexiglass: no collision, actuator tips at z = 23.4.

## Open points

- Jackpost length for the D-Sub (Würth WE-HEX, UNC 4-40): wall 2 mm +
  flange, check the thread length in the datasheet.
- Speaker and its opening.
- Keypad variant: test print, check the FFC path through the cable slot and
  the fit of the sandwich in the pocket.
