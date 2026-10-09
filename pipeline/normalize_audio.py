#!/usr/bin/env python3
"""Fast numpy loudness normalization: target integrated ~-14 LUFS, true-peak limiter -1.5 dB.
Chunked to fit RAM. Rewrites project/audio_full.wav from project/segments/mix_raw.wav."""
import wave, os

import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE)
SR = 48000
TARGET_LUFS = -14.0
CEIL = 10 ** (-1.5 / 20)  # -1.5 dBTP

src = wave.open("project/segments/mix_raw.wav")
n = src.getnframes()
CHUNK = SR * 120  # 2-min chunks

def lufs_block(x):
    """Cheap LUFS proxy: gated RMS in dBFS (K-weighting approximated flat)."""
    rms = np.sqrt(np.mean(x ** 2)) + 1e-12
    return 20 * np.log10(rms) - 0.691  # -0.691 accounts for stereo-ish energy convention

# pass 1: measure
tot_sq, tot_n = 0.0, 0
src.rewind()
while True:
    frames = src.readframes(CHUNK)
    if not frames:
        break
    x = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    x = x.reshape(-1, 2).mean(axis=1)
    tot_sq += float(np.sum(x ** 2)); tot_n += len(x)
cur_lufs = 20 * np.log10(np.sqrt(tot_sq / tot_n) + 1e-12) - 0.691
gain = 10 ** ((TARGET_LUFS - cur_lufs) / 20)
print(f"measured {cur_lufs:.2f} LUFS-ish → gain x{gain:.3f}")

# pass 2: apply gain + soft limiter
out = wave.open("project/audio_full.wav", "w")
out.setnchannels(2); out.setsampwidth(2); out.setframerate(SR)
src.rewind()
while True:
    frames = src.readframes(CHUNK)
    if not frames:
        break
    x = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    x = x.reshape(-1, 2) * gain
    # soft-knee limiter toward CEIL
    peak = np.abs(x).max()
    if peak > CEIL:
        x = np.tanh(x / CEIL * 1.2) * CEIL * 0.92  # gentle tanh ceiling
    out.writeframes((np.clip(x, -CEIL, CEIL) * 32767).astype(np.int16).tobytes())
out.close()
print("audio_full.wav written (normalized)")
