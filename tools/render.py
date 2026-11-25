#!/usr/bin/env python3
"""Render a xeloba.ge Facebook post (photo card or Reel video) from a JSON spec.

Usage:
  python3 tools/render.py spec.json out_dir

Spec fields:
  id          post number (int)
  format      "photo" (1080x1350 JPG) or "reel" (1080x1920 MP4, ~14 s, plus a cover JPG)
  kicker      short label above the title, e.g. "ზამთრის რჩევა" (optional)
  title       main headline (required)
  items       list of up to 5 short lines (optional)
  item_style  "check" | "number" | "none"   (default "check")
  mascot      true/false — draw ჭანჭიკა (default true)
  bubble      short speech-bubble text for ჭანჭიკა (optional)
  cta         button text (default "xeloba.ge")
"""
import json, math, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASCOT = os.path.join(ROOT, "assets", "chanchika.png")
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

BG = (17, 17, 19)
CARD = (32, 32, 36)
ORANGE = (232, 116, 59)
WHITE = (245, 245, 245)
GREY = (170, 170, 175)
DARK = (20, 20, 20)
SLOGAN = "ჭკვიანი ჭანჭიკა ირჩევს ხელობას"

_fc = {}
def font(size, bold=True):
    k = (int(size), bold)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FB if bold else FR, int(size))
    return _fc[k]

