"""Cutting / print drawing for Folika, keypad variant 2b (backlit).

python make_folika_2b.py  ->  folika_keypad_12_2b.pdf and folika_keypad_12_2b.dxf
Needs PyMuPDF and shapely. The school logo is copied from ../../keypad/docs/folika_keypad_12.pdf.
Geometry in mm, origin = keypad centre, y up (front view). PCB: x = 150 + x, y = 100 - y.
"""
import os
import pymupdf
from shapely.geometry import box, Point
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
ORIG = os.path.join(HERE, "..", "..", "keypad", "docs", "folika_keypad_12.pdf")
MM = 72 / 25.4

W, H, R = 48.0, 150.0, 1.5
KX = 12.0
ROWS = [56.40, 33.84, 11.28, -11.28, -33.84, -56.40]
POCKET = 16.3
NOSE_W, NOSE_D = 5.8, 1.45           # diode notch
LED_DX, LED_DY = 8.6, 9.6            # window LED (WL-ICLED 2121) from the key centre, outer top corner
LED_POCKET = 3.0
WIN_D = 3.0                          # window in the foil
BITE_R = 2.4                         # key field / frame cut out around the window
SV_POCKET = (-1.9, -0.85, 1.9, 1.0)  # side view LED pocket (x0, y0, x1, y1) around (0, row); lens towards -y
HOLE_D, HOLE_X, HOLE_Y = 6.6, 12.0, 70.0

DARK = (0x28 / 255, 0x7E / 255, 0x48 / 255)     # left column F7-F12, Pantone 348 C, approx. RAL 6002
LIGHT = (0x9E / 255, 0xCB / 255, 0x58 / 255)    # right column F1-F6, Pantone 375 C, approx. RAL 6018
GREY_BG = (0.784, 0.792, 0.8)
GREY_FRAME = (0.503, 0.51, 0.52)
MAG = (0.75, 0.0, 0.55)
TXT = (0.137, 0.122, 0.125)

KEYS = []   # (label, x, y, colour, side)  side = -1 left column (outer = left), +1 right column
for i, y in enumerate(ROWS):
    KEYS.append(("F%d" % (7 + i), -KX, y, DARK, -1))
    KEYS.append(("F%d" % (1 + i), KX, y, LIGHT, 1))


def rrect(x0, y0, x1, y1, r):
    return box(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, resolution=16)


def window(k):
    _, x, y, _, s = k
    return (x + s * LED_DX, y + LED_DY)


# ---------------- plexiglass ----------------
pg_outline = rrect(-W / 2, -H / 2, W / 2, H / 2, R)
cuts = []
for k in KEYS:
    _, x, y, _, s = k
    parts = [box(x - POCKET / 2, y - POCKET / 2, x + POCKET / 2, y + POCKET / 2)]
    top_row = y == ROWS[0]
    nx = x + s * 3.5
    if top_row:     # diode below the key
        parts.append(box(nx - NOSE_W / 2, y - POCKET / 2 - NOSE_D, nx + NOSE_W / 2, y - POCKET / 2))
    else:
        parts.append(box(nx - NOSE_W / 2, y + POCKET / 2, nx + NOSE_W / 2, y + POCKET / 2 + NOSE_D))
    wx, wy = window(k)
    parts.append(box(wx - LED_POCKET / 2, wy - LED_POCKET / 2, wx + LED_POCKET / 2, wy + LED_POCKET / 2))
    if not top_row:  # no thin web between diode notch and LED pocket
        a, b = sorted((nx + s * NOSE_W / 2, wx - s * LED_POCKET / 2))
        parts.append(box(a, y + POCKET / 2, b, y + POCKET / 2 + NOSE_D))
    cuts.append(unary_union(parts))
for y in ROWS:      # side view LEDs in the centre strip
    x0, y0, x1, y1 = SV_POCKET
    cuts.append(box(x0, y + y0, x1, y + y1))
holes = [Point(sx * HOLE_X, sy * HOLE_Y).buffer(HOLE_D / 2, resolution=32) for sx in (-1, 1) for sy in (-1, 1)]

