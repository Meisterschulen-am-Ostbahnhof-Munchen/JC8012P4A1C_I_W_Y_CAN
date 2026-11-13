"""Textures for the Blender rendering (python make_textures.py, needs PyMuPDF and Pillow).

- tex/foil.png:   print of the keypad foil, cut from ../../pcbs/keypad/docs/folika_keypad_12.pdf
                  (1:1 drawing, foil outline 48 x 150 mm at x 31..79, y 73..223 mm of the page)
- tex/screen.png: espVT screen "GNSS / Teilbreiten" redrawn at 1280 x 800 (the display resolution)
"""
import os
import pymupdf
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
TEX = os.path.join(HERE, "tex")
os.makedirs(TEX, exist_ok=True)
MM = 72 / 25.4


def foil():
    doc = pymupdf.open(os.path.join(REPO, "pcbs", "keypad", "docs", "folika_keypad_12.pdf"))
    # 0.3 mm inside the outline, so the magenta cutting line is not in the picture
    clip = pymupdf.Rect(31.3 * MM, 73.3 * MM, 78.7 * MM, 222.7 * MM)
    pix = doc[0].get_pixmap(clip=clip, dpi=600)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    img.save(os.path.join(TEX, "foil.png"))
    print("foil", img.size)


def font(names, size):
    for n in names:
        p = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", n)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def screen():
    W, H = 1280, 800
    img = Image.new("RGB", (W, H), (14, 22, 32))
    d = ImageDraw.Draw(img)
    mono = ["CascadiaMono.ttf", "consola.ttf", "DejaVuSansMono.ttf"]
    monob = ["CascadiaMono.ttf", "consolab.ttf", "DejaVuSansMono-Bold.ttf"]
    f_title = font(monob, 34)
    f_sub = font(mono, 20)
    f_btn = font(monob, 21)
    f_head = font(mono, 38)
    f_row = font(mono, 22)
    f_small = font(mono, 15)
    cyan = (120, 210, 230)
    # left menu
    d.text((40, 34), "ISOBUS VT", font=f_title, fill=(235, 240, 245))
    d.text((40, 78), "Terminalmenü", font=f_sub, fill=(150, 165, 180))
    items = ["Maschinen", "Terminal", "ISOBUS", "AUX-N", "GNSS / Teilbreiten", "Ton", "Information"]
    y = 124
    for it in items:
        active = it.startswith("GNSS")
        box = (34, y, 236, y + 54)
        if active:
            d.rectangle(box, fill=(60, 200, 90), outline=(220, 240, 225), width=2)
            d.text((135, y + 27), it, font=font(monob, 17), fill=(255, 255, 255), anchor="mm")
        else:
            d.rectangle(box, fill=(20, 34, 50), outline=(110, 150, 180), width=2)
            d.text((135, y + 27), it, font=f_btn, fill=(225, 235, 245), anchor="mm")
        y += 66
    d.rectangle((40, 676, 230, 760), fill=(70, 205, 95), outline=(220, 240, 225), width=3)
    d.text((135, 718), "Zurück", font=f_btn, fill=(255, 255, 255), anchor="mm")
    # right panel
    px0 = 262
    d.rectangle((px0, 0, W, H), fill=(226, 234, 242))
    d.text((px0 + 30, 40), "GNSS / Teilbreiten", font=f_head, fill=(30, 45, 60))
    d.text((px0 + 30, 92), "Empfänger, NTRIP und Automatiksperren", font=f_sub, fill=(50, 120, 130))
    d.line((px0 + 30, 126, W - 30, 126), fill=(40, 140, 150), width=2)
    rows = [("Quelle", "Modul aus"), ("Fix", "OFF"), ("Satelliten", "0     HDOP 0.00"),
            ("Geschwindigkeit / Kurs", "0.00 km/h    0.0°"), ("Position", "0.0000000    0.0000000"),
            ("NTRIP", "Aus"), ("Minimum für Teilbreiten", "Nur RTK Fix"),
            ("Automatik", None)]
    y = 148
    for i, (k, v) in enumerate(rows):
        d.rectangle((px0 + 30, y, W - 30, y + 54), fill=(214, 224, 234) if i % 2 == 0 else (222, 231, 240))
        d.line((px0 + 30, y + 54, W - 30, y + 54), fill=(190, 202, 214), width=1)
        d.text((px0 + 46, y + 27), k, font=f_row, fill=(40, 55, 70), anchor="lm")
        if v:
            d.text((W - 46, y + 27), v, font=f_row, fill=(40, 55, 70), anchor="rm")
        else:
            d.text((W - 46, y + 27), "GNSS INPUT OFF   0 Teilbreiten   Ausgänge gesperrt",
                   font=f_small, fill=(40, 55, 70), anchor="rm")
        y += 58
    d.text((px0 + 46, y + 30), "Ausgänge bleiben bis zur TC-SC-Umsetzung gesperrt", font=f_row, fill=cyan)
    img.save(os.path.join(TEX, "screen.png"))
    print("screen", img.size)


if __name__ == "__main__":
    foil()
    screen()
