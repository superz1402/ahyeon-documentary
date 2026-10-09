#!/usr/bin/env python3
"""Renderer: Phase1 per-visual segments (zoompan Ken Burns) → Phase2 concat →
Phase3 audio mix (ducked music + voices) + caption burn + loudnorm. Resumable."""
import json, os, subprocess, sys, math

BASE = "/home/z/my-project/ahyeon-doc"
os.chdir(BASE)
tl = json.load(open("project/timeline.json"))
FPS, W, H = tl["fps"], tl["w"], tl["h"]
TOTAL = tl["actual"]
SEGS = "project/segments"
os.makedirs(SEGS, exist_ok=True)
PRESCALE = 2160  # headroom for zoom

def run(cmd, tag=""):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(f"FAIL {tag}: {r.stderr[-600:]}\n")
        raise SystemExit(1)

def kb_filter(mode, dur, fade_in=True, fade_out=False):
    frames = int(dur * FPS)
    p = f"(on/{max(frames - 1, 1)})"
    if mode == "in":
        z = f"1+0.10*{p}"; x = f"(iw-iw/zoom)/2"; y = f"(ih-ih/zoom)/2"
    elif mode == "out":
        z = f"1.10-0.10*{p}"; x = f"(iw-iw/zoom)/2"; y = f"(ih-ih/zoom)/2"
    elif mode == "left":
        z = "1.09"; x = f"(iw-iw/zoom)*(1-{p}*0.6)"; y = "(ih-ih/zoom)/2"
    else:
        z = "1.09"; x = f"(iw-iw/zoom)*({p}*0.6)"; y = "(ih-ih/zoom)/2"
    f = (f"scale={PRESCALE}:-2,crop={PRESCALE}:{int(PRESCALE * H / W)},"
         f"zoompan=z='{z}':x='{x}':y='{y}':d=1:s={W}x{H}:fps={FPS}")
    f += ",eq=contrast=1.03:saturation=1.05"
    if fade_in: f += f",fade=t=in:st=0:d=0.28"
    if fade_out: f += f",fade=t=out:st={max(dur - 2.6, 0):.2f}:d=2.6"
    return f

def seg_out(name, dur, filt, source_args):
    out = f"{SEGS}/{name}.mp4"
    done = f"{SEGS}/{name}.done"
    if os.path.exists(done):
        return out
    tmp = f"{SEGS}/{name}.tmp.mp4"
    cmd = (["ffmpeg", "-y", "-loglevel", "error"] + source_args +
           ["-vf", filt, "-frames:v", str(int(dur * FPS)), "-r", str(FPS),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-pix_fmt", "yuv420p", tmp])
    run(cmd, name)
    os.replace(tmp, out)
    open(done, "w").write(f"{dur}\n")
    return out

# ---- Phase 1: intro + all visual segments + outro ----
order = []

# intro (music-only opening over ambient card, fade from black)
n = "seg_intro"
order.append(seg_out(n, tl["intro_music_s"],
    kb_filter("in", tl["intro_music_s"], fade_in=True).replace(",eq=", ",fade=t=in:st=0:d=1.4:color=black,eq="),
    ["-loop", "1", "-t", str(tl["intro_music_s"]), "-i", "project/cards/ambient_seg0.png"]))

for c in tl["clips"]:
    for i, v in enumerate(c["visuals"]):
        name = f"{c['beat_id']}_{i}"
        is_last_of_film = (c["beat_id"] == tl["clips"][-1]["beat_id"] and i == len(c["visuals"]) - 1)
        fade_out = is_last_of_film
        order.append(seg_out(name, v["dur_s"], kb_filter(v["kb"], v["dur_s"], True, fade_out),
                             ["-loop", "1", "-t", str(v["dur_s"]), "-i", v["path"]]))
    print(f"seg {c['beat_id']} ok", flush=True)

# outro black
n = "seg_outro"
out = f"{SEGS}/{n}.mp4"; done = f"{SEGS}/{n}.done"
if not os.path.exists(done):
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
         f"color=c=black:s={W}x{H}:r={FPS}:d={tl['outro_music_s']}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
         f"{SEGS}/{n}.tmp.mp4"], n)
    os.replace(f"{SEGS}/{n}.tmp.mp4", out); open(done, "w").write(str(tl["outro_music_s"]))
order.append(out)

with open(f"{SEGS}/list.txt", "w") as f:
    for o in order:
        f.write(f"file '{o}'\n")

# ---- Phase 2: concat (video-only master) ----
if not os.path.exists("project/master_video.mp4") or os.path.getsize("project/master_video.mp4") < 10_000_000:
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{SEGS}/list.txt",
         "-c", "copy", "project/master_video.mp4"], "concat")
print("master video ready", flush=True)

# ---- Phase 3: audio mix + captions + final ----
if os.path.exists("project/final.mp4") and os.path.getsize("project/final.mp4") > 50_000_000:
    print("final.mp4 exists — skipping Phase 3"); sys.exit(0)

inputs = ["-i", "project/master_video.mp4", "-stream_loop", "-1", "-t", str(TOTAL), "-i", "project/music/bed.mp3"]
fc = []
vins = []
for idx, c in enumerate(tl["clips"]):
    inputs += ["-i", c["voice"]]
    ms = int(c["start"] * 1000)
    fc.append(f"[{idx + 2}:a]aresample=48000,adelay={ms}|{ms}[v{idx}]")
    vins.append(f"[v{idx}]")
fc.append("".join(vins) + f"amix=inputs={len(vins)}:normalize=0,volume=1.0[voice]")
fc.append("[1:a]aloop=loop=-1:size=2e9,atrim=0:" + str(TOTAL) + ",aresample=48000,volume=0.32,afade=t=in:st=0:d=2.5,afade=t=out:st=" + str(TOTAL - 4) + ":d=4[bed]")
fc.append("[bed][voice]sidechaincompress=threshold=0.015:ratio=7:attack=120:release=700[bedd]")
fc.append("[voice][bedd]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[aout]")

cmd = (["ffmpeg", "-y", "-loglevel", "error", "-threads", "0"] + inputs +
       ["-filter_complex", ";".join(fc),
        "-map", "0:v", "-map", "[aout]",
        "-vf", "ass=project/captions.ass",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", "-t", str(TOTAL),
        "project/final.mp4"])
run(cmd, "final")
print("FINAL RENDER DONE")
