#!/usr/bin/env python3
"""shorts.py — MoneyPrinterTurbo-powered YouTube Shorts engine.

Cuts three hook-first vertical Shorts from the VERIFIED documentary narration
(fact-gated to docs/INTEGRATIONS.md + dossier; no LLM at render time — scripts are
pinned, so CI is deterministic). MoneyPrinterTurbo (harry0703, MIT) provides the
render methodology: local materials -> 9:16 cover-crop -> edge-tts voiceover ->
burned captions -> mp4. A CC0 music bed is mixed at -26 dB post-render and the
master is normalized to -14 LUFS to match the film.

Usage:
  python3 pipeline/shorts.py render    # run MPT CLI x3 + post + QC
  python3 pipeline/shorts.py plan      # print the plan JSON, exit
Env:
  MPT_DIR   path to MoneyPrinterTurbo checkout (default integrations/MoneyPrinterTurbo)
  SKIP_MPT  if 1, only post-process existing MPT outputs (project/shorts/mpt_*.mp4)
"""
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
MPT_DIR = Path(os.environ.get("MPT_DIR", BASE / "integrations" / "MoneyPrinterTurbo"))
MEDIA = BASE / "project" / "media"
MUSIC = BASE / "project" / "music" / "bed.mp3"
OUT = BASE / "project" / "shorts"
OUT.mkdir(exist_ok=True)

VOICE = "en-US-AndrewMultilingualNeural"
CLIP_S = 4
BGM = None  # set by prepare_bgm() in main()

SHORTS = [
    {
        "id": "short1_the_wait",
        "title": "The debut that launched without her",
        "hashtags": "#BABYMONSTER #Ahyeon #Kpop #documentary",
        "queries": [
            "empty chair single light dark room",
            "airport night terminal lights window",
            "seoul night city neon skyline",
            "winter branch sky minimal",
        ],
        "script": (
            "YG's most-anticipated debut launched without its most-anticipated member. "
            "November 15th, 2023 — days before launch — YG announced Jung Ahyeon's health hiatus. "
            "The show did not stop. November 27th: Batter Up. "
            "Twenty-two point five nine million views in twenty-four hours — a record for any K-pop group debut, ever. "
            "One hundred million in eighteen days. "
            "Ahyeon watched all of it from the outside. Seven months. "
            "April 1st, 2024, she came back. Five weeks later came SHEESH — "
            "the debut that broke records without her, now doubled by her return. "
            "The full 29-minute documentary is on the channel."
        ),
    },
    {
        "id": "short2_the_records",
        "title": "The numbers stopped making sense",
        "hashtags": "#BABYMONSTER #Ahyeon #Kpop #records",
        "queries": [
            "seven silhouettes stage fog lights",
            "concert crowd lights dark arena",
            "award show stage spotlights audience",
            "concert phone lights raised hands",
            "rocket launch night long exposure",
        ],
        "script": (
            "2026 did not begin with a song. It began with a chart. "
            "Really Like You — a track from the previous autumn — hit number one on YouTube's "
            "global viral fifty, driven entirely by fan edits. "
            "March: Vogue Hong Kong. A cover titled The Only Way Is Up — "
            "a nineteen-year-old from Chuncheon on fashion's front page. "
            "Then the numbers stopped making sense. "
            "SHEESH: four hundred million views in seven hundred forty-seven days. "
            "The group: ten billion total views. "
            "Ahyeon: voted KGMA's Golden award with thirty-three thousand three hundred eighty fan votes. "
            "The full 29-minute documentary is on the channel."
        ),
    },
    {
        "id": "short3_the_dome",
        "title": "Fifty-five thousand seats, and her name",
        "hashtags": "#BABYMONSTER #Ahyeon #Kpop #dome",
        "queries": [
            "seven silhouettes stage fog lights",
            "hand microphone closeup stage light",
            "butterfly wings macro dark background",
            "sunrise over clouds airplane window",
            "concert crowd lights dark arena",
        ],
        "script": (
            "September 22nd and 23rd, 2026. Kyocera Dome, Osaka. Fifty-five thousand seats — "
            "a building that has hosted the biggest acts on the planet. "
            "For a K-pop group, headlining a Japanese dome is not a tour stop. It is an arrival. "
            "Three years earlier, Ahyeon was a trainee from Chuncheon "
            "singing Charlie Puth covers into a dorm-room microphone — "
            "a cover good enough that Puth himself sent a gift. "
            "Now fifty-five thousand people scream her name. "
            "A debut that broke records without her. A return that doubled it. "
            "The full 29-minute documentary is on the channel."
        ),
    },
]


def prepare_bgm() -> str | None:
    """MPT only accepts BGM inside its storage/bgm dir — copy the CC0 bed in."""
    if not MUSIC.exists():
        return None
    bgm_dir = MPT_DIR / "storage" / "bgm"
    bgm_dir.mkdir(parents=True, exist_ok=True)
    dest = bgm_dir / "bed.mp3"
    if not dest.exists() or dest.stat().st_size != MUSIC.stat().st_size:
        dest.write_bytes(MUSIC.read_bytes())
    return str(dest)


