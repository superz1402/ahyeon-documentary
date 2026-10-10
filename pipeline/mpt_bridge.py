#!/usr/bin/env python3
"""mpt_bridge.py — MoneyPrinterTurbo-style HD stock-footage enrichment (Pexels / Pixabay videos).

Adopted from harry0703/MoneyPrinterTurbo (MIT): search terms per script beat -> API video
search -> download -> normalize (scale/crop 1920x1080 30fps, silent) -> media pool.

Env-gated + CI-safe:
  ENABLE_MPT_STOCK=1  +  PEXELS_API_KEY / PIXABAY_API_KEY   -> fetches video clips
  otherwise                                                 -> clean skip (exit 0)
  --dry-run          -> print what it WOULD fetch, exit 0

License: Pexels License / Pixabay Content License — commercial use OK, attribution
appreciated but not required. We record author + origin URL per clip anyway.
"""
import json, os, subprocess, sys, urllib.parse, urllib.request

import os as _os
BASE = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
VIDDIR = f"{BASE}/project/media/videos"
os.makedirs(VIDDIR, exist_ok=True)
HDR = {"User-Agent": "AhyeonDocPipeline/1.1 (contact: agent@superz1402)"}
W, H, FPS = 1920, 1080, 30
MAX_PER_QUERY = 2
MAX_CLIP_S = 12


def run(cmd, tag=""):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(f"[mpt] FAIL {tag}: {r.stderr[-400:]}\n")
        return False
    return True


def http_json(url, key, timeout=20):
    req = urllib.request.Request(url, headers={**HDR, "Authorization": key})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def download(url, dest, timeout=90):
    req = urllib.request.Request(url, headers=HDR)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r, open(dest, "wb") as f:
            while True:
                chunk = r.read(1 << 16)
                if not chunk:
                    break
                f.write(chunk)
        return os.path.getsize(dest) > 20_000
    except Exception as e:
        sys.stderr.write(f"[mpt] DL fail {url[:80]}: {e}\n")
        return False


def normalize(src, dest, dur_s):
    """Scale+crop to 1920x1080 30fps, strip audio, cap length. MoneyPrinterTurbo 'frame fitting: crop'."""
    return run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-t", str(dur_s),
                "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                       f"fps={FPS},eq=contrast=1.03:saturation=1.05",
                "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                "-pix_fmt", "yuv420p", dest], "normalize")


def pexels_videos(q, key, n=6):
    """Pexels video search — HD landscape first (MPT picks top result per query)."""
    try:
        d = http_json(f"https://api.pexels.com/videos/search?query={urllib.parse.quote(q)}"
                      f"&per_page={n}&orientation=landscape&size=medium", key)
    except Exception as e:
        sys.stderr.write(f"[mpt] pexels '{q}': {e}\n")
        return []
    out = []
    for v in d.get("videos", []):
        files = v.get("video_files", []) or []
        hd = [f for f in files if f.get("width") and 1280 <= f["width"] <= 2560
              and f.get("file_type") == "video/mp4"]
        hd.sort(key=lambda f: abs((f.get("width") or 0) - W))
        if not hd:
            continue
        out.append({"url": hd[0]["link"], "w": hd[0]["width"], "h": hd[0]["height"],
                    "dur": v.get("duration", 0), "title": (v.get("url", "") or "").rstrip("/").split("/")[-1] or q,
                    "artist": (v.get("user") or {}).get("name", "Unknown"),
                    "origin": v.get("url", "")})
    return out


def pixabay_videos(q, key, n=6):
    try:
        d = http_json(f"https://pixabay.com/api/videos/?key={urllib.parse.quote(key)}"
                      f"&q={urllib.parse.quote(q)}&per_page={n}&safesearch=true", key)
    except Exception as e:
        sys.stderr.write(f"[mpt] pixabay '{q}': {e}\n")
        return []
    out = []
    for v in d.get("hits", []):
        files = v.get("videos", {}) or {}
        cand = files.get("large") or files.get("medium") or files.get("small")
        if not cand or not cand.get("url"):
            continue
        out.append({"url": cand["url"], "w": cand.get("width", W), "h": cand.get("height", H),
                    "dur": v.get("duration", 0), "title": q,
                    "artist": v.get("user", "Unknown"), "origin": v.get("pageURL", "")})
    return out


def main():
    dry = "--dry-run" in sys.argv
    enabled = os.environ.get("ENABLE_MPT_STOCK", "") == "1"
    pex_key = os.environ.get("PEXELS_API_KEY", "").strip()
    pix_key = os.environ.get("PIXABAY_API_KEY", "").strip()

    if not enabled:
        print("[mpt] ENABLE_MPT_STOCK not set — skip (base media unchanged)")
        return
    if not (pex_key or pix_key):
        print("[mpt] no PEXELS_API_KEY / PIXABAY_API_KEY — skip (license-pure base media stays)")
        return

    mpath = f"{BASE}/project/media_manifest.json"
    manifest = json.load(open(mpath))
    queries = manifest.get("queries") or []
    have = {a["query"] for a in manifest["assets"] if a["kind"] == "video"}
    todo = [q for q in queries if q not in have]
    print(f"[mpt] queries={len(todo)} pexels={'yes' if pex_key else 'no'} pixabay={'yes' if pix_key else 'no'}")
    if dry:
        for q in todo[:20]:
            print(f"  would fetch: {q}")
        return

    idx = 1 + sum(1 for a in manifest["assets"] if a["asset_id"].startswith("vid"))
    added = 0
    for q in todo:
        got = 0
        cands = (pexels_videos(q, pex_key) if pex_key else []) + (pixabay_videos(q, pix_key) if pix_key else [])
        for c in cands:
            if got >= MAX_PER_QUERY:
                break
            aid = f"vid{idx:03d}"
            raw = f"{VIDDIR}/{aid}_raw.mp4"
            dest = f"{VIDDIR}/{aid}.mp4"
            dur = min(MAX_CLIP_S, c["dur"] or MAX_CLIP_S)
            if download(c["url"], raw) and normalize(raw, dest, dur):
                os.remove(raw)
                manifest["assets"].append({
                    "asset_id": aid, "kind": "video", "query": q,
                    "source": "pexels" if "pexels" in c["origin"] else "pixabay",
                    "title": c["title"][:100], "origin_url": c["origin"],
                    "local_path": f"project/media/videos/{aid}.mp4",
                    "license": "Pexels License" if "pexels" in c["origin"] else "Pixabay Content License",
                    "artist": c["artist"][:80], "credit": c["origin"],
                    "w": c["w"], "h": c["h"], "dur_s": dur})
                print(f"[{aid}] '{q}' <- {c['origin'][:70]} ({dur:.0f}s)")
                idx += 1; got += 1; added += 1
            elif os.path.exists(raw):
                os.remove(raw)
        json.dump(manifest, open(mpath, "w"), indent=1)   # checkpoint per query

    print(f"[mpt] DONE. video clips added={added}")


if __name__ == "__main__":
    main()
