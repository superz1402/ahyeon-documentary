#!/usr/bin/env python3
"""Build timeline.json (EDL), captions.ass, metadata.json. Calibrates gaps to land 29:00."""
import json, math, os, re, subprocess

import os as _os
BASE = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
s = json.load(open(f"{BASE}/project/script.json"))
timing = json.load(open(f"{BASE}/project/timing.json"))
manifest = json.load(open(f"{BASE}/project/media_manifest.json"))

TARGET = s["target_total_s"]
INTRO, OUTRO = s["intro_music_s"], s["outro_music_s"]
FPS, W, H = s["fps"], s["width"], s["height"]

def relpath(p):
    p = p.replace("\\", "/")
    if "project/" in p:
        p = "project/" + p.split("project/")[-1]
    return p

tmap = {b["id"]: {**b, "file": relpath(b["file"]), "srt": relpath(b.get("srt", b["file"]))} for b in timing["beats"]}
qidx = {}
for a in manifest["assets"]:
    if a["kind"] == "image":
        qidx.setdefault(a["query"], []).append(a)
spare_pool = [a for a in manifest["assets"] if a["kind"] == "image" and a["query"] not in qidx]
all_imgs = [a for a in manifest["assets"] if a["kind"] == "image"]

def asset_for(query, used):
    cands = qidx.get(query) or spare_pool or all_imgs
    for a in cands:
        key = a["local_path"]
        if used.get(key, 0) < 2:  # reuse any image at most twice
            return a
    return (cands or all_imgs)[0]

dur_of = {bid: b["duration_s"] for bid, b in tmap.items()}
sum_dur = sum(dur_of.values())
base_pauses = [b.get("pause_after", s["beat_gap_s"]) for sg in s["segments"] for b in sg["beats"]]
sum_pause = sum(base_pauses)
scale = (TARGET - INTRO - OUTRO - sum_dur) / sum_pause
scale = max(0.4, min(2.6, scale))
print(f"speech={sum_dur:.0f}s pauses(base)={sum_pause:.0f}s scale={scale:.2f}")

clips, used, kb_i, cursor = [], {}, 0, 0.0
cursor = INTRO
kb_modes = ["in", "out", "left", "right"]
seg_starts = []
final_meta = []

for seg in s["segments"]:
    seg_starts.append({"seg": seg["id"], "act": seg["act"], "title": seg["chapter_title"], "start": round(cursor, 2)})
    for b in seg["beats"]:
        t = tmap[b["id"]]
        dur = t["duration_s"]
        vis, local_used = [], set()
        for i, v in enumerate(b.get("visuals", [])):
            if v.get("kind") == "card":
                p = f"project/cards/{b['id']}_{i}.png"
                if not os.path.exists(f"{BASE}/{p}"):
                    p = f"project/cards/ambient_{seg['id']}.png"
                vis.append({"kind": "card", "path": p})
            else:
                a = asset_for(v["query"], used)
                used[a["local_path"]] = used.get(a["local_path"], 0) + 1
                vis.append({"kind": "image", "path": a["local_path"], "asset_id": a["asset_id"],
                             "license": a["license"], "artist": a.get("artist", ""),
                             "credit": a.get("credit", ""), "origin_url": a.get("origin_url", ""),
                             "title": a.get("title", "")})
        if not vis:
            vis = [{"kind": "card", "path": f"project/cards/ambient_{seg['id']}.png"}]
        # share beat duration across visuals (each >= 2.4s)
        n = len(vis)
        share = max(2.4, dur / n)
        cuts = [share] * n
        # normalize to beat duration
        f = dur / sum(cuts)
        cuts = [c * f for c in cuts]
        for j, c in enumerate(cuts):
            mode = kb_modes[kb_i % 4]; kb_i += 1
            vis[j]["dur_s"] = round(c, 3)
            vis[j]["kb"] = mode
        clips.append({"beat_id": b["id"], "seg": seg["id"], "start": round(cursor, 3),
                       "dur_s": round(dur, 3), "voice": t["file"].replace(f"{BASE}/", ""),
                       "visuals": vis, "on_screen": b.get("on_screen", [])})
        cursor += dur + t["pause_after"] * scale

total = cursor + OUTRO
print(f"calibrated total: {total:.1f}s ({total/60:.2f} min) target {TARGET}s")