# ---------------- foil ----------------
fields = []
for k in KEYS:
    wx, wy = window(k)
    bite = Point(wx, wy).buffer(BITE_R, resolution=24)
    _, x, y, col, s = k
    frame = rrect(x - 9, y - 9, x + 9, y + 9, 1.5).difference(bite)
    inner = rrect(x - 7, y - 7, x + 7, y + 7, 0.8).difference(bite)
    fields.append((k, frame, inner, (wx, wy)))


# ---------------- PDF ----------------
def P(x, y, ox, oy):
    return pymupdf.Point((ox + x) * MM, (oy - y) * MM)


def poly_paths(geom):
    gs = getattr(geom, "geoms", [geom])
    out = []
    for g in gs:
        out.append(list(g.exterior.coords))
        out += [list(i.coords) for i in g.interiors]
    return out


def fill_geom(page, geom, ox, oy, fill=None, color=None, width=0.0):
    sh = page.new_shape()
    for ring in poly_paths(geom):
        sh.draw_polyline([P(x, y, ox, oy) for x, y in ring])
    sh.finish(fill=fill, color=color, width=width * MM if width else 0, closePath=True, even_odd=True)
    sh.commit()


doc = pymupdf.open()
page = doc.new_page(width=210 * MM, height=297 * MM)
FX, FY = 55.0, 148.0      # foil centre on the page
GX, GY = 150.0, 148.0     # plexiglass centre


def text(x, y, s, size=7.8, bold=False, color=(0, 0, 0)):
    page.insert_text(pymupdf.Point(x * MM, y * MM), s, fontsize=size, fontname="hebo" if bold else "helv", color=color)


RED = (0.9, 0, 0)
text(15, 12, "Tastatur 2 x 6, Variante 2b (beleuchtet) - PU-Folie + 3 mm Plexiglas (PG)", 13, True, MAG)
text(15, 19, "für JC8012P4A1C_I_W_Y_CAN, Variante 2b - wie folika_keypad_12.pdf, dazu Fenster, Farben und LED-Taschen", 8.5)
lines = [
    ("Maßstab 1:1 auf A4 (ohne Skalierung drucken), Maße in mm, Ansicht von vorne.", (0, 0, 0)),
    ("Kontur 48 x 150 mm, Eckradius 1,5 mm - Folie, Plexiglas und Platine haben dieselbe Kontur.", (0, 0, 0)),
    ("PU-Folie: bedruckt, Rückseite 3M 468MP, Klebefreiheit in den Tastenfeldern (14 x 14 mm) und über den Fenstern (Ø 4 mm).", RED),
    ("HINTERLEUCHTET: Tastenfelder und grauer Grund lichtdurchlässig drucken (transluzente Farben, kein deckender Unterdruck),", RED),
    ("   Fenster Ø 3 mm transluzent weiß (Diffusor), Beschriftung schwarz deckend.", RED),
    ("Farben: linke Reihe F7-F12 dunkelgrün Pantone 348 C (ca. RAL 6002), rechte Reihe F1-F6 hellgrün Pantone 375 C (ca. RAL 6018).", RED),
    ("Plexiglasplatte 3 mm, glasklar: Rückseite 3M 300LSE, wird auf die Platine geklebt (nicht über den LED-Taschen).", (0, 0, 0)),
    ("Ausschnitte im PG: 12 Tastentaschen 16,3 x 16,3 mm mit Nase (Diode) und Tasche 3 x 3 mm (Fenster-LED) an der äußeren oberen Ecke,", RED),
    ("   6 Taschen 3,8 x 1,85 mm im Mittelsteg (Seiten-LEDs für den Hintergrund), 4 x Ø 6,6 mm für die Abstandshülsen.", RED),
    ("Tastenraster 24 mm (Spalten) x 22,56 mm (Reihen). Gesamtdicke 5,5 mm (flacher Teil).", (0, 0, 0)),
]
for i, (s, c) in enumerate(lines):
    text(15, 25 + 4.2 * i, s, 7.8, False, c)
text(31, 69.5, "PU-Folie, Druckbild (Ansicht von vorne)", 9, True, MAG)
text(126, 69.5, "Plexiglas 3 mm (Ansicht von vorne)", 9, True, MAG)

