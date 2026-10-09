#!/usr/bin/env python3
"""Expand script.json to full 29-min length: insert additional beats after anchor ids."""
import json

P = "/home/z/my-project/ahyeon-doc/project/script.json"
s = json.load(open(P))

NEW = {
 "b106": [
  {"id": "b107", "narration": "The audition circuit that produced her is its own economy. Hundreds of thousands of Korean kids audition every year across the big agencies and the mid-tier ones. Of those signed, the large majority are released from their contracts before debut. The math is closer to elite athletics than to music school — early specialization, private coaching, and a pyramid with almost no middle.", "pause_after": 0.6,
   "on_screen": ["THE PYRAMID"], "visuals": [
    {"kind": "image", "query": "seoul subway station crowd blur"},
    {"kind": "image", "query": "stack of papers desk dim light"}]},
  {"id": "b108", "narration": "And YG's version of the pyramid is steeper than most. The company debuted exactly two girl groups in the fourteen years between 2NE1 and BABYMONSTER. That is the entire point — and the entire risk. When you launch that rarely, you cannot launch small. Every debut is a bet of the label's whole reputation. Which is why, in 2023, everything about this project was engineered to be oversized.", "pause_after": 0.8,
   "on_screen": ["2NE1 (2009) → BLACKPINK (2016) → BABYMONSTER (2023)"], "visuals": [
    {"kind": "card", "card": "timeline", "date": "2009 → 2016 → 2023", "event": "YG girl groups: 2NE1 → BLACKPINK → BABYMONSTER — two debuts in fourteen years"},
    {"kind": "image", "query": "chess pieces dark gold light"}]}
 ],
 "b205": [
  {"id": "b207", "narration": "The reveal films themselves became objects of study. Each member performed alone in a plain studio — one take, one lighting rig, no styling theatrics — because YG was selling raw material, not packaging. The comment sections turned into scouting combine reports. Tone, breath control, stage instinct, star presence, scored frame by frame by an audience that had been trained by a decade of survival shows to know exactly what it was looking at.", "pause_after": 0.6,
   "visuals": [
    {"kind": "image", "query": "empty studio softbox light equipment"},
    {"kind": "image", "query": "person silhouette studio backdrop"}]},
  {"id": "b208", "narration": "Ahyeon's file was the one that kept circulating. The rap segments landed with the cadence of someone who'd studied the label's founders, not just its stars. The vocal takes swung from chest voice into a light head register without the seams most trainees leave showing. And underneath the technique, the thing scouts call presence — the camera finding her even when she wasn't the one performing.", "pause_after": 0.8,
   "visuals": [
    {"kind": "image", "query": "sound waveform visualization dark gold"},
    {"kind": "card", "card": "quote", "quote": "The camera finds her.", "attr": "the trainee-file consensus, early 2023"}]}
 ],
 "b303": [
  {"id": "b304x", "narration": "Vocally, the cover was a statement of range. Puth writes melodies that sit in an awkward middle zone — too low for pure belt, too high for comfort — and the Dangerously chorus demands you cross that zone in public, audibly, on camera. Her version treated the verse as a whisper and the bridge as a launchpad, which is exactly the dynamics-first approach that later became her stage signature.", "pause_after": 0.6,
   "visuals": [
    {"kind": "image", "query": "audio mixing console knobs closeup"},
    {"kind": "image", "query": "mountain range silhouette gradient dusk"}]}
 ],
 "b402": [
  {"id": "b403x", "narration": "The debut era rolled on without pause. Award-show rotations, year-end stages, brand shoots — a full rookie campaign executed at six. Behind the scenes, the group's formation photographs kept one position subtly offset, the way teams do when a roster is known to change. Fans read the framing like weather patterns. The company, to its credit, never once performed the absence — no tribute edits, no sympathy messaging. The work carried on, and the empty chair stayed empty in silence.", "pause_after": 0.7,
   "on_screen": ["THE SIX-MEMBER ERA"], "visuals": [
    {"kind": "image", "query": "camera crew film set industry"},
    {"kind": "image", "query": "winter branch sky minimal"}]},
  {"id": "b404a", "narration": "For the members themselves, the period demanded a specific kind of discipline. Six teenagers, some of them fifteen and sixteen, answering interview questions about a seventh member they shared a dorm practice schedule with — day after day, market after market. Their collective answer became a running theme of the debut era: she is part of this, the formation is temporary, the group is seven. Said differently by every member, in every language, for four straight months.", "pause_after": 0.7,
   "visuals": [
    {"kind": "image", "query": "dorm hallway night light soft"},
    {"kind": "card", "card": "quote", "quote": "The formation is temporary. The group is seven.", "attr": "the debut-era answer, all six members, all markets"}]}
 ],
 "b404": [
  {"id": "b404b", "narration": "The announcement itself was three sentences long. No video, no teaser, no photo. In an industry that bills a member's return as a comeback special with countdown content, YG handled the most anticipated return of the year like a press release from a different decade — and the restraint read as confidence. The fans who had spent four months organizing welcome projects didn't get a warning. They got a date.", "pause_after": 0.7,
   "visuals": [
    {"kind": "image", "query": "typewriter paper closeup vintage"},
    {"kind": "image", "query": "calendar page flip time lapse dark"}]}
 ],
 "b502": [
  {"id": "b503a", "narration": "The album numbers told the story of a fanbase that had spent the wait converting anxiety into infrastructure. Four hundred sixty thousand first-week pre-orders — a figure most established groups would celebrate — for a group whose full lineup had existed publicly for about a month. The Circle chart debut at number three. Music show wins arrived within the first week, with the standard rookie grace period skipped entirely.", "pause_after": 0.6,
   "on_screen": ["CIRCLE ALBUM CHART — #3"], "visuals": [
    {"kind": "card", "card": "stat", "kicker": "CIRCLE CHART", "big": "#3", "small": "album chart debut — BABYMONS7ER, April 2024"},
    {"kind": "image", "query": "vinyl records collection dark light"}]},
  {"id": "b503b", "narration": "Live, the Sheesh era made the case in person. Her stage rap in the second verse drew a hard line under the vocal-versus-rapper question — the flip from sung chorus into a tightened, percussive delivery became the clip that editors reached for first. Vocally, the belt at the final hook became the moment crowds came to film. A star turn, executed in month one of the actual career.", "pause_after": 0.7,
   "visuals": [
    {"kind": "image", "query": "concert phone lights raised hands"},
    {"kind": "card", "card": "quote", "quote": "Rapper on the verse. Belter on the hook.", "attr": "the Sheesh-era live consensus"}]}
 ],
 "b601": [
  {"id": "b601a", "narration": "Before DRIP, though, came the summer single that taught the fanbase how to miss a song on purpose. Forever was built light — retro synth, open vowels, a chorus that asked to be sung in a stadium parking lot. It was also, quietly, a demo of the group's post-hiatus chemistry: parts arranged to interlock seven ways, with the seventh voice threaded through harmonies instead of stacked above them. Arrangers write differently when the full instrument finally exists.", "pause_after": 0.7,
   "on_screen": ["JUL 1, 2024 — \"FOREVER\""], "visuals": [
    {"kind": "card", "card": "timeline", "date": "JUL 1, 2024", "event": "\"Forever\" — the summer single between records"},
    {"kind": "image", "query": "summer field sunset warm haze"}]}
 ],
 "b603": [
  {"id": "b603a", "narration": "Tour life restructured the group's year. Thirty-two shows across Asia means airport departures, arena load-ins, and rest days measured in hotel hours — a rhythm that ages rookies fast. Setlists from the tour's first leg show the engineering: each member rotated through solo moments built to showcase a different register of the group's sound. Ahyeon's slot drew the loudest documented reactions of the run, and the fan-cam economy did the rest, one four-minute vertical video at a time.", "pause_after": 0.7,
   "visuals": [
    {"kind": "image", "query": "airport night terminal lights window"},
    {"kind": "image", "query": "road highway night long exposure lights"}]}
 ],
 "b703": [
  {"id": "b703a", "narration": "The KGMA result deserves its own arithmetic, because fan-voted awards measure something charts can't: mobilization. Thirty-three thousand votes in a solo category means fanbases coordinating across time zones, on apps, against other mobilized fanbases — and eighty-five percent of the share means it wasn't close. For a member whose fandom identity was built during four months of waiting, the vote was the wait, cashed in.", "pause_after": 0.7,
   "visuals": [
    {"kind": "image", "query": "voting ballot box minimal dark"},
    {"kind": "card", "card": "quote", "quote": "The wait, cashed in.", "attr": "on the KGMA fan vote — 33,380 votes, 85.81%"}]}
 ],
 "b704": [
  {"id": "b704a", "narration": "Mediabase deserves a plain-language translation, because it is the least glamorous and most serious number in the story. It counts actual radio spins — airplay logged from monitored stations across the United States. No streaming bundles, no fan purchasing power, no algorithm. Real programmers, playing a Korean-language title track in daytime rotation. For a genre that spent two decades being told its ceiling was the internet, charting on US radio in year three is the kind of line that ends arguments.", "pause_after": 0.8,
   "visuals": [
    {"kind": "image", "query": "american highway dusk radio tower"},
    {"kind": "card", "card": "quote", "quote": "Measured in spins, not streams.", "attr": "what Mediabase #35 actually means"}]}
 ],
 "b705": [
  {"id": "b705a", "narration": "The March itself is worth forty seconds of analysis, because virality of this kind is engineering plus accident. The move is simple enough to learn in one watch — a stride, a shoulder line, a snap of the chin — and distinctive enough to read at thumbnail size. Short-form platforms reward exactly that signature: recognizable in half a second, copyable in ten seconds, hard to do well, which keeps the imitations coming. The name attached to it traveled the way names do now — first a joke, then a tag, then a fact.", "pause_after": 0.7,
   "visuals": [
    {"kind": "image", "query": "dance shoes floor studio spotlight"},
    {"kind": "image", "query": "city night walking crowd neon reflections"}]}
 ],
 "b706": [
  {"id": "b706a", "narration": "Context for ten billion: the only K-pop girl group channel ahead of it belongs to BLACKPINK, and that channel needed eight years and one of the most dominant runs in music history to get there. BABYMONSTER crossed the line in roughly three, on the strength of a catalog of barely thirty songs. The pace, not the total, is the story — and the pace is what makes the next decade of projections genuinely unstable.", "pause_after": 0.8,
   "visuals": [
    {"kind": "card", "card": "stat", "kicker": "THE PACE", "big": "~3 YEARS", "small": "to 10B views — vs 8 for the only channel ahead of it"},
    {"kind": "image", "query": "speedometer night motion blur"}]}
 ],
 "b802": [
  {"id": "b802a", "narration": "It is worth saying plainly what the last three years actually contained, because speed blinds. A fifteen-year-old announced as a label's future, then removed from the biggest launch of her company's decade for reasons she never controlled. Four months of public silence at an age when most careers haven't started. A return under the heaviest comparison nickname the internet could manufacture. And then — instead of the cautious, managed mediocrity that usually follows a health pause — a run of records, covers, charts, and domes executed at full sprint.", "pause_after": 0.8,
   "visuals": [
    {"kind": "image", "query": "lighthouse storm coast night beam"},
    {"kind": "image", "query": "runner starting blocks stadium empty"}]}
 ],
 "b803": [
  {"id": "b803a", "narration": "The butterfly has become the thing her fans carry — the official symbol of a fandom that learned patience as a group activity. It fits, in a way that branding rarely does. A thing that spends its early life unrecognizable from what it becomes, and arrives on the other side of the wait with entirely new wings. You can call that a metaphor if you like. Her fans call it a record of what actually happened.", "pause_after": 0.9,
   "on_screen": ["FOR THE MONSTIEZ 🦋"], "visuals": [
    {"kind": "card", "card": "quote", "quote": "New wings.", "attr": "on the butterfly — the MONSTIEZ symbol of the wait"},
    {"kind": "image", "query": "butterfly wings macro dark background"}]}
 ]
}

seg_of = {}
for seg in s["segments"]:
    for i, b in enumerate(seg["beats"]):
        seg_of[b["id"]] = (seg, i)

inserted = 0
for anchor, beats in NEW.items():
    seg, idx = seg_of[anchor]
    seg["beats"][idx+1:idx+1] = beats
    inserted += len(beats)
    # rebuild seg_of for correct subsequent insertion (ids unchanged, indexes shift)
    seg_of = {}
    for sg in s["segments"]:
        for i, b in enumerate(sg["beats"]):
            seg_of[b["id"]] = (sg, i)

words = sum(len(b["narration"].split()) for sg in s["segments"] for b in sg["beats"])
nbeats = sum(len(sg["beats"]) for sg in s["segments"])
json.dump(s, open(P, "w"), indent=1, ensure_ascii=False)
print(f"Inserted {inserted} beats → total {nbeats} beats, {words} narration words")
print(f"Est: {words/155:.1f} min speech + ~{nbeats*0.65/60:.1f} min gaps + bookends ≈ {words/155 + nbeats*0.65/60 + 0.5:.1f} min")
