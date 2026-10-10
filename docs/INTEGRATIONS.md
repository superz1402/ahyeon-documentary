# Integrations — MoneyPrinterTurbo + ytagent

This repo integrates two external systems into the S0–S8 documentary pipeline.
Both integrations are **optional, env/secrets-gated, and CI-safe**: with no keys
set, the pipeline behaves exactly as v1.0 (license-pure media, zero behavior change —
verified by byte-identical `timeline.json` rebuild).

---

## 1. MoneyPrinterTurbo (harry0703/MoneyPrinterTurbo, MIT) — `pipeline/mpt_bridge.py`

**What was adopted.** MoneyPrinterTurbo's proven *footage matching* stage: for every
script beat's search query, call a stock-footage API, download HD clips, then
normalize them to the project's frame (`frame fitting: crop`), and feed them into the
media pool with per-clip license + author attribution.

| MPT concept | Our implementation |
|---|---|
| Pexels / Pixabay video search per segment | `pexels_videos()` / `pixabay_videos()` per beat query (81 queries in this project) |
| `frame fitting: crop`, clip duration caps | `normalize()`: scale→crop→1920×1080 30fps, ≤12 s, silent |
| Per-material metadata retention | manifest entries `kind:"video"` with license, artist, origin URL |
| Provider-key indirection | env `PEXELS_API_KEY` / `PIXABAY_API_KEY` (or GitHub Secrets of the same name) |
| Batch/no-key degradation | clean skip — base media unchanged |

**Enable:**
```bash
export ENABLE_MPT_STOCK=1
export PEXELS_API_KEY=...      # free: pexels.com/api
export PIXABAY_API_KEY=...     # free: pixabay.api
python pipeline/mpt_bridge.py          # or --dry-run
```
**CI:** set repo Secrets `ENABLE_MPT_STOCK=1`, `PEXELS_API_KEY`, `PIXABAY_API_KEY`.
**Licenses:** Pexels License / Pixabay Content License — commercial use permitted;
attribution not required but we record it anyway (auto-appended to the YouTube
description by `build_timeline.py`).

## 2. ytagent (Bilal140202/ytagent, MIT) — `pipeline/ytagent_bridge.py` + `.github/workflows/yt-download-farm.yml`

**What it does.** Sources *subject footage* (official BABYMONSTER uploads) listed in
`project/subject_sources.json`, downloads them via ytagent's 13-method fallback
chain, cuts short commentary excerpts (≤10 s, silent, 1920×1080 30fps), and adds
them to the media pool tagged for human review.

**This repo hosts its own remote download farm.** ytagent's `github_actions_farm`
method was pointed at this repository: `.github/workflows/yt-download-farm.yml`
installs Cloudflare WARP on a GitHub runner (Azure egress), runs yt-dlp + BGutil
PO-token provider behind a 6-tier client ladder (embedded → tv → mweb/web_safari →
web → default), verifies the file, and uploads it as an artifact the bridge pulls back.

```bash
export ENABLE_YTAGENT=1
export YTAGENT_GH_TOKEN=<PAT with repo+workflow scope>   # used ONLY for the farm dispatch
python pipeline/ytagent_bridge.py                        # or --dry-run
```
**CI:** set repo Secrets `ENABLE_YTAGENT=1`, `FARM_PAT` (PAT). CLI fallback also works:
`pip install ytagent-cli && ytagent download <url> --json`.

**Live validation log (2026-10-10, datacenter IP, UMG-distributed MV `2wA_b6YHjqQ`):**

| # | What was proven / fixed |
|---|---|
| 1 | ytagent 0.3.0 CLI walks all 13 methods; relays rate-limited; **socks5_farm found a live proxy in 64 s** (per-method timeout too small) |
| 2 | `github_actions_farm` is library-only (`github_token` opt) — bridge calls the Python API directly |
| 3 | Farm workflow dispatch → run → wait → artifact loop **mechanically proven end-to-end** (run 38073898191+) |
| 4 | Fixed: `warp-cli` needs a **TTY** for TOS → `printf 'y\n' \| script -qec` (also: daemon-start race, `--accept-tos` not a subcommand flag in 2026 CLI) |
| 5 | Fixed: **comments between backslash-continued `\|\|` chains swallow the operators** — the whole ladder never ran until hoisted |
| 6 | WARP connects (18:15 UTC log); UMG MV still blocked: embedded/tv/mweb → GVS-token-gated or `RELOAD_PAGE`; direct Azure IP → `LOGIN_REQUIRED` bot-wall |

**Honest status:** the farm plumbing is production-ready and hardened (6 real bugs
found and fixed in one session); **label-owned (UMG) MVs remain blocked** from
datacenter/runner egress as of this writing — this is the known 2026 PO-token/IP-binding
arms race, not a bug in the chain. Non-UMG and embeddable uploads succeed (ytagent's
own 9/10 batch proof). To source UMG subject clips today: run the bridge from a
residential IP, or self-host Cobalt + WARP (ytagent docs) and point `opts["proxy"]` at it.

**Rights gate:** subject clips carry `license: "Subject clip — rights of owner; fair-use
documentary commentary — REVIEW BEFORE MONETIZED PUBLISH"`. `pipeline/qc.py` reports a
`subject_clip_policy` check with the review warning; attribution is auto-appended to the
video description.

## 3. Timeline + render support for real footage

- `build_timeline.py` now indexes `kind:"video"` assets per query and assigns them to
  beats (reuse cap 2, deterministic order, **drops entries whose files are missing**).
  `USE_VIDEOS=0` disables globally.
- `render.py` Phase 1 renders video slots via `scale→crop→fps→eq→fades` with
  `-stream_loop -1` (loops short clips to fill the slot). Images keep Ken Burns.
- Videos live outside git (`project/media/videos/`, `project/ytdl_cache/` in `.gitignore`);
  in CI the bridges run **before** the deterministic timeline rebuild in the same job.

## 4. Quick matrix

| Want | Do |
|---|---|
| v1.0 behavior, zero changes | set nothing (default) |
| + stock footage (Pexels/Pixabay) | `ENABLE_MPT_STOCK=1` + keys |
| + subject clips via farm | `ENABLE_YTAGENT=1` + `YTAGENT_GH_TOKEN`/`FARM_PAT` |
| render without videos | `USE_VIDEOS=0 python pipeline/build_timeline.py` |