# foil: background with 2 mm bleed, fields, windows, labels, logo, cut line
fill_geom(page, rrect(-W / 2 - 2, -H / 2 - 2, W / 2 + 2, H / 2 + 2, 0.01), FX, FY, fill=GREY_BG)
for (k, frame, inner, (wx, wy)) in fields:
    fill_geom(page, frame, FX, FY, fill=GREY_FRAME)
    fill_geom(page, inner, FX, FY, fill=k[3])
    sh = page.new_shape()
    sh.draw_circle(P(wx, wy, FX, FY), WIN_D / 2 * MM)
    sh.finish(fill=(1, 1, 1), color=(0.55, 0.55, 0.55), width=0.15 * MM)
    sh.commit()
    lab = k[0]
    tw = pymupdf.get_text_length(lab, fontname="hebo", fontsize=20)
    c = P(k[1], k[2], FX, FY)
    page.insert_text(pymupdf.Point(c.x - tw / 2, c.y + 7.0), lab, fontsize=20, fontname="hebo", color=TXT)
src = pymupdf.open(ORIG)
logo = pymupdf.Rect(46.5 * MM, 214.8 * MM, 63.5 * MM, 222.3 * MM)
page.show_pdf_page(logo, src, 0, clip=logo)
fill_geom(page, rrect(-W / 2, -H / 2, W / 2, H / 2, R), FX, FY, color=MAG, width=0.3)

# plexiglass
fill_geom(page, pg_outline, GX, GY, color=MAG, width=0.3)
for g in cuts + holes:
    fill_geom(page, g, GX, GY, color=MAG, width=0.3)
text(126, 229, "48.0", 7)
text(176, 148, "150.0", 7)

text(15, 270, "Fenster / LED 2121: Mitte 8,6 mm neben und 9,6 mm über der Tastenmitte, zum Außenrand (links: oben links, rechts: oben rechts).", 7)
text(15, 274, "Seiten-LEDs (3210): Mitte x = 0, y wie die Tastenreihen; Licht strahlt im Mittelsteg nach unten.", 7)
text(15, 278, "Mitten der Tastentaschen ab Tastaturmitte: x = ±12,0, y = ±11,28, ±33,84, ±56,40; Löcher Hülsen x = ±12,0, y = ±70,0", 7)
text(15, 282, "Nasen (Diode): Mitte 3,5 mm neben Tastenmitte zum Außenrand, bis 9,6 mm ab Tastenmitte; oberste Reihe unten, sonst oben", 7)
text(15, 286, "DXF mit derselben Geometrie: folika_keypad_12_2b.dxf (Layer FOIL_OUTLINE, FOIL_KEY_FIELD_14, FOIL_FRAME_18, FOIL_WINDOW_3,", 7)
text(15, 290, "PG_OUTLINE, PG_CUT_POCKET, PG_CUT_HOLE_6_6). Erst Probedruck / Musterteil: Lichtverteilung und Farben prüfen.", 7)
doc.save(os.path.join(HERE, "folika_keypad_12_2b.pdf"), garbage=4, deflate=True)


# ---------------- DXF (R12, LINE / CIRCLE) ----------------
ents = []


def dxf_geom(geom, layer):
    for ring in poly_paths(geom):
        for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
            ents.append("0\nLINE\n8\n%s\n10\n%.4f\n20\n%.4f\n11\n%.4f\n21\n%.4f\n" % (layer, x1, y1, x2, y2))


def dxf_circle(x, y, r, layer):
    ents.append("0\nCIRCLE\n8\n%s\n10\n%.4f\n20\n%.4f\n40\n%.4f\n" % (layer, x, y, r))


dxf_geom(rrect(-W / 2, -H / 2, W / 2, H / 2, R), "FOIL_OUTLINE")
for (k, frame, inner, (wx, wy)) in fields:
    dxf_geom(inner, "FOIL_KEY_FIELD_14")
    dxf_geom(frame, "FOIL_FRAME_18")
    dxf_circle(wx, wy, WIN_D / 2, "FOIL_WINDOW_3")
dxf_geom(pg_outline, "PG_OUTLINE")
for g in cuts:
    dxf_geom(g, "PG_CUT_POCKET")
for sx in (-1, 1):
    for sy in (-1, 1):
        dxf_circle(sx * HOLE_X, sy * HOLE_Y, HOLE_D / 2, "PG_CUT_HOLE_6_6")
