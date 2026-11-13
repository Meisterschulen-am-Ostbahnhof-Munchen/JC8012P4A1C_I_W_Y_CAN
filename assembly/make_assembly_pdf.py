# Assembly drawings, step 2 of 2: PDF drawings (A3 landscape) from the renderings of
# make_assembly.py, with position balloons and parts list.
# Run:  python make_assembly_pdf.py        (needs PyMuPDF and Pillow)
# Output: JC8012P4A1C_assembly_variant1.pdf, JC8012P4A1C_assembly_variant2_keypad.pdf
# Position numbers 1-20 are those of ../assembly_bom.csv, letters A-E are the main parts.
import os, csv, json, math, datetime
import pymupdf
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
IMG = os.path.join(HERE, "img")
mm = 72 / 25.4
PW, PH = 420, 297
BLK = (0, 0, 0); GRY = (0.45, 0.45, 0.45); LGR = (0.92, 0.92, 0.92)

MAIN = {
    "A": ("1", "Display Guition JC8012P4A1C, 10.1\", ESP32-P4, with display cover", "Guition", "JC8012P4A1C_I_W_Y"),
    "B": ("1", "CAN addon board pcbs/can_power/, under the display cover on S1-S4", "", "JC8012P4A1C_I_W_Y_CAN"),
    "C1": ("1", "Frame, 3D printed, mechanics/frame.stl", "", ""),
    "C2": ("1", "Frame with keypad chamber, 3D printed, mechanics/frame_keypad.stl", "", ""),
    "D1": ("1", "Back plate PCB pcbs/backplate/, with VESA spacers H1-H4", "", ""),
    "D2": ("1", "Back plate PCB pcbs/backplate_keypad/, with VESA spacers H1-H4", "", ""),
    "E": ("1", "Keypad PCB pcbs/keypad/ (keys F1-F12, spacers H1-H4)", "", ""),
}
NOT_SHOWN = {"2", "4", "5", "6", "11", "12", "18"}
KEYPAD_ONLY = {"16", "17", "18", "19"}


def bom():
    rows = list(csv.DictReader(open(os.path.join(REPO, "assembly_bom.csv"), encoding="utf-8")))
    return {r["Pos"]: r for r in rows}


