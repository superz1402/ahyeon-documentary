#!/usr/bin/env python3
"""Assemble full 29-min audio in numpy: voices placed at beat starts, CC0 bed ducked
under voice envelope, fades. Output: project/segments/mix_raw.wav (48k stereo s16)."""
import json, os, subprocess, sys, wave

import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE)
tl = json.load(open("project/timeline.json"))
TOTAL = tl["actual"]
SR = 48000
N = int(TOTAL * SR)
SEGS = "project/segments"
os.makedirs(SEGS, exist_ok=True)

def decode(path, mono=True):
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-f", "s16le", "-acodec", "pcm_s16le",
           "-ac", "1" if mono else "2", "-ar", str(SR), "-"]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0 or len(r.stdout) < 1000:
        raise SystemExit(f"decode failed {path}: {r.stderr[-200:]}")
    a = np.frombuffer(r.stdout, dtype=np.int16).astype(np.float32) / 32768.0
    return a

mix = np.zeros(N, dtype=np.float32)
env = np.zeros(N, dtype=np.float32)

for c in tl["clips"]:
    wav = f"{SEGS}/voice_{c['beat_id']}.wav"
    if not os.path.exists(wav) or os.path.getsize(wav) < 1000:
        pcm = decode(c["voice"])
        with wave.open(wav, "w") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((np.clip(pcm, -1, 1) * 32767).astype(np.int16).tobytes())
    else:
        with wave.open(wav) as w:
            pcm = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    s0 = int(c["start"] * SR)
    s1 = min(N, s0 + len(pcm))
    if s1 > s0:
        seg = pcm[: s1 - s0]
        mix[s0:s1] += seg
        env[s0:s1] += np.abs(seg)
    print(f"{c['beat_id']} placed @ {c['start']:.1f}s", flush=True)

# voice envelope: smooth abs peak for ducking
k = int(0.25 * SR)  # 250ms
kernel = np.ones(k, dtype=np.float32) / k
env = np.convolve(env, kernel, mode="same")
env = np.clip(env / max(env.max(), 1e-6), 0, 1)

# bed: decode, loop, gain, duck, fades
bed = decode("project/music/bed.mp3")
reps = int(np.ceil(N / len(bed)))
bed = np.tile(bed, reps)[:N]
bed_gain = 0.32 * (1.0 - 0.78 * env)  # duck to ~22% under voice
bed *= bed_gain
fade_in = int(2.5 * SR); fade_out = int(4 * SR)
bed[:fade_in] *= np.linspace(0, 1, fade_in)
bed[-fade_out:] *= np.linspace(1, 0, fade_out)

final = np.clip(mix + bed, -1.0, 1.0)
stereo = np.repeat(final[:, None], 2, axis=1)
pcm = (stereo * 32767).astype(np.int16)
with wave.open(f"{SEGS}/mix_raw.wav", "w") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f"mix_raw.wav written: {TOTAL}s, peak {np.abs(final).max():.3f}")
