# Assembly drawings, step 1 of 2: build the assembly in FreeCAD and render the views.
# Run with the FreeCAD GUI (rendering needs it), FreeCAD 1.1:
#     freecad.exe make_assembly.py            (both variants)
# Environment: ASSY_VARIANTS="1" or "2" or "1,2" (default), KICAD_CLI = path of kicad-cli.
# Output: img/<variant>_<view>.png and img/<variant>_views.json (camera and anchor points
# of the position balloons). Step 2: python make_assembly_pdf.py makes the PDF drawings.
#
# Frame coordinates (see ../mechanics/README.md): x = long side, +x right seen from the FRONT,
# +y = top of the display, z = 0 back side of the frame, glass front of the display z = 25.
# The PCB STEP files are exported with kicad-cli into cache/ (not in the repository).
import os, sys, json, subprocess, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
CACHE = os.path.join(HERE, "cache")
IMG = os.path.join(HERE, "img")
MODELS = os.path.join(HERE, "models")
os.makedirs(CACHE, exist_ok=True)
LOG = open(os.path.join(CACHE, "make_assembly.log"), "w")
KICAD_CLI = os.environ.get("KICAD_CLI", r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe")
VARIANTS = [v.strip() for v in os.environ.get("ASSY_VARIANTS", "1,2").split(",")]
# ASSY_EXPORT=1: instead of the drawings, export every part as STL (mm, frame coordinates) into
# render/cache/variant<n>/ for the Blender rendering (render/render_blender.py)
EXPORT = os.environ.get("ASSY_EXPORT", "") == "1"

XK = 148.2          # keypad centre x (frame), see make_frame.py KP_*
ZPCB_KP = 17.5      # back of the keypad PCB
CAN_POS = (133.75, 140.0, 13.49)  # CAN board: frame x = 133.75 - pcb x, y = 140 - pcb y, B side at z 13.49
# (position of the CAN board under the display cover is schematic: J2 below FPC3, on S1-S4)

def log(*a):
    LOG.write(" ".join(str(x) for x in a) + "\n"); LOG.flush()


def export_pcb_steps():
    os.makedirs(CACHE, exist_ok=True)
    out = {}
    for key, rel in (("can", "pcbs/can_power/JC8012P4A1C_I_W_Y_CAN.kicad_pcb"),
                     ("bp1", "pcbs/backplate/JC8012P4A1C_backplate.kicad_pcb"),
                     ("bp2", "pcbs/backplate_keypad/JC8012P4A1C_backplate_keypad.kicad_pcb"),
                     ("kp", "pcbs/keypad/JC8012P4A1C_keypad.kicad_pcb")):
        src = os.path.join(REPO, rel); dst = os.path.join(CACHE, key + ".step")
        if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
            subprocess.run([KICAD_CLI, "pcb", "export", "step", "-o", dst, "--subst-models", "-f", src],
                           cwd=os.path.dirname(src), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        out[key] = dst
    return out


try:
    import FreeCAD as App, FreeCADGui as Gui, Part, Import
    from FreeCAD import Vector as V, Placement as PL, Rotation as ROT
    os.makedirs(IMG, exist_ok=True)
    steps = export_pcb_steps()
    log("steps", steps)

    def read(path):
        s = Part.Shape(); s.read(path); return s

    # ------------------------------------------------------------ simple parts
    def screw(x, y, zh, d, L, dk, k):
        """Pan head screw, head on the -z side (all screws go in from behind), head face at z = zh."""
        h = Part.makeCylinder(dk / 2, k, V(x, y, zh - k))
        h = h.cut(Part.makeBox(d * 0.9, d * 0.25, 0.6 * k, V(x - d * 0.45, y - d * 0.125, zh - k)))
        return h.fuse(Part.makeCylinder(d / 2 * 0.95, L, V(x, y, zh)))

    WUEPLAST_STEP = os.path.join(MODELS, "WUEPLAST_Wuerth_4234_3_10.step")
    _wp = []

    def wueplast(x, y, zh):
        """WUEPLAST WN 1451 3 x 10 (Wurth 4234 3 10), head on the -z side, bearing face at z = zh.
        Original Wurth model (axis along +x, bearing face at x = 0); simple model if the file is missing."""
        if not os.path.exists(WUEPLAST_STEP):
            return screw(x, y, zh, 3.0, 10, 6.0, 2.2)
        if not _wp:
            _wp.append(read(WUEPLAST_STEP))
        w = _wp[0].copy()
        w.rotate(V(0, 0, 0), V(0, 1, 0), -90)      # +x (towards the tip) -> +z
        w.translate(V(x, y, zh))
        return w

    def nut(x, y, z0, s, m, d):
        pts = []
        import math
        r = s / math.sqrt(3)
        for i in range(7):
            a = math.radians(30 + 60 * i); pts.append(V(x + r * math.cos(a), y + r * math.sin(a), z0))
        f = Part.Face(Part.makePolygon(pts)).extrude(V(0, 0, m))
        return f.cut(Part.makeCylinder(d / 2, m, V(x, y, z0)))

    def box(x0, x1, y0, y1, z0, z1):
        return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))

    def rbox(x0, x1, y0, y1, z0, z1, r):
        """box with rounded vertical edges (radius r)"""
        b = box(x0 + r, x1 - r, y0, y1, z0, z1).fuse(box(x0, x1, y0 + r, y1 - r, z0, z1))
        for cx in (x0 + r, x1 - r):
            for cy in (y0 + r, y1 - r):
                b = b.fuse(Part.makeCylinder(r, z1 - z0, V(cx, cy, z0)))
        return b.removeSplitter()

    def fx(px): return px - 150.0          # back plate PCB -> frame
    def fy(py): return 100.0 - py

    # ------------------------------------------------------------ geometry common to both variants
    disp = read(os.path.join(MODELS, "JC8012P4A1_envelope.step"))
    disp.translate(V(-121.4, -79.35, 0)); disp.rotate(V(0, 0, 0), V(0, 0, 1), 180); disp.translate(V(0, 0, 25))
    # D-Sub in the bottom wall (6.0 mm thick at the D-Sub, outside y = -79.35, inside y = -73.35), centre x -7, z 9.0.
    # Jackposts 94513200 (hex 5.0, thread 8.2) from outside into the 5 mm hex pockets, flush with the wall;
    # D-Sub 618009221923 (without nuts) from inside over the threads, its shell is flush with the wall outside;
    # nuts 94505009 (SW 4.5, 5 mm) from inside. Clamped: 1.0 wall + 0.4 flange + 3.0 body + 0.36 rivet collar
    # = 4.76 mm, so 3.4 mm of the 8.2 mm thread are in the nut.
    DSUB_X, DSUB_Z, WALL_IN = -7.0, 9.0, -79.35 + 6.0
    dsub = read(os.path.join(MODELS, "D-Sub_Wurth_618009221923.step")); dsub.translate(V(DSUB_X, WALL_IN + 0.4, DSUB_Z))
    jp_step = read(os.path.join(MODELS, "Jackpost_Wurth_94513200.step"))      # axis +y, hex y 0..5
    nut_step = read(os.path.join(MODELS, "HexNut_Wurth_94505009.step"))        # axis +z, z 0..5
    nut_step.rotate(V(0, 0, 0), V(1, 0, 0), -90)                              # +z -> +y
    jps, nts = [], []
    for x in (DSUB_X - 12.5, DSUB_X + 12.5):
        j = jp_step.copy(); j.translate(V(x, -79.35, DSUB_Z)); jps.append(j)
        n = nut_step.copy(); n.translate(V(x, WALL_IN + 0.4 + 3.36, DSUB_Z)); nts.append(n)
    jack = Part.makeCompound(jps)
    dnuts = Part.makeCompound(nts)
    # speaker XHXDZ-2828 on the inside of the back plate (LS1 at PCB 237 / 70), lugs with 4 holes
    sx, sy = fx(237.0), fy(70.0)
    spk = box(sx - 13.75, sx + 13.75, sy - 13.75, sy + 13.75, 0, 1.5)
    spk = spk.fuse(Part.makeCylinder(12.0, 11.5, V(sx, sy, 1.5)))
    spk_holes = [(fx(a), fy(b)) for a, b in ((225.5, 58.5), (248.5, 58.5), (225.5, 81.5), (248.5, 81.5))]
    for hx, hy in spk_holes:
        spk = spk.cut(Part.makeCylinder(1.35, 2, V(hx, hy, -0.2)))

    # screws (pos. numbers of ../assembly_bom.csv)
    def ray_seat(shape, x, y, ztop, r=2.1):
        """lowest z of the material column below ztop next to a screw hole at (x, y) (the lug)"""
        z = ztop - 0.05; zlow = None
        while z > -5:
            if shape.isInside(V(x + r, y, z), 0.01, True):
                zlow = z
            elif zlow is not None:
                break
            z -= 0.1
        return zlow if zlow is not None else ztop

    def variant(vn):
        kp = vn == "2"
        frame = read(os.path.join(REPO, "mechanics", "frame_keypad.step" if kp else "frame.step"))
        items = {}      # key -> dict(shape|obj, colour, explode vector, label)
        def add(key, shape, col, ex=(0, 0, 0), label=None, trans=0):
            items[key] = dict(shape=shape, col=col, ex=V(*ex), label=label, trans=trans)
        # explode offsets, view from behind: -z = towards the viewer
        EXD, EXC, EXF, EXP = 0, -120, -240, -380
        add("A", disp, (0.16, 0.16, 0.18), (0, 0, EXD), "A")
        add("C", frame, (0.55, 0.57, 0.60), (0, 0, EXF), "C")
        add("3", dsub, (0.20, 0.35, 0.75), (0, 25, EXF), "3")
        add("7", jack, (0.80, 0.80, 0.82), (0, -22, EXF), "7")
        add("20", dnuts, (0.80, 0.80, 0.82), (0, 75, EXF), "20")
        # 6 screws M2.5 x 6 frame -> display posts (pos. 9), head on the back of the frame lugs
        s9 = []
        for x in (-106.4, 16.4, 106.4):
            for y in (-64.35, 64.35):
                zs = ray_seat(frame, x, y, 13.5)
                s9.append(screw(x, y, zs, 2.5, 6, 4.5, 1.7))
        add("9", Part.makeCompound(s9), (0.80, 0.80, 0.82), (0, 0, EXF - 45), "9")
        # back plate
        add("D", read(steps["bp2" if kp else "bp1"]), (0.12, 0.45, 0.22), (0, 0, EXP), "D")
        items["D"]["shape"].translate(V(-150, 100, -1.6))
        add("13", spk, (0.10, 0.10, 0.10), (0, 0, EXP + 75), "13")
        add("15", Part.makeCompound([nut(hx, hy, 1.5, 5, 2, 2.5) for hx, hy in spk_holes]), (0.80, 0.80, 0.82), (0, 0, EXP + 105), "15")
        add("14", Part.makeCompound([screw(hx, hy, -1.6, 2.5, 8, 4.5, 1.7) for hx, hy in spk_holes]), (0.80, 0.80, 0.82), (0, 0, EXP - 25), "14")
        bp_holes = [(34.3, 26.4), (265.7, 26.4), (34.3, 173.6), (265.7, 173.6), (90, 23.65), (210, 23.65), (90, 176.35), (210, 176.35)]
        add("8", Part.makeCompound([wueplast(fx(a), fy(b), -1.6) for a, b in bp_holes]), (0.80, 0.80, 0.82), (0, 0, EXP - 32), "8")
        vesa = [(100, 50), (200, 50), (100, 150), (200, 150)]
        add("10", Part.makeCompound([screw(fx(a), fy(b), -1.6, 4.0, 12, 7.0, 2.6) for a, b in vesa]), (0.80, 0.80, 0.82), (0, 0, EXP - 40), "10")
        # CAN board under the display cover, M2 x 6 into the standoffs S1-S4
        can = read(steps["can"]); can.rotate(V(0, 0, 0), V(0, 1, 0), 180); can.translate(V(*CAN_POS))
        add("B", can, (0.10, 0.30, 0.65), (0, 175, EXC), "B")
        can_h = [(104, 104), (162, 104), (104, 150), (162, 150)]
        add("1", Part.makeCompound([screw(CAN_POS[0] - a, CAN_POS[1] - b, CAN_POS[2] - 1.6 - 2.5, 2.0, 6, 3.8, 1.3) for a, b in can_h]),
            (0.80, 0.80, 0.82), (0, 175, EXC - 40), "1")
        if kp:
            k = read(steps["kp"]); k.translate(V(XK - 150.0, 100.0, ZPCB_KP))
            add("E", k, (0.15, 0.55, 0.30), (0, 0, EXF), "E")
            z0 = ZPCB_KP + 1.6 + 0.17
            pg = rbox(XK - 24, XK + 24, -75, 75, z0, z0 + 3.0, 1.5)      # same outline as the PCB (R 1.5)
            for c, cx in enumerate((XK - 12, XK + 12)):
                for r in range(6):
                    cy = (r - 2.5) * 22.56
                    pg = pg.cut(box(cx - 8.15, cx + 8.15, cy - 8.15, cy + 8.15, z0 - 1, z0 + 4))
                    sg = -1 if cx < XK else 1; dy = 1 if 5 - r == 0 else -1
                    nx = cx + sg * 3.5; ny0, ny1 = sorted((cy - dy * 8.0, cy - dy * 9.6))
                    pg = pg.cut(box(nx - 2.9, nx + 2.9, ny0, ny1, z0 - 1, z0 + 4))
                for cy in (-70, 70):
                    pg = pg.cut(Part.makeCylinder(3.3, 5, V(cx, cy, z0 - 1)))
            foil = rbox(XK - 24, XK + 24, -75, 75, ZPCB_KP + 5.1, ZPCB_KP + 5.5, 1.5)
            add("19", pg, (0.70, 0.85, 0.95), (0, 0, EXF), "19", trans=35)
            add("19f", foil, (0.78, 0.79, 0.80), (0, 0, EXF), "19")
            add("16", Part.makeCompound([screw(XK + dx, dy_, ZPCB_KP - 4.0, 2.5, 8, 4.5, 1.7) for dx in (-12, 12) for dy_ in (-70, 70)]),
                (0.80, 0.80, 0.82), (0, 0, EXF - 45), "16")
            hb = [(319.8, 26.4), (319.8, 173.6)]
            add("17", Part.makeCompound([wueplast(fx(a), fy(b), -1.6) for a, b in hb]), (0.80, 0.80, 0.82), (0, 0, EXP - 32), "17")
        return items

    # ------------------------------------------------------------ rendering
    def render(vn, items):
        name = "variant%s" % vn
        doc = App.newDocument(name)
        objs = {}
        for key, it in items.items():
            o = doc.addObject("Part::Feature", "P_" + key); o.Shape = it["shape"]; objs[key] = o
            it["base"] = App.Placement(o.Placement)   # translate()/rotate() of a shape only set its placement
        doc.recompute(); Gui.updateGui()
        gd = Gui.getDocument(name)
        for key, it in items.items():
            vo = gd.getObject("P_" + key)
            vo.ShapeColor = it["col"]; vo.LineColor = (0.12, 0.12, 0.12); vo.Transparency = it["trans"]
        v = gd.ActiveView
        v.setAnimationEnabled(False)
        v.setCameraType("Orthographic")
        from pivy import coin
        views = {}

        def place(explode, extra=None):
            for key, o in objs.items():
                e = items[key]["ex"] if explode else V(0, 0, 0)
                if extra and key in extra:
                    e = extra[key]
                o.Placement = PL(e, ROT()).multiply(items[key]["base"])
            doc.recompute()

        def shot(view, c, up, anchors, W=2400, H=1600, hide=()):
            for key in objs:
                gd.getObject("P_" + key).Visibility = key not in hide
            c = V(*c); c.normalize()
            u = V(*up); u = u - c * u.dot(c); u.normalize()
            x = u.cross(c)
            m = App.Matrix(x.x, u.x, c.x, 0, x.y, u.y, c.y, 0, x.z, u.z, c.z, 0, 0, 0, 0, 1)
            v.setCameraOrientation(ROT(m))
            # frame all visible shapes for the image aspect
            pts = []
            for key, o in objs.items():
                if key in hide:
                    continue
                bb = o.Shape.BoundBox
                for px in (bb.XMin, bb.XMax):
                    for py in (bb.YMin, bb.YMax):
                        for pz in (bb.ZMin, bb.ZMax):
                            pts.append(V(px, py, pz))
            xs = [p.dot(x) for p in pts]; ys = [p.dot(u) for p in pts]; zs = [p.dot(c) for p in pts]
            cx_, cy_ = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
            hgt = max(max(ys) - min(ys), (max(xs) - min(xs)) * H / W) * 1.06
            centre = x * cx_ + u * cy_ + c * (max(zs) + 50)
            cam = v.getCameraNode()
            cam.position.setValue(coin.SbVec3f(centre.x, centre.y, centre.z))
            cam.height.setValue(hgt)
            cam.focalDistance.setValue(50)
            Gui.updateGui()
            fn = "%s_%s.png" % (name, view)
            v.redraw(); Gui.updateGui()
            v.saveImage(os.path.join(IMG, fn), 400, 300, "White")   # warm-up: the first image is sometimes empty
            v.saveImage(os.path.join(IMG, fn), W, H, "White")
            an = {}
            for lab, p in anchors.items():
                q = p - centre
                an[lab] = [W / 2 + q.dot(x) * H / hgt, H / 2 - q.dot(u) * H / hgt]
            views[view] = dict(file=fn, W=W, H=H, anchors=an)
            log("saved", fn)

        def anchor(key, where):
            o = objs[key]; bb = o.Shape.BoundBox
            if callable(where):
                return where(bb, o)
            return V(*where) + o.Placement.Base

        back = (0.80, -0.25, -0.55)           # from behind, from the +x side (keypad side), a bit from below
        # anchors (frame coordinates before the explode offset is added)
        def A_back():
            a = {"A": V(60, -40, 2.49), "B": V(0, 20, CAN_POS[2] - 1.6 - 7.0),
                 "C": V(-45, -79.0, 14), "3": V(-7, -70, 3.5), "7": V(-19.5, -79.35, 11.4),
                 "20": V(-19.5, -66.5, 11.5),
                 "9": V(-106.4, -64.35, 11.0), "D": V(-100, -50, -1.6), "13": V(fx(237), fy(70) - 12, 6),
                 "14": V(spk_holes[2][0], spk_holes[2][1], -3.3), "15": V(spk_holes[0][0], spk_holes[0][1], 3.5),
                 "8": V(fx(34.3), fy(173.6), -3.8), "10": V(fx(100), fy(150), -4.2),
                 "1": V(CAN_POS[0] - 104, CAN_POS[1] - 150, CAN_POS[2] - 4.1 - 1.3)}
            if "E" in objs:
                a.update({"E": V(XK, 30, ZPCB_KP), "16": V(XK - 12, -70, ZPCB_KP - 5.7), "17": V(fx(319.8), fy(173.6), -3.8),
                          "19": V(XK + 24, -40, 21)})
            return {k: p + items[k]["ex"] for k, p in a.items() if k in objs}
        place(True)
        shot("exploded_back", back, (0, 1, 0), A_back())
        place(False)
        bb = None
        for key, o in objs.items():
            bb = o.Shape.BoundBox if bb is None else bb.united(o.Shape.BoundBox)
        views["overall"] = [round(bb.XLength, 1), round(bb.YLength, 1), round(bb.ZLength, 1)]
        shot("assembled_back", (0.30, -0.45, -0.84), (0, 1, 0), {})
        shot("assembled_front", (0.22, -0.40, 0.89), (0, 1, 0), {})
        if "E" in objs:
            # keypad from the front, sandwich pulled out of the pocket
            extra = {"E": V(0, 0, 45), "19": V(0, 0, 80), "19f": V(0, 0, 115)}
            place(False, extra)
            hide = ("B", "1", "D", "13", "14", "15", "8", "10", "17", "9", "3", "7", "20")
            an = {"E": V(XK - 24, -20, ZPCB_KP + 1.6 + 45), "19": V(XK - 24, 20, ZPCB_KP + 5.0 + 80),
                  "19f": V(XK + 24, -50, ZPCB_KP + 5.5 + 115),
                  "C": V(XK + 27.3, -40, 25), "A": V(-60, 30, 25)}
            shot("exploded_keypad", (-0.55, -0.35, 0.76), (0, 1, 0), an, hide=hide)
        views["overall"] = views.pop("overall")
        json.dump(views, open(os.path.join(IMG, "%s_views.json" % name), "w"), indent=1)
        App.closeDocument(name)

    def export_meshes(vn, items):
        import MeshPart
        out = os.path.join(HERE, "render", "cache", "variant%s" % vn)
        os.makedirs(out, exist_ok=True)
        meta = {}
        for key, it in items.items():
            m = MeshPart.meshFromShape(Shape=it["shape"], LinearDeflection=0.02, AngularDeflection=0.12, Relative=False)
            m.write(os.path.join(out, key + ".stl"))
            meta[key] = dict(col=list(it["col"]), ex=[it["ex"].x, it["ex"].y, it["ex"].z], label=it["label"])
            log("mesh", vn, key, m.CountFacets)
        json.dump(meta, open(os.path.join(out, "parts.json"), "w"), indent=1)

    for vn in VARIANTS:
        if EXPORT:
            export_meshes(vn, variant(vn))
        else:
            render(vn, variant(vn))
except Exception:
    log(traceback.format_exc())
finally:
    log("end")
    LOG.close()
    os._exit(0)