def place_balloons(img_path, anchors, r_px):
    """Balloon centres in image pixels: next free (white) place near each anchor, outwards."""
    im = Image.open(img_path).convert("L")
    W, H = im.size
    S = 4                                                     # work on a 1/4 grid
    small = im.resize((W // S, H // S))
    occ = small.point(lambda v: 255 if v < 245 else 0)        # occupied = drawing
    clear = occ.filter(ImageFilter.MaxFilter(2 * int(r_px * 1.3 / S) + 1))
    px = clear.load(); w, h = clear.size
    cx = sum(a[0] for a in anchors.values()) / max(1, len(anchors))
    cy = sum(a[1] for a in anchors.values()) / max(1, len(anchors))
    placed = {}
    # anchors far from the centre first, they have the shortest way out
    for lab, (ax, ay) in sorted(anchors.items(), key=lambda kv: -math.hypot(kv[1][0] - cx, kv[1][1] - cy)):
        base = math.atan2(ay - cy, ax - cx)
        best = None
        for k in range(0, 36):
            ang = base + math.radians(10 * ((k + 1) // 2) * (1 if k % 2 else -1))
            for d in range(int(r_px * 2), int(max(W, H)), int(r_px / 2)):
                bx, by = ax + d * math.cos(ang), ay + d * math.sin(ang)
                if not (r_px * 1.5 < bx < W - r_px * 1.5 and r_px * 1.5 < by < H - r_px * 1.5):
                    break
                if px[int(bx / S), int(by / S)]:
                    continue
                if any(math.hypot(bx - qx, by - qy) < 2.6 * r_px for qx, qy in placed.values()):
                    continue
                cost = d * (1 + 0.04 * abs((k + 1) // 2))
                if best is None or cost < best[0]:
                    best = (cost, bx, by)
                break
        if best is None:
            best = (0, ax + 3 * r_px, ay - 3 * r_px)
        placed[lab] = (best[1], best[2])
    return placed


class Sheet:
    def __init__(self, doc, title, variant, sheet, nsheets):
        self.pg = doc.new_page(width=PW * mm, height=PH * mm)
        self.title, self.variant = title, variant
        sh = self.pg.new_shape()
        sh.draw_rect(pymupdf.Rect(10 * mm, 10 * mm, (PW - 10) * mm, (PH - 10) * mm))
        sh.finish(color=BLK, width=0.7); sh.commit()
        # title block, bottom right
        x0, y0, x1, y1 = PW - 150, PH - 42, PW - 10, PH - 10
        sh = self.pg.new_shape()
        sh.draw_rect(pymupdf.Rect(x0 * mm, y0 * mm, x1 * mm, y1 * mm))
        for yy in (y0 + 12, y0 + 21):
            sh.draw_line(pymupdf.Point(x0 * mm, yy * mm), pymupdf.Point(x1 * mm, yy * mm))
        sh.draw_line(pymupdf.Point((x0 + 95) * mm, (y0 + 21) * mm), pymupdf.Point((x0 + 95) * mm, y1 * mm))
        sh.finish(color=BLK, width=0.5); sh.commit()
        self.text(x0 + 2, y0 + 5, "JC8012P4A1C_I_W_Y_CAN", 9, bold=True)
        self.text(x0 + 2, y0 + 9.5, title, 11, bold=True)
        self.text(x0 + 2, y0 + 17.5, variant, 9)
        self.text(x0 + 2, y0 + 25.5, "Meisterschulen am Ostbahnhof München", 7)
        self.text(x0 + 2, y0 + 29.5, "not to scale, dimensions in mm", 7)
        self.text(x0 + 97, y0 + 25.5, "Date %s" % datetime.date.today().isoformat(), 7)
        self.text(x0 + 97, y0 + 29.5, "Sheet %d / %d" % (sheet, nsheets), 7)

    def text(self, x, y, s, size=8, col=BLK, bold=False):
        self.pg.insert_text(pymupdf.Point(x * mm, y * mm), s, fontsize=size, color=col, fontname="hebo" if bold else "helv")

    def view(self, view, area, caption, balloons=True):
        """view: entry of <variant>_views.json; area: (x0, y0, x1, y1) in mm"""
        path = os.path.join(IMG, view["file"])
        W, H = view["W"], view["H"]
        x0, y0, x1, y1 = area
        y0c = y0 + 6
        s = min((x1 - x0) / W, (y1 - y0c) / H)
        ox, oy = x0 + ((x1 - x0) - W * s) / 2, y0c + ((y1 - y0c) - H * s) / 2
        self.pg.insert_image(pymupdf.Rect(ox * mm, oy * mm, (ox + W * s) * mm, (oy + H * s) * mm), filename=path)
        self.text(x0, y0 + 4, caption, 9, bold=True)
        if not balloons or not view["anchors"]:
            return
        R = 4.2                              # balloon radius in mm
        an = view["anchors"]
        pos = place_balloons(path, an, R / s)
        for key, (bx, by) in pos.items():
            lab = key.rstrip("f")
            ax, ay = an[key]
            A = pymupdf.Point((ox + ax * s) * mm, (oy + ay * s) * mm)
            B = pymupdf.Point((ox + bx * s) * mm, (oy + by * s) * mm)
            d = math.hypot(B.x - A.x, B.y - A.y)
            E = pymupdf.Point(B.x + (A.x - B.x) * R * mm / d, B.y + (A.y - B.y) * R * mm / d) if d > R * mm else B
            sh = self.pg.new_shape()
            sh.draw_line(A, E); sh.finish(color=BLK, width=0.5); sh.commit()
            sh = self.pg.new_shape(); sh.draw_circle(A, 0.7 * mm); sh.finish(color=BLK, fill=BLK); sh.commit()
            sh = self.pg.new_shape(); sh.draw_circle(B, R * mm); sh.finish(color=BLK, fill=(1, 1, 1), width=0.7); sh.commit()
            fs = 10 if len(lab) == 1 else 9
            tw = pymupdf.get_text_length(lab, fontname="hebo", fontsize=fs)
            self.pg.insert_text(pymupdf.Point(B.x - tw / 2, B.y + 0.36 * fs), lab, fontsize=fs, fontname="hebo", color=BLK)

    def parts_list(self, x0, y0, rows, width=138):
        cols = (0, 11, 20, width)             # Pos | Qty | Part
        self.text(x0, y0 - 2, "Parts list", 10, bold=True)
        sh = self.pg.new_shape()
        rh = 4.6
        y = y0
        hdr = ("Pos", "Qty", "Part / manufacturer, MPN")
        sh.draw_rect(pymupdf.Rect(x0 * mm, y * mm, (x0 + width) * mm, (y + rh) * mm))
        sh.finish(color=BLK, fill=LGR, width=0.4); sh.commit()
        for c, t in zip(cols, hdr):
            self.text(x0 + c + 1, y + 3.3, t, 7, bold=True)
        y += rh
        for pos, qty, part, extra, grey in rows:
            lines = wrap(part + ((" - " + extra) if extra else ""), 7, width - cols[2] - 2)
            hh = rh * max(1, len(lines)) * 0.8 + rh * 0.25
            sh = self.pg.new_shape()
            sh.draw_rect(pymupdf.Rect(x0 * mm, y * mm, (x0 + width) * mm, (y + hh) * mm))
            for c in cols[1:3]:
                sh.draw_line(pymupdf.Point((x0 + c) * mm, y * mm), pymupdf.Point((x0 + c) * mm, (y + hh) * mm))
            sh.finish(color=BLK, width=0.3); sh.commit()
            col = GRY if grey else BLK
            self.text(x0 + 1.5, y + 3.3, pos, 7, col, bold=True)
            self.text(x0 + cols[1] + 1.5, y + 3.3, qty, 7, col)
            for i, ln in enumerate(lines):
                self.text(x0 + cols[2] + 1, y + 3.3 + i * rh * 0.8, ln, 6.5, col)
            y += hh
        self.text(x0, y + 4, "Grey: not shown in the views. Pos. 1-20 as in assembly_bom.csv (notes there).", 6.5, GRY)
        return y


def wrap(s, size, width_mm):
    words, lines, cur = s.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if pymupdf.get_text_length(t, fontname="helv", fontsize=size * 0.93) > width_mm * mm and cur:
            lines.append(cur); cur = w_
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines


def rows_for(vn, b):
    kp = vn == "2"
    rows = [("A",) + (MAIN["A"][0], MAIN["A"][1], "", False),
            ("B",) + (MAIN["B"][0], MAIN["B"][1], "", False),
            ("C",) + (MAIN["C2" if kp else "C1"][0], MAIN["C2" if kp else "C1"][1], "", False),
            ("D",) + (MAIN["D2" if kp else "D1"][0], MAIN["D2" if kp else "D1"][1], "", False)]
    if kp:
        rows.append(("E", MAIN["E"][0], MAIN["E"][1], "", False))
    for pos in sorted(b, key=int):
        if pos in KEYPAD_ONLY and not kp:
            continue
        r = b[pos]
        part = r["Part"].replace("keypad variant only: ", "")
        mpn = ", ".join(x for x in (r["Manufacturer"], r["MPN"]) if x)
        rows.append((pos, r["Qty"], part, mpn, pos in NOT_SHOWN))
    return rows


def make(vn):
    kp = vn == "2"
    views = json.load(open(os.path.join(IMG, "variant%s_views.json" % vn)))
    b = bom()
    title = "Assembly drawing"
    var = "Variant 2: with keypad (12 keys F1-F12)" if kp else "Variant 1: without keypad"
    doc = pymupdf.open()
    n = 2
    s1 = Sheet(doc, title, var, 1, n)
    s1.view(views["exploded_back"], (15, 13, 268, 284), "Exploded view, seen from behind")
    yl = s1.parts_list(PW - 150, 20, rows_for(vn, b))
    steps = ["Order of assembly:",
             "0  First: glue jackposts 7 into the hex pockets of C from outside (2K epoxy on the side walls",
             "    only, female thread kept clean with a screw), let it cure (up to 24 h).",
             "1  B onto the display board (cover off), screws 1; FFC 2 to FPC3, cable 11/12 to CN2.",
             "2  Cover back on. C onto A, screws 9 (6x)." + (" E with 19 into the pocket of C, screws 16." if kp else ""),
             "3  D-Sub 3 from inside over the jackposts 7, nuts 20 (SW 4.5, only about 0.1 Nm,",
             "    secure with locking lacquer)." + (" FFC 18 from FPC4 to J1 of E." if kp else ""),
             "4  Speaker 13 onto D (screws 14, nuts 15), plug into CN3.",
             "5  D onto C, screws 8" + (" and 17." if kp else "."), "6  VESA bracket onto the spacers of D, screws 10."]
    for i, t in enumerate(steps):
        s1.text(PW - 150, yl + 11 + i * 4, t, 7, bold=(i == 0))
    s2 = Sheet(doc, title, var, 2, n)
    if kp:
        s2.view(views["assembled_front"], (15, 13, 210, 140), "Assembled, front", balloons=False)
        s2.view(views["assembled_back"], (215, 13, 405, 140), "Assembled, back", balloons=False)
        s2.view(views["exploded_keypad"], (15, 145, 265, 284), "Keypad: E and 19 into the pocket of the frame from the front")
    else:
        s2.view(views["assembled_front"], (15, 40, 210, 200), "Assembled, front", balloons=False)
        s2.view(views["assembled_back"], (215, 40, 405, 200), "Assembled, back", balloons=False)
    ov = views["overall"]
    s2.text(15, 248, "Overall size (with jackposts and screw heads, without VESA bracket): "
            "%.0f x %.0f x %.0f mm (width x height x depth)" % tuple(ov), 9, bold=True)
    out = os.path.join(HERE, "JC8012P4A1C_assembly_variant1.pdf" if not kp else "JC8012P4A1C_assembly_variant2_keypad.pdf")
    doc.save(out, garbage=3, deflate=True)
    print("saved", out)
    return out


if __name__ == "__main__":
    for vn in ("1", "2"):
        make(vn)
