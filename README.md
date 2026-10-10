# JUNG AHYEON — The One Who Was Worth the Wait
### An autonomous AI-agent documentary, built end-to-end by @superz1402

**Runtime 29:00 · 1920×1080 · 30fps · H.264/AAC · −14 LUFS · 67 narration beats · 8 acts**

This repository IS the studio. Everything that made the film lives here:

```text
project/
  script.json          67-beat broadcast script (fact-gated; NIM-audited)
  facts/               verified dossier (sources + confidence tags)
  voice/               edge-tts narration, 67 mp3 + srt (word-chunk timing)
  media/               57 licensed images (Commons/Openverse, license per asset)
  music/               CC0 ambient bed
  cards/               68 generated title/stat/quote/timeline cards (Pillow)
  timeline.json        the EDL — beats, Ken Burns moves, gap-calibrated to 29:00
  captions.ass         word-chunk captions + gold receipt overlays
  metadata.json        YouTube title/description/chapters/tags/attribution appendix
  media_manifest.json  license ledger (every asset: source, license, artist, url)
pipeline/
  tts.py               narration batch (lexicon for Korean names)
  source_media.py      Commons/Openverse sourcing + CC0 music, license-gated
  mpt_bridge.py        MoneyPrinterTurbo-style stock footage (Pexels/Pixabay, secrets-gated)
  ytagent_bridge.py    subject-footage via ytagent 13-method chain (secrets-gated)
  build_cards.py       the visual identity system
  build_timeline.py    EDL + ASS captions + metadata generator (images + video slots)
  render.py            zoompan segments + footage slots → concat → ducked mix → caption burn → loudnorm
  qc.py                QC battery (duration/res/fps/loudness/size + subject-clip policy)
  qa_nim.py            NVIDIA NIM fact-check + slop audit pass
.github/workflows/render.yml          one click → enrich → render → QC → GitHub Release
.github/workflows/yt-download-farm.yml ytagent remote download worker (WARP + BGutil, 6-tier ladder)
docs/INTEGRATIONS.md    MoneyPrinterTurbo + ytagent integration guide & live test log
```

**The run:** `Actions → Render Documentary → Run workflow`. It rebuilds the timeline deterministically, renders all segments, runs the QC battery, uploads the artifact, and attaches `final.mp4` to Release v1.0.

**Editorial standards:** narration may only assert facts from the dossier (VERIFIED/PUBLISHED tags); fan-wiki items are excluded or attributed; K-pop performance footage policy = short transformed commentary clips (audio stripped) or none — this cut uses zero MV footage, by license discipline.

**Optional media enrichment (secrets-gated, default off):** the pipeline accepts two bridges that add real *video* to the media pool — MoneyPrinterTurbo-style stock footage (Pexels/Pixabay, commercial-OK licenses) and ytagent subject-clip sourcing via this repo's own remote download farm. With no secrets set, behavior is identical to v1.0. Full guide + live test log: [`docs/INTEGRATIONS.md`](docs/INTEGRATIONS.md).

**Credits:** narration en-US-Andrew (edge-tts) · music CC0 via Openverse · imagery Wikimedia Commons & Openverse (per-asset attribution in `metadata.json`) · fact-check NVIDIA Nemotron (NIM) · built by the Super Z autonomous studio system.
