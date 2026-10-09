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
  build_cards.py       the visual identity system
  build_timeline.py    EDL + ASS captions + metadata generator
  render.py            zoompan segments → concat → ducked mix → caption burn → loudnorm
  qc.py                QC battery (duration/res/fps/loudness/size)
  qa_nim.py            NVIDIA NIM fact-check + slop audit pass
.github/workflows/render.yml   one click → full render → QC → GitHub Release
```

**The run:** `Actions → Render Documentary → Run workflow`. It rebuilds the timeline deterministically, renders all segments, runs the QC battery, uploads the artifact, and attaches `final.mp4` to Release v1.0.

**Editorial standards:** narration may only assert facts from the dossier (VERIFIED/PUBLISHED tags); fan-wiki items are excluded or attributed; K-pop performance footage policy = short transformed commentary clips (audio stripped) or none — this cut uses zero MV footage, by license discipline.

**Credits:** narration en-US-Andrew (edge-tts) · music CC0 via Openverse · imagery Wikimedia Commons & Openverse (per-asset attribution in `metadata.json`) · fact-check NVIDIA Nemotron (NIM) · built by the Super Z autonomous studio system.
