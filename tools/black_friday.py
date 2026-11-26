#!/usr/bin/env python3
"""One-off Black Friday 2026 VIP sale card (1080x1350)."""
import sys
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
BG = (12, 12, 14); CARD = (30, 30, 34); ORANGE = (232, 116, 59)
WHITE = (245, 245, 245); GREY = (150, 150, 156); RED = (239, 83, 60); DARK = (20, 20, 20)
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
def f(s, b=True): return ImageFont.truetype(FB if b else FR, s)

tiers = [  # name, colour, text colour, new, old, days, extra
    ("BRONZE",   (199, 123, 48),  DARK, "15",   "30",   "9 დღე",  None),
    ("SILVER",   (184, 190, 198), DARK, "27.5", "55",   "30 დღე", None),
    ("GOLD",     (232, 183, 48),  DARK, "50",   "100",  "30 დღე", None),
    ("PLATINUM", (217, 220, 224), DARK, "140",  "350",  "30 დღე", "+ რეკლამა სოც. მედიაში"),
    ("DIAMOND",  (111, 208, 240), DARK, "480",  "1200", "30 დღე", "+ ვიდეორგოლი, ბანერი"),
]

LAST_DAY = len(sys.argv) > 3 and sys.argv[3] == "last-day"
img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)
d.ellipse([W - 300, -200, W + 200, 300], fill=(42, 26, 18))

fb = f(38)
d.text((70, 62), "xeloba", font=fb, fill=WHITE)
d.text((70 + d.textlength("xeloba", font=fb), 62), ".ge", font=fb, fill=ORANGE)

d.text((70, 140), "BLACK FRIDAY", font=f(104), fill=WHITE)
# discount badge
bx, by = 70, 275
txt = "-60%-მდე"
bw = d.textlength(txt, font=f(52)) + 60
d.rounded_rectangle([bx, by, bx + bw, by + 84], radius=42, fill=RED)
d.text((bx + 30, by + 12), txt, font=f(52), fill=WHITE)
d.text((bx + bw + 30, by + 8), "VIP პაკეტები", font=f(40), fill=WHITE)
d.text((bx + bw + 30, by + 54), "ხელოსნებისთვის", font=f(30, False), fill=GREY)

y = 395
row_h = 140
for name, col, tcol, new, old, days, extra in tiers:
    d.rounded_rectangle([70, y, W - 70, y + row_h - 18], radius=26, fill=CARD)
    pf = f(30)
    pw = d.textlength(name, font=pf) + 44
    d.rounded_rectangle([98, y + 26, 98 + pw, y + 78], radius=26, fill=col)
    d.text((120, y + 34), name, font=pf, fill=tcol)
    sub = days if not extra else f"{days}  {extra}"
    d.text((100, y + 88), sub, font=f(26, False), fill=GREY)
    # prices, right aligned
    nf, of = f(64), f(30, False)
    new_t, old_t = new, f"{old} ლარი"
    lf = f(30)
    lw = d.textlength("ლარი", font=lf)
    nw, ow = d.textlength(new_t, font=nf), d.textlength(old_t, font=of)
    rx = W - 100
    d.text((rx - lw, y + 60), "ლარი", font=lf, fill=WHITE)
    d.text((rx - lw - 12 - nw, y + 26), new_t, font=nf, fill=WHITE)
    ox, oy = rx - lw - 12 - nw - 28 - ow, y + 58
    d.text((ox, oy), old_t, font=of, fill=GREY)
    d.line([(ox - 2, oy + 19), (ox + ow + 2, oy + 19)], fill=RED, width=3)
    y += row_h

# footer
d.text((70, y + 8), "აქცია დღეს მთავრდება!" if LAST_DAY else "აქცია 30 ნოემბრამდე!", font=f(40), fill=ORANGE)
if LAST_DAY:
    t = "ბოლო დღე!"
    tf = f(44)
    tw = d.textlength(t, font=tf) + 50
    d.rounded_rectangle([W - 70 - tw, 72, W - 70, 136], radius=32, fill=RED)
    d.text((W - 70 - tw + 25, 80), t, font=tf, fill=WHITE)
cta = "xeloba.ge/vipmanager"
cf = f(46)
cw = d.textlength(cta, font=cf) + 80
d.rounded_rectangle([70, H - 140, 70 + cw, H - 50], radius=45, fill=ORANGE)
d.text((110, H - 125), cta, font=cf, fill=DARK)

m = Image.open(sys.argv[1]).convert("RGBA")
m = m.resize((int(m.width * 210 / m.height), 210), Image.LANCZOS)
img.paste(m, (W - m.width - 50, H - m.height - 25), m)

img.save(sys.argv[2], quality=93)
print(sys.argv[2])
