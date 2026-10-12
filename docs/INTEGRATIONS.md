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

---

## 5. Round 2 — 2026-10-12: full MPT engine + farm hardening

### MoneyPrinterTurbo is now IN the repo

- Vendored as a **pinned git submodule**: `integrations/MoneyPrinterTurbo` @ `4204d0f` (MIT, v1.3.8).
- **Live NIM script-generation run** (the real MPT LLM path): MPT CLI `--stop-at script`,
  `llm_provider="openai"` → `https://integrate.api.nvidia.com/v1`,
  `nvidia/nemotron-3-super-120b-a12b`. Task `c422312c` produced a fact-correct,
  slop-free Short script from a fact-guarded prompt (verified against the dossier).
  Config lives inside the submodule working tree (`config.toml`, MPT-gitignored).
- **Shorts engine**: `pipeline/shorts.py` + `.github/workflows/shorts.yml`.
  Three hook-first 9:16 Shorts cut from the VERIFIED narration (no LLM at render
  time — deterministic CI): local licensed media pool → MPT render methodology
  (9:16 cover-crop, sequential concat, 4 s clips) → edge-tts `en-US-Andrew` →
  burned captions → CC0 music bed via `--bgm-type custom` (must live inside MPT's
  `storage/bgm/` — the workflow stages it) → mp4 → −14 LUFS master → QC gate
  (1080×1920, h264, aac, 25–90 s) → Release `shorts-v1`.
- **Smoke-render proof** (sandbox, 12 s task): MPT produced `1080×1920 h264+aac`,
  materials + TTS + captions + custom BGM all verified. PPU throttling limits
  sandbox render speed; CI renders the real Shorts.
- MPT lessons encoded: `--task-id` must be a UUID; `--subtitle-enabled` is a
  BooleanOptionalAction (flag only); BGM file path must be inside `storage/bgm/`
  or `resource/songs/`; output discovery prefers `storage/tasks/<task_id>/final-1.mp4`.

### ytagent farm — round 2 results (runs 38188083171 → 38188954349)

| # | What was fixed / proven |
|---|---|
| 1 | `warp-cli` **2026.8 does accept a global `--accept-tos`** flag on every subcommand (registration/mode/connect/status) — non-interactive TOS acceptance on runners |
| 2 | Interleaved comments in backslash-continued `\|\|` ladders still bit us in a different form — replaced the ladder with a `try_dl()` shell function (no continuation parsing hazards) |
| 3 | Restrictive format strings break web clients — relaxed to `bv*[height<=720]+ba/b/bv*+ba` |
| 4 | **AUTH WALL BEATEN via WARP + BGutil PO tokens**: `mweb`, `web`, `web_safari` clients generate player/GVS PO tokens through the farm's BGutil server and **pass YouTube's bot-check** (round 1 saw `LOGIN_REQUIRED` on every client) |
| 5 | Remaining ceiling for THIS video (UMG-distributed MV `2wA_b6YHjqQ`): web clients return an **empty format list** post-auth (stream-gating), `android_vr` reaches real download but needs a client GVS token → `HTTP 403`. Direct-IP (no WARP) attempts stay bot-walled |
| 6 | Verdict unchanged from round 1, but one step closer: **farm infra is production-ready and auth passes**; UMG stream-gating remains. Subject clips from residential IPs (or self-hosted Cobalt+WARP) still work — see `pipeline/ytagent_bridge.py` usage |

### Where everything lives

| Piece | Path |
|---|---|
| MPT checkout (pinned) | `integrations/MoneyPrinterTurbo/` (submodule) |
| Shorts engine | `pipeline/shorts.py` (plan / render / post / QC) |
| Shorts CI | `.github/workflows/shorts.yml` → Release `shorts-v1` |
| Subject-footage wishlist | `project/subject_sources.json` |
| Farm worker | `.github/workflows/yt-download-farm.yml` |
| MPT bridge (stock footage, key-gated) | `pipeline/mpt_bridge.py` |
| ytagent bridge (subject clips, farm) | `pipeline/ytagent_bridge.py` |

## 6. SUCCESS RECORD — first production Shorts run (2026-10-12)

| Item | Result |
|---|---|
| Workflow run | `Render Shorts (MoneyPrinterTurbo)` #38191435800 / #38191436028 — **completed / success** |
| Release | **`shorts-v1` — "Shorts Pack — MoneyPrinterTurbo × Ahyeon Documentary"** |
| Assets | `short1_the_wait.mp4` (16.2 MB, 43.9 s) · `short2_the_records.mp4` (11.2 MB) · `short3_the_dome.mp4` (11.7 MB) |
| Specs | 1080×1920 (9:16), H.264 + AAC 192k 48 kHz **stereo**, −14 LUFS, faststart — QC PASS on all three |
| Render time | ~12 min for all three on a GitHub runner (MPT CLI + moviepy) |

Bugs fixed to get there (all in `pipeline/shorts.py`): MPT CLI must run with
`cwd=MPT_DIR`; post-master must map the filter output `[a]` (not `0:a`, else
"unconnected output"); BGM staged into MPT's `storage/bgm/`; UUID task-ids;
deterministic output discovery via `storage/tasks/<task_id>/final-1.mp4`.

Side effect: a `pipeline/**` push also re-triggered the film render
(run #38190435198, success) which **rebuilt v1.0 natively with the 48 kHz-stereo
audio fix** — re-verified: 1740.0 s, 1080p30, AAC 48 kHz stereo. `render.yml` is
now `workflow_dispatch`-only so pushes no longer re-render the film.

**Full integration status: MoneyPrinterTurbo = OPERATIONAL (NIM script-gen +
Shorts render + CI); ytagent = OPERATIONAL infra, UMG stream-gate documented.**
