#!/usr/bin/env python3
"""Fast QC: ffprobe metadata checks + sampled loudness (numpy, 4x60s windows)."""
import json, subprocess, sys, os
import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE)
tl = json.load(open("project/timeline.json"))
target = tl["actual"]
report = {"checks": []}

def check(name, ok, detail):
    report["checks"].append({"name": name, "pass": bool(ok), "detail": detail})

p = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                    "format=duration,size,bit_rate:stream=codec_name,width,height,r_frame_rate,codec_type",
                    "-of", "json", "project/final.mp4"], capture_output=True, text=True)
d = json.loads(p.stdout)
fmt, streams = d["format"], d["streams"]
dur = float(fmt["duration"])
v = next(s for s in streams if s["codec_type"] == "video")
a = next(s for s in streams if s["codec_type"] == "audio")

check("duration_29min", abs(dur - target) < 45, f"{dur:.1f}s vs {target}s (±45s)")
check("resolution_1080p", v["width"] == 1920 and v["height"] == 1080, f"{v['width']}x{v['height']}")
check("fps_30", abs(eval(v["r_frame_rate"]) - 30) < 0.1, v["r_frame_rate"])
check("video_h264", v["codec_name"] == "h264", v["codec_name"])
check("audio_aac", a["codec_name"] == "aac", a["codec_name"])
check("size_sane", 100e6 < float(fmt["size"]) < 3e9, f"{float(fmt['size'])/1e6:.0f} MB @ {float(fmt['bit_rate'])/1e6:.2f} Mbps")

# sampled loudness: 4 windows x 60s
vals = []
for pos in [0.08, 0.35, 0.62, 0.9]:
    start = dur * pos
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{start:.0f}", "-t", "60", "-i", "project/final.mp4",
                        "-f", "s16le", "-ac", "1", "-ar", "48000", "-"], capture_output=True)
    x = np.frombuffer(r.stdout, dtype=np.int16).astype(np.float32) / 32768.0
    if len(x) > 48000:
        rms = np.sqrt(np.mean(x ** 2)) + 1e-12
        vals.append(20 * np.log10(rms) - 0.691)
avg = sum(vals) / len(vals)
check("loudness~-14LUFS(sampled)", -18 <= avg <= -10, f"sampled avg {avg:.1f} dBFS-LUFS-ish {[round(v,1) for v in vals]}")

report["overall"] = "PASS" if all(c["pass"] for c in report["checks"]) else "FAIL"
json.dump(report, open("project/qc_report.json", "w"), indent=1)
print(json.dumps(report, indent=1))
sys.exit(0 if report["overall"] == "PASS" else 2)
