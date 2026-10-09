#!/usr/bin/env python3
"""Final script additions to land 29:00 runtime."""
import json

P = "/home/z/my-project/ahyeon-doc/project/script.json"
s = json.load(open(P))

NEW = {
 "b304x": [
  {"id": "b304y", "narration": "The rollout metrics around her told the same story from the business side. Pre-registration for the debut had become, per YG's own releases, the largest in the channel's history for a rookie act. Brand anticipation indexes ranked a group that had performed zero official songs inside the top tier of upcoming launches. This is the part of K-pop outsiders consistently underestimate: by the time a group debuts, the market has already spent months pricing it — and the market had priced this one as the biggest launch of the year.", "pause_after": 0.7,
   "on_screen": ["THE MARKET HAD PRICED IT"], "visuals": [
    {"kind": "image", "query": "stock market screen numbers glow"},
    {"kind": "card", "card": "quote", "quote": "The biggest launch of the year.", "attr": "the market's pricing, autumn 2023"}]}
 ],
 "b504": [
  {"id": "b504a", "narration": "Finding your own color, in idol terms, is not a metaphor — it is a production problem with a deadline. It means the arrangement of your voice inside the group's sound: which frequencies you claim, which registers you lend to harmonies, which ad-libs are yours by law. Comparisons blur that map, because a comparison asks you to occupy someone else's frequencies. The fix is not to imitate less. It is to write parts that only one person can sing — and then sing them until the map redraws itself.", "pause_after": 0.8,
   "visuals": [
    {"kind": "image", "query": "color palette paint swatches dark"},
    {"kind": "image", "query": "sound mixing board sliders closeup"}]}
 ],
 "b702": [
  {"id": "b702a", "narration": "The Mandarin moment deserves its own footnote. At the Taipei encore, mid-tour, she addressed the arena in Mandarin — not a rehearsed greeting, by every account, but long enough to count as crowd work. Trilingual stage presence is rare in any generation of idol; using the third language as a connective gesture toward the audience that showed up for you is the kind of detail that converts casual viewers into permanent ones.", "pause_after": 0.7,
   "on_screen": ["TAIPEI ARENA — MANDARIN ENCORE"], "visuals": [
    {"kind": "card", "card": "stat", "kicker": "THE THIRD LANGUAGE", "big": "3", "small": "languages on stage — Korean, English, Mandarin"},
    {"kind": "image", "query": "arena crowd warm lights evening"}]}
 ]
}

seg_of = {}
for seg in s["segments"]:
    for i, b in enumerate(seg["beats"]):
        seg_of[b["id"]] = (seg, i)

for anchor, beats in NEW.items():
    seg, idx = seg_of[anchor]
    seg["beats"][idx+1:idx+1] = beats

words = sum(len(b["narration"].split()) for sg in s["segments"] for b in sg["beats"])
nbeats = sum(len(sg["beats"]) for sg in s["segments"])
json.dump(s, open(P, "w"), indent=1, ensure_ascii=False)
print(f"Total {nbeats} beats, {words} words. Est ≈ {words/150 + nbeats*0.65/60 + 0.5:.1f} min at 150wpm")
