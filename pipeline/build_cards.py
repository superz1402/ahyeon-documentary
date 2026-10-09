#!/usr/bin/env python3
"""Build all card PNGs (1920x1080) from script.json — the film's visual identity system."""
import json, math, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

import os as _os
BASE = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
s = json.load(open(f"{BASE}/project/script.json"))
OUT = f"{BASE}/project/cards"
os.makedirs(OUT, exist_ok=True)

W, H = 1920, 1080
BG = (10, 10, 10)
GOLD = (201, 168, 76)
IVORY = (245, 240, 230)
DIM = (138, 131, 120)
F_DISPLAY = s["fonts"]["display"]
F_BLACK = s["fonts"]["display_black"]
F_BODY = s["fonts"]["body"]

_vign = None
def vignette():
    global _vign
    if _vign is None:
        v = Image.new("L", (W, H), 0)
        d = ImageDraw.Draw(v)
        d.ellipse([-W * 0.25, -H * 0.35, W * 1.25, H * 1.35], fill=70)
        v = v.filter(ImageFilter.GaussianBlur(220))
        _vign = v
    return _vign

def base_card():
    img = Image.new("RGB", (W, H), BG)
    img.paste(Image.new("RGB", (W, H), (0, 0, 0)), (0, 0), vignette())
    return img

def font(path, size):
    return ImageFont.truetype(path, size)

def tracked(draw, xy, text, fnt, fill, tracking=8, anchor_center_w=None):
    x, y = xy
    widths = [draw.textlength(ch, font=fnt) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    if anchor_center_w:
        x = (anchor_center_w - total) / 2
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += w + tracking
    return total

def wrap(draw, text, fnt, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= maxw:
            cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def rule(draw, x, y, w=120, color=GOLD, h=3):
    draw.rectangle([x, y, x + w, y + h], fill=color)

def card_title(kicker, title, subtitle):
    img = base_card(); d = ImageDraw.Draw(img)
    fk = font(F_BODY, 36); ft = font(F_BLACK, 148); fs = font(F_DISPLAY, 52)
    tracked(d, (0, 400), kicker.upper(), fk, GOLD, 14, W)
    tw = d.textlength(title, font=ft)
    d.text(((W - tw) / 2, 452), title, font=ft, fill=IVORY)
    rule(d, (W - 130) / 2, 646, 130)
    if subtitle:
        sw = d.textlength(subtitle, font=fs)
        d.text(((W - sw) / 2, 690), subtitle, font=fs, fill=DIM)
    return img

def card_chapter(act, title):
    img = base_card(); d = ImageDraw.Draw(img)
    fk = font(F_BODY, 40); ft = font(F_BLACK, 110)
    tracked(d, (0, 430), act.upper(), fk, GOLD, 16, W)
    lines = wrap(d, title, ft, 1600)
    y = 520
    for ln in lines:
        tw = d.textlength(ln, font=ft)
        d.text(((W - tw) / 2, y), ln, font=ft, fill=IVORY)
        y += 130
    rule(d, (W - 130) / 2, y + 10, 130)
    return img

def card_stat(kicker, big, small):
    img = base_card(); d = ImageDraw.Draw(img)
    fk = font(F_BODY, 36); fb = font(F_BLACK, 210); fsm = font(F_BODY, 40)
    tracked(d, (0, 300), kicker.upper(), fk, GOLD, 14, W)
    bw = d.textlength(big, font=fb)
    size = 210
    while bw > 1700 and size > 90:
        size -= 10; fb = font(F_BLACK, size); bw = d.textlength(big, font=fb)
    d.text(((W - bw) / 2, 370), big, font=fb, fill=GOLD)
    y = 640
    for ln in wrap(d, small, fsm, 1500)[:2]:
        lw = d.textlength(ln, font=fsm)
        d.text(((W - lw) / 2, y), ln, font=fsm, fill=IVORY)
        y += 58
    rule(d, (W - 90) / 2, y + 24, 90)
    return img

def card_quote(quote, attr):
    img = base_card(); d = ImageDraw.Draw(img)
    fq = font(F_DISPLAY, 88); fa = font(F_BODY, 34)
    q = f"\u201c{quote}\u201d"
    lines = wrap(d, q, fq, 1440)
    y = 470 - (len(lines) - 1) * 55
    d.rectangle([260, y - 30, 266, y + len(lines) * 110], fill=GOLD)
    x = 320
    for ln in lines:
        d.text((x, y), ln, font=fq, fill=IVORY)
        y += 110
    y += 40
    tracked(d, (x, y), ("— " + attr).upper(), fa, DIM, 4)
    return img

def card_timeline(date, event):
    img = base_card(); d = ImageDraw.Draw(img)
    fd = font(F_BLACK, 84); fe = font(F_DISPLAY, 62)
    tracked(d, (0, 430), date.upper(), fd, GOLD, 10, W)
    y = 560
    for ln in wrap(d, event, fe, 1560)[:3]:
        lw = d.textlength(ln, font=fe)
        d.text(((W - lw) / 2, y), ln, font=fe, fill=IVORY)
        y += 78
    d.ellipse([W / 2 - 7, y + 30, W / 2 + 7, y + 44], fill=GOLD)
    return img

def card_credits(lines, note):
    img = base_card(); d = ImageDraw.Draw(img)
    fl = font(F_BODY, 32); fn = font(F_BODY, 27)
    y = 420
    for ln in lines:
        lw = d.textlength(ln, font=fl)
        d.text(((W - lw) / 2, y), ln, font=fl, fill=DIM)
        y += 54
    y += 40
    for i, ln in enumerate(wrap(d, note, fn, 1400)):
        lw = d.textlength(ln, font=fn)
        d.text(((W - lw) / 2, y + i * 40), ln, font=fn, fill=(90, 85, 76))
    rule(d, (W - 90) / 2, 380, 90)
    return img

def card_ambient(act_label, variant):
    """Abstract minimal texture card — gold geometry on black."""
    img = base_card(); d = ImageDraw.Draw(img, "RGBA")
    cx, cy = W / 2, H / 2
    n = [7, 11, 13][variant % 3]
    for i in range(n):
        r = 140 + i * 68
        a = max(18, 60 - i * 5)
        wdt = 2 if i % 2 else 3
        d.arc([cx - r, cy - r, cx + r, cy + r], i * (360 / n), i * (360 / n) + 110 + variant * 20,
              fill=(201, 168, 76, a), width=wdt)
    fk = font(F_BODY, 34)
    tracked(d, (0, 940), act_label.upper(), fk, (110, 100, 84), 12, W)
    return img

count = 0
for seg in s["segments"]:
    amb = f"{OUT}/ambient_{seg['id']}.png"
    card_ambient(f"{seg['act']} · {seg['chapter_title']}", abs(hash(seg['id'])) % 3).save(amb)
    for b in seg["beats"]:
        for i, v in enumerate(b.get("visuals", [])):
            if v.get("kind") != "card":
                continue
            c = v["card"]
            if c == "title":
                img = card_title(v["kicker"], v["title"], v.get("subtitle", ""))
            elif c == "chapter":
                img = card_chapter(v["act"], v["title"])
            elif c == "stat":
                img = card_stat(v["kicker"], v["big"], v["small"])
            elif c == "quote":
                img = card_quote(v["quote"], v["attr"])
            elif c == "timeline":
                img = card_timeline(v["date"], v["event"])
            elif c == "credits":
                img = card_credits(v["lines"], v["small_note"])
            else:
                continue
            img.save(f"{OUT}/{b['id']}_{i}.png")
            count += 1

print(f"cards built: {count} + {len(s['segments'])} ambient")
