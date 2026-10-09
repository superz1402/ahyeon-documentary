#!/usr/bin/env python3
"""Local finalizer in resumable chunks (2-core friendly):
  step=audio   → mixed bed+voices, two-pass loudnorm → audio_full.m4a
  step=beats   → per-beat caption burn (ass shifted per beat), batched+resumable
  step=mux     → concat captioned beats + mux audio → project/final.mp4
Usage: python3 pipeline/render_final.py audio|beats|mux
"""
import json, os, re, subprocess, sys, time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE)
tl = json.load(open("project/timeline.json"))
TOTAL = tl["actual"]
FPS = tl["fps"]
SEGS = "project/segments"
os.makedirs(f"{SEGS}/beats", exist_ok=True)

def run(cmd, tag, timeout=None):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        sys.stderr.write(f"FAIL {tag}: {r.stderr[-500:]}\n")
        raise SystemExit(1)
    return r

def ts(sec):
    h = int(sec // 3600); m = int(sec % 3600 // 60); s2 = sec % 60
    return f"{h}:{m:02d}:{int(s2):02d}.{int((s2 % 1) * 100):02d}"

def beat_ass(clip):
    """Write per-beat shifted ASS; return path."""
    bs, be = clip["start"], clip["start"] + clip["dur_s"]
    path = f"{SEGS}/cap_{clip['beat_id']}.ass"
    if os.path.exists(path):
        return path
    head = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080",
            "WrapStyle: 0", "ScaledBorderAndShadow: yes", "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            "Style: Cap,DejaVu Sans,46,&H00E6F0F5,&H000000FF,&H00101010,&H88000000,0,0,0,0,100,100,0.5,0,1,3,1,2,240,240,64,1",
            "Style: Receipt,Noto Serif SC,44,&H004CA8C9,&H000000FF,&H00101010,&H88000000,1,0,0,0,100,100,3.5,0,1,2,1,2,240,240,150,1",
            "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    evs = []
    txt = open("project/captions.ass", encoding="utf-8").read()
    for line in txt.splitlines():
        if not line.startswith("Dialogue:"):
            continue
        m = re.match(r"Dialogue: (\d+),([^,]+),([^,]+),(Cap|Receipt),.*?,(.*?)$", line)
        if not m:
            continue
        layer, t0s, t1s, style, text = m.groups()
        def to_sec(t):
            h, m2, rest = t.split(":")
            return int(h) * 3600 + int(m2) * 60 + float(rest)
        t0, t1 = to_sec(t0s), to_sec(t1s)
        if t1 <= bs or t0 >= be:
            continue
        t0n, t1n = max(0.0, t0 - bs), min(t1, be) - bs
        evs.append(f"Dialogue: {layer},{ts(t0n)},{ts(t1n)},{style},,0,0,0,,{text}")
    open(path, "w").write("\n".join(head + evs))
    return path

step = sys.argv[1]

if step == "audio":
    # 1) build raw mix (voices + ducked bed)
    if not os.path.exists(f"{SEGS}/mix_raw.wav"):
        inputs = ["-stream_loop", "-1", "-t", str(TOTAL), "-i", "project/music/bed.mp3"]
        fc, vins = [], []
        for idx, c in enumerate(tl["clips"]):
            inputs += ["-i", c["voice"]]
            ms = int(c["start"] * 1000)
            fc.append(f"[{idx + 1}:a]aresample=48000,adelay={ms}|{ms}[v{idx}]")
            vins.append(f"[v{idx}]")
        fc.append("".join(vins) + f"amix=inputs={len(vins)}:normalize=0[voice]")
        fc.append("[0:a]aloop=loop=-1:size=2e9,atrim=0:" + str(TOTAL) + ",aresample=48000,volume=0.32,afade=t=in:st=0:d=2.5,afade=t=out:st=" + str(TOTAL - 4) + ":d=4[bed]")
        fc.append("[voice]asplit=2[sc][vmix]")
        fc.append("[bed][sc]sidechaincompress=threshold=0.015:ratio=7:attack=120:release=700[bedd]")
        fc.append("[vmix][bedd]amix=inputs=2:normalize=0[mix]")
        run(["ffmpeg", "-y", "-loglevel", "error"] + inputs +
            ["-filter_complex", ";".join(fc), "-map", "[mix]", "-ac", "2",
             f"{SEGS}/mix_raw.wav"], "audio-mix", timeout=520)
    # 2) loudnorm measure
    if not os.path.exists(f"{SEGS}/loud.json"):
        r = subprocess.run(["ffmpeg", "-i", f"{SEGS}/mix_raw.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                           capture_output=True, text=True, timeout=520)
        j = r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1]
        open(f"{SEGS}/loud.json", "w").write(j)
    # 3) apply measured loudnorm
    lj = json.load(open(f"{SEGS}/loud.json"))
    ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={lj['input_I']}:measured_TP={lj['input_TP']}:"
          f"measured_LRA={lj['input_LRA']}:measured_thresh={lj['input_thresh']}:offset={lj['target_offset']}")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{SEGS}/mix_raw.wav", "-af", ln,
         "-c:a", "aac", "-b:a", "192k", "project/audio_full.m4a"], "loudnorm", timeout=520)
    print("audio_full.m4a done")

elif step == "beats":
    t0 = time.time()
    done = 0
    for c in tl["clips"]:
        out = f"{SEGS}/beats/{c['beat_id']}.mp4"
        if os.path.exists(f"{out}.done"):
            continue
        if time.time() - t0 > 470:
            print(f"chunk budget reached at {done} beats this call"); break
        ass = beat_ass(c)
        # concat beat visuals with copy → temp, then burn captions (re-encode)
        lst = f"{SEGS}/beats/{c['beat_id']}_list.txt"
        with open(lst, "w") as f:
            for v in c["visuals"]:
                f.write(f"file '../../{SEGS}/{c['beat_id']}_{c['visuals'].index(v)}.mp4'\n")
        run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
             "-vf", f"ass={ass}", "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast",
             "-crf", "21", "-pix_fmt", "yuv420p", out], c["beat_id"], timeout=460)
        open(f"{out}.done", "w").write("1")
        done += 1
    n_done = len([x for x in os.listdir(f"{SEGS}/beats") if x.endswith('.done')])
    print(f"beats done: {n_done}/{len(tl['clips'])}")

elif step == "mux":
    with open(f"{SEGS}/beats/all.txt", "w") as f:
        for c in tl["clips"]:
            f.write(f"file '{c['beat_id']}.mp4'\n")
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{SEGS}/beats/all.txt",
         "-i", "project/audio_full.m4a", "-map", "0:v", "-map", "1:a",
         "-c:v", "copy", "-c:a", "copy", "-movflags", "+faststart", "-t", str(TOTAL),
         "project/final.mp4"], "mux", timeout=520)
    print("final.mp4 done")
