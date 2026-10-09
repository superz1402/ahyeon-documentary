#!/usr/bin/env python3
"""NVIDIA NIM QA pass: fact-check narration against the dossier + slop audit."""
import json, urllib.request

BASE = "/home/z/my-project/ahyeon-doc"
KEY = open("/home/z/my-project/.nimkey").read().strip()
s = json.load(open(f"{BASE}/project/script.json"))

facts = open("/home/z/my-project/download/ahyeon-documentary-dossier.md").read()
narr = "\n".join(f"[{b['id']}] {b['narration']}" for sg in s["segments"] for b in sg["beats"])

prompt = f"""You are a documentary fact-checker and script doctor for a 29-minute YouTube film about K-pop idol Jung Ahyeon (BABYMONSTER).

TASK 1 — FACT CHECK: Compare every narration claim below against the FACT SHEET. List any claim NOT supported by the fact sheet as: {{beat_id, claim, problem}}. Ignore framing/interpretation language — flag only concrete factual assertions (numbers, dates, attributions, causality).

TASK 2 — SLOP AUDIT: Flag any AI-slop patterns: generic filler ("in today's world", "delve", "testament to", "game-changer"), repeated sentence openers, hollow superlatives without receipts. List as {{beat_id, phrase}}.

TASK 3 — TONE: Rate tone consistency 1-10 for a Cold Fusion-style documentary.

FACT SHEET:
{facts[:12000]}

NARRATION:
{narr[:26000]}

Reply with compact JSON only:
{{"unsupported": [{{"beat_id":"...","claim":"...","problem":"..."}}], "slop": [{{"beat_id":"...","phrase":"..."}}], "tone_score": N, "notes": "1-3 sentences"}}"""

req = urllib.request.Request(
    "https://integrate.api.nvidia.com/v1/chat/completions",
    headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
    data=json.dumps({
        "model": "nvidia/nemotron-3-super-120b-a12b",
        "messages": [{"role": "system", "content": "Output compact JSON only. No explanations."},
                     {"role": "user", "content": prompt}],
        "temperature": 0.2, "max_tokens": 8000
    }).encode())

with urllib.request.urlopen(req, timeout=180) as r:
    d = json.loads(r.read().decode())
content = d["choices"][0]["message"]["content"]
try:
    j = json.loads(content[content.index("{"):content.rindex("}") + 1])
except Exception:
    j = {"raw": content}
json.dump(j, open(f"{BASE}/project/nim_qa.json", "w"), indent=1)
print(json.dumps(j, indent=1)[:4000])