def resolve_assets(queries, want=12):
    manifest = json.load(open(BASE / "project" / "media_manifest.json"))
    assets = manifest["assets"]
    per_q = max(1, want // len(queries))
    picked = []
    for q in queries:
        ids = [a["asset_id"] for a in assets if a["query"] == q]
        for aid in ids[:per_q]:
            p = MEDIA / f"{aid}.jpg"
            if p.exists():
                picked.append(str(p))
    # top up deterministically if short
    if len(picked) < want:
        for a in assets:
            p = MEDIA / f"{a['asset_id']}.jpg"
            if str(p) not in picked and p.exists():
                picked.append(str(p))
            if len(picked) >= want:
                break
    return picked[:want]


def run(cmd, tag, timeout=1800, cwd=None):
    print(f"[shorts] {tag} ...", flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd)
    if r.returncode != 0:
        print(r.stderr[-1500:], file=sys.stderr)
        raise SystemExit(f"[shorts] FAIL {tag}")
    return r


def mpt_render(short):
    assets = resolve_assets(short["queries"])
    if not assets:
        raise SystemExit("[shorts] no media assets resolved")
    raw = OUT / f"mpt_{short['id']}.mp4"
    task_id = str(uuid.uuid4())
    cmd = [
        sys.executable, "cli.py",
        "--video-script", short["script"],
        "--video-source", "local",
        "--video-materials", ",".join(assets),
        "--video-aspect", "9:16",
        "--video-fit-mode", "cover",
        "--video-concat-mode", "sequential",
        "--video-transition-mode", "none",
        "--video-clip-duration", str(CLIP_S),
        "--voice-name", VOICE,
        "--voice-volume", "1.0",
        "--subtitle-enabled",
        "--font-size", "9",
        "--text-fore-color", "#FFFFFF",
        "--stroke-color", "#000000",
        "--stroke-width", "1.5",
        "--n-threads", "4",
        "--video-count", "1",
        "--stop-at", "video",
        "--task-id", task_id,
    ]
    if BGM:
        cmd[cmd.index("--stroke-width") + 2:cmd.index("--stroke-width") + 2] = \
            ["--bgm-type", "custom", "--bgm-file", BGM, "--bgm-volume", "0.15"]
    # MPT resolves --video-materials and storage/ against CWD — run inside MPT dir.
    r = run(cmd, f"MPT render {short['id']}", timeout=3300, cwd=str(MPT_DIR))
    # Discovery order: deterministic task dir -> stdout JSON -> newest final-*.mp4
    for cand in [MPT_DIR / "storage" / "tasks" / task_id / "final-1.mp4",
                 MPT_DIR / "storage" / "tasks" / task_id / "combined-1.mp4"]:
        if cand.exists() and cand.stat().st_size > 100_000:
            os.replace(cand, raw)
            return raw
    for line in r.stdout.splitlines():
        line = line.strip()
        if line.startswith("{"):
            data = json.loads(line)
            res = data.get("result", {})
            paths = res.get("videos") or res.get("video_paths") or []
            if paths and Path(paths[0]).exists():
                os.replace(paths[0], raw)
                return raw
    if raw.exists():
        return raw
    # last resort: newest file in MPT storage/tasks/<id>/...
    raise SystemExit(f"[shorts] MPT produced no video for {short['id']}")


def post(raw: Path, out: Path):
    """MPT already mixed the CC0 bed (custom BGM) — master to -14 LUFS + faststart."""
    fc = "[0:a]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]"
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw),
         "-map", "0:v", "-map", "0:a", "-filter_complex", fc,
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
         "-movflags", "+faststart", str(out)], f"post {out.name}")


def qc(path: Path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        capture_output=True, text=True)
    d = json.loads(r.stdout)
    v = [s for s in d["streams"] if s["codec_type"] == "video"][0]
    a = [s for s in d["streams"] if s["codec_type"] == "audio"][0]
    dur = float(d["format"]["duration"])
    checks = {
        "vertical_1080x1920": (v["width"], v["height"]) == (1080, 1920),
        "h264": v["codec_name"] == "h264",
        "aac": a["codec_name"] == "aac",
        "duration_25_90s": 25 <= dur <= 90,
    }
    ok = all(checks.values())
    return {"file": path.name, "dur_s": round(dur, 1), **checks, "pass": ok}


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "render"
    if mode == "plan":
        print(json.dumps([{**s, "materials": resolve_assets(s["queries"])} for s in SHORTS],
                         indent=2))
        return
    global BGM
    BGM = prepare_bgm()
    report = []
    for s in SHORTS:
        raw = OUT / f"mpt_{s['id']}.mp4"
        if os.environ.get("SKIP_MPT") != "1" or not raw.exists():
            if MPT_DIR.exists() and os.environ.get("SKIP_MPT") != "1":
                raw = mpt_render(s)
            else:
                raise SystemExit("[shorts] MPT outputs missing and SKIP_MPT set")
        final = OUT / f"{s['id']}.mp4"
        post(raw, final)
        report.append(qc(final))
    (OUT / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    if not all(r["pass"] for r in report):
        raise SystemExit("[shorts] QC FAILED")


if __name__ == "__main__":
    main()
