#!/usr/bin/env python3
"""ytagent_bridge.py — subject-footage sourcing via Bilal140202/ytagent (MIT).

Feeds curated official-upload URLs + segment hints from project/subject_sources.json
through ytagent's 13-method fallback chain (incl. the github_actions_farm remote
download worker hosted in THIS repo), then cuts commentary segments into the
media pool for the timeline.

Env-gated + CI-safe:
  ENABLE_YTAGENT=1        -> attempts downloads (ytagent library mode -> CLI fallback)
  otherwise               -> clean skip (exit 0)
  --dry-run               -> list planned sources/segments, exit 0

Rights note: subject clips remain rights of their owners. Used here as short,
commentary-adjacent excerpts for a documentary context. Manifest entries carry a
"review before monetized publish" license flag — QC gate blocks auto-publish when
any subject clip is present (pipeline/qc.py policy flag below).
"""
import json, os, subprocess, sys, urllib.request
from pathlib import Path

import os as _os
BASE = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
VIDDIR = f"{BASE}/project/media/videos"
CACHE = f"{BASE}/project/ytdl_cache"
os.makedirs(VIDDIR, exist_ok=True); os.makedirs(CACHE, exist_ok=True)
W, H, FPS = 1920, 1080, 30
MAX_SEG_S = 10


def run(cmd, tag="", timeout=180):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        sys.stderr.write(f"[ytagent] FAIL {tag}: {r.stderr[-400:]}\n")
        return False
    return True


def normalize_cut(src, dest, start, dur):
    """Cut [start, start+dur] -> silent 1920x1080 30fps segment."""
    return run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(start), "-t", str(dur),
                "-i", src, "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,"
                                   f"crop={W}:{H},fps={FPS},eq=contrast=1.03:saturation=1.05",
                "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                "-pix_fmt", "yuv420p", dest], f"cut@{start}")


def probe_dur(path):
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "json", path], capture_output=True, text=True, timeout=30)
        return float(json.loads(r.stdout)["format"]["duration"])
    except Exception:
        return 0.0


def ytagent_download(video_id, out_dir):
    """Library mode first (opts the CLI can't pass: github_token), CLI fallback. Returns (path, meta)."""
    token = os.environ.get("YTAGENT_GH_TOKEN", "") or os.environ.get("GITHUB_TOKEN", "")
    # 1) library mode — full control incl. our-repo farm
    try:
        sys.path.insert(0, "")
        from ytagent.orchestrator import Orchestrator
        from ytagent.methods.base import default_opts
        from ytagent.agents.truth import TruthAgent
        from ytagent.agents.verifier import Verifier
        opts = default_opts(timeout=240)
        if token:
            opts.update(github_token=token, github_owner=os.environ.get("FARM_OWNER", "superz1402"),
                        github_repo=os.environ.get("FARM_REPO", "ahyeon-documentary"),
                        github_workflow="yt-download-farm.yml", github_wait_timeout=600)
        res = Orchestrator(TruthAgent(state_dir=Path(f"{BASE}/ytdl-agent/state")),
                           Verifier()).download(video_id, Path(out_dir), opts=opts)
        meta = {"mode": "library", "ok": res.ok, "method": res.method_used,
                "trace": res.trace_id, "attempts": [a.__dict__ for a in (res.attempts or [])]}
        if res.ok and res.final_path and os.path.exists(res.final_path):
            return res.final_path, meta
        return None, meta
    except ImportError:
        pass
    except Exception as e:
        sys.stderr.write(f"[ytagent] lib error: {e}\n")
    # 2) CLI fallback (pip install ytagent-cli)
    if not run(["bash", "-lc", "command -v ytagent >/dev/null"], "which"):
        return None, {"mode": "cli", "ok": False, "method": None, "trace": None, "attempts": []}
    r = subprocess.run(["ytagent", "download", f"https://www.youtube.com/watch?v={video_id}",
                        "--out-dir", out_dir, "--timeout", "240", "--json"],
                       capture_output=True, text=True, timeout=900)
    try:
        data = json.loads(r.stdout)
        meta = {"mode": "cli", "ok": data.get("ok", False), "method": data.get("method_used"),
                "trace": data.get("trace_id"), "attempts": data.get("attempts", [])}
        if data.get("ok") and data.get("final_path") and os.path.exists(data["final_path"]):
            return data["final_path"], meta
    except Exception:
        meta = {"mode": "cli", "ok": False, "method": None, "trace": None, "attempts": []}
    return None, meta