# ---- captions.ass ----
def ts(sec):
    h = int(sec // 3600); m = int(sec % 3600 // 60); sec2 = sec % 60
    return f"{h}:{m:02d}:{int(sec2):02d}.{int((sec2 % 1) * 100):02d}"

def parse_srt(path, offset):
    ev = []
    txt = open(path, encoding="utf-8").read()
    for block in re.split(r"\n\s*\n", txt.strip()):
        lines = [l for l in block.splitlines() if l.strip()]
        if len(lines) < 2 or "-->" not in lines[1]:
            continue
        m = re.match(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)", lines[1])
        if not m:
            continue
        g = [int(x) for x in m.groups()]
        t0 = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000 + offset
        t1 = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000 + offset
        text = " ".join(lines[2:]).strip()
        ev.append((t0, t1, text))
    return ev

ass = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 0", "ScaledBorderAndShadow: yes",
       "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: Cap,DejaVu Sans,46,&H00E6F0F5,&H000000FF,&H00101010,&H88000000,0,0,0,0,100,100,0.5,0,1,3,1,2,240,240,64,1",
       "Style: Receipt,Noto Serif SC,44,&H004CA8C9,&H000000FF,&H00101010,&H88000000,1,0,0,0,100,100,3.5,0,1,2,1,2,240,240,150,1",
       "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]

for c in clips:
    for t0, t1, text in parse_srt(f"{BASE}/{c['voice'].replace('.mp3', '.srt')}", c["start"]):
        text = text.replace("{", "(").replace("}", ")")
        ass.append(f"Dialogue: 0,{ts(t0)},{ts(min(t1, c['start'] + c['dur_s']))},Cap,,0,0,0,,{{\\fad(140,140)}}{text}")
    lines = c.get("on_screen") or []
    n = len(lines)
    for i, line in enumerate(lines):
        t0 = c["start"] + 0.45 + (c["dur_s"] - 1.2) * (i / n)
        t1 = c["start"] + 0.45 + (c["dur_s"] - 1.2) * ((i + 1) / n)
        line = line.replace("{", "(").replace("}", ")")
        ass.append(f"Dialogue: 1,{ts(t0)},{ts(t1)},Receipt,,0,0,0,,{{\\fad(200,200)}}{line}")

open(f"{BASE}/project/captions.ass", "w").write("\n".join(ass))

# ---- metadata.json ----
def mmss(sec):
    return f"{int(sec // 60):02d}:{int(sec % 60):02d}"

sources = ["Wikipedia — Babymonster / Jung Ahyeon", "YG Press (yg-life.com, ygfamily.com)",
           "NME", "Korea Herald", "Chosun Biz", "allkpop", "kprofiles.com",
           "KGMA / Mediabase via press reports", "Fan archive: ahyeonjung.netlify.app (flagged items only)"]
attribs = []
for a in manifest["assets"]:
    if a["kind"] == "image":
        who = a.get("artist") or a.get("credit") or "Unknown"
        attribs.append(f"· {a['title'][:70]} — {a['license']} — {who[:60]} — {a['origin_url']}")
    elif a["kind"] == "audio_music":
        attribs.append(f"· Music: {a['title']} by {a.get('artist','')} — {a['license']} — {a.get('origin_url','')}")

chapters = "\n".join(f"{mmss(x['start'])} {x['act']} — {x['title']}" for x in seg_starts)
desc = (f"{s['title']}\n\n"
        "A 29-minute documentary on BABYMONSTER's Jung Ahyeon — the most-watched debut in K-pop history, "
        "the seven months of silence, and the records that followed. Every figure in this film is sourced.\n\n"
        "CHAPTERS\n" + chapters +
        "\n\nSOURCES\n" + "\n".join("· " + x for x in sources) +
        "\n\nMUSIC & IMAGE ATTRIBUTIONS\n" + "\n".join(attribs[:80]) +
        "\n\nBuilt end-to-end by an autonomous AI agent pipeline: research → verified script → neural narration → "
        "licensed media → motion system → render. System: github.com/superz1402/ahyeon-documentary")
meta = {"title": "JUNG AHYEON — The One Who Was Worth the Wait (Documentary)",
        "description": desc[:4900], "tags": ["BABYMONSTER", "Ahyeon", "Jung Ahyeon", "K-pop documentary",
        "YGFanumentary", "BABYMONSTER Ahyeon", "MONSTIEZ", "K-pop", "documentary", "Ahyeon March", "Sheesh", "DRIP", "K-pop 2026"],
        "category_id": "24", "privacy_status": "unlisted", "language": "en",
        "chapters": seg_starts, "total_s": round(total, 1)}

json.dump({"target": TARGET, "actual": round(total, 1), "fps": FPS, "w": W, "h": H,
            "intro_music_s": INTRO, "outro_music_s": OUTRO, "gap_scale": round(scale, 3),
            "music": "project/music/bed.mp3", "clips": clips},
          open(f"{BASE}/project/timeline.json", "w"), indent=1)
json.dump(meta, open(f"{BASE}/project/metadata.json", "w"), indent=1, ensure_ascii=False)
print(f"clips={len(clips)} captions+metadata written")
