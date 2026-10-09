#!/usr/bin/env python3
"""Source license-safe media: Wikimedia Commons + Openverse images, CC0 music, optional subject clips.
Writes project/media_manifest.json with licenses per asset."""
import json, os, subprocess, sys, time, urllib.parse, urllib.request

import os as _os
BASE = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
MEDIA = f"{BASE}/project/media"
MUSIC = f"{BASE}/project/music"
os.makedirs(MEDIA, exist_ok=True); os.makedirs(MUSIC, exist_ok=True)
HDR = {"User-Agent": "AhyeonDocResearch/1.0 (contact: agent@superz1402)"}

s = json.load(open(f"{BASE}/project/script.json"))
queries = []
for seg in s["segments"]:
    for b in seg["beats"]:
        for v in b.get("visuals", []):
            if v.get("kind") == "image":
                q = v["query"]
                if q not in queries:
                    queries.append(q)

manifest = {"assets": [], "queries": queries}

def get_json(url, timeout=25):
    req = urllib.request.Request(url, headers=HDR)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

def download(url, dest, timeout=60):
    if os.path.exists(dest) and os.path.getsize(dest) > 5000:
        return True
    req = urllib.request.Request(url, headers=HDR)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r, open(dest, "wb") as f:
            while True:
                chunk = r.read(1 << 16)
                if not chunk: break
                f.write(chunk)
        return os.path.getsize(dest) > 5000
    except Exception as e:
        sys.stderr.write(f"DL fail {url[:80]}: {e}\n")
        return False

def commons_search(q, n=6):
    url = ("https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search"
           f"&gsrsearch={urllib.parse.quote(q)}&gsrnamespace=6&gsrlimit={n}"
           "&prop=imageinfo&iiprop=url|extmetadata|size&iiurlwidth=1920")
    try:
        d = get_json(url)
    except Exception:
        return []
    out = []
    for p in (d.get("query", {}).get("pages", {}) or {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        if not ii.get("url"): continue
        mime = ii.get("mime", "")
        if not mime.startswith("image/"): continue
        if mime == "image/svg+xml": continue
        w, h = ii.get("width", 0), ii.get("height", 0)
        if w < 900 or h < 600: continue
        meta = ii.get("extmetadata", {}) or {}
        lic = (meta.get("LicenseShortName", {}) or {}).get("value", "Unknown")
        if any(x in lic for x in ("fair use", "Fair use")): continue
        artist = (meta.get("Artist", {}) or {}).get("value", "Unknown")
        credit = (meta.get("Credit", {}) or {}).get("value", "")
        out.append({"source": "wikimedia", "query": q, "title": p.get("title", ""),
                    "url": ii.get("thumburl") or ii.get("url"), "page": ii.get("descriptionurl", ""),
                    "license": f"Commons:{lic}", "artist": artist, "credit": credit,
                    "w": w, "h": h})
    return out

def openverse_search(q, n=6):
    url = (f"https://api.openverse.org/v1/images/?q={urllib.parse.quote(q)}&license_type=commercial"
           f"&page_size={n}&mature=false")
    try:
        d = get_json(url)
    except Exception:
        return []
    out = []
    for r in d.get("results", []):
        w, h = r.get("width") or 0, r.get("height") or 0
        if (w and h) and (w < 1000 or h < 650): continue
        out.append({"source": "openverse", "query": q, "title": r.get("title", ""),
                    "url": r.get("url"), "page": r.get("foreign_landing_url", ""),
                    "license": f"CC:{(r.get('license') or '?').upper()} {r.get('license_version','')}".strip(),
                    "artist": (r.get("creator") or "Unknown"), "credit": r.get("source", ""),
                    "w": w, "h": h})
    return out

def clean(s):
    return s.replace("&nbsp;", " ").replace("&#39;", "'").replace("&quot;", '"')

idx = 0
per_q_cap = 3
for q in queries:
    got = 0
    for cand in commons_search(q) + openverse_search(q):
        if got >= per_q_cap: break
        idx += 1
        aid = f"img{idx:03d}"
        ext = ".jpg"
        dest = f"{MEDIA}/{aid}{ext}"
        if download(cand["url"], dest):
            got += 1
            manifest["assets"].append({
                "asset_id": aid, "kind": "image", "query": q, "source": cand["source"],
                "title": clean(cand["title"])[:120], "origin_url": cand["page"],
                "local_path": f"project/media/{aid}{ext}", "license": cand["license"],
                "artist": clean(cand["artist"])[:100], "credit": clean(cand["credit"])[:100],
                "w": cand["w"], "h": cand["h"]})
            print(f"[{aid}] {q} ← {cand['source']} ({cand['license']})", flush=True)
        time.sleep(0.4)

# CC0 / CC music
music_done = False
for q in ["ambient cinematic drone", "cinematic ambient pad", "ambient atmosphere dark"]:
    try:
        d = get_json(f"https://api.openverse.org/v1/audio/?q={urllib.parse.quote(q)}&license=cc0&page_size=8")
        for r in d.get("results", []):
            url = r.get("url") or ""
            if not url or not url.startswith("http"): continue
            if download(url, f"{MUSIC}/bed.mp3", timeout=120):
                manifest["assets"].append({"asset_id": "music01", "kind": "audio_music", "query": q,
                    "source": "openverse-audio", "title": r.get("title", "")[:120],
                    "origin_url": r.get("foreign_landing_url", ""), "local_path": "project/music/bed.mp3",
                    "license": f"CC0 ({r.get('license_version','')})",
                    "artist": (r.get("creator") or "Unknown")[:100], "credit": r.get("source", "")})
                print(f"[music01] {q} ← {r.get('title','')[:60]}", flush=True)
                music_done = True; break
    except Exception as e:
        sys.stderr.write(f"music {q}: {e}\n")
    if music_done: break

json.dump(manifest, open(f"{BASE}/project/media_manifest.json", "w"), indent=1)
print(f"DONE. images={sum(1 for a in manifest['assets'] if a['kind']=='image')} music={'yes' if music_done else 'NO'} queries={len(queries)}")
