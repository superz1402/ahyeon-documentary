#!/usr/bin/env python3
"""QC battery: duration, resolution, loudness, streams. Writes qc_report.json."""
import json, subprocess, sys, os

BASE = "/home/z/my-project/ahyeon-doc"
os.chdir(BASE)
tl = json.load(open("project/timeline.json"))
target = tl["actual"]
report = {"checks": []}

def check(name, ok, detail):
    report["checks"].append({"name": name, "pass": bool(ok), "detail": detail})

p = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                    "format=duration,size:stream=codec_name,width,height,r_frame_rate,codec_type",
                    "-of", "json", "project/final.mp4"], capture_output=True, text=True)
d = json.loads(p.stdout)
streams = d["streams"]
fmt = d["format"]
dur = float(fmt["duration"])
v = next(s for s in streams if s["codec_type"] == "video")
a = next(s for s in streams if s["codec_type"] == "audio")

check("duration_29min", abs(dur - target) < 45, f"{dur:.1f}s vs target {target}s (±45s)")
check("resolution", v["width"] == 1920 and v["height"] == 1080, f"{v['width']}x{v['height']}")
check("fps", abs(eval(v["r_frame_rate"]) - 30) < 0.1, v["r_frame_rate"])
check("video_codec", v["codec_name"] == "h264", v["codec_name"])
check("audio_codec", a["codec_name"] == "aac", a["codec_name"])
check("size", float(fmt["size"]) > 100e6, f"{float(fmt['size'])/1e6:.0f} MB")

loud = subprocess.run(["ffmpeg", "-i", "project/final.mp4", "-af", "loudnorm=print_format=json",
                       "-f", "null", "-"], capture_output=True, text=True).stderr
try:
    j = loud[loud.rindex("{"):loud.rindex("}") + 1]
    lj = json.loads(j)
    i_ = float(lj["input_i"])
    check("loudness_-14LUFS", -18 <= i_ <= -11, f"integrated {i_} LUFS")
except Exception as e:
    check("loudness_-14LUFS", False, f"measure failed: {e}")

report["overall"] = "PASS" if all(c["pass"] for c in report["checks"]) else "FAIL"
json.dump(report, open("project/qc_report.json", "w"), indent=1)
print(json.dumps(report, indent=1))
sys.exit(0 if report["overall"] == "PASS" else 2)