def wrap(d, text, f, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines

def fit_title(d, text, max_w, max_lines, start, minimum):
    size = start
    while size > minimum:
        lines = wrap(d, text, font(size), max_w)
        if len(lines) <= max_lines:
            return size, lines
        size -= 4
    return minimum, wrap(d, text, font(minimum), max_w)

def blend(c, a, bg=BG):
    a = max(0.0, min(1.0, a))
    return tuple(int(bg[i] + (c[i] - bg[i]) * a) for i in range(3))

def ease(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3

def load_mascot(height):
    m = Image.open(MASCOT).convert("RGBA")
    w = int(m.width * height / m.height)
    return m.resize((w, height), Image.LANCZOS)

def brand(d, x, y, size=40):
    f = font(size)
    d.text((x, y), "xeloba", font=f, fill=WHITE)
    d.text((x + d.textlength("xeloba", font=f), y), ".ge", font=f, fill=ORANGE)

def bullet(d, style, i, x, y, a=1.0, r=34):
    d.ellipse([x, y, x + 2 * r, y + 2 * r], fill=blend(ORANGE, a))
    if style == "number":
        s = str(i + 1); f = font(r * 1.2)
        d.text((x + r - d.textlength(s, font=f) / 2, y + r - r * 0.72), s, font=f, fill=blend(DARK, a))
    else:
        # check mark
        pts = [(x + r * 0.55, y + r * 1.05), (x + r * 0.9, y + r * 1.4), (x + r * 1.5, y + r * 0.65)]
        d.line(pts, fill=blend(DARK, a), width=max(4, r // 5), joint="curve")

def bubble(img, d, text, tip_x, tip_y, max_w=420, a=1.0):
    f = font(34)
    lines = wrap(d, text, f, max_w - 50)
    lh = 44
    w = max(d.textlength(l, font=f) for l in lines) + 50
    h = lh * len(lines) + 34
    x0, y0 = tip_x - w + 40, tip_y - h - 30
    d.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=26, fill=blend(WHITE, a))
    d.polygon([(tip_x - 10, y0 + h - 2), (tip_x + 20, y0 + h - 2), (tip_x + 10, tip_y)], fill=blend(WHITE, a))
    for i, l in enumerate(lines):
        d.text((x0 + 25, y0 + 17 + i * lh), l, font=f, fill=blend(DARK, a, (255, 255, 255)) if a < 1 else DARK)

# ---------------------------------------------------------------- photo card
def render_photo(spec, out_path):
    W, H = 1080, 1350
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.ellipse([W - 260, -160, W + 160, 260], fill=(40, 26, 20))
    d.ellipse([-180, H - 330, 200, H + 50], fill=(34, 24, 19))
    brand(d, 70, 70)

    y = 170
    if spec.get("kicker"):
        f = font(34)
        k = spec["kicker"]
        kw = d.textlength(k, font=f) + 56
        d.rounded_rectangle([70, y, 70 + kw, y + 62], radius=31, fill=ORANGE)
        d.text((98, y + 11), k, font=f, fill=DARK)
        y += 95

    items = spec.get("items") or []
    max_title_lines = 3 if items else 5
    size, lines = fit_title(d, spec["title"], W - 140, max_title_lines, 78 if items else 92, 50)
    for l in lines:
        d.text((70, y), l, font=font(size), fill=WHITE)
        y += int(size * 1.25)
    y += 30

    mascot_on = spec.get("mascot", True)
    style = spec.get("item_style", "check")
    if items:
        n = len(items)
        avail = (H - (350 if mascot_on else 200)) - y
        row_h = min(130, avail // n)
        fs = 40 if row_h >= 110 else 34
        right_pad = 70
        for i, it in enumerate(items):
            ry = y + i * row_h
            d.rounded_rectangle([70, ry, W - right_pad, ry + row_h - 18], radius=24, fill=CARD)
            r = min(30, (row_h - 18) // 2 - 10)
            bullet(d, style, i, 95, ry + (row_h - 18) / 2 - r, r=r)
            tl = wrap(d, it, font(fs), W - right_pad - 190)
            if len(tl) > 2:
                fs2 = fs - 6; tl = wrap(d, it, font(fs2), W - right_pad - 190)[:2]
            else:
                fs2 = fs
            th = len(tl) * fs2 * 1.2
            for j, t in enumerate(tl):
                d.text((95 + 2 * r + 30, ry + (row_h - 18 - th) / 2 + j * fs2 * 1.2), t, font=font(fs2), fill=WHITE)

    # CTA
    cta = spec.get("cta") or "xeloba.ge"
    cf = font(50)
    cw = d.textlength(cta, font=cf) + 90
    by = H - 160
    d.rounded_rectangle([70, by, 70 + cw, by + 100], radius=50, fill=ORANGE)
    d.text((115, by + 22), cta, font=cf, fill=DARK)

    if mascot_on:
        m = load_mascot(300 if items else 520)
        mx, my = W - m.width - 40, H - m.height - 30
        img.paste(m, (mx, my), m)
        if spec.get("bubble"):
            bubble(img, d, spec["bubble"], mx + m.width * 0.35, my + 10)
    img.save(out_path, quality=92)
    return out_path

# ---------------------------------------------------------------- reel
def render_reel(spec, out_path, cover_path):
    W, H, FPS = 1080, 1920, 30
    items = (spec.get("items") or [])[:5]
    style = spec.get("item_style", "check")
    mascot = load_mascot(520)
    small_mascot = load_mascot(420)
    t_intro = 3.2
    t_item = 1.7
    t_items = len(items) * t_item + (1.2 if items else 0)
    t_end = 3.6
    total = t_intro + t_items + t_end

    tmp = Image.new("RGB", (W, H)); td = ImageDraw.Draw(tmp)
    tsize, tlines = fit_title(td, spec["title"], W - 160, 4, 84, 52)

    def frame(t):
        img = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(img)
        d.ellipse([W - 300, 120, W + 200, 620], fill=(40, 26, 20))
        brand(d, 80, 260, 44)
        d.rectangle([0, H - 12, W, H], fill=ORANGE)
        if t < t_intro:
            a = ease(t / 0.5)
            if spec.get("kicker"):
                f = font(38); k = spec["kicker"]; kw = d.textlength(k, font=f) + 60
                d.rounded_rectangle([80, 360, 80 + kw, 428], radius=34, fill=blend(ORANGE, a))
                d.text((110, 372), k, font=f, fill=blend(DARK, a))
            for i, l in enumerate(tlines):
                la = ease((t - 0.2 - i * 0.25) / 0.45)
                d.text((80, 470 + i * tsize * 1.25 + (1 - la) * 40), l, font=font(tsize), fill=blend(WHITE, la))
            bounce = abs(math.sin(min(t, 1.2) * math.pi * 1.6)) * 60 * max(0, 1 - t / 1.2)
            ma = ease((t - 0.3) / 0.4)
            if ma > 0:
                mx = (W - mascot.width) // 2
                my = int(H - 380 - mascot.height - bounce + (1 - ma) * 200)
                img.paste(mascot, (mx, my), mascot)
            fade = max(0.0, (t_intro - t) / 0.3) if t > t_intro - 0.3 else 1.0
            if fade < 1:
                img = Image.blend(Image.new("RGB", (W, H), BG), img, fade)
            return img
        t2 = t - t_intro
        if t2 < t_items:
            f = font(54 if len(items) <= 3 else 46)
            d.text((80, 360), tlines[0] + ("…" if len(tlines) > 1 else ""), font=font(44), fill=ORANGE)
            for i, it in enumerate(items):
                ia = ease((t2 - i * t_item) / 0.4)
                if ia <= 0:
                    continue
                y = 470 + i * 235 + (1 - ia) * 50
                d.rounded_rectangle([80, y, W - 80, y + 205], radius=30, fill=blend(CARD, ia))
                bullet(d, style, i, 110, y + 62, ia, r=40)
                tl = wrap(d, it, f, W - 80 - 230)[:2]
                for j, s in enumerate(tl):
                    d.text((225, y + 102 - len(tl) * 34 + j * 66), s, font=f, fill=blend(WHITE, ia))
            img.paste(small_mascot, (W - small_mascot.width - 50, H - 360 - small_mascot.height), small_mascot)
            return img
        t3 = t2 - t_items
        a = ease(t3 / 0.5)
        f1 = font(110)
        w1 = d.textlength("xeloba.ge", font=f1)
        d.text(((W - w1) / 2 - 0, 520 + (1 - a) * 40), "xeloba", font=f1, fill=blend(WHITE, a))
        d.text(((W - w1) / 2 + d.textlength("xeloba", font=f1), 520 + (1 - a) * 40), ".ge", font=f1, fill=blend(ORANGE, a))
        a2 = ease((t3 - 0.4) / 0.5)
        sl = wrap(d, SLOGAN, font(52), W - 200)
        for i, l in enumerate(sl):
            w = d.textlength(l, font=font(52))
            d.text(((W - w) / 2, 700 + i * 68), l, font=font(52), fill=blend(WHITE, a2))
        a3 = ease((t3 - 0.8) / 0.5)
        cta = spec.get("cta") or "დადე განცხადება უფასოდ"
        cf = font(50); cw = d.textlength(cta, font=cf) + 100
        pulse = 1 + 0.03 * math.sin(max(0, t3 - 1.3) * 5)
        bw, bh = cw * pulse, 120 * pulse
        d.rounded_rectangle([(W - bw) / 2, 900, (W + bw) / 2, 900 + bh], radius=60, fill=blend(ORANGE, a3))
        d.text(((W - d.textlength(cta, font=cf)) / 2, 900 + bh / 2 - 32), cta, font=cf, fill=blend(DARK, a3))
        if a3 > 0:
            img.paste(mascot, ((W - mascot.width) // 2, H - 360 - mascot.height + int((1 - a3) * 120)), mascot)
        return img

    ff = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-shortest", "-movflags", "+faststart", out_path], stdin=subprocess.PIPE)
    n = int(total * FPS)
    for k in range(n):
        im = frame(k / FPS)
        if k == int((t_intro - 0.6) * FPS):
            im.save(cover_path, quality=90)
        ff.stdin.write(im.tobytes())
    ff.stdin.close(); ff.wait()
    return out_path

def main():
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    out_dir = sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.join(out_dir, f"post-{int(spec['id']):02d}")
    if spec.get("format") == "reel":
        print(render_reel(spec, base + ".mp4", base + "-cover.jpg"))
        print(base + "-cover.jpg")
    else:
        print(render_photo(spec, base + ".jpg"))

if __name__ == "__main__":
    main()
