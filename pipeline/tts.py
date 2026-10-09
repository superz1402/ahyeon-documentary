#!/usr/bin/env python3
"""Batch TTS for all beats via edge-tts CLI. Outputs voice/beat_<id>.mp3 + .srt + timing.json"""
import json, os, re, subprocess, sys, time

import os as _os
BASE = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
s = json.load(open(f"{BASE}/project/script.json"))
VOICE = s["voice"]
RATE = "-3%"
LEX = s["lexicon"]
OUT = f"{BASE}/project/voice"
os.makedirs(OUT, exist_ok=True)

def ttsify(text):
    for k, v in LEX.items():
        text = re.sub(rf"\b{re.escape(k)}\b", v, text)
    return text

timing = {"beats": [], "total_s": 0.0}
fails = []
for seg in s["segments"]:
    for b in seg["beats"]:
        bid = b["id"]
        mp3 = f"{OUT}/beat_{bid}.mp3"
        srt = f"{OUT}/beat_{bid}.srt"
        if os.path.exists(mp3) and os.path.getsize(mp3) > 1000:
            pass  # resumable
        else:
            ok = False
            for attempt in range(4):
                try:
                    r = subprocess.run(
                        ["edge-tts", "--text", ttsify(b["narration"]), "--voice", VOICE,
                         f"--rate={RATE}", "--write-media", mp3, "--write-subtitles", srt],
                        capture_output=True, timeout=90)
                    if r.returncode == 0 and os.path.exists(mp3) and os.path.getsize(mp3) > 1000:
                        ok = True; break
                except Exception as e:
                    sys.stderr.write(f"{bid} attempt {attempt}: {e}\n")
                time.sleep(2 * (attempt + 1))
            if not ok:
                fails.append(bid); continue
        dur = float(subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp3]).decode().strip())
        timing["beats"].append({"id": bid, "file": mp3, "srt": srt, "duration_s": round(dur, 3),
                                 "pause_after": b.get("pause_after", s["beat_gap_s"]), "provider": "edge-tts"})
        print(f"{bid}: {dur:.1f}s", flush=True)
        time.sleep(0.35)

timing["total_s"] = round(sum(x["duration_s"] for x in timing["beats"]), 2)
json.dump(timing, open(f"{BASE}/project/timing.json", "w"), indent=1)
print(f"DONE. beats={len(timing['beats'])} total_speech={timing['total_s']:.1f}s fails={fails}")