def main():
    dry = "--dry-run" in sys.argv
    enabled = os.environ.get("ENABLE_YTAGENT", "") == "1"
    src_path = f"{BASE}/project/subject_sources.json"
    if not os.path.exists(src_path):
        print("[ytagent] no project/subject_sources.json — skip")
        return
    if not enabled:
        print("[ytagent] ENABLE_YTAGENT not set — skip (license-pure base media stays)")
        return

    cfg = json.load(open(src_path))
    mpath = f"{BASE}/project/media_manifest.json"
    manifest = json.load(open(mpath))
    have = {a.get("origin_video_id") for a in manifest["assets"] if a["kind"] == "video" and a.get("source") == "youtube_subject"}

    log = {"sources": []}
    idx = 1 + sum(1 for a in manifest["assets"] if a["asset_id"].startswith("subj"))
    added = 0
    for src in cfg.get("sources", []):
        vid = src["video_id"]
        entry = {"video_id": vid, "label": src.get("label", ""), "segments": []}
        if vid in have:
            entry["status"] = "already-in-manifest"
            log["sources"].append(entry)
            continue
        segs = [s for s in src.get("segments", []) if 0 < s.get("dur_s", 0) <= MAX_SEG_S]
        if dry:
            print(f"  would fetch {vid} ({src.get('label', '')}) segments={len(segs)}")
            entry["status"] = "dry-run"
            log["sources"].append(entry)
            continue

        cached = f"{CACHE}/{vid}.mp4"
        if os.path.exists(cached) and os.path.getsize(cached) > 100_000:
            path, meta = cached, {"mode": "cache", "ok": True, "method": "cache", "trace": None, "attempts": []}
        else:
            path, meta = ytagent_download(vid, CACHE)
        entry["method"] = meta.get("method"); entry["trace"] = meta.get("trace")
        if not path:
            entry["status"] = "download-failed"
            log["sources"].append(entry)
            print(f"[ytagent] {vid}: all methods failed — skipping (base media unchanged)")
            continue

        total = probe_dur(path)
        for i, s in enumerate(segs):
            start = max(0.0, min(s["start_s"], max(total - s["dur_s"], 0)))
            aid = f"subj{idx:03d}"
            dest = f"{VIDDIR}/{aid}.mp4"
            if normalize_cut(path, dest, start, s["dur_s"]):
                manifest["assets"].append({
                    "asset_id": aid, "kind": "video", "query": s.get("query", src.get("label", vid)),
                    "source": "youtube_subject", "title": f"{src.get('label', vid)} seg{i + 1}",
                    "origin_url": f"https://www.youtube.com/watch?v={vid}&t={int(start)}s",
                    "local_path": f"project/media/videos/{aid}.mp4",
                    "license": "Subject clip — rights of owner; fair-use documentary commentary — REVIEW BEFORE MONETIZED PUBLISH",
                    "artist": src.get("credit", "YouTube uploader"), "credit": src.get("credit", ""),
                    "origin_video_id": vid, "w": W, "h": H, "dur_s": s["dur_s"]})
                entry["segments"].append({"asset_id": aid, "start": start, "dur": s["dur_s"]})
                print(f"[{aid}] {vid}@{start:.0f}s +{s['dur_s']}s ({src.get('label', '')})")
                idx += 1; added += 1
        json.dump(manifest, open(mpath, "w"), indent=1)   # checkpoint per source
        log["sources"].append(entry)

    json.dump(log, open(f"{BASE}/project/ytagent_log.json", "w"), indent=1, default=str)
    print(f"[ytagent] DONE. subject clips added={added}")


if __name__ == "__main__":
    main()