with open(os.path.join(HERE, "folika_keypad_12_2b.dxf"), "w", newline="\n") as f:
    f.write("0\nSECTION\n2\nHEADER\n9\n$INSUNITS\n70\n4\n0\nENDSEC\n0\nSECTION\n2\nENTITIES\n")
    f.write("".join(ents))
    f.write("0\nENDSEC\n0\nEOF\n")
print("ok", len(ents), "DXF entities")


# ---------------- print file for Folika (foil only, CorelDraw friendly) ----------------
# One plain page 1:1: print image with 2 mm bleed and the cut line (magenta hairline), no notes.
# No embedded PDF page, no fonts: labels and logo are curves. Written as SVG and PDF.
import re
PW, PH = W + 10, H + 10          # page = foil + 5 mm margin each side
PX, PY = PW / 2, PH / 2
pd = pymupdf.open()
pp = pd.new_page(width=PW * MM, height=PH * MM)


def pfill(geom, fill=None, color=None, width=0.0):
    sh = pp.new_shape()
    for ring in poly_paths(geom):
        sh.draw_polyline([P(x, y, PX, PY) for x, y in ring])
    sh.finish(fill=fill, color=color, width=width * MM if width else 0, closePath=True, even_odd=True)
    sh.commit()


pfill(rrect(-W / 2 - 2, -H / 2 - 2, W / 2 + 2, H / 2 + 2, 0.01), fill=GREY_BG)
for (k, frame, inner, (wx, wy)) in fields:
    pfill(frame, fill=GREY_FRAME)
    pfill(inner, fill=k[3])
    sh = pp.new_shape()
    sh.draw_circle(P(wx, wy, PX, PY), WIN_D / 2 * MM)
    sh.finish(fill=(1, 1, 1), color=None, width=0)
    sh.commit()
    tw = pymupdf.get_text_length(k[0], fontname="hebo", fontsize=20)
    c = P(k[1], k[2], PX, PY)
    pp.insert_text(pymupdf.Point(c.x - tw / 2, c.y + 7.0), k[0], fontsize=20, fontname="hebo", color=TXT)
# logo: redraw the vector paths of the original foil (no embedded page)
dx, dy = (PX - FX) * MM, (PY - FY) * MM
for dr in src[0].get_drawings():
    if not dr["rect"].intersects(logo) or dr["rect"].width > 100:
        continue
    sh = pp.new_shape()
    for it in dr["items"]:
        q = [a + (dx, dy) if isinstance(a, pymupdf.Point) else a for a in it[1:]]
        if it[0] == "l":
            sh.draw_line(q[0], q[1])
        elif it[0] == "c":
            sh.draw_bezier(*q[:4])
        elif it[0] == "re":
            sh.draw_rect(pymupdf.Rect(q[0]) + (dx, dy, dx, dy))
        elif it[0] == "qu":
            sh.draw_quad(pymupdf.Quad(q[0]) * pymupdf.Matrix(1, 0, 0, 1, dx, dy))
    sh.finish(fill=dr.get("fill"), color=dr.get("color"), width=dr.get("width") or 0,
              closePath=dr.get("closePath", True), even_odd=dr.get("even_odd", False))
    sh.commit()
pfill(rrect(-W / 2, -H / 2, W / 2, H / 2, R), color=MAG, width=0.1)
svg = pp.get_svg_image(text_as_path=True)
glyphs = dict(re.findall(r'<path id="([^"]+)" d="([^"]+)"/>', svg))
svg = re.sub(r'<use data-text="[^"]*" xlink:href="#([^"]+)" transform="([^"]+)"([^>]*)/>',
             lambda m: '<path transform="%s" d="%s"%s/>' % (m.group(2), glyphs[m.group(1)], m.group(3)), svg)
svg = re.sub(r"<defs>.*?</defs>\n?", "", svg, flags=re.S)
svg = re.sub(r'width="[^"]+" height="[^"]+"', 'width="%gmm" height="%gmm"' % (PW, PH), svg, count=1)
base = os.path.join(HERE, "folika_keypad_12_2b_print")
open(base + ".svg", "w", encoding="utf-8", newline="\n").write(svg)
out = pymupdf.open("pdf", pymupdf.open(base + ".svg").convert_to_pdf())
out.save(base + ".pdf", garbage=4, deflate=True)
print("ok print file", PW, "x", PH, "mm")
