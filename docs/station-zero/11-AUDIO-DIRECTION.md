# 11 · AUDIO DIRECTION

How STATION ZERO sounds: one idea (the station is the instrument), one ambience per zone, the music, the cue
sheets of every key moment, the list of voice lines to record later, and what it costs and how it is proven.
Design only. No audio has been made and no voice has been generated. Voice lines stay a todo (none are
generated); sound effects are made with the ElevenLabs sound-effect tools, from the list in section 8. Every name
is canon from `01-LORE.md`.
Where a detail was not fixed by the owner it is marked "(decided here)". Every choice carries its reason.

Binding rules (owner): everything is original (no sound, melody, song or voice from any game, film or
commercial recording; no real artist named as a source; eras and styles may be named); no heroic or epic music
(the owner rejected the old cues as "too heroic, Origins-like", and the old round cues were the 80s synth-rock
house style of the stock game); a result is a measured run, never a prediction.

## 0. The facts this chapter stands on

| # | Fact | Source | What this chapter does with it |
|---|---|---|---|
| F1 | Engine zone beds stay silent in a usermap; beds are played per player by script | `research/C` 2.6, audio NOTES builds 9 to 14 | every bed and every per-player layer is a script-played clip |
| F2 | `playlocalsound` refuses looping aliases. Beds are non-looping 26 s clips (24 s seamless body plus a 2 s head) retriggered every 24 s; a twin alias on a second channel alternates, because a new `playlocalsound` on a channel replaces that channel's voice (a 2 s dip at the seam until the twin fix) | audio NOTES f6 to f11 | beds, the Carrier and the Roller track use this method (the Roller track in 32 s chunks) |
| F3 | Loop caps: 8 per zone, 36 at once | `research/C` 2.6 | section 2.4 counts them per zone and per listening position |
| F4 | A mono file measures about 3.5 dB quieter in game (the game sums channels), so music is stored dual-mono | `research/A` (j) | all music is stored dual-mono; measured loudness is taken on the stored file |
| F5 | Stock music masters sit at -12 LUFS with a loudness range of 1 to 3 LU | `research/A` (j) | our music masters match, so a DJ track and ours are the same level |
| F6 | A dedicated server returns 0 for `lookupsoundlength` of mod-bank sounds | `research/A` (j) | every timed sound has a length in a table (section 6.4) |
| F7 | A sound played in space cannot be stopped; a loop on an entity can (`stoploopsound`), a local sound can (`stoplocalsound`) | owner brief | spatial one-shots are short; anything that must stop is a loop or a local sound |
| F8 | A player who joins during a song does not hear it | `research/A` (j), NEIL-FINALE | the Roller track is chunked so a joiner hears it within 32 s; the hidden song is a single file and a late joiner misses it |
| F9 | Bank sources are FLAC at 12 to 48 kHz and must use 1024-frame blocks, or they are silent in game (the old music was silent for that reason) | audio NOTES s4, s5 | the bank tool re-encodes and verifies; a bank build that fails the check is refused |
| F10 | Measured zone medians in game: -35.6 to -47 dBFS; the stock purchase sound peaks about -29; zombie spawn bursts about -25 | audio NOTES s3 to s5 | zone targets in 2.2; music sits under gameplay cues, as measured |
| F11 | The stock round-end music alias is picked at random and was never drawn in 6 round ends; direct plays by script were matched every time | audio NOTES s6 | round start and end are played by script on the round notifications, not by the stock alias |
| F12 | The stock pause from the round-end cue to the next round start is 9.7 s | audio NOTES s5 | the silence between rounds is about 5 s (4.5 s end cue, then quiet) |
| F13 | Captures contain short isolated full-scale click spans (cause not proven; stock and custom sounds alike); the owner packs are declicked | audio NOTES s5 | every level in this chapter is measured on a declicked capture, 60 s windows, median |
| F14 | How a UI sound is played from Lua is not stated; Maxis has no UI sound | `research/B` 1.7, `10-EMOTES.md` 4.6 | section 4.12 gives the two routes and the first proof |
| F15 | A weapon sound has never been measured as audible from the game | `research/C`, `research/A` | the first task of the weapon sounds is to measure the donor's fire sound (section 6.5) |
| F16 | Stock heroes speak through `vo_prefix` p1_ to p4_ aliases; a custom actor's voice and custom hero lines are not stated as working | `research/A` (j) | voice section lists slots only; routing is a build question |
| F17 | Players' microphones (voice chat) never worked | `research/A` (j) | nothing here depends on voice chat |

## 1. The station is the instrument

Three layers play everywhere. Each has one owner and one reason to exist.

| Layer | What it is | Whose it is | How it is played | Reason |
|---|---|---|---|---|
| a. The room | air, hum, drips, the room's own machine | the place | per-player bed plus positioned emitters (section 2) | tells you where you are with your eyes shut |
| b. The Carrier | a faint tone in the rails and the PA lines; rises with the round number; drops out completely between rounds | ZERO | per-player 2D clips, six stages (1.3) | the Carrier is what moves the dead, so it is the pressure of the round; its absence is the reward for finishing one |
| c. The Three-Tone and the Voice | the PA chime and the recorded announcer | ZERO and Evelyn Marsh's recording | round-start stinger, announcements, clock strikes | the station talks to the players the way a real station does: a chime, then a sentence |

### 1.1 The pitch plan (decided here)

Everything is tuned to C so the layers never fight.

| Thing | Pitch | Reason |
|---|---|---|
| Departure Note | C1 32.7 Hz, with the second and third harmonics C2 65.4 Hz and C3 130.8 Hz at 0, -2 and -4 dB | the fundamental is felt; the harmonics are what a small speaker carries (the missing-fundamental effect keeps the pitch identity) |
| Three-Tone | E5 659 Hz, D5 587 Hz, G sharp 4 415 Hz, falling, 0.9 s apart, each note slightly detuned (E5 +12 cents, D5 -15 cents, G sharp 4 +20 cents) | a whole tone down, then a tritone down: three falling notes that are not a triad. The chime is ours and slightly wrong, which is what a control tone leaking into an old tube would make. It must never be the notes G, E, C or any falling major triad: those are another broadcaster's chime and the stock "ding-ding-ding" of every shop and airport PA |
| Round-start harmony | chords under the three notes: C major (E is its third), B flat major (D is its third), E major (G sharp is its third) | I, flat VII, then a borrowed major III: a chain that never settles on C, bittersweet, never heroic (the E major chord is the "sag": its third is the chime's wrong note) |
| Carrier | partials built on C4 261.6 Hz, detuned flat at round 1 and rising to exactly C at round 30 | in the lore the Carrier meets the tunnel's resonance; at round 30 the two are in tune |
| Lodestar's electricity | 50 Hz and 100 Hz hum (close to G1 and G2, 35 cents sharp) | the 1984 mains is a fifth above Vayle's note and slightly out of tune with it, so the two eras never share a frequency |
| Roller track | A minor, chorus in C major | the relative major joins the Party Car to the station without sharing its mode |
| Terminus | no music: a line printer that never stops, the Departure Note (C1) very low, the clock's mechanism, the Voice reading times | the place is made of printout: a printer has paper and no tune, and a timetable has times and no music |
| Hidden song | D minor, ends on A (the dominant) | a song about a train that never comes must never arrive on its tonic |
| UI family | C pentatonic (C, D, E, G, A) | short blips that can sit on any other layer without a clash |

### 1.2 The Departure Note: where it lives and where it never does

Rule: the Departure Note belongs to Ambrose Vayle's things only. It is the sound of the old tunnel.

| Allowed | How |
|---|---|
| the Capsule Post | under every launch and ride; the empty-tube "hoom"; the changeover exhale |
| the Bellows (the blower) | idle breathing carries only the 65 and 131 Hz harmonics; the Bellows trap and the changeover carry the full chord; the organ ghost chord (C and G) |
| the Dispatcher | the send (the bellows cough carries the 65 and 131 Hz harmonics) and the burst (an organ pedal cut off by a wet slap) |
| the teleport | the 3 s crossing swell, and the muffled swell heard through the car walls |
| the Terminus | the quiet pedal that is its only tone (it comes from the paper wall that the "WAY OUT" sign points at) |
| the Parlour | the long-case clock's gong (a clock of Vayle's); Vayle's notebook pages (1 s at -30 dB when picked up) |

It never appears in: boards, printers, PA horns, the Voice, the Carrier (except the round-30 convergence, 1.3),
any weapon other than the Dispatcher, Lodestar's machines (they hum at 50 and 100 Hz). Reason: when a player
hears the low C, it must always mean "Vayle's tube is involved", the way a leitmotif works.

### 1.3 The Carrier by round (decided here)

Six stages, each a 26 s non-looping clip retriggered with a twin (F2). Level is the median over a 60 s solo
window in a quiet zone, declicked (the Carrier is faint so that the quiet zones, Shelter 7 and the Parlour, are
where you hear it first).

| Stage | Rounds | Partials | Detune from C4 | Beating | Level |
|---|---|---|---|---|---|
| S1 | 1 to 4 | 1 (261.6 Hz) | -80 cents | 0.25 Hz | -54 dBFS |
| S2 | 5 to 9 | 2 (C4, G4) | -60 cents | 0.3 Hz | -51 dBFS |
| S3 | 10 to 14 | 3 (C4, G4, E5) | -40 cents | 0.4 Hz | -48 dBFS |
| S4 | 15 to 19 | 3 plus a thin 2 kHz PA-line shimmer | -25 cents | 0.5 Hz | -45 dBFS |
| S5 | 20 to 29 | 4 (adds F#4, the dissonance against G) | -10 cents | 0.7 Hz | -42 dBFS |
| S6 | 30 and later | 4, F#4 removed, shimmer kept | 0 (in tune) | 0 (locked) | -39 dBFS |

Reasons: three dB per stage is a rise the ear can follow over a match without noticing any single step; the
detune shrinking to nothing is the Carrier locking on to the Note; at S6 the beating stops, which is the sound
of the machine being satisfied, and it is the only stage that is calm, which is the wrong calm.
Between rounds the Carrier is absent (4.2). It returns inside the round-start stinger (4.1). It is absent
during a Roller round (the Orbit's track replaces it), at the Terminus, and while the hidden song plays.

### 1.4 Mix priority (decided here)

1 the Voice, 2 stingers and key cues, 3 weapon and enemy sounds, 4 music tracks, 5 positioned emitters,
6 beds, 7 the Carrier. The engine's own mix tables apply (they are not changed here); ducking by script is not
assumed to exist. Instead each layer is mastered at its own level (the targets in 2.2 and 3.9) so the order holds
without ducking. Reason: ducking is unproven in a usermap (F1); levels are what the capture tool can measure.

### 1.5 Rules that every cue obeys

- No cue is in the same register as the Voice while the Voice speaks: stingers decay below -22 dB of their peak
  by the time a line starts (the round-start timing in 4.1 is built on this).
- A spatial one-shot that something could need to cancel is 12 s or shorter; anything that may need to stop is a
  loop on an entity or a local sound (F7). Longer spatial one-shots are allowed only where nothing can
  interrupt them and the length is fixed: the changeover organ (12 s; the lever
  locks for 45 s), the Bellows trap's held Note (15 s), and the escalator's
  30 s cooling-tick clip (an ambience that is harmless if it finishes).
- Random scatter (the "S" emitters) plays only when a player is within its radius (the old module's gating,
  which removed the click crowding in the old build) and pauses between rounds (4.2).
- Before power the scatter rates run 1.4 times denser than after, as in the old darkness contract (the dark
  station is eventful; the lit station is busy with machines).
- Every source file: true peak -1 dBTP or lower, no DC offset, FLAC with 1024-frame blocks, dual-mono for music
  (F4, F9).

## 2. Ambience, zone by zone

### 2.1 Vocabulary

- **Bed**: the room tone, a per-player clip (F2). One bed per zone, one file; there is no separate dark and lit
  bed: the change at power-on is carried by emitters released bank by bank (as in the old build, where the
  released hums rose +18 dB and the bed stayed). Reason: half the bank size, and it is the method already proven.
- **Emitter**: a positioned sound at a prop (anchored by `audio_layout.py` to lights, decor, quest and
  interaction records). **L** = loop on an entity (stoppable). **S** = scattered one-shot or event. Radii are
  the audible maximum in game units.
- **State**: **A** always, **P** starts at that zone's light bank at power-on, **D** dark only (stops at power),
  **swap** = the loop is replaced by its lit twin at the bank.
- **C** (carry) marks the one loop per zone that is allowed a radius up to 900 so that you hear what is
  through the door. Every other loop is local (radius 500 or less). Reason: this is the rule that keeps the
  count under the cap (2.4).
- Level means the median of a 60 s walking capture inside the zone, declicked (F10, F13). Reference **R** is the
  old ticket hall measured at -44 dBFS. Tolerance plus or minus 2 dB. A zone's 90th percentile may rise at most
  12 dB over its median, except for the signature, which may reach +20 dB over the zone floor when played alone
  (the old solo test measured +2.8 to +29 dB for the stock set).

### 2.2 The 19 zones

Loops = bed plus the L emitters, worst case (after power). Cap 8 per zone.

| # | Zone | Bed (what it is made of) | Signature (exists nowhere else) | At power-on (pairs with the light of `02-WORLD.md` section 8) | Level dark / lit | Loops |
|---|---|---|---|---|---|---|
| 1 | Cordon | heavy rain on a torn plastic canopy and wet concrete, gutter run-off, city traffic as a far low bass | rain on the canopy and the news van's idling generator with a live microphone feeding back faintly | lit from the start. The van's feedback jumps a fifth and settles; the station's PA grating below coughs one muffled Three-Tone | -40 / -40 | 5 |
| 2 | Fare Hall | big tiled hall air: reverberant room tone, ventilation breath, drips returning from the stairwell | the split-flap board flapping | the amber board gets its tubes: tube buzz and PA hiss arrive, the board's flap rate doubles for 10 s | -46 / -44 | 4 |
| 3 | Escalator Hall | a long tiled shaft: air moving down toward the platform, tile ring, the platform's rumble below | the hum of advertising boxes and one escalator motor ticking as it cools | half the boxes light, each hum arriving as its box lights; the cooling ticks do not change | -48 / -46 | 4 |
| 4 | Underpass Arcade | low ceiling hush: dead panels' 50 Hz bed, dust, the thump and whir of copiers through the walls | Copy Stop's photocopiers flashing and cycling under their lids (three machines, out of sync) and the floor polisher | ceiling panels strike half dead: panel crackle in the scatter; shop neon buzzes with the bank. Copy Stop's copiers and the polisher never lost power | -43 / -42 | 6 |
| 5 | Shelter 7 | sealed concrete: almost nothing, a 40 Hz ear-pressure tone, dry air | the hand-cranked ventilator turning by itself | the one hand lamp becomes bare bulbs (a soft 100 Hz buzz). The ventilator keeps turning: it never needed power | -50 / -49 | 4 |
| 6 | Transit Police Post | small office air: a radiator tick, muffled street rumble from above | a typewriter key struck once in a while; a radio with only carrier hiss | desk lamp to cold tubes. The radio's hiss pulses once in time with the Three-Tone | -48 / -47 | 3 |
| 7 | Staff Stair | brick stairwell echo, a slow air column, a drip chain far down (decided here: the owner's list did not name this zone) | a time clock that thunks once with no card in it (decided here) | the caged lamps buzz; the time clock thunks twice, as if it heard something | -49 / -48 | 3 |
| 8 | Platform A West | wide platform air with tunnel breath and a long reverb tail, distant water | the wind that comes before a train, and no train | emergency red to warm tubes over the deck; the third rail hums in the pit (the trap's rail is live) | -47 / -45 | 3 |
| 9 | Platform A East | carriage interiors: car fan whirr, subdued platform air, a muted bass thump from car 6 | the train's interior: door chime, fluorescent buzz, the Party Car's sound system leaking four bars now and then | the train was lit from the start; platform tubes join: the car buzz swaps to its lit twin (+3 dB) | -42 / -42 | 4 |
| 10 | Signal Cabin | wooden room: wind at the window frames, stove tick, old timber | lever-frame creaks and the block bell | the block bell rings one stroke when power comes on; the grey Lodestar desk starts its fan | -47 / -46 | 4 |
| 11 | Car Barn | big steel shed: roof panel flex, far oil drips, high-bay air | chain hoist ticking, a compressor cycling | sodium bays buzz; welding crackle begins at the lathe; the compressor's next cycle starts at once | -46 / -43 | 4 |
| 12 | Converter Hall | a cavernous dead room: 30 Hz hall resonance, louvre air | G-2's diesel and the rectifiers' arc (a crackling 100-cycle buzz) | the diesel catches, the two rectifiers strike violet and their buzz beats against each other; the loudest room on the map | -52 / -38 | 5 |
| 13 | Lodestar Exchange | raised-floor plenum: air-handling hush, faint relay flutter | relays clicking in travelling waves and the line printer | cold tubes; the tape drives spin up (a 2 s rising whine); the printer starts; relay waves come twice as often | -46 / -44 | 4 |
| 14 | The Sump | black water lapping slowly on concrete, hollow drain air | the one running pump and water | two caged lamps hum; a second pump tries to start, coughs and fails | -43 / -42 | 4 |
| 15 | The Breach | cold air in a cut, a low settle rumble, wood | scaffold boards and dripping | work lamps are lit before and after; the Bellows' breath reaches through the rock for the first time | -47 / -47 | 5 |
| 16 | The Parlour | dry marble salon: a warm 1893 room tone, high-ceiling reverb, tiny wood ticks | the long-case clock (silent until wound), gas hiss after power, one tuning fork of the fork wall that rings by itself when a zombie walks past | three gas chandeliers light with a soft "whump" each; the hiss and sparker ticks begin; the dispatch desk's gauges tick | -49 / -48 | 4 |
| 17 | The Bellows Vault | a huge dark volume: pipe air with a faint shimmer of organ overtones, grating wind | the blower's slow breathing | the Lodestar motor slams in, then the blower takes its first breath after a held silence; the pipes begin their ghost chord | -49 / -41 | 5 |
| 18 | The Boneyard | dead-end tunnel: a low draught, metal ticks, far rail hum | a barrel fire and a cassette player with a dying battery playing an original breakbeat loop slower and slower | the string of stolen lamps buzzes; the fire and the cassette do not change | -45 / -44 | 4 |
| 19 | The Terminus | none: no bed, only the machine below | a line printer that never stops, under the low Departure Note, the clock's mechanism ticking, and the Voice calmly reading times that are all the same time; no music | always the same | -36 / -36 | 3 |

Terminus note: `04-PAP-QUEST.md` gives the Terminus no music: "no music. The Departure Note, very low; a line
printer somewhere, never stopping; the Voice, calm, reading times that are all the same time." That is the whole
soundscape: no dance music and no tune. The line printer (TE4) is the room tone: it never stops, not even when the
clock does. The clock ticks once a second from 23:59:19 and stops at 23:59:59; after its last tick the printer is the
only thing left for the rest of the visit. The Pack-a-Punch machine uses the stock machine sounds, which are not ambience.

Level reasons: the Cordon's rain and the Converter Hall's arc are the two loudest rooms because they are the two
rooms you must notice (the start and the power switch); Shelter 7 and the Parlour are the quietest because the
Carrier and the single ringing fork are meant to be heard there; the Sump and the Bellows Vault are loud because
their machine is the room.

### 2.3 The emitters (105: 60 loops, 45 scatter)

Radius in game units. C = the carry loop of the zone.

**Cordon**

| ID | Type, state | What | Where | Radius |
|---|---|---|---|---|
| CO1 | L C A | news van generator, diesel put-put with a slow stumble every 20 s | beside the Channel 9 van | 900 |
| CO2 | L A | the live microphone feeding back: a thin whine at the Carrier's S1 pitch, wobbling 0.3 Hz, swelling when a player stands within 200 | on the van's mast | 450 |
| CO3 | L A | sodium floodlight hum (100 Hz with ballast ticks) | the central floodlight stand | 450 |
| CO4 | L A | "STATION 0" canopy transformer hum and a sign-tube tick | the entrance canopy | 500 |
| CO5 | S A | heavy drops from a canopy tear on a barrier slab, 3 variants, every 2 to 6 s | barrier slabs | 450 |
| CO6 | S A | tent canvas flap and guy-rope creak in gusts | the decontamination tents | 500 |

**Fare Hall**

| ID | Type, state | What | Where | Radius |
|---|---|---|---|---|
| FH1 | L C A | board motors idling, a soft ratchet purr | the split-flap board | 900 |
| FH2 | S A | flap cascades of 1.5 to 4 s: "the board re-checks" every 25 to 45 s, plus a burst for every state change (round, clock, road, Handle) | the board | 1400 |
| FH3 | L A | draught whistle through the fare gates | the turnstiles | 450 |
| FH4 | L P | lit hall hum: uneven tube buzz (one row in three dead) and PA horn hiss | ceiling over the banquet table | 500 |
| FH5 | S A | the Announcer's Booth: a closed room's breath, and once in a long while one paper rustle (hook H4) | the booth window, high on the east wall | 400 |
| FH6 | S A | bunting and ribbon flutter, a fallen banquet chair settling | the ribbon across the gates | 400 |

**Escalator Hall**

| ID | Type, state | What | Where | Radius |
|---|---|---|---|---|
| EH1 | L P | advertising-box hum | west wall, mid hall | 450 |
| EH2 | L P | advertising-box hum at a different pitch (beats 2 Hz against EH1) | east wall | 450 |
| EH3 | S A | the escalator motor cooling: ticks slowing from three a second to one every 3 s over 30 s, then a 30 to 90 s pause | west escalator foot | 500 |
| EH4 | L C A | the draught up the lanes, a low whistle with the train's air in it | the foot of the lanes | 900 |
| EH5 | S A | loose handrail rubber squeal and click | east escalator | 450 |
| EH6 | S P | advertising-box tube crackle | the boxes | 450 |

**Underpass Arcade**

| ID | Type, state | What | Where | Radius |
|---|---|---|---|---|
| AR1 | L A | Copy Stop photocopier, west row: lamp bar sweep and drum whir, cycle A, 8.0 s | Copy Stop bay | 500 |
| AR2 | L A | photocopier, centre: lid thunk and paper feed, cycle B, 10.0 s | Copy Stop bay | 500 |
| AR3 | L A | blueprint machine, east: ammonia fan and paper roller, cycle C, 12.0 s | Copy Stop bay | 500 |
| AR4 | L C A | the floor polisher: motor drone and brush swish, the origin moving in a 160-unit circle, 12 s a lap | the arcade straight | 900 |
| AR5 | L A | Needle Drop: a stuck needle in a run-out groove, hiss and a thump every 1.8 s | the record shop | 450 |
| AR6 | S A/P | scatter group: coin-slot clatter, Hole Number Nine's coffee machine gurgle, the photo booth's flash capacitor whine, ceiling panel crackle (P) | the shop bays | 500 |

The three cycles run 8, 10 and 12 s, so they realign only every 120 s (decided here: that is "out of sync").
They are machine loops (a lamp bar sweeping under glass, a drum and a paper feed, a fan and a roller), not music.

**Shelter 7**

| ID | Type, state | What | Where | Radius |
|---|---|---|---|---|
| S71 | L C A | the ventilator crank turning by itself: one squeak per turn every 2.4 s over a paper-fan whirr | back wall | 800 |
| S72 | L A | the escape hatch whispering: air in the shaft, barely a sound | the hatch | 450 |
| S73 | L P | bare bulbs, a soft 100 Hz buzz | ceiling | 400 |
| S74 | S A | water drum drip, a hollow plink every 3 to 7 s | water drums | 450 |
| S75 | S A | cracker tins settling, a bunk chain creaking | stacked tins | 400 |

**Transit Police Post**

| ID | Type, state | What | Where | Radius |
|---|---|---|---|---|
| PP1 | S A | one typewriter key struck, clack and spring return, every 45 to 110 s | the duty desk | 600 |
| PP2 | L A | the radio on a dead channel: carrier hiss, a squelch click every 20 to 35 s, never a voice | desk radio | 500 |
| PP3 | L P | cold tube hum | the armoury cage | 450 |
| PP4 | S A | a slow drip and a hinge tick | the holding cell | 450 |
| PP5 | S A | chain and padlock rattle | the evidence cage | 400 |

**Staff Stair**

| ID | Type, state | What | Where | Radius |
|---|---|---|---|---|
| SS1 | S A | the time clock thunks once with no card, every 70 to 130 s | clocking-in machine | 500 |
| SS2 | L P | caged lamp buzz | the stair lamps | 400 |
| SS3 | L A | a draught down the stair, a breath that rises and falls | mid stair | 500 |

**Platform A West**

| ID | Type, state | What | Where | Radius |
|---|---|---|---|---|
| PW1 | S A | the wind before a train, 9 s: a low-passed rush swelling over 6 s from the west tunnel along the deck, the rails singing at the Carrier's pitch, then a cut to 2 s of silence and a soft fall. No train. Every 70 to 110 s. The origin moves from x -3600 to the zero stud | the deck | 2600 |
| PW2 | L P | tube row hum over the deck | the deck | 500 |
| PW3 | L P | the third rail live in the pit: 50 and 150 Hz | pit centre | 600 |
| PW4 | S A | rails ticking as they settle | the pit | 500 |
| PW5 | S A | the newspaper kiosk shutter rattling (triggered by PW1) | the kiosk | 450 |
| PW6 | S A | ballast drips | the pit | 450 |

**Platform A East**

| ID | Type, state | What | Where | Radius |
|---|---|---|---|---|
| PE1 | L C A, swap | fluorescent buzz of the lit cars (a 100 Hz buzz with a ballast tick, slight beating); the lit twin is +3 dB with the platform tubes | car 3 | 900 |
| PE2 | S A | the door chime, E5 then C5 (the last two notes of the Three-Tone), from a random car, no door closes; every 80 to 150 s | the car doors | 1200 |
| PE3 | S A | the Party Car leaks four bars (8 s) of the Roller track's hook, muffled and bass-heavy, every 90 to 150 s; it foreshadows the Roller round from round 1 | car 6 | 1500 |
| PE4 | S A | the cab's brake-release sigh: the train breathes, every 2 to 3 min | car 1 | 700 |
| PE5 | L A | the east signal's relay: a tick every 2.0 s while red; a steady buzz once green (after the road is set) | the east signal | 450 |
| PE6 | L A | the cess draught: a low moan along the walkway beside cars 5 and 6 | the cess | 500 |

**Signal Cabin**

| ID | Type, state | What | Where | Radius |
|---|---|---|---|---|
| SC1 | S A | one of the eight working levers settling in the frame, a creak | the lever frame | 500 |
| SC2 | S A | the block bell: one stroke every 60 to 100 s (three strokes when the road is set) | the block instrument | 700 |
| SC3 | L A | stove tick and a kettle on a low simmer | the stove | 350 |
| SC4 | L A | the track diagram's relay, lamp-proving ticks | the diagram | 400 |
| SC5 | L P | the grey Lodestar desk: fan and a thin 8 kHz screen whine | the desk | 350 |

**Car Barn**

| ID | Type, state | What | Where | Radius |
|---|---|---|---|---|
| CB1 | L A | the chain hoist: a link ticking through as the wheel set sways, 12 s | the overhead crane | 700 |
| CB2 | L C A | the compressor: pump-up 8 s, hold 30 s, relief valve "pfft", a 50 s cycle | the compressor | 900 |
| CB3 | S P | welding crackle bursts | the wheel lathe | 500 |
| CB4 | S A | pit drips, a work-lamp cable swinging | the inspection pits | 450 |
| CB5 | S A | a hung tool swinging on the shadow board | the tool wall | 450 |
| CB6 | L P | high-bay sodium lamp buzz | roof | 500 |

**Converter Hall**

| ID | Type, state | What | Where | Radius |
|---|---|---|---|---|
| CH1 | L C P | G-2 idling, a deep four-cylinder tick-over | G-2 | 900 |
| CH2 | L P | rectifier cage 1: the arc, a crackling 100-cycle buzz | cage 1 | 700 |
| CH3 | L P | rectifier cage 2: 101.3 Hz, beating against CH2 | cage 2 | 700 |
| CH4 | S P | the marble switchboard: meter ticks and a knife-switch clack | the switchboard | 500 |
| CH5 | S D | the "DO NOT RESTART" tag tapping on the housing | G-2 | 500 |
| CH6 | L A | wind howling in the ventilation louvres | louvres | 600 |

**Lodestar Exchange**

| ID | Type, state | What | Where | Radius |
|---|---|---|---|---|
| EX1 | S A | relay wave, near end of the aisle: 40 clicks in 2 s | rack row start | 500 |
| EX2 | S A | the same wave 0.45 s later, mid aisle | rack row middle | 500 |
| EX3 | S A | the same wave 0.9 s later, far end. Waves every 6 to 9 s (twice as often after power) | rack row end | 500 |
| EX4 | L P | the line printer: chatter, ratchet, paper feed | the printer room | 600 |
| EX5 | L P | the tape drives: capstan whine, a vacuum pump thump | the drives | 500 |
| EX6 | L P | cooling fans and screen hum | the raised floor | 450 |

**The Sump**

| ID | Type, state | What | Where | Radius |
|---|---|---|---|---|
| SU1 | L C A | the one running pump: a shaking thud every 1.1 s with water slosh | the pump | 900 |
| SU2 | L A | the culvert: storm water gurgling in the drain, with an echo | the culvert mouth | 600 |
| SU3 | L P | two caged lamps humming | the lamps | 400 |
| SU4 | S A | echoing drips | the pool | 500 |
| SU5 | S A | catwalk steel creak | the catwalk | 450 |
| SU6 | S A/P | floating things bumping the wall; at power-on the second pump coughs and fails (once) | the pool | 500 |

**The Breach**

| ID | Type, state | What | Where | Radius |
|---|---|---|---|---|
| BR1 | S A | scaffold boards creaking and shifting as if walked on | the ramp | 600 |
| BR2 | L A | drips on a steel plate, an irregular 20 s loop | the core-sample trays | 500 |
| BR3 | L A | work lamps on a cable: buzz and a slow sway squeak | the cable | 450 |
| BR4 | L A | Dr. Strand's desk lamp, a faint hum | her field desk | 250 |
| BR5 | S A | dust and pebble trickle | the rubble layer | 450 |
| BR6 | L P | the Bellows breathing through the rock: a 6 s breath low-passed at 150 Hz | the ramp foot | 600 |

**The Parlour**

| ID | Type, state | What | Where | Radius |
|---|---|---|---|---|
| PA1 | L A* | the long-case clock's tock, 1 s; silent until step 1 winds it | the clock | 500 |
| PA2 | L P | gas hiss from three chandeliers and sparker ticks | the chandeliers | 700 |
| PA3 | S A | one tuning fork of the fork wall rings by itself, a clear G4 decaying over 6 s, when a zombie passes within 120 units of the wall; 8 s cooldown | the fork wall | 800 |
| PA4 | L P | the dispatch desk's pressure gauges ticking | the dispatch desk | 350 |
| PA5 | S A | brass and leather creak from capsule No. 12 on its cradle in the arch; very rarely one dry tap from inside the glass | the capsule | 500 |

**The Bellows Vault**

| ID | Type, state | What | Where | Radius |
|---|---|---|---|---|
| BV1 | L C P | the blower breathing: a 6 s cycle in a 12 s loop; carries only the 65 and 131 Hz harmonics of the Note | the blower | 900 |
| BV2 | L P | the organ pipes' ghost chord (C and G), swelling with each breath | the pipes | 700 |
| BV3 | L P | the Lodestar motor and switchgear: 50 Hz hum and contactor ticks | the yellow graft | 500 |
| BV4 | L A | wind in the high gratings from the street far above | the gratings | 600 |
| BV5 | S P | the yellow beacon motor tick | the beacons | 450 |
| BV6 | S A | loose bolts rattling in the intake | the intake grille | 500 |

**The Boneyard**

| ID | Type, state | What | Where | Radius |
|---|---|---|---|---|
| BO1 | L C A | the cassette player: an original breakbeat (94 bpm, dusty drum machine through a tiny speaker) that slows from 100 to 72 percent over 44 s, takes a thump, and restarts; one 48 s clip | the camp | 900 |
| BO2 | L A | the barrel fire, crackle and wood pops | the barrel | 500 |
| BO3 | L P | the string of stolen lamps buzzing | the lamp string | 400 |
| BO4 | S A | rats and mattress rustle | the camp | 450 |
| BO5 | S A | a shopping trolley rolls a metre by itself, squeaking | the trolleys | 500 |
| BO6 | S A | wreck metal ticking and groaning | the car shells | 500 |

**The Terminus**

| ID | Type, state | What | Where | Radius |
|---|---|---|---|---|
| TE1 | L A | the clock's mechanism: a heavy tick each second from 23:59:19, stopping dead at 23:59:59 | the Terminus clock | 1400 |
| TE2 | L A | the Departure Note, a quiet pedal | the paper wall that the "WAY OUT" sign points at | 1400 |
| TE3 | S A | the Voice reading the time, calm: "twenty-three fifty-nine", three variants, one reading every 10 to 14 s | the platform speakers | 1400 |
| TE4 | L A | a line printer that never stops: a steady dry dot-matrix chatter with a carriage return every 2 s and paper feeding; it does not stop with the clock | the paper wall behind benches 1 and 2 | 1400 |

### 2.4 The loop budget, and why 36 holds

The bound by rule. A position hears: the Carrier (1), its own zone's loops (bed plus L emitters, at most 8),
the carry loops of the zones within 900 units (box to box, 3D) of its zone, and one departing bed during the 2 s
bed crossfade. Local loops (radius 500 or less) are inaudible outside their own zone. The table is computed from
the plan boxes of `02-WORLD.md` (distance 900 or less counts as a neighbour; walls and doors are ignored, which
is the worst case).

| Zone | Own loops | Carry loop of this zone | Neighbours within 900 (carry loops heard) | Audible, worst case |
|---|---|---|---|---|
| Cordon | 5 | 1 | Fare Hall, Arcade, Police Post (2) | 9 |
| Fare Hall | 4 | 1 | Cordon, Escalator Hall, Arcade, Police Post, Platform A West, Platform A East, Breach (4) | 10 |
| Escalator Hall | 4 | 1 | Fare Hall, Arcade, Platform A West, Platform A East, Breach (3) | 9 |
| Arcade | 6 | 1 | Cordon, Fare Hall, Escalator Hall, Shelter 7, Breach, Parlour, Bellows Vault (5) | **13** |
| Shelter 7 | 4 | 1 | Arcade, Parlour, Bellows Vault (2) | 8 |
| Police Post | 3 | 0 | Cordon, Fare Hall, Staff Stair, Exchange (2) | 7 |
| Staff Stair | 3 | 0 | Police Post, Converter Hall, Exchange (1) | 6 |
| Platform A West | 3 | 0 | Fare Hall, Escalator Hall, Platform A East, Breach, Parlour, Boneyard (4) | 9 |
| Platform A East | 4 | 1 | Fare Hall, Escalator Hall, Platform A West, Signal Cabin, Car Barn, Converter Hall, Exchange, Sump (5) | 11 |
| Signal Cabin | 4 | 0 | Platform A East, Car Barn, Converter Hall, Exchange (3) | 9 |
| Car Barn | 4 | 1 | Platform A East, Signal Cabin, Converter Hall, Exchange, Sump (3) | 9 |
| Converter Hall | 5 | 1 | Staff Stair, Platform A East, Signal Cabin, Car Barn, Exchange (2) | 9 |
| Exchange | 4 | 0 | Police Post, Staff Stair, Platform A East, Signal Cabin, Car Barn, Converter Hall (3) | 9 |
| Sump | 4 | 1 | Platform A East, Car Barn (2) | 8 |
| Breach | 5 | 0 | Fare Hall, Escalator Hall, Arcade, Platform A West, Parlour, Boneyard (4) | 11 |
| Parlour | 4 | 0 | Arcade, Shelter 7, Platform A West, Breach, Bellows Vault, Boneyard (4) | 10 |
| Bellows Vault | 5 | 1 | Arcade, Shelter 7, Parlour, Boneyard (3) | 10 |
| Boneyard | 4 | 1 | Platform A West, Breach, Parlour, Bellows Vault (1) | 7 |
| Terminus | 3 | 0 | none (far box) | 5 |

"Audible, worst case" = 1 Carrier + own loops + carry loops heard + 1 departing bed. The maximum is 13 (the
Arcade). Without the carry rule the sum would be worse than the cap: if every loop of every neighbour of the
Arcade were audible the count would be 39, which is over 36. So the radius rule is binding, and the proof
(6.3) checks it by measurement rather than by this table.

The dynamic reserve (things that start during play), capped by script and shared by priority:

| Source | Cap audible at once | Reason |
|---|---|---|
| music track or stinger (2D) | 2 (one fading) | one track plus a crossfade |
| Roller chain wheel loops, or the Night Inspector pulse and lamp (never both: no Inspector on a Roller round) | 4 | one loop per chain, four chains at most (16 Rollers in chains of 4 to 6) |
| Live Rail fence hums | 6 (the nearest six; others are muted) | eight players with two fences each would be 16 |
| Capsule Post flights in a tube | 2 | two capsules per hatch |
| trap loops (Decon Foam, third rail, Flashover, Bellows draw) | 2 | at most two traps are live in one hearing range |
| Top to Bottom spray, tag ticks, ALL STAND shuffles | 4 (3 shuffles, 1 spray; ticks and whistles are one-shots) | each is short and local |
| **Reserve total** | **20** |  |

Worst case audible at one position: 13 plus 20 is 33, under 36 by 3. That is tighter than I want. Two
tightening rules (decided here): the Live Rail cap drops to 4 (reserve 18, worst case 31), and the script keeps
a global running count of loops it has started and refuses new dynamic loops above 34, dropping the farthest
first (the old module's "only with a player within radius" gating is extended from random sounds to loops:
start when a player is within radius plus 400, stop when none is within radius plus 600). All 60 emitter loops
could run at once only with players spread over every zone; the global governor keeps the map at 36 or fewer
running loops (emitters, not beds, and the carry loops are dropped first).

## 3. Music

Principle: ordinary rounds have no music. The Carrier does that job. Music is an event: a stinger, a special
round, a place, a secret. Reason: the owner rejected the old cues as heroic; silence plus a rising tone is the
opposite of heroic, and it makes the few real songs land.

All music: no brass, no heroic gestures, no choir, no orchestral hits; stored dual-mono (F4); FLAC, 1024-frame
blocks (F9); master -12 LUFS integrated, loudness range 3 LU or less, true peak -1 dBTP (F5). Sample rate 44.1
kHz (32 kHz for cues heard through a small speaker).

### 3.1 Cue list

| Cue | Length | Tempo, key | Played how | Heard by |
|---|---|---|---|---|
| M1 round-start stinger (3 variants) | 5.5 s | free, chords I, flat VII, III in C | script on the round-start notification, music channel | everyone |
| M2 Three-Tone plain (PA) | 1.8 s | E5 D5 G sharp 4, 300 Hz to 3.5 kHz | local, before an announcement or a clock strike | everyone |
| M3 round-end resolve (6 stage variants) | 4.5 s | the Carrier's partials glide to C | local, on the Carrier's channel | everyone |
| M4 Roller track "Orbit Roll-In" | 3:44 | 120 bpm, A minor to C major | 7 chunks of 32 s, per player | everyone, from the round start |
| M5 Party Car teaser and leaks | 8 s each (3) | 120 bpm | positioned one-shot at car 6 | the platform |
| M6 tape stop | 1.5 s | 100 to 0 percent | replaces the track's channel | everyone |
| M7 Inspector pulse tock (3 variants) | 0.35 s | 60 or 120 bpm | script timer, local | everyone |
| M8 power-on cue | 20 s | the Three-Tone reversed, pad in C major | local plus positioned parts | everyone |
| M9 Pack-a-Punch crossing | 3 s | the Note swelling | local to riders | riders |
| M11 hidden song "Thirteen Minutes" | 3:30 | 112 bpm, D minor | one file, local | everyone |
| M12 perk jingles (4 new) | 8 to 10 s each | one per machine | stock perk-machine call | the buyer's zone |
| M13 match intro | 15 s | no music: a Three-Tone, board flaps, the Carrier's first fade-in | local | everyone |
| M14 game over | 8 s | the Three-Tone slowed and the Carrier cut | local | everyone |
| M15 Boneyard cassette and Copy Stop copier cycles | 48 s; 8, 10, 12 s | see 2.3 | loops on entities | the zone |

M10 is not used (the Terminus has no music); the other numbers stay as they are so that the build plan's references hold.

M13 and M14 are small replacements for the old intro and game-over slots; the old pack's other cues were
written for the old map and are superseded by this chapter (they stay in the bank only as stand-ins until the
new ones pass the tone gate, 7).

### 3.2 (a) Round music: stingers (M1, M2, M3)

- **Round start (M1)**: 5.5 s. A glassy electric-piano chime plays E5, D5, G sharp 4, 0.9 s apart, each slightly detuned as in 1.1 (an FM tine sound with a 1.4 s decay, the Three-Tone harmonised). Under each note a warm analogue string-machine chord (C major, B flat major, E major) swells and rings out to -30 dB at 5.5 s. No drums, no bass. Three variants
  differ only in voicing and in the chime's attack, so the stinger does not become a tune. Reason: the chime is
  what the station says; the chords make it feel like a place deciding something about you.
- **Plain Three-Tone (M2)**: the same three notes with no chords, band-limited to 300 Hz to 3.5 kHz, a touch of
  tape-hiss splice at the start, as if it came down a PA line. Used before the Voice and on every clock strike.
- **Round end (M3)**: the Carrier's current stage partials glide over 2.5 s to C4, G4 and C5 exactly (in tune),
  hold 1.0 s, then fade to nothing over 1.0 s. 4.5 s in total, then silence. Six variants, one per stage,
  each starting from that stage's detune and level; it is played on the Carrier's own channel so that it
  replaces the Carrier voice (the proven replace behaviour, F2) with no seam. Reason: the round "resolves" and
  then there is nothing: the silence is what the player earns.

### 3.3 (b) The Roller round: "Orbit Roll-In" (working title)

One original instrumental. It belongs to the Orbit Rink's Party Car, so it is the only warm, danceable
sound on the map, and the dead skate to it.

Brief for a songwriter or a music generator:

- Style and era: 1984 roller-disco. Analogue-synth octave bass (a bouncing, slightly slapped pattern), a
  drum-machine kit (kick on every beat, snare with a short gated reverb on 2 and 4, open hi-hat on every
  off-beat, handclaps doubling the snare), electric-piano stabs, a warm string-machine pad, one synth lead for
  the hook. No brass, no guitar solo, no vocals (a short synthetic vocal "oh" chop is allowed, no words).
- Tempo 120 bpm, 4/4 (decided here: one beat is 0.5 s, the same count the emote beat sheets in `10-EMOTES.md`
  use, so a dance and the track agree). Key A minor; the chorus lifts to C major.
- The wrong detail (decided here): the lead is played through the Party Car's old tape machine: a slow pitch
  wobble of plus or minus 15 cents at 0.2 Hz. Reason: it is the only cue that tells the player the party is
  not alive.
- Length 3:44, in 7 chunks of 16 bars (32.0 s) so that a player who joins mid-round hears the music within 32 s
  (F8), and so the script can time chunks from a length table (F6):

| Chunk | Time | Bars | Content |
|---|---|---|---|
| S1 | 0:00 to 0:32 | 1 to 16 | intro: drums and claps; bass bar 5; pad bar 9; the 4-bar hook teaser (bars 13 to 16) |
| S2 | 0:32 to 1:04 | 17 to 32 | verse A: bass, kit, stabs |
| S3 | 1:04 to 1:36 | 33 to 48 | chorus 1: lead hook, full kit |
| S4 | 1:36 to 2:08 | 49 to 64 | break: bass and kit only, a riser into the next chunk |
| S5 | 2:08 to 2:40 | 65 to 80 | verse B: new stab pattern |
| S6 | 2:40 to 3:12 | 81 to 96 | chorus 2, the hook doubled an octave up |
| S7 | 3:12 to 3:44 | 97 to 112 | outro: the kit thins, a drum fill into S2 |

- Loop: S7 returns to S2 (the intro is heard once).
- Seams: odd chunks play on one channel and even chunks on a twin, each chunk with a 0.5 s overlap tail baked
  in, the same twin method as the beds (F2). The proof measures the seams (6.3).
- In the round: the Party Car plays the S1 teaser muffled (8 s, positioned) as the Rollers roll out; the global
  track then begins at S1. At the end of the round the tape-stop (M6) replaces the track's channel: pitch and
  speed fall to zero over 1.5 s (the Party Car's system running down), then silence, then the stock pause, then
  the next round's M1. The Carrier is absent for the whole round.

### 3.4 (c) The Night Inspector: no music

A pulse built from two things the player can locate: the lamp's wire squeak (3D, on his every step) and the
Carrier. His waddle is 1.0 s for two steps (clip 2, 150 units per second), so a step is 0.5 s (120 per minute); the
scuttle (every 10 s, 2 s long, 260 units per second) runs a step every 0.3 s.

- Start: a low "tock" (a wood-block and relay click, with the Carrier's C4 partial blooming under it) every
  second step, 1.0 s apart (60 per minute), played 2D to everyone while he walks. Script-timed, in step with
  the squeak, so the two never drift (a script timer drives both). In a scuttle the squeak and the rasp of his
  paper ribbon speed up while the tock keeps its 1.0 s grid, so the pulse never loses time.
- Under half health: the tock plays on every step (120 per minute) and the partial rises one semitone.
  Reason: doubling is the cleanest "speeding up" that stays locked to his walk; his walking speed never
  changes with his health, so the sound is the only thing that tells the team the fight has turned.
- The pulse stops dead at the moment the lamp bursts (4.8). Silence for 2 s is the reward.
- The Carrier is untouched during his visit (he is the Carrier's inspector).

### 3.5 (d) Power-on cue (20 s), the music layer

A 20 s cue (M8). The Three-Tone reversed (G sharp 4, D5, E5 rising: the station waking, the odd note first) strikes as the first light bank
lights (2.65 s), then a warm analogue pad opens its filter over 12 s on a C major ninth chord, and settles at 16
s under the Voice. No drums. Reason: rising where every other Three-Tone falls makes it the one moment the
station is helping. The full timeline with every other layer is in 4.3.

### 3.6 (e) The Pack-a-Punch crossing (M9) and the Terminus (no music)

- **Crossing (3 s)**: the Departure Note swells from -40 to 0 dB (re the cue peak) over 2.6 s as the car's
  lights rise to white; the Carrier's partials glide to C and lock; at 3.0 s everything cuts. Riders only.
- **The Terminus (40 s, no music).** There is no cue and no M10. The sound of the visit is four things from 2.3:
  a line printer that never stops (TE4, the room tone), the Departure Note pedal (TE2), the clock's mechanism (TE1,
  a tick each second that stops with the clock at 23:59:59) and the Voice reading the time (TE3: "twenty-three
  fifty-nine", three variants, never another time and never an arrival). Reason: the Terminus is the station as a
  timetable knows it, made of printout: a printer has paper and no tune, and a timetable has times and no music.
  When the clock stops, the one second with only the printer left running before the return is the loudest thing
  in the room. The
  length table needs no entry for it: the visit is fixed at 40 s by the quest.

### 3.7 (f) The hidden song: "Thirteen Minutes" (3:30)

Trigger: activating the three brass skate-wheel trophies (the Platform A East car, the Car Barn, the Sump). It
plays to every player. While it plays, the round stingers, the Roller track, the Inspector pulse and the Carrier
are silent (the NEIL finale's rule, kept: owner change of 2026-11-06). `.mute` mutes it per player, as for all
music. A player who joins during it does not hear it (F8): accepted, it is a one-time secret.

Brief for a songwriter or a music generator (original in every note and word; nothing from any existing song):

| Item | Brief |
|---|---|
| Idea | 1984 synth-pop about waiting for a train that never comes: patience turning into dread. It is the song the Orbit party was playing when the Midnight Service left. |
| Tempo, key | 112 bpm, 4/4, D minor. 98 bars, which is exactly 3:30.00. It ends on A (the dominant): the song never resolves to its tonic. |
| Instruments | analogue polysynth pads, a sequenced 16th-note synth bass in octaves, a drum machine with a gated-reverb snare and electronic toms, an FM electric piano, a chorused clean electric guitar (a few jangling lines), one synth lead hook. No brass, no saxophone, no orchestra. |
| Voice | one lead vocal, plain, a little tired, close and dry (alto or baritone, not a belter); chorus double-tracked; no spoken part. Language: English. |
| Structure | intro 8 bars (0:00 to 0:17); verse 1, 16 bars (0:17 to 0:51); chorus, 16 (0:51 to 1:26); verse 2, 16 (1:26 to 2:00); chorus, 16 (2:00 to 2:34); bridge, 8 (2:34 to 2:51); final chorus, 16 (2:51 to 3:26); outro, 2 bars (3:26 to 3:30). |
| The station in the song | the bridge ends on the Three-Tone (E D G sharp) played on the chime, unharmonised, over a held A, its last note a half step short of the A; the outro is the Carrier's S6 partials fading with nothing under them. |
| Lyric themes | verse 1: the departure board, a platform bench, counting minutes. Chorus: the idea that it is only thirteen minutes, always only thirteen minutes. Verse 2: holding a coat for someone, a ticket kept too tight, the wind that comes before the train. Bridge: the board changes and nobody reads it. Final chorus: the same line, now said as a fact, not a hope. A working title phrase is "thirteen minutes"; no line may be taken from, or built to echo, any existing lyric. |
| Delivery | stereo mix and a dual-mono master at -12 LUFS, loudness range 3 LU or less, true peak -1 dBTP; instrumental stem; a plain lyric sheet |
| Originality gate | before it enters the bank: two independent listeners who do not know this brief confirm that no existing song comes to mind in the melody or hook; the writer or the generator's plan is recorded in the ledger. A song that fails goes back for new material; it is not edited around. |
| Route | a human songwriter, or the music generator the owner already has (the plan includes a commercial licence), from a composition plan that contains exactly this table. No voice cloning, no artist prompts. |

### 3.8 (g) Perk jingles

The six stock machines (Up 'N Atoms, Tuff 'Nuff, Racin' Stripes, Bang Bangs, Quickies, Deadeye Dewdrops) keep
the game's own jingles. The four new machines get one each: **Double Takes** (Underpass Arcade), **Baker's Dozens**
(Lodestar Exchange), **Bon Voyages** (the Parlour), **Sour Grudges** (the Boneyard).

`06-PERKS.md` gives each machine a "Jingle idea", and those lines name instruments that would make four different
kinds of music (a swing counting song with a baker's bell, a harmonium, a cheap organ, a vocal duo). **The one family
below overrides every instrument idea in 06**; only each idea's hook, mood and ending are kept.

**The family (decided here, in one line): all four are 1984 radio commercials for a sweet, made by one small jingle
house**: an electric piano, a glockenspiel with a few tubular bells, a plucked synth bass, a drum machine with a light
shuffle, and one sung or spoken tag line. They then sit together like four spots from one advertiser, and next to the
six stock jingles. What differs is the hook, the tempo and the single extra sound in each. What is fixed:

| Item | Spec |
|---|---|
| Length | 8 to 10 s each; the power-on cue plays the first bar (about 1.6 s) of each in turn (4.3) |
| Family | the jingle house above: bright, bouncy, a little too sweet; the machines are "the film's product placement". No organ, harmonium, fairground or barbershop instrument is used: where an idea says organ, the electric piano's organ patch is meant |
| Loudness | master -12 LUFS; in game within 2 dB of a stock jingle measured the same way on the same server |
| Shape | a 2-second hook, a 4-second development, a 2-second tag that returns to the hook's first note |
| Name hints (decided here, from the names only; the briefs below override them) | Double Takes: the hook played twice, the second time a half step up; Baker's Dozens: a counter climbs to thirteen and a bell rings on it; Bon Voyages: a figure that leaves the key and comes back to it; Sour Grudges: a squeezed minor second inside a sweet major tune |

The four briefs (hooks and endings from the "Jingle idea" lines of `06-PERKS.md`, instruments from the family; the
rest is decided here). All are original; any sung words are the idea only and are written fresh for the piece, and if
the music generator cannot sing them the hook is wordless and the words are added by the voice package later. The
1.5 s stings of 8.4 are cut or built from each jingle's first hook.

| Perk | Length | Style and instruments | The hook, as an idea | Ending |
|---|---|---|---|---|
| Baker's Dozens | 9 s | the family kit in a light swing at 108 bpm; one small tuned shop bell added | a counting song, "...eleven, twelve, and one for luck", each count a step up the glockenspiel while a flip counter clicks from one to thirteen under it | the baker's bell on the thirteenth beat, then the hook's first note once (the tag returns to it) |
| Sour Grudges | 8 s | the family kit at 100 bpm, the electric piano on a cheap wheezing organ patch, a tambourine in the drum kit; a children's chorus in unison, too sweet | a falling two-note taunt in a bright major tune, repeated, with one squeezed wrong note inside it | a wet raspberry, blown once, with the kit cutting off under it |
| Bon Voyages | 10 s | the family kit at a brisk 132 bpm, the electric piano on a harmonium-like patch for the patter | a brisk patter, "...all aboard for the journey", then a guard's call, "all aboard!", on three notes that leave the key and land back in it | a tin lid snapping shut on the beat, then the hook's first note once |
| Double Takes | 8 s | the family kit with a bright vocal duo in close harmony over the electric piano, a flash "pof" on the beat | every line sung twice, the second a half step up | a flash pof and a shutter click, then the first hook note once more, echoed |

### 3.9 (h) The Needle Drop jukebox

It switches the Arcade's music among the tracks the servers' own playlist feature provides. No new music is
written for it. Rules: 100 points per change (`02-WORLD.md`); the playlist's lengths come from its length table
(F6); the chosen track plays to the Arcade's zone only; the round stingers, the Roller track and the hidden
song override it. One thing is unproven and is a first check: the playlist's aliases live in the mod's bank
(`mod.sabl/.sabs`) and the map's in its own usermap bank; that a usermap can play a mod-bank alias on the same
server has not been shown.

### 3.10 Loudness targets (from the measured facts)

Capture RMS or median over the cue's window, declicked, three repeats, tolerance as stated.

| Layer | Target | Reason |
|---|---|---|
| Master files, all music | -12 LUFS, LRA 3 LU or less, -1 dBTP, dual-mono | F4, F5: the same as the stock DJ tracks, which the owner accepted on 2026-11-09 |
| Zone medians | 2.2 (R = -44 dBFS), plus or minus 2 dB | F10 |
| Carrier | -54 to -39 dBFS by stage, 1.3 | solo window in a quiet zone |
| Round-start stinger M1 | -30 dBFS RMS, plus or minus 3 | the old music measured -28 to -36 and sat under gameplay cues, as wanted (F10) |
| Roller track, hidden song | -27 dBFS RMS, plus or minus 3 | 17 dB over a zone median, 3 dB over a stinger, under a purchase sound's peak of -29 plus zombie bursts at -25 |
| Terminus printer, clock and Voice | -34 dBFS RMS while sounding, plus or minus 3 | the only sounds; speech level |
| Departure Note under cues | 6 to 12 dB under that cue's other layers | a pedal, never the lead |
| Voice (PA) | -32 dBFS RMS while speaking | 12 dB over a typical zone median, so it is understood without ducking |
| Positioned signature, solo | at least 6 dB over its zone floor within 250 units; at most 20 dB | audible but not a shock; the old solo test sounds +2.8 to +29 dB |
| Scripted cues (clock, lever, Handle, teleport) | peak -24 to -20 dBFS | above ambience, equal to the stock purchase sound at its loudest |
| Weapons | within 2 dB RMS of the donor weapon's fire sound, measured first (F15) | the donor sets the stock expectation |
| UI terminal family | peaks: open -34, tick -42, confirm -34, Tab open -36, Tab close -40 dBFS | quieter than the stock purchase sound (-29), above the zone median |

## 4. Key sound moments (cue sheets)

Where heard: **ALL** everyone (2D local); **ZONE** positioned, heard within its radius; **1P** one player.
Times are from the trigger. "Local" means a per-player local sound; "3D" means a positioned sound.

### 4.1 Round start

Trigger: the wave loop's round-start notification, played by script (F11).

| t (s) | Layer | Detail | Where |
|---|---|---|---|
| 0.0 | M1 stinger | chime E5 at 0.0, D5 at 0.9, G sharp 4 at 1.8, chords under each; the stinger is 5.5 s | ALL |
| 0.4 | board flaps | the round number flaps over (a cascade of 1.4 s) | ZONE (Fare Hall, radius 1400) |
| 3.2 | the Voice (some rounds) | the plain Three-Tone first (M2, 1.8 s), then the line. Played for round 1, every fifth round, a Roller round, an Inspector round. Other rounds: no Voice | ALL |
| 4.0 | the Carrier | the current stage clip fades in over 2 s on the Carrier's channel | ALL |
| 5.5 | stinger ends | the first zombies spawn on the stock wave delay | n/a |

Reason: the stinger decays under -22 dB before the Voice starts, so no ducking is needed. Exceptions: on a
Roller round the Carrier is not started (the Orbit's track replaces it, 4.9); while the hidden song plays,
neither M1 nor the Carrier plays (3.7).

### 4.2 Round end

Trigger: the end-of-round notification, played by script (F11). Total: 4.5 s, then quiet.

| t (s) | Layer | Detail | Where |
|---|---|---|---|
| 0.0 | M3 resolve | replaces the Carrier voice: partials glide to C4, G4, C5, rising 3 dB | ALL |
| 2.5 | hold | 1.0 s | ALL |
| 3.5 | fade | to silence over 1.0 s | ALL |
| 4.5 to the next round | quiet | no Carrier. Random scatter pauses. Loops and beds stay. About 5.2 s of quiet before the next M1 (9.7 s stock pause, F12) | ALL |

### 4.3 Power-on (20 s)

Trigger: the breaker of G-2 is thrown. Banks come on zone by zone outward, 0.8 to 1.3 s apart (the existing
darkness kit). Zone sounds start at that zone's bank.

| t (s) | Layer | Detail | Where |
|---|---|---|---|
| 0.0 | breaker | the stock fuse-box close and a contactor slam | ZONE (Converter Hall) |
| 0.0 to 2.65 | diesel turning over | starter grind rising, three coughs, then it catches; plus a low-passed (under 200 Hz) copy at -24 dB for everyone, through the structure | ZONE and ALL |
| 2.65 | M8 begins | the reversed Three-Tone (G sharp 4, D5, E5) and the pad's first chord | ALL |
| 2.65 | rectifiers strike | the violet arc: a crackle burst, then CH2 and CH3 | ZONE |
| 2.65 to about 18 | banks | per zone at its bank: the stock relay and tube-strike sounds (`power_buy_large_light_turn_on`, `power_buy_group_florescents_turn_on`), then that zone's P emitters start, each rising about +18 dB over the bed as the old build measured; D emitters stop | ZONE |
| 4.0 to 20 | perk bars | each of the ten machines plays one bar (about 1.6 s) of its jingle in turn, outward from the Converter Hall | ZONE (each machine) |
| 14.0 | Capsule Post gauges | needles tick up at the four hatches, 1.5 s of ticks | ZONE (each hatch) |
| 15.5 | M2 | the plain Three-Tone | ALL |
| 17.3 | the Voice | the map's first full sentence (V16) | ALL |
| 20.0 | cue ends | the pad is gone by 20 s; the Carrier continues at its stage level | ALL |

### 4.4 The four steps of the road

**Step 1, a clock wound** (hold Use 3 s; each of the four clocks has its own bell):

| t (s) | Layer | Detail | Where |
|---|---|---|---|
| 0.0 to 3.0 | winding | a clockwork ratchet, tick rate rising from 2 to 8 a second | ZONE (the clock, radius 600) |
| 3.0 | hands sweep | thirteen minutes in 1.0 s: a fast gear whirr | ZONE |
| 4.0 | the strike | that clock's bell (table below), 3D | ZONE (radius 1200) |
| 4.3 | M2 | the plain Three-Tone | ALL |
| 4.5 | board | one digit of "047 · DUE 00:00 · NOW" flaps (0.6 s) | ZONE (Fare Hall) |
| 4.5 | the burst | the stock zombie spawn sounds | ZONE |
| 4.6 | Tab | "CLOCKS n/4" tick, terminal family (4.12) | 1P each |

| Clock | Bell | Pitch | Reason |
|---|---|---|---|
| Fare Hall | thin electric glass bell, short decay | B5 988 Hz | the brightest, the first one met |
| Platform A West | cast bronze platform bell, 3 s decay | G4 392 Hz | the platform's own voice |
| Car Barn | struck steel, the foreman's workshop bell, hard attack | E4 330 Hz | a working clock |
| the Parlour | the long-case gong, with the Departure Note's partials at -18 dB | C3 131 Hz | Vayle's clock, Vayle's note |

The four bells together make C, E, G, B (a C major seventh). When the fourth clock strikes (4/4), the four bells
play once more, falling B, G, E, C, 0.6 s apart (a falling line like the Three-Tone, but this one lands in tune), 3D at the
board, and the Voice follows (V21). Reason: the quest teaches the chord; the finish is the chord falling home.

**Step 2, the levers** (the cabin):

| Moment | Layers | Where |
|---|---|---|
| right lever | a heavy clack, then a relay "chunk" and the lamp going green; the relay tone climbs the chord: C5 on the first pull, E5 on the second, G5 on the third | ZONE (cabin) |
| third right lever | three block-bell strokes 1.2 s apart (the line is clear), the east signal's motor 2 s and a semaphore thunk, the signal relay (PE5) goes from ticking to a steady buzz, the board flaps "ROAD SET FOR 047", then the Voice (V22) 3 s later | ZONE (cabin, platform), then ALL |
| wrong lever | every pulled lever springs back (a rattle per spring, 0.8 s), a harsh reed buzzer 1.2 s, a vent grate "clang" and 4 zombies drop | ZONE (cabin) |

**Step 3, the Conductor of 047:**

| Moment | Layers | Where |
|---|---|---|
| appears | the Party Car door hiss, then his guard's whistle: a high pea-whistle trill of 1.4 s; he whistles again every 8 s while he walks (a different whistle from the Inspector's, 5.4) | ZONE (radius 1800) |
| walking | heavy footsteps with the stock zombie walk pitched down; the hand lamp's chain clinks on every step | ZONE (radius 700) |
| doors | as he goes he pulls each car's doors shut behind him: a pneumatic hiss, rubber leaves sliding 1.2 s and a lock "thunk", car by car; when he dies they all sigh open together | ZONE (each car) |
| killed | the lamp glass tinkles, the brass Handle clunks on the ground, one detuned bell | ZONE |
| the Handle lies lit | a faint hum, the Carrier's C5 partial at -48 dBFS, radius 300, so it can be found by ear | ZONE |
| picked up | a key jingle, a rising "lock-on" blip (terminal family) and the HUD key blip | 1P, and a small blip to ALL |

**Step 4, the cab** (hold Use 1.5 s to fit the Handle):

| t (s) | Layer | Detail | Where |
|---|---|---|---|
| 0.0 | the key slides in | brass on brass, 0.3 s | ZONE |
| 0.3 to 1.5 | turning | a ratchet | ZONE |
| 1.5 | the cab wakes | four relay slams ripple along the car, then the fluorescents stutter on (2 to 4 buzz strikes) | ZONE (car 1) |
| 2.2 | headsign | a flap burst of 1.2 s: "047 TERMINUS" | ZONE |
| 3.4 | door chime | D5 then G sharp 4, twice | ZONE (radius 1200) |
| 5.0 | board and Voice | the board flaps "TERMINUS · BOARDING", the plain Three-Tone, the Voice (V25) | ZONE then ALL |

### 4.5 The teleport

Times from the first Use of the Handle by any player.

| t (s) | Layer | Detail | Where |
|---|---|---|---|
| 0.0 to 4.0 | boarding window | the door chime (D5, G sharp 4) once a second, four times | ZONE |
| 4.0 | doors close | a pneumatic hiss 0.6 s, the leaves sliding on rubber 1.2 s, a lock "thunk" | ZONE (car 1) |
| 5.2 | crossing begins (3 s) | fluorescent buzz rising in pitch and level; the Departure Note swelling (the M9 cue); the Carrier's partials gliding to C; tunnel wind rising | riders (1P each) |
| 5.2 | outside the car | the same swell, muffled and low-passed at -24 dB, as if the car were singing | ZONE |
| 8.2 | the cut | everything stops; 0.8 s of pure quiet before the printer starts | riders |
| 9.0 | arrival | a soft pneumatic "psh" and one clean C6 chime with a long decay (not the platform's D5 G sharp 4) | riders |
| 9.0 | the 40 s | the line printer (TE4), the Departure Note pedal (TE2) and the Terminus clock's mechanism (TE1) begin; the Voice reads the time (TE3) three times in the visit | riders |
| 48.0 (39.0 after arrival) | the clock stops | the last tick at 23:59:59; the Note and the Voice fall away and the printer runs on alone for one second | riders |
| 49.0 (40.0 after arrival) | return | everyone is placed in car 1, the doors open with the platform's "psh", the Carrier and the platform bed fade in over 2 s | riders, then ZONE |
| after return | cooldown 150 s | headsign "NOT IN SERVICE": a flap burst and a flat lamp-out thud; at 150 s the flaps and the D5 G sharp 4 chime say it is ready | ZONE |

### 4.6 The Capsule Post

| Moment | Layers | Where |
|---|---|---|
| unsealing a hatch (750 points; hold Use 1.5 s) | the pressure wheel squeaks for 1.5 s, a steam release 1.2 s, the needle ticks up to rest (six ticks), the lamp relay "click", an enamel plate "ting" | ZONE |
| dialling an address | the pointer turned round the brass ring: one detent "tick-clack" for each of the three enamel name plates it passes, and the lamp relay click of the plate chosen | 1P, ZONE at -9 dB |
| paying postage (250, 400 or 550) | coins dropped into the postage slot, one clink-clunk for the near address, two for the middle one and three for the far one (the price can be heard); the glass door opens with a brass hinge "clack" | ZONE |
| seal (t 0) | a cork-and-leather thump 0.25 s; the Departure Note starts under everything | rider 1P, ZONE at -12 dB |
| take-up (0 to 1.0 s) | the Bellows takes up: bandpassed air rising from 200 to 600 Hz; the needle ticks to "charged" | rider, ZONE |
| launch (1.0 s) | a cork-pop 0.15 s, a fast whoosh rising; the Note held | rider, ZONE |
| the ride (5, 9 or 13 s) | wind roar, the Note, and a "thump" every 0.51 s as tube lamps pass (256 units apart at about 500 units a second, about 2 a second) | rider 1P |
| a junction passed (once on the 9 s ride, twice on the 13 s) | a double iron "clack" and a short pitch dip in the roar | rider 1P |
| a capsule passing (bystanders) | a whoosh with a pitch fall of 5 semitones over 1.2 s, moving along the pipe, and a flash-tick at each inspection window; lit amber | ZONE (radius 1200, in every zone the tube crosses) |
| arrival (1.0 s plus the ride) | a hiss of released air 1.2 s, then a two-note brass bell rising, C5 then G5 (rising is arrival; the Three-Tone falls); 2 s later any zombies drawn in pop out of the hatch, one pop each, and fall | rider, ZONE |
| refused | one dull clunk, plus a 0.6 s tail that says why (decided here): not enough points, coins rattling back out of the slot; "TUBE SEALED", the hatch rattles and the wheel creaks; no capsule, an empty tube's low "hoom" (the Note at -30 dB); changeover, three amber relay ticks; inspection, a short guard's whistle and a plate rattle; REST (the rider arrived less than 45 s ago), a cradle latch clicking shut and a tired sigh of air | 1P and ZONE |
| changeover (12 s) | the lever "ka-thunk" in the Vault; all four hatch lamps tick to amber; the whole organ exhales: the Departure Note rises from -30 to 0 dB over 2 s, a C, G, C flue-pipe chord held for 8 s, then a long diminuendo to 12 s; at 12 s each hatch's lamp goes green with two relay ticks and a "ting" | the Vault ZONE at full level; ALL as a low (under 120 Hz) felt layer at -24 dB |

### 4.7 The wonder weapons (signature sounds, from `05-WONDER-WEAPONS.md`)

All four are balanced to the rule in 3.10 (within 2 dB of the donor's fire sound, measured first, F15).
Each also has one sound no other weapon makes, so it is known at 30 m.

**EXACT CHANGE**
- Fire: a coin dropping into a steel chute (0.12 s), then a sharp spring crack. Four coin variants. The price is
  audible (decided here): the coin's pitch rises one semitone for every 10 points above 30 (30, 40 up to 100,
  so up to 7 semitones), and falls back after 1.5 s without firing.
- Lever: a turnstile ratchet (0.25 s) on every cycle. Empty: a coin rejected (a "tink", a thunk and a return).
- Refund: a till bell (0.5 s). Token pickup: a bright C6 "ting". Reload: the lever racked twice and a hopper
  cascade of coins, 2.4 s. Penalty fare (Inspector alive): a second, deeper "clonk" layered on the coin.
- Upgrade, Keep the Change: dropped tokens clatter and spin on edge (1 s) and glint.

**LIVE RAIL**
- Fire: a contactor slam (0.2 s) and a cable whip (0.15 s). Stake lands: a ceramic knock.
- Fence forming: a breaker's two-step "thunk, hum". The standing fence hums at Lodestar's mains, with a
  different timbre per fuse: AMBER a steady 50 Hz with its third harmonic; RED a 100 Hz buzz with dense
  crackle; GREEN a soft 50 Hz with a slow 0.5 Hz swell and a small bell "ping" when a zombie is marked.
- Charges running out: three crackle-density versions of the loop (full, half, quarter), swapped by script
  as the charge falls. Burn-out: a fuse pop. Zombie crossing: a 0.15 s "zzt".
- Fuse swap at a box: a fuse out ("tink"), a fuse in ("thok"), 2 s. Failed pair: 1 s of spat sparks.
- The fence hum is a positioned loop (the cap of four, 2.4).

**THE DISPATCHER**
- Stamp (fire): a post-office rubber-stamp "thump" with a wet edge (0.15 s), then a paper tag fluttering onto the
  zombie (0.3 s). Empty pad: a dry stamp. Pad change: a pad slid out and a fresh one pressed in, two slow bellows
  pumps and a latch click.
- Send (aim held 0.4 s): a bellows cough, then one rising whistle for each parcel, 0.1 s apart and each a step
  higher (up to four, so a full send is a rising run), each ending in a thud of arrival at the point. A send into a
  hatch: the Capsule Post's cork-pop in small. A send with no stamps out: a short bellows puff. After every send
  the bellows refills for 3 s: a slow leather inhale with the brass collar ticking, ending on a soft latch click
  that says it can send again; a trigger pulled before it ends gets the dry stamp click.
- Burst: the Departure Note as an organ pedal (the three partials), cut off after 0.6 s by a wet slap (a paper bag
  popped under water is the model), then a paper-scrap rain (1.5 s). Upgraded FORWARDING ADDRESS: a fuller burst, and
  a lower falling whistle for the surviving parcel as it walks back.
- Charging at the organ console: a glass chime rising while the Bellows breathes on the pistol.

**TOP TO BOTTOM**
- Spray: a dry, close can hiss (start, loop, end). Can switch: a ball rattle, three pitches, one per colour (0.5 s).
  A tag: a wet slap. ALL STAND (MAGENTA): a single short platform whistle (a guard's peep, 0.4 s) as the zombie turns,
  then the shuffle of feet walking to its waiting place and a soft settle behind the line; no drum, no beat, no
  music, and at most three shuffles audible at once. HAZARD (YELLOW): a relay tick every 0.5 s on the zombie, then a
  "pop and splat" with a flat ring "fwip". WET PAINT (CYAN): the slick squeaks under feet; a fall is a wet "splat,
  slide". END TO END's splash: a hiss and flick.

### 4.8 The Night Inspector

| Moment | Layers | Where |
|---|---|---|
| announced (about 17 s into the round) | the plain Three-Tone, then the Voice (V12 to V14); the first time in a match, V50 (the penalty-fare sentence) | ALL |
| arrival (20 s) | the brass inspection plate in the floor rattles on its frame for 2 s, lifts with a hinge "clank", and he hauls himself out (leather and cloth, then boots on tile); his whistle (a long low single blast of 1.2 s, lower and slower than the Conductor's); the pulse begins (3.4), the lamp's squeak on every step | ZONE (the plate), and a far low-passed whistle at -26 dB to ALL |
| moving | a brisk rolling waddle: short quick steps with a wet leather creak and the satchel's swing; the paper ribbon of punched tickets rasping along the floor behind him, always audible; every 10 s a 2 s scuttle: faster steps, the lamp squeaking quicker, the ribbon's rasp louder | ZONE (radius 700) |
| leaving, or following a player who left | the plate rattles again, he climbs down and the plate settles with a hollow clank | ZONE |
| marked | "TICKET, PLEASE" (line, plus a terminal blip) | 1P |
| the Punch | tell: the hydraulic arm's whine rising from 400 to 1200 Hz over 0.9 s; the hit: a clean metal "chunk"; on the marked player, a ticket torn off and a rubber stamp (the fine); recovery 0.7 s | ZONE (radius 1500) |
| the Sweep | tell: a satchel strap and arm creak over 0.6 s; then a "whoosh" and a "thwack" | ZONE |
| Penalty Notice | plants his feet (a thud), a rising whine for 1.2 s (the longest tell), a ring thud and a low 50 Hz swell for the ring | ZONE (radius 1500) |
| the Whistle | three blasts at 0.0, 0.5 and 1.0 s of 0.35 s each; six zombies rise (stock) | ZONE |
| lamp opens (any of the five ways) | one identical sound: a glass hinge squeal (0.2 s) and an amber chime, a clean C6 swelling for 0.7 s (decided here: every opening makes the same sound so the team learns "shoot now") | ZONE (radius 2000) |
| death | the lamp bursts at 0.4 s (glass pop, tinkle, a dying flare hiss) and the pulse stops dead; the tunic collapses at 1.2 s (a heavy thud, brass buttons clattering, a stiff cloth "whump"); the cap falls at 2.0 s (a flop and a roll); 2 s of near-silence | ZONE |
| reward | each fined player's pile of fines pours out (coin cascade, 3D) and its owner alone hears a bright "ting" as they collect it; each living player gets a ticket punch "ka-chunk" and a UI blip; the ledger slaps on the floor (first kill) | ZONE, 1P each |

### 4.9 The Rollers

| Moment | Layers | Where |
|---|---|---|
| round start | the plain Three-Tone, the Voice (party-train announcement, V08 to V10); car 6's door opens; the Party Car plays the S1 teaser (8 s) muffled; a mirror-ball shimmer sweeps Platform A (a 3 s moving glitter sound); the global track begins at S1 at 11 s | ALL, ZONE |
| a chain approaching | one moving loop on the leader: polyurethane wheels on tile, a broadband rumble from 150 Hz to 2.5 kHz, a bearing whine that rises with speed, a "tk-tk" stride click every 0.6 s; audible from 1800 units, so a line is heard before it is seen. A 2 s pass-by clip (the whine rising then falling by 4 semitones) is triggered 0.8 s before the closest approach, because the engine has no Doppler | ZONE |
| the whoop | the chain leader's referee-style whoop (non-speech vocal, 3 variants; recorded later, see 5.6) | ZONE |
| swipe | a satin "fwip"; a hit lands as the stock player-hurt sound plus a "thwap" | ZONE |
| wall crash | a flat body "whump", a skate rattle, a small "oof" (vocal) | ZONE |
| death | a glitter-burst pop with a bead shimmer (0.8 s); the skate comes off and rolls away: one wheel spinning for 3.5 s, tapping a wall at the end (a moving 3D origin) | ZONE |
| tripped (a token, an AMBER fence, CYAN paint, a sent Roller) | wheels skid out, a flat back landing and a slide on the back with wheels spinning (1 s loop); after 2 s a wobbling get-up | ZONE |
| the skate throw (every living player out of reach for 10 s) | the chain skids to a stop outside the opening (0.5 s); then, in turn, a release "fwip", loose wheels whirring in flight, and a wooden "thock" on a wall or a flat "thwap" on a player (30 damage); one throw every 2 s per Roller | ZONE |
| round end | the last Roller drops Max Ammo (stock sound); the tape-stop M6 (1.5 s) replaces the track's channel; the 500 point payout (stock); silence for the stock pause; the next M1 | ALL |

### 4.10 The four traps

| Trap | Moment | Layers | Where |
|---|---|---|---|
| Decon Foam (Cordon, 750, 15 s) | start | three beacon beeps (Lodestar yellow), the pump spins up 1.0 s, four valve "chunks" | ZONE |
|  | running | a thick foam hiss and gurgle loop (one loop at the corridor's centre), a slow sticky squelch and a muffled struggle for each zombie that wades in (the foam holds, it does not kill: no kill sound) | ZONE |
|  | end | four valve "chunks", the pump runs down 1.5 s, drips | ZONE |
| Third Rail (Platform A West, 750, 25 s) | start | the fuse-box lever clunk and a big contactor "ka-chunk" (0.4 s), the pit's hum rising to 50 Hz and 150 Hz | ZONE (radius 1100) |
|  | running | the hum loop, a "zzap" per kill, arcs every 384 units | ZONE |
|  | end | a contactor "clack", the hum decays over 1.0 s | ZONE |
| Flashover (Converter Hall, 750, 8 s) | start | the marble switchboard's knife switches slam; every hall loop cuts to silence for 0.3 s (the hall goes dark); then the rectifiers flash: a white-violet crack, a rising capacitor whine and an ozone hiss | ZONE (radius 1500) |
|  | running | the cages' arc-jump loop (+8 dB); a stumbling scuff and a muffled groan for each blinded zombie standing with its hands over its eyes | ZONE |
|  | end | the lights strike back one bank at a time with tube buzzes, and the cages drop back to their idle buzz over 1 s | ZONE |
| the Bellows (Vault, 750, 15 s) | start | a lever "ka-thunk", the intake grating opens, an air-draw roar rising over 2 s, and the Departure Note (full chord) held for 15 s | ZONE (radius 1500) and the Vault |
|  | running | blades chopping ("chunk, whump") per zombie; players pulled get a wind rush | ZONE, 1P |
|  | end | the Note fades, the blower exhales for 3 s; at 90 s the breath resumes | ZONE |

Level: each trap loop is at least 8 dB over its zone median and within 2 dB of the stock trap sound measured
the same way (decided here).

### 4.11 Pay phone, lore pickups, secrets

| Item | Layers | Where |
|---|---|---|
| a pay phone rings (three phones, three events: the Fare Hall's once per match; the Police Post's when the Night Inspector arrives; the Car Barn's does not ring) | an electromechanical bell: a double ring "brr-ring" of 2 s, then 4 s of silence, three rounds of it; hangs up silent if a player comes within 180 units (the old module) | ZONE (radius 900) |
| answering (Fare Hall, Police Post) | the handset's lift clack, a line hum with the Carrier faintly in it, then a line assembled from the Voice (5.1, the pay-phone fragments), with splices audible (the Police Post reads out the Inspector's roster), and a hang-up clunk | 1P |
| the Car Barn phone lifted | the lift clack, a number tapped out in pulse-dial clicks, then an engaged tone (0.5 s on, 0.5 s off) for 8 s, and a hang-up clunk; no voice | 1P |
| Dr. Strand's tape | the micro-cassette's record button click, 1 s of room tone of the place where she recorded it, then her voice (5.3), a stop click | 1P (others read the text in the Tab screen) |
| a page of Vayle's notebook | a paper rustle and the Departure Note, 1 s at -30 dB | 1P |
| a mural logged (3 s in front) | a spray can's rattle and a hiss, a soft register click | 1P |
| the zero stud knifed | every clock ticks once: six positioned "tock" sounds (one per stopped clock; the Terminus clock is too far to hear) and one low 2D "tick" at -18 dB for everyone | ZONE and ALL |
| the photo booth (500) | a flash, a whirr and a strip falling into the tray; the fourth frame: a single close breath 1 s behind the player at +5 dB | 1P |
| the printer prints names | a dot-matrix burst and a paper tractor feed, 3 s | ZONE |
| Lost Property | a service bell "ting" and a drawer slide | ZONE |
| the supply locker | a latch and a clank | ZONE |
| the hidden song's three trophies | each trophy: a brass wheel spinning down, a click; the third starts M11 | 1P, then ALL |

### 4.12 The terminal family (UI)

A single family: short, dry (no reverb), made of relay and solenoid clicks and sine blips on the C pentatonic
(1.1). Peaks at 3.10.

| Sound | Length | Build | For |
|---|---|---|---|
| wheel open | about 180 ms | a relay click, then a soft rising C5 to G5 two-note chime, quieter than the Three-Tone | the emote wheel (`10-EMOTES.md` 4.6) |
| wheel hover tick | about 20 ms | one mechanical relay tick, at least 8 dB under the open sound | each wedge |
| wheel confirm | about 120 ms | a ticket-punch "ka-chunk" (the dance 7 punch) with a C5 blip | choosing an emote |
| Tab screen open | about 150 ms | relay chatter and two data blips, E5 then A5 | the Tab screen (the intel tab) |
| Tab screen close | about 100 ms | the same blips reversed, A5 then E5, softer | closing the Tab screen |

How they are played is not stated anywhere (F14). Two routes, to be proven in this order:
(1) a client-side call from the Lua of the Maxis wheel, which is the only route fast enough for a hover tick
(20 ms must not wait for a server round trip); (2) for Tab open and close, the server plays a local sound on the
`intel_tab` notification (one of the four reused client-to-server names; latency one server frame plus the round
trip, acceptable for open and close but not for ticks). If route 1 does not exist, the hover tick is dropped
and the wheel has open, confirm and a server-side "tick" only on page change. The first proof is a
minimal Lua probe that plays one banked alias in the lab client and is seen in the capture.

## 5. Voice lines needed later (todo only; nothing is generated now)

Slots, not final text. The example line in each row fixes tone only. Recording or generating is a later task and
the choices at the end of this section belong to the owner.

### 5.1 The Voice of the Rapid (Evelyn Marsh, 1984)

Direction: warm, exact, slightly amused; a 1984 station announcer, plain mid-Atlantic diction, never sinister,
never in a hurry. Processing: band-limited 250 Hz to 4 kHz, light compression, a faint splice crackle between
glued words, as ZERO assembles sentences from recordings; one slot is a sentence with a word that was never
recorded (a 0.8 s hole). 52 slots, plus 14 glue words (the, twenty-three, forty-seven, to, Zero Line, is, now,
boarding, midnight, late, thirteen, minutes, please, edge).

| Group | IDs | Count | Example (tone only) |
|---|---|---|---|
| round start | V01 first departure; V02 to V04 ordinary (three variants); V05 every fifth round; V06 round 25 and later; V07 a single passenger | 7 | "The twenty-three forty-seven for Zero Line is now boarding. Please watch the edge, and each other." |
| Roller round | V08 to V10 party-train announcements; V11 the party service has ended | 4 | "A private party service is arriving at Platform A. Skates are not permitted on the platform." |
| Night Inspector | V12 to V14 inspection in progress; V15 inspection complete; V50 the first-time sentence, once a match | 5 | "Fare inspection is now in progress. Please have your ticket ready, and be honest with yourself." V50: "Passengers found without a valid ticket will be charged a penalty fare." |
| power | V16 the first full sentence; V17 the garbled "main power on" of the old build | 2 | "Main power has been restored. Thank you for your patience. It has been a long time." |
| quest steps | V18 to V21 clocks 1/4 to 4/4; V22 road set; V23 Conductor on the platform; V24 Handle taken; V25 Handle fitted (Terminus boarding); V26a to V26c the Terminus times (three readings of the same time; there is no arrival announcement); V27 return; V28 out of service | 13 | "The thirteen minutes have been accounted for. Thank you." |
| Capsule Post | V29 not enough points; V30 tube sealed; V31 no capsule; V32 changeover; V33 inspection; V34 hatch unsealed | 6 | "The tubes are changing direction. Please stand clear of the hatches." |
| pay-phone fragments | V35 to V46 (twelve fragments: V35 to V40 the Fare Hall line, V41 to V45 the Police Post's roster read out, V46 the sentence with the hole) | 12 | "...your call to the twenty-three forty-seven... will be... connected... shortly." |
| other | V47 the zero stud; V48 the manifest printer; V49 this service terminates here (the game over) | 3 | "This service terminates here. Passengers should leave by the nearest exit, if there is one." |

### 5.2 The four heroes, in their film roles (40 slots each, 160 in all)

Structure: the base game's categories of player lines (round start, low ammo, revive, perk bought, wonder
weapon obtained, special enemy seen, each quest step), plus this map's own. Stock heroes speak through
`vo_prefix` p1_ to p4_ aliases (F16); our new lines need their own aliases and a routing by character that is
not proven (a build question for the voice package).

| Category | Count per hero | Notes |
|---|---|---|
| round start (match opening) | 2 | in the Cordon, after the intro |
| round start (every fifth round) | 1 | |
| low ammo | 2 | |
| reviving a teammate | 2 | |
| thanks when revived | 1 | |
| downed, calling for help | 3 | |
| a new perk bought (Double Takes, Baker's Dozens, Bon Voyages, Sour Grudges) | 4 | the six stock perks keep the stock lines |
| wonder weapon obtained (Exact Change, Live Rail, the Dispatcher, Top to Bottom) | 4 | one each |
| Roller seen | 2 | |
| the Night Inspector seen | 1 | |
| the Night Inspector marked me | 1 | |
| the Night Inspector killed | 1 | |
| the Conductor seen | 1 | |
| quest steps: power, first clock, last clock, road set, Handle taken, boarding, Terminus arrival, return | 8 | |
| zone discoveries (the Arcade, the Parlour, the Bellows Vault) | 3 | |
| pay phone rings, pay phone answered | 2 | |
| a tape picked up | 1 | |
| the hidden song heard | 1 | |
| **Total** | **40** | |

| Hero (film role) | Voice direction | Example line |
|---|---|---|
| A.J. (the Transit Cop) | dry, procedural, a man who signed a false report and knows it | "I wrote 'gas' on a form. This is not gas." |
| Andre (the Graffiti King) | loud, cocky, delighted by a clean canvas | "That's the cleanest train in the city. Not for long." |
| Poindexter (the Signal Engineer) | nervous, exact, talks to the equipment | "The diagram says it is approaching. The diagram has no right to." |
| Sally (the Night Desk Reporter) | a broadcast voice, composed on camera, cracking off it | "Channel 9 Night Desk, one year after the gas incident, and I am standing in the gas incident." |

### 5.3 Dr. Strand's eight tapes (8 slots, one speaker)

Imogen Strand: Lodestar's lead engineer, dry, careful, tired, a voice that has rehearsed what it will say to a
board. Each tape is 25 to 50 s (decided here; the wiki's text sets the real length, which goes into the length
table). The text of all eight tapes, with dates, is in `wiki/strand-tapes.md` (tape 1 to tape 8 there are
the slots below, in the same order and found in the same places); the "Example" column is tone only and the wiki
text is what is recorded. Each tape starts with 1 s of room tone of the place she recorded it (the seven room
tones are in 8.10).

| Tape | Where it is found | Direction | Example (tone only) |
|---|---|---|---|
| 1 | the Cordon, in the van | the first, formal, for the record | "Tape one. The tube answers. I have written that sentence four times and I still do not like it." |
| 2 | the Arcade, Hole Number Nine | wry, an engineer eating a doughnut | "Tape two. The doughnuts here are the only thing in this project on schedule." |
| 3 | the Police Post, the evidence tag | tighter, she is being ignored | "Tape three. I have sent the memo to four people. Nobody has sent it back." |
| 4 | Platform A East, car 2, a seat | quieter, in the train | "Tape four. I am sitting where the passengers will sit." |
| 5 | the Car Barn | working, a little breathless | "Tape five. If the Carrier is a lamp-proving current then it is also a request." |
| 6 | the Exchange | afraid, controlled | "Tape six. ZERO cannot log a failure. It can only wait." |
| 7 | the Exchange | decision | "Tape seven. I am going to ride it myself. Somebody should keep a hand on it." |
| 8 | the Terminus, bench 4 | the last, ends mid-sentence in the cab (hook H1) | "Tape eight. We are exactly on time, and I think that means that" |

### 5.4 The Night Inspector (8 slots)

Horace Pell, thirty-one years of service. A flat, courteous, bureaucratic baritone, never shouted.

| Slot | When | Example |
|---|---|---|
| P1 | arrival | "Tickets, please." |
| P2 | marked | "Your ticket, sir. Madam. Whoever you are." |
| P3 | the Punch lands | "Not valid for this journey." |
| P4 | fine taken | "Penalty fare. Thank you." |
| P5 | the Whistle | "Passengers will remain behind the yellow line." |
| P6 | under half health | "Tickets, please. Tickets, please." (faster) |
| P7 | the lamp opens | "Ah." |
| P8 | death | "Valid." |

### 5.5 The Conductor of 047 (3 slots)

A guard's voice, loud and cheerful, from 1984. "All aboard for the twenty-three forty-seven." (appears);
"Doors closing. Stand clear." (walking, as he shuts each car); "Terminus. All change." (killed).

### 5.6 Other voices (23 slots)

| Who | Slots | Notes and example |
|---|---|---|
| the photo booth | 5 | a recorded patter: "Please hold still." "Three, two, one." "Please do not look behind you." "Your strip is ready." "Thank you for your custom." |
| pay-phone oddities | 4 | non-Voice: breath on the line, a child's hum, a man saying "hello?" twice, an operator's "number, please" (one each; one is never answered) |
| the Rollers' non-speech vocals | 14 | whoop (3 variants), pain (4), crash "oof" (3), laugh (2), death (2): recorded with the same care as lines, and never words. The three whoops are made as sound effects (8.6); the other 11 stay here |
| the Voice's glue words | counted in 5.1 | |

### 5.7 Counts and the owner's choice (later)

| Speaker | Slots |
|---|---|
| the Voice of the Rapid | 52 (plus 14 glue words) |
| the four heroes | 160 |
| Dr. Strand | 8 |
| the Night Inspector | 8 |
| the Conductor | 3 |
| the photo booth, pay-phone oddities, Rollers | 23 |
| **Total** | **254 slots, plus 14 glue words** |

Hero voices have two routes, and the choice is the owner's, later: (a) match the base game's actors, which
needs those performers' agreement and a studio, and cloning or sound-alike imitation of their voices from game
audio must not be done without it; (b) new voices for new "film roles" (the film recast four actors in 1986,
which is the premise of the map), recorded or generated for this map only. Route (b) is simpler, legal and
fits the lore, but the heroes would not sound like themselves in the stock game's lines on the same server.
This chapter does not decide it.

## 6. Buildability, budget and proofs

### 6.1 What exists and what does not

| Exists (proven or merged) | Evidence |
|---|---|
| the bank writer for usermaps: `iw7_sab.py`, `iwz_audio_bank.py`; FLAC 1024-frame check; non-stock re-encode | merged 10 Nov; audio NOTES s4, s5 |
| 25 positioned emitters and `audio_layout.py`, anchored to lights, decor, quest and interaction records | `research/C` 2.6 |
| per-player beds as retriggered clips with twins (F2), proven audible across 6 zones and seams | audio NOTES builds 12 to 14 |
| the soundscape module: scatter, loops, PA, flicker, power (bank-by-bank release), phone with hang-up, train, "lonely", intro; radius gating | audio NOTES, soundscape task |
| the hidden-song module (`song_ee_init`): the real key, the song across a bed retrigger | audio NOTES f12 |
| music synthesis (`station_zero_music.py`), `soundscape_dsp.py`, the stock-sample derivations | audio NOTES |
| measurement: `Capture-ProcessAudio.ps1`, `audio_report.py`, `audio_measure.py`, `music_find.py`, `capstats.py`, `declick.py`, the solo-window fixture (hold time, quiet spot) | merged 10 Nov; audio NOTES s1 to s6 |
| proven audible: bank cues at +0.08 to +0.16 s after their trigger (xcorr 0.48 to 0.98); the stock round-start alias re-banked | audio NOTES s5, s6 |

| Does not exist (or is not proven) | Consequence |
|---|---|
| sound measured from the game is on a side tool; weapon sounds never measured audible (F15) | the weapon package starts by measuring the donor |
| stopping a sound played in space (F7) | the rules in 1.5; the changeover organ and the Bellows trap's held Note are the long exceptions |
| music for a player who joins mid-song (F8) | the Roller track is chunked; the hidden song is not |
| ducking by script in a usermap | cues are mastered at their own level (1.4) |
| the engine's voice count is not readable | the loop count is the script's counter plus geometry (6.3) |
| a moving emitter playing a loop (the polisher, the wind, a Roller chain's wheels) | not shown for loops; a first proof (6.3, P5) |
| a usermap playing a mod-bank alias (the Needle Drop playlist) | one check (3.9) |
| a UI sound from Lua (F14) | 4.12 |
| custom hero VO routing by character (F16) | the voice package's first question |
| the stock round-end alias (F11) | replaced by script |

### 6.2 Alias count and bank size (decided here: estimates; the first bank build replaces them)

Against the existing 60 aliases of the current bank (`station_zero_audio.json`; the audio NOTES' last bank,
src15, also holds 183 rows because it re-banks stock sources: the two counts are different things).

| Group | Aliases | Basis |
|---|---|---|
| beds | 36 | 18 zones, a twin each |
| the Carrier | 18 | 6 stages with twins, and 6 round-end resolves |
| stingers, intro, game over, Three-Tones | 8 | M1 (3), M2, the reversed Three-Tone, M13, M14 |
| Roller track, teaser, leaks, tape stop | 12 | 7 chunks, 1 teaser, 3 leaks, 1 stop |
| other music and music-like | 20 | the hidden song and its sting, the crossing, the power-on cue, 4 jingles, the cassette, 3 copier cycles and 4 copier effects, 3 Inspector tocks |
| zone emitters | 151 | 60 loops, 45 scatter groups at about 2.5 variants, less about 25 shared sets, plus lit twins |
| key-moment cues | 175 | round and power 6; the road and teleport 27; the Capsule Post 16; the four weapons 54; the Inspector 20; the Rollers 14; traps 16; phone, lore, secrets 16; UI 5 |
| **Total (no voice)** | **about 420** (range 380 to 460) | against 60 today: about 7 times |

| Group | Size (FLAC) | Basis |
|---|---|---|
| beds | 12.6 MB | 18 clips of 26 s at 22.05 kHz, about 0.7 MB each, streamed |
| the Carrier | 3.1 MB | 6 stage clips of 26 s (tonal, compresses well) and 6 resolves |
| stingers and intro | 1.4 MB | |
| music | 28.0 MB | Roller track 11, hidden song 10.6, teaser and leaks 1.5, power-on cue 1.0, jingles 1.8, cassette 1.2, the rest 0.9 |
| zone emitters | 15 MB | 59 loops of about 10 s at 16 kHz, 45 scatter sets |
| key-moment cues | 12 MB | about 130 files of 2 to 3 s |
| **Total (no voice)** | **about 72 MB** (range 60 to 95) | loaded memory budget 30 MB (cues, stingers, short emitters); the rest streamed |
| voice, later | about 33 MB | the Voice 6, heroes 19, tapes 6.4, others 2 |
| **With voice** | **about 105 MB** | at the measured 5.4 to 8.6 MB per second from the Canada host, 12 to 19 s of download |

Delivery: the usermap route's download is unproven for a dedicated server (`research/A` (o)); the mod route
works. Whichever carries the bank, 72 MB is within what the old bank carried (44.9 MB loaded, 79.8 MB streamed).

### 6.3 The proofs (all measured; "looks right" is not used for audio either)

| # | Proof | Pass rule |
|---|---|---|
| P1 | every cue is audible from the game | each cue found in the capture by the audio witness (`music_find.py` or the solo-window fixture), within 0.3 s of its logged trigger; structured sounds with normalised cross-correlation 0.4 or more (the old runs measured 0.4 to 0.98); noisy 3D sounds, which stay under 0.2 even alone, by level over the zone floor in a solo window, at least +6 dB (the old runs measured +2.8 to +29 dB). The cue list is the sheet in section 4 plus all 104 emitters. |
| P2 | loudness within targets | each layer within its 3.10 target on three declicked 60 s captures; masters verified on the stored dual-mono file before bank build |
| P3 | no more than 36 loops at once | at 20 sampled positions (the centre of each of the 18 zones plus the Fare Hall to Arcade mouth and the Escalator Hall foot): the script logs the loops it is running, and the audible set by distance; the maximum audible must be 36 or fewer, and with the dynamic reserve in use (a Live Rail fence pair, a Roller chain, the Capsule Post and a trap running together) 34 or fewer. The engine's own voice count is not readable (6.1), so this stays a script-side measurement plus geometry |
| P4 | the Carrier is real | the Carrier's partial lines in the capture rise by 3 dB per stage within 1 dB, and fall by 20 dB or more within 1.5 s of every round end (the narrow-band measure of the same tool) |
| P5 | the new mechanisms work | (a) the round-end resolve replaces the Carrier voice with no click above the declicker's span; (b) the Roller chunk seams: the 100 ms envelope at all 6 seams stays within 6 dB of its neighbours (the old seam test found -72 dBFS dips before the twin fix); (c) a second client joining mid-round hears the track within 32 s; (d) a moving emitter keeps its loop (the polisher) with the origin moving; (e) the UI route plays one banked alias from Lua or is declared unavailable |
| P6 | independent listeners judge a recorded walk-through | three listeners who have not read this chapter get one capture: a walk through all 19 zones before and after power, a round start and end at rounds 1 and 12, a Roller round, an Inspector, the Pack-a-Punch trip. Zone test: 19 clips of 20 s, each named from a list; at least 70 percent right overall and no zone under 50 percent (decided here). Questions: did you hear a tone that rose; did you notice it stop between rounds; was anything tiring or confusing; which sound stood out most in each zone. A "tiring" report on the Carrier from two or more listeners reopens its level. The owner is not counted as independent |
| P7 | the originality and tone gate | each music piece: 30 s of draft played to the owner before full production (7); the hidden song passes its originality gate (3.7) |

Order of the first measured runs (cheapest question first): the bank checks (seconds), then one plan that proves
the Carrier stages and the round-end replace, then the Roller chunks with a second client joining, then the loop
count at 20 positions, then the moving emitter and the UI route. Package names are for `12-BUILD-PLAN.md`;
suggested (decided here): AU1 bank and layout, AU2 music, AU3 voice, AU4 weapon sounds with W1, AU5 UI with U1;
SFX1 (build plan) makes the sound effects of section 8.

### 6.4 The length table (F6)

The script needs a length for every sound it times; the dedicated server returns 0 for mod-bank sounds. One
table, filled by the bank tool from the files, in seconds: the Roller chunks (32.000 each), the teaser and leaks
(8.000), the hidden song (210.000), the Carrier clips (26.000), the
round-start stingers (5.500), the round-end resolves (4.500), the power-on cue (20.000), the crossing (3.000),
and every voice line and tape. A row with a missing length fails the bank check.

## 7. Risks and decisions left to the owner

| # | Item | Why it matters |
|---|---|---|
| 1 | the tone gate | the owner rejected the old music as heroic, and the old round cues were the stock game's 80s synth-rock house style. This chapter still asks for 1984 synth music for the Roller track and the hidden song (the owner's brief), so each piece gets a 30 s draft heard by the owner before a full production |
| 2 | the Carrier may tire players over an hour | it is a tone that rises for a whole match. P6 asks listeners. If it is tiring the first lever is the level (-3 dB per stage), the second is a per-player option; `.mute` as it stands silences music only, not ambience |
| 3 | the quiet between rounds is only about 5 s | the stock pause is 9.7 s (F12). Lengthening the pause means changing the wave loop, which this chapter does not assume |
| 4 | hero voices | the choice in 5.7 is the owner's |
| 5 | the hidden song | a late joiner misses it (F8); the human or generator route is the owner's call |
| 6 | the Needle Drop playlist on a usermap | one unproven check (3.9) |
| 7 | the UI sounds | depend on a Lua route nobody has shown (4.12) |
| 8 | the ambience is large | 105 emitters against 25 today. The first complete version may ship the signature, the bed and the carry loop of every zone (about 55 emitters) and add the rest zone by zone while the loop count is measured |

## 8. Sound-effects generation list (for package SFX1)

Added after the owner's decision that sound effects are made with the ElevenLabs sound-effect tools (a text
prompt, a duration of 0.5 to 30 s, an optional seamless loop, and a prompt-influence setting) while voice lines
stay a todo. This is the complete list of the sound effects of STATION ZERO that the cue sheets (section 4),
the ambience (2.3) and the other chapters (`03` to `07`, `09`, `10`, `wiki/strand-tapes.md`) call for, except
what is listed once as "not generated" below. 406 rows in 11 groups. Where a sound was needed but no chapter
defined it, the row is an addition (listed in 8.16).

How to read a row. The alias is the bank alias. "Length" is the final file length in seconds; a row marked
"(v3)" needs three variants, generated as three separate takes. "Loop" means the file is cut to join seamlessly;
"one-shot" is played once. The brief is the text sent to the generator: a concrete physical source, material,
space, perspective and envelope, with no brand names, no named game, film or artist, and no music unless the row
says so. "Must NOT sound like" is never sent in the prompt (a negative can pull the generator toward the cliche);
it is what the second listener judges the result against. The last column says whether the engine plays the sound
in space (3D) or as a local sound (2D). A row marked with an asterisk after its alias is one of the 30 for the
first playable build (8.15).

Target level. Levels are written against the game's own comparable sound, measured the way 3.10 measures
(declicked captures, 60 s windows, median, three repeats, plus or minus 2 dB):

| Code | Means | Basis |
|---|---|---|
| = P, P-6, P+3 | the stock purchase sound at its loudest (peak about -29 dBFS), then so many dB under or over it | F10; the stock door purchase is P |
| Cue band | peak -24 to -20 dBFS, equal to the stock purchase sound at its loudest | 3.10, scripted cues |
| D-2, D+0 | RMS relative to the donor weapon's measured fire sound | 3.10 and F15; the donor is measured first |
| F+8 | so many dB over the floor, the median of the zone where it sounds | 2.2; a signature may reach +20 over the floor |
| -44 dBFS median | a bed's own level, the zone median of 2.2 (lit value) | 2.2 |
| peak -34 dBFS and the like | the UI peaks of 3.10 | 3.10 |

The stock music sits at -12 LUFS (F5). No row here is music, so none is normalised to LUFS. The rows that come
close to music (the copier cycles AR1 to AR3, the cassette BO1) are mastered to their F level, not to
the music level, because they are emitters.

### Not generated (listed once)

| Not generated | Why |
|---|---|
| mystery wheel sounds, the stock perk-machine purchases and jingles of the six stock perks and Up 'N Atoms, the stock door and trap purchase sounds, wall-buy, Max Ammo, round-end money, the stock power relay and tube-strike sounds (`power_buy_large_light_turn_on`, `power_buy_group_florescents_turn_on`), the Pack-a-Punch machine's own sounds | stock stays stock |
| stock zombie voices, spawn bursts, attacks, hit reactions, deaths, gibs and footsteps; the donor weapons' own handling sounds; the stock player-hurt sound | stock stays stock (the Rollers' swipe hit and the Conductor's footsteps are layered on the stock sounds) |
| the Departure Note, the Carrier clips (six stages, six resolves), the Three-Tone, the reversed Three-Tone, the power-on cue, the crossing swell M9, the Roller track and the Party Car teaser and leaks, the tape stop, the hidden song, the four long jingles, the Needle Drop playlist, the intro and game-over cues | music or synthesis (section 3); made by the music package, not by the sound-effect generator |
| every voice line of section 5: the Voice, the heroes, Strand's tapes, the Inspector, the Conductor, the photo booth patter, the pay-phone oddities, and the Rollers' pain, crash "oof", laugh and death vocals | voice stays a todo; none is generated |
| low-passed copies for "everyone" (the diesel, the far whistle, the muffled crossing swell, the changeover's felt layer), the pitch steps of the relay tone (C5, E5, G5), the Dispatcher's whistle steps (each parcel of a send a step higher), Exact Change's price pitch steps, the lit twins and the second rectifier cage (CH3) | made from one generated file by the bank tools (DSP), so they cost no generation |

Three fallbacks are named in the rows where they apply: pitched sounds are measured and shifted if more than 30
cents off; the sub-100 ms UI sounds fall back to the generated click plus a synthesised blip; and the cassette BO1
is generated at 16 s and stretched to its 44 s slowdown by the tools.

### 8.1 Transport: the Capsule Post

Source: 4.6 and `03-TRANSPORT.md` section 5 (hatches, address dial, postage; nothing in this group is a train, a line or a stop). The Departure Note under launches and the changeover is synthesised (music package), not generated here; the cork-pop, whoosh and bell below are laid over it.

| # | Alias | What | Length (s) | Loop or one-shot | Generation brief | Must NOT sound like | Target level | 3D or 2D |
|---|---|---|---|---|---|---|---|---|
| 1 | `iwz_post_wheel_turn` | Pressure wheel turned to unseal a hatch | 1.5 | one-shot | Cast iron pressure wheel on a brass spindle turned slowly by hand, dry metal squeak rising in pitch with stick-slip, close microphone, small tiled room, abrupt stop at the end. | cartoon squeaky toy | P-3 | 3D |
| 2 | `iwz_post_dial_click` | Address dial turned: one detent click per name plate (v3) | 0.3 | one-shot | A brass ring on a spindle turned by hand to the next enamel name plate, one crisp spring detent tick and clack with a tiny brass rattle, close, dry, no reverb. | combination safe dial | P-6 | 3D |
| 3 | `iwz_post_steam_release` | Steam let out after unsealing | 1.2 | one-shot | Short burst of steam escaping from a brass valve, sharp hiss decaying into soft sputtering, close perspective in a tiled room, one faint metallic tick at the start. | kettle whistle | P-4 | 3D |
| 4 | `iwz_post_gauge_ticks` | Needle ticks up to rest, six ticks | 1.0 | one-shot | Six small mechanical ticks of a brass pressure gauge needle climbing, each a dry spring click with a tiny pointer tap, evenly spaced, quiet and close, no reverb. | digital beeps | P-9 | 3D |
| 5 | `iwz_post_lamp_relay` | Hatch lamp relay click | 0.3 | one-shot | One crisp electromagnetic relay click with a small bakelite clack, short dry transient, close microphone, no tail. | synthesiser blip | P-8 | 3D |
| 6 | `iwz_post_plate_ting` | Enamel plate ting on unsealing | 0.6 | one-shot | Single light tap on an enamel sign plate, bright short ting with a ring that decays in half a second, small room, close. | modern notification ping | P-8 | 3D |
| 7 | `iwz_post_postage_coin` | Coin dropped into the postage slot (v3: one, two or three coins) | 0.8 | one-shot | A coin dropped into a steel postage slot, bright clink then a dull clunk as it lands in a metal box, close microphone, dry, two distinct events 0.2 s apart. | slot machine jackpot | P-4 | 3D |
| 8 | `iwz_post_door_open` | Glass door of the hatch opens | 0.7 | one-shot | Riveted glass door in a cast iron frame swinging open on brass hinges, one sharp brass hinge clack and a short glass rattle, small tiled room, close. | sci-fi airlock | P-3 | 3D |
| 9 | `iwz_post_seal_thump` | Hatch seals around the rider | 0.4 | one-shot | Dull cork and leather thump of a heavy hatch seating on a rubber gasket, low body, quick decay, a faint breath of air escaping at the end, close. | explosion boom | P+0 | 3D |
| 10 | `iwz_post_takeup` | The Bellows takes up before launch | 1.0 | one-shot | Large bellows drawing air through a brass pipe, band-limited air rising from low to mid pitch over one second, soft leather creak underneath, enclosed tube space. | jet engine spool | P-3 | 3D |
| 11 | `iwz_post_launch` | Cork-pop and fast whoosh on launch | 1.5 | one-shot | A tight cork pop followed at once by a fast rising air whoosh down a metal pipe, bright burst at the start, tube resonance, perspective inside the pipe, ends in a rush. | laser shot | P+3 | 3D |
| 12 | `iwz_post_ride_loop` | Rider's wind roar in the tube | 6.0 | loop | Steady rushing wind in a long iron tube, broadband roar with a slow low swirl and faint pipe resonance, no tonal element, close and enveloping, seamless. | jet engine whine | F+14 | 2D |
| 13 | `iwz_post_junction_clack` | Double clack at a junction passed (v2) | 0.4 | one-shot | Two quick iron clacks as a capsule passes over a pipe junction, heard from inside the pipe, hollow ring and a brief dip in the airflow, close, dry. | train wheels on rail joints | P-6 | 2D |
| 14 | `iwz_post_lamp_thump` | Thump as a tube lamp passes | 0.2 | one-shot | One soft low thump with a short air flutter, like a lamp bracket passing a moving capsule in a pipe, round and dull, no tail, script repeats it every half second. | film heartbeat thump | P-9 | 2D |
| 15 | `iwz_post_passby` | Capsule passing a bystander in a pipe | 1.4 | one-shot | A copper capsule hurtling past inside an iron pipe overhead, whoosh falling in pitch by about five semitones over one second, pipe ring, moving left to right, slight metallic rattle. | jet fly-by | P+0 | 3D |
| 16 | `iwz_post_window_flash` | Flash-tick at an inspection window | 0.2 | one-shot | A very short dry tick like a lamp reflection flashing across a glass window, one tiny glassy tap with a faint electrical click, no tail. | camera shutter | P-9 | 3D |
| 17 | `iwz_post_arrive_hiss` | Released air on arrival | 1.2 | one-shot | Compressed air venting from a large iron hatch, clean hiss with a quick start and a slow soft fade, small tiled room, wide mouth sound, no pitch. | steam locomotive | P-3 | 3D |
| 18 | `iwz_post_arrive_bell` | Two-note bell on arrival, C5 then G5 | 1.5 | one-shot | Two small brass hand bells struck in turn, rising a fifth from C5 to G5, bright strike and clean ring about one second, small hall, close, no vibrato. | doorbell chime | P-3 | 3D |
| 19 | `iwz_post_blowback_suck` | Zombie drawn into the hatch | 0.6 | one-shot | Short sharp suction of air into a pipe mouth with a wet cloth flap and a muffled thud as a heavy body is pulled in, close, dry. | vacuum cleaner | P-3 | 3D |
| 20 | `iwz_post_blowback_pop` | Zombie thrown out of the hatch | 0.4 | one-shot | A cork-like pop of a pipe hatch spitting out something heavy, short air burst with a hollow thump and a cloth slap, close, dry, no tail. | champagne cork | P+0 | 3D |
| 21 | `iwz_post_refuse_clunk` | Dull refusal clunk | 0.5 | one-shot | One dull heavy clunk of a brass lever hitting a stop inside a metal housing, short, no ring, close, flat and slightly deflated. | error buzzer | P-6 | 3D |
| 22 | `iwz_post_refuse_coins` | Coins rattling back out of the slot | 0.8 | one-shot | Several coins dropping and rattling back out through a metal return chute into a tin cup, quick scatter then settling, close, dry. | casino payout | P-6 | 3D |
| 23 | `iwz_post_refuse_hatch` | Sealed hatch rattles and wheel creaks (TUBE SEALED) | 0.8 | one-shot | A sealed iron hatch door rattling once in its frame and a stiff wheel creaking a quarter turn, dull metallic knock, close, small room. | horror door slam | P-6 | 3D |
| 24 | `iwz_post_empty_hoom` | Empty tube hoom | 2.0 | one-shot | Deep hollow hoom of wind across the mouth of a very long iron pipe, low pitch, slow swell and fade over two seconds, no tonal melody, distant, enclosed. | sci-fi drone | P-12 | 3D |
| 25 | `iwz_post_refuse_ticks` | Three amber relay ticks (changeover) | 0.8 | one-shot | Three evenly spaced electromagnetic relay ticks, dry and close, each slightly duller than a click, as an amber lamp proving relay. | digital countdown beeps | P-8 | 3D |
| 26 | `iwz_post_refuse_whistle` | Short guard whistle and plate rattle (inspection) | 1.0 | one-shot | A single short sharp blast of a metal pea whistle then a quick rattle of an enamel plate, close, small room, dry, whistle under half a second. | police siren | P-3 | 3D |
| 27 | `iwz_post_refuse_rest` | Rest refusal: cradle latch and a tired sigh (REST) | 0.8 | one-shot | A brass capsule cradle latch clicking shut with a small metallic clack, then a slow tired sigh of air from a leather bellows through a short iron pipe, close, dry, nothing rising. | error buzzer | P-6 | 3D |
| 28 | `iwz_post_lever` | Direction lever thrown in the Vault | 1.2 | one-shot | Very heavy cast iron lever hauled over in a stone vault, deep ka then a thunk as it locks, metal ring decaying in a big dark reverberant space, close then far. | sword unsheathing | P+0 | 3D |
| 29 | `iwz_post_lamps_amber` | Four hatch lamps tick to amber | 0.7 | one-shot | Four relay clicks in quick sequence 0.15 s apart, dry bakelite relay ticks as lamps are switched, all in the same dull timbre, close. | computer boot beeps | P-9 | 3D |
| 30 | `iwz_post_plate_arrow` | Enamel plate arrow turns to a new direction | 1.0 | one-shot | A small brass indicator arrow turning on a spindle behind an enamel plate, soft gear whirr and two escapement ticks, ending with a tiny snap, close. | robot servo whine | P-9 | 3D |
| 31 | `iwz_post_changeover_organ` | Whole organ exhales (changeover, 12 s) | 12.0 | one-shot | Huge old organ pipes exhaling in a vast stone vault, a low breathy swell rising over two seconds into a held soft C and G flue-pipe chord for eight seconds, long slow diminuendo, no melody, no vibrato. | cinematic horror drone | P+3 | 3D |
| 32 | `iwz_post_hatch_ready` | Hatch lamp goes green after changeover | 0.9 | one-shot | Two relay ticks and one small enamel plate ting, evenly spaced across about a second, dry close mechanical sounds, small room. | video game level up | P-8 | 3D |

Count, group 1: **32**.

### 8.2 Power, the road to Pack-a-Punch, the teleport and the Terminus

Source: 4.3 to 4.5 and `04-PAP-QUEST.md`. The Three-Tone, the power-on cue and the crossing swell are music or synthesis and are not here. The Pack-a-Punch machine keeps its stock sounds. Where a pitch is named the file is checked and shifted by the bank tools if it is off by more than 30 cents.

| # | Alias | What | Length (s) | Loop or one-shot | Generation brief | Must NOT sound like | Target level | 3D or 2D |
|---|---|---|---|---|---|---|---|---|
| 33 | `iwz_power_breaker_slam` * | Breaker of G-2 thrown, contactor slam | 1.0 | one-shot | Large industrial knife switch slammed shut, heavy copper blade clack followed by a deep contactor thunk and a short metallic ring, dry concrete hall, close. | movie explosion | Cue band | 3D |
| 34 | `iwz_power_diesel_start` * | Diesel turning over, three coughs, catches | 2.65 | one-shot | Large diesel generator starter motor grinding with rising pitch, three rough coughing misfires, then catching into a steady rumble, in a big concrete hall, close. | car engine ignition | Cue band | 3D |
| 35 | `iwz_power_rectifier_strike` * | Mercury-arc rectifiers strike | 1.5 | one-shot | Violent crackling electric arc igniting inside a large glass cage, sharp snapping burst then a settling hundred-cycle buzzing crackle, ozone hiss, big hall reverb. | sci-fi laser | Cue band | 3D |
| 36 | `iwz_power_post_gauges` | Four hatch gauges tick up at power-on | 1.5 | one-shot | A run of about twelve small brass gauge needle ticks rising in rate over one and a half seconds, dry spring clicks, close microphone, no beeps. | digital counter | P-6 | 3D |
| 37 | `iwz_clock_wind_ratchet` * | Winding key ratchet, 2 to 8 ticks a second | 3.0 | one-shot | Clockwork winding key turned by hand, ratchet pawl clicks starting slow at two a second and quickening to eight a second, brass spring tension, close, small hall. | ticking time bomb | P-3 | 3D |
| 38 | `iwz_clock_hands_sweep` * | Hands sweep thirteen minutes | 1.0 | one-shot | Fast whirr of a large station clock movement spinning its hands forward, rapid gear train buzz with a tiny ratchet flutter and an abrupt stop, close. | film projector | P-3 | 3D |
| 39 | `iwz_clock_bell_fare` * | Fare Hall clock strike, B5 thin glass bell | 2.5 | one-shot | One strike of a thin electric glass bell, bright high B5 pitch, short decay about two seconds, slight beating shimmer, big tiled hall, mid distance. | church bell | Cue band | 3D |
| 40 | `iwz_clock_bell_platform` * | Platform clock strike, G4 cast bronze | 4.0 | one-shot | One strike of a cast bronze platform bell, warm G4 pitch, strong hum and a three second decay, large open underground platform space, mid distance. | cathedral bell | Cue band | 3D |
| 41 | `iwz_clock_bell_barn` * | Car Barn clock strike, E4 struck steel | 2.5 | one-shot | One hard strike of a steel workshop bell, E4 pitch, hard attack, short ringing decay, big steel shed with a flutter echo, mid distance. | school bell | Cue band | 3D |
| 42 | `iwz_clock_bell_parlour` * | Parlour long-case gong, C3 | 5.0 | one-shot | One slow strike of a long-case clock gong, deep C3 pitch with a long inharmonic ring, marble salon with high ceiling, a faint low organ-like partial beneath. | temple gong | Cue band | 3D |
| 43 | `iwz_board_flap_digit` * | One digit of the 047 due line flaps over | 0.6 | one-shot | A single split-flap board digit flipping, a short fast riffle of plastic flaps ending in a firm clack, close, tiled hall. | slot machine reel | P-6 | 3D |
| 44 | `iwz_board_flap_round` * | Round number flap cascade | 1.4 | one-shot | A short cascade of split-flap display panels flipping over, a rolling riffle of many clacking plastic flaps decaying over one and a half seconds, big tiled hall, mid distance. | rain on a roof | P-3 | 3D |
| 45 | `iwz_board_flap_long` | Board re-checks, long flap cascade | 4.0 | one-shot | A long cascade of split-flap display panels flipping in waves across a wide board, dense rolling riffle swelling and thinning, a last few stragglers clacking, big tiled hall, mid distance. | typewriter pool | P-3 | 3D |
| 46 | `iwz_board_headsign_burst` | Train headsign flap burst | 1.2 | one-shot | A fast burst of flaps from a small train destination blind rolling over, quick riffle of cloth and plastic ending in two clacks, inside a metal carriage. | slot machine reel | P-4 | 3D |
| 47 | `iwz_lever_clack_right` * | Right lever locks over, lamp goes green | 1.0 | one-shot | Heavy cast iron signal lever pulled over with a deep clack, then a relay chunk and a small bakelite lamp click, wooden cabin, close. | sword clang | Cue band | 3D |
| 48 | `iwz_lever_relay_tone` | Relay tone for the chord (shifted to C5, E5, G5) | 0.6 | one-shot | A single clean tone of an electric relay buzzer, steady mid pitch around G5, short with a soft attack and a quick cut, dry, no vibrato, close. Three pitched copies are made by shifting. | video game power-up | P-6 | 3D |
| 49 | `iwz_lever_springback` | Pulled levers spring back | 0.8 | one-shot | Several spring loaded signal levers snapping back to rest one after another, a quick rattle of metal and springs ending in clanks, wooden cabin, close. | trap door | P-3 | 3D |
| 50 | `iwz_lever_buzzer_wrong` * | Harsh reed buzzer, wrong lever | 1.2 | one-shot | A harsh nasal electromechanical reed buzzer sounding steadily for one second, rough and unpleasant, dry cabin, close, abrupt stop. | game show buzzer | Cue band | 3D |
| 51 | `iwz_lever_vent_clang` | Vent grate clangs open | 0.8 | one-shot | A rusted sheet metal vent grate banging open and swinging on its hinge, one big clang and a rattling ring, small room, close. | prison door | Cue band | 3D |
| 52 | `iwz_signal_semaphore` | East signal motor and semaphore thunk | 2.5 | one-shot | Small electric motor whirring for two seconds and a semaphore signal arm dropping with a heavy wooden and metal thunk at the end, outdoor tunnel mouth, mid distance. | traffic light beep | P+0 | 3D |
| 53 | `iwz_conductor_door_hiss` | Party Car door hiss | 1.2 | one-shot | Pneumatic train carriage door unlocking with a hiss of air and a metallic thunk as the leaves release, inside a tunnel mouth, mid distance. | spaceship door | P-3 | 3D |
| 54 | `iwz_conductor_doors_shut` | Car doors pulled shut behind the Conductor (v2) | 1.6 | one-shot | A train carriage door pulled shut by hand on rubber seals, a short pneumatic hiss, the leaves sliding together and a firm lock thunk, one car, inside a tunnel, mid distance. | elevator ding | P-3 | 3D |
| 55 | `iwz_conductor_whistle` | Guard's pea-whistle trill, 1.4 s | 1.4 | one-shot | A cheerful high guard's pea whistle with a trill, a single long loud blast with the pea rattling, bright and piercing, outdoors in a tunnel, mid distance. | referee foul whistle | Cue band | 3D |
| 56 | `iwz_conductor_lamp_chain` | Hand lamp chain clinks on a step (v3) | 0.4 | one-shot | A brass hand lamp swinging on a short chain, two or three small metallic clinks with a faint wire squeak, one walking step, close, dry. | jingle bells | P-9 | 3D |
| 57 | `iwz_conductor_death` | Lamp glass tinkles, Handle clunks, one detuned bell | 2.0 | one-shot | A glass hand lamp shattering and tinkling on tile, a brass key controller dropping with a heavy clunk, then one slightly flat small bell ringing out, tiled platform. | video game drop | P-3 | 3D |
| 58 | `iwz_handle_hum_loop` | Dropped Handle's faint hum, found by ear | 4.0 | loop | A very faint steady electrical hum with a thin high tone at C5 pitch, soft and slightly wavering, like a tiny energised brass object, nearly inaudible, seamless. | magic item glow | F+3 | 3D |
| 59 | `iwz_handle_pickup` | Handle picked up, key jingle | 1.0 | one-shot | A brass key and a small ring of keys picked up from stone floor, short metallic jingle and a heavy key knock, close, dry. | video game item pickup | P-3 | 1P |
| 60 | `iwz_cab_key_slide` | Handle slides into the cab slot | 0.4 | one-shot | A brass key sliding into a brass lock, short smooth metal on metal scrape and a small click at the end, very close, dry. | sci-fi keycard | P-4 | 3D |
| 61 | `iwz_cab_key_ratchet` | Handle turned, ratchet | 1.2 | one-shot | A heavy brass controller handle turned through a ratchet, slow coarse clicks of a geared mechanism, close, small metal cab. | safe cracking | P-4 | 3D |
| 62 | `iwz_cab_relay_slams` * | Four relay slams ripple along the car | 1.2 | one-shot | Four heavy electrical relays slamming in a row along a train, each a loud bakelite thunk with a metal ring, rippling away from close to far over a second. | machine gun | Cue band | 3D |
| 63 | `iwz_cab_fluor_stutter` | Fluorescent tubes stutter on | 1.0 | one-shot | Fluorescent tube lights flickering on, two to four sharp buzzing strikes with ballast ticks, ending in a steady buzz, inside a metal carriage. | horror light flicker | P-3 | 3D |
| 64 | `iwz_train_door_chime` * | Door chime D5 then G sharp 4 | 1.2 | one-shot | Two note electric train door chime, a clean D5 then a lower G sharp 4, soft bell tone with a short decay, inside a tiled station platform, mid distance, no vibrato. | doorbell ding dong | P-3 | 3D |
| 65 | `iwz_train_doors_close` * | Car doors close: hiss, slide, lock | 2.2 | one-shot | Train carriage doors closing, a short pneumatic hiss, rubber edged leaves sliding together over a second, then a firm lock thunk, close to the doors. | elevator ding | Cue band | 3D |
| 66 | `iwz_train_doors_open` | Car doors open at the Terminus return | 1.5 | one-shot | Train carriage doors opening, a soft pneumatic psh, rubber leaves sliding apart, ending with a gentle thunk, clean and quiet, close to the doors. | spaceship door | P-3 | 3D |
| 67 | `iwz_tele_cross_buzz` | Crossing: rising fluorescent buzz and tunnel wind | 3.0 | one-shot | Fluorescent tube buzz rising in pitch and level over three seconds with soft tunnel wind swelling underneath, enclosed carriage interior, ends abruptly. A low note is added later. | warp drive | Cue band | 2D |
| 68 | `iwz_tele_arrive_psh` | Soft pneumatic psh on arrival | 0.6 | one-shot | A single soft pneumatic puff, like a clean carriage door releasing, gentle and brief, quiet room, no echo. | steam hiss | P-6 | 2D |
| 69 | `iwz_tele_arrive_chime` * | One clean C6 chime, long decay | 3.0 | one-shot | A single pure high C6 chime from a small brass bell, soft strike, clean long decay over three seconds, quiet bright room, no vibrato. | wind chimes | P-3 | 2D |
| 70 | `iwz_tele_cooldown_thud` | Headsign lamp-out thud (not in service) | 0.6 | one-shot | A flat dull thud of a lamp box switching off with a short relay clunk and a faint tick of cooling metal, close, small cab. | power down whine | P-6 | 3D |

Count, group 2: **38**.

### 8.3 The four wonder weapons and their upgraded forms

Source: 4.7 and `05-WONDER-WEAPONS.md`. Weapon rows are weapon-owned local or world sounds. Per rule 3.10 each weapon's fire sound is first compared with the donor weapon's measured fire sound (F15); "D" levels are relative to that. Upgraded forms are marked "up". Rows for the three fuses and the three cans are named by colour.

| # | Alias | What | Length (s) | Loop or one-shot | Generation brief | Must NOT sound like | Target level | 3D or 2D |
|---|---|---|---|---|---|---|---|---|
| 71 | `iwz_ec_fire` | EXACT CHANGE shot: coin into chute and spring crack (v4) | 0.5 | one-shot | A single coin dropping into a steel chute with a bright clink then a sharp dry spring crack, like a spring-loaded carbine, tight, close, no tail. The coin pitch is raised by shifting for the surge price. | slot machine | D-2 | 3D |
| 72 | `iwz_ec_lever` | Turnstile ratchet on each cycle (v2) | 0.3 | one-shot | A short turnstile arm ratchet, two fast mechanical clicks of a heavy pawl on a toothed wheel, close, dry, metal. | ratchet wrench | D-8 | 3D |
| 73 | `iwz_ec_empty` | Coin rejected on empty | 0.7 | one-shot | A coin rejected by a coin mechanism, a small tink of metal, a dull thunk and the coin rolling back down into a return tray, close, dry. | error beep | D-8 | 3D |
| 74 | `iwz_ec_refund` | Till bell on a refund | 0.5 | one-shot | A brass cash register till bell struck once, a bright short ring with a metal ting decaying in half a second, close, dry. | cash register jackpot | D-6 | 3D |
| 75 | `iwz_ec_token_pickup` | Token picked up, bright C6 ting | 0.6 | one-shot | A small brass token tapped against metal, a single bright high C6 ting with a short ring, very close, clean, no reverb. | video game coin | P-3 | 3D |
| 76 | `iwz_ec_reload` | Lever racked twice, hopper cascade | 2.4 | one-shot | A heavy lever racked twice, two mechanical clacks, then a cascade of metal tokens pouring from a hopper into a steel box, settling rattle, close, dry. | shotgun pump | D-4 | 3D |
| 77 | `iwz_ec_penalty` | Penalty fare clonk while the Inspector is alive | 0.4 | one-shot | A deep dull clonk of a heavy brass coin hitting an iron plate, low and short, close, to be layered under the coin sound. | temple gong hit | D-6 | 3D |
| 78 | `iwz_ec_impact` | Spray of coins on impact (v2) | 0.8 | one-shot | A small handful of coins striking a concrete wall and bouncing away, quick bright scatter of clinks decaying in under a second, close, dry. | coin payout | D-8 | 3D |
| 79 | `iwz_ec_up_fire` | KEEP THE CHANGE shot, heavier (v4) | 0.6 | one-shot | A heavier coin dropping into a deep steel chute, a rounder clunk then a harder spring crack with a short brass ring, tight, close, dry. | slot machine | D-1 | 3D |
| 80 | `iwz_ec_up_skip` | Upgraded token skips to another zombie | 0.5 | one-shot | A thin ricochet ping of a small brass disc skipping off metal then a soft tick, fast, bright, short, dry, close. | cartoon boing | D-9 | 3D |
| 81 | `iwz_ec_up_drop` | Dropped tokens clatter and spin on edge (v3) | 1.0 | one-shot | Several brass tokens falling onto a concrete floor, clattering, then one spinning on its edge with a rising whirr and settling with a ring, close, dry. | coin jackpot | P-6 | 3D |
| 82 | `iwz_ec_up_reload` | Eighteen-token hopper refill | 3.0 | one-shot | A lever racked twice then a longer cascade of many tokens pouring into a glass fronted hopper, larger and fuller than a small refill, settling rattle, close, dry. | ammo pickup | D-4 | 3D |
| 83 | `iwz_lr_fire` | LIVE RAIL stake fired: contactor slam and cable whip (v3) | 0.6 | one-shot | A heavy electrical contactor slamming shut with a deep thunk and a quick cable whip crack, tight, close, dry, no tail. | sci-fi laser | D-2 | 3D |
| 84 | `iwz_lr_stake_land` | Stake lands, ceramic knock (v3) | 0.4 | one-shot | A copper spike with a ceramic collar striking a concrete wall, a sharp ceramic knock and a small ring, dry, close, short. | arrow thud | D-8 | 3D |
| 85 | `iwz_lr_stake_hit` | Stake pins a zombie | 0.4 | one-shot | A heavy spike striking a body and a wooden board, a thick wet thunk and a dull knock, close, dry, no ring. | sword stab | D-6 | 3D |
| 86 | `iwz_lr_fence_form_amber` | Amber fence forms: thunk, hum | 1.0 | one-shot | Substation breaker closing in two steps, a heavy thunk then a rising mains hum settling at fifty cycles with a bright third harmonic, big hall, mid distance. | forcefield activate | P+0 | 3D |
| 87 | `iwz_lr_fence_form_red` | Red fence forms: harsher | 1.0 | one-shot | A breaker closing with a harsh double snap and a sharp crackle, hum rising to a buzzy hundred cycles with dense crackle on top, big hall, mid distance. | forcefield activate | P+0 | 3D |
| 88 | `iwz_lr_fence_form_green` | Green fence forms: soft | 1.0 | one-shot | A breaker closing with a soft muffled thunk and a gentle low hum swelling slowly, calm and smooth, with a tiny bell ping at the end, big hall, mid distance. | forcefield activate | P-2 | 3D |
| 89 | `iwz_lr_loop_amber_full` | Amber fence hum, full charge | 4.0 | loop | Steady fifty cycle mains hum with a strong third harmonic and sparse electrical crackle, taut wire singing, close perspective, seamless loop, no melody. | sci-fi energy field | F+8 | 3D |
| 90 | `iwz_lr_loop_amber_half` | Amber fence hum, half charge | 4.0 | loop | Steady fifty cycle mains hum with a third harmonic and a rather denser fizzing crackle than usual, taut wire singing, close, seamless loop, no melody. | sci-fi energy field | F+8 | 3D |
| 91 | `iwz_lr_loop_amber_quarter` | Amber fence hum, quarter charge | 4.0 | loop | Fifty cycle mains hum with a third harmonic and very busy fast sputtering crackle, unstable and about to fail, close, seamless loop, no melody. | sci-fi energy field | F+8 | 3D |
| 92 | `iwz_lr_loop_red_full` | Red fence buzz, full charge | 4.0 | loop | Harsh hundred cycle electrical buzz with dense rapid crackle and snaps, aggressive and bright, close, seamless loop, no melody. | sci-fi energy field | F+10 | 3D |
| 93 | `iwz_lr_loop_red_half` | Red fence buzz, half charge | 4.0 | loop | Harsh hundred cycle electrical buzz with an even denser crackle and uneven snaps, aggressive, close, seamless loop, no melody. | sci-fi energy field | F+10 | 3D |
| 94 | `iwz_lr_loop_red_quarter` | Red fence buzz, quarter charge | 4.0 | loop | Hundred cycle electrical buzz breaking up into frantic sputtering and sparks, unstable, close, seamless loop, no melody. | sci-fi energy field | F+10 | 3D |
| 95 | `iwz_lr_loop_green` | Green fence, soft hum with slow swell | 6.0 | loop | Soft low fifty cycle hum swelling and fading slowly at half a cycle per second, calm, smooth, very little crackle, close, seamless loop, three swells. | healing aura | F+6 | 3D |
| 96 | `iwz_lr_green_ping` | Green fence marks a zombie, small bell ping | 0.5 | one-shot | One small clear bell ping of a tiny brass bell, bright, short decay, close, dry. | video game checkpoint | P-6 | 3D |
| 97 | `iwz_lr_burnout` | Fence burns out, fuse pop | 0.4 | one-shot | A sharp electrical fuse blowing, a loud pop with a tiny sizzle and a ceramic crack, close, dry. | bomb explosion | P+0 | 3D |
| 98 | `iwz_lr_cross_zzt` | Zombie crosses the arc (v3) | 0.25 | one-shot | A very short electrical zap, a sharp zzt crackle with a small snap, bright and dry, close. | laser blast | P-6 | 3D |
| 99 | `iwz_lr_red_chain` | Red fuse arcs on to more zombies | 0.5 | one-shot | A quick forked electrical arc jumping between targets, a rapid crackling zip with two snaps, bright, close, dry. | lightning thunder | P-4 | 3D |
| 100 | `iwz_lr_fuse_swap` | Fuse out and fuse in at a box | 2.0 | one-shot | A ceramic fuse pulled out of a metal holder with a tink, a short pause, and a new fuse pushed in with a solid thok and a small click of the cover, close, dry. | battery change | P-6 | 3D |
| 101 | `iwz_lr_pair_fail` | Failed pair: stakes spit sparks | 1.0 | one-shot | Two spikes sputtering and spitting sparks for one second, uneven frying crackle fading away with a final small pop, close, dry. | fireworks display crackle | P-3 | 3D |
| 102 | `iwz_lr_player_shock` | Player touches the arc | 0.4 | one-shot | A sharp electrical shock crackle with a deep buzz, short and unpleasant, close, dry, no voice. | stun gun zap | P-3 | 1P |
| 103 | `iwz_lr_reload` | Break-open two-stake reload | 2.0 | one-shot | A hot-stick launcher broken open with a hinge snap, two metal spikes slid in with clicks, then closed with a firm snap, close, dry. | rifle reload | D-4 | 3D |
| 104 | `iwz_lr_build` | Parts assembled at the workbench | 2.5 | one-shot | Three metal parts fitted together on a workbench, a clack of a bronze shoe on an insulator, a screw tightening, a snap of a cable clip and a final solid knock, close, dry. | sci-fi crafting | P-3 | 3D |
| 105 | `iwz_lr_up_fire` | THE FOURTH RAIL shot, heavier (v3) | 0.6 | one-shot | A heavier electrical contactor slamming with a deep thunk, a thicker cable whip with a faint rising whine, tight, close, dry. | sci-fi laser | D-1 | 3D |
| 106 | `iwz_lr_up_link` | Third stake links the triangle | 1.0 | one-shot | Three taut wires snapping into tension one after another with a rising hum swelling into a triple arc crackle, close, mains tone at fifty cycles. | forcefield activate | P+0 | 3D |
| 107 | `iwz_dp_stamp` | STAMP: post-office thump with a wet edge (v4) | 0.4 | one-shot | A heavy rubber address stamp thumped down on a sheaf of paper with a flat post-office thump and a wet slap of ink at its edge, close, dry, short. | pistol shot | D-2 | 3D |
| 108 | `iwz_dp_tag` | Stamped label flutters onto the zombie (v2) | 0.5 | one-shot | A small paper luggage label fluttering down and settling onto cloth with a faint dry rustle and a tiny wet tack, close, quiet. | sticker peel | D-9 | 3D |
| 109 | `iwz_dp_stamp_empty` | Empty pad: a dry stamp | 0.4 | one-shot | A dry rubber stamp pressed on bare paper, a dull thump with no wet ink sound and a small brass collar rattle, close, dry. | error buzzer | D-8 | 3D |
| 110 | `iwz_dp_send_cough` | SEND: bellows cough | 0.5 | one-shot | A single bellows cough, a short punchy puff of air through a leather bag and a brass horn with a low thump, close, dry. | shotgun blast | D-3 | 3D |
| 111 | `iwz_dp_parcel_whistle` | A parcel's flight whistle, rising (stepped by shifting) | 1.0 | one-shot | A thin rising whistle of a small object flying through a long tube, pitch climbing over one second, airy, ending on a soft thud of arrival on cloth and wood, close then far, dry. | cartoon slide whistle | D-4 | 3D |
| 112 | `iwz_dp_launch` | Sent into a hatch: small cork-pop and vapour hiss | 0.8 | one-shot | A small cork pop out of a brass horn followed by a short trailing vapour hiss, tight, close, dry, tiny scale of a pipe launch. | rocket launch | D-2 | 3D |
| 113 | `iwz_dp_puff` | Send with no stamps out: bellows puff | 0.4 | one-shot | A short soft puff of air from a leather bellows through a brass horn, no thump, close, dry. | air freshener spray | D-6 | 3D |
| 114 | `iwz_dp_refill` | Bellows refills for 3 s after a send, ready click | 3.0 | one-shot | A large leather bellows slowly drawing in air for three seconds with a soft leather creak, a few small brass collar ticks, ending on a single soft latch click, close, dry. | vacuum cleaner | D-8 | 3D |
| 115 | `iwz_dp_reload` | Pad change: ink pad swapped, two bellows pumps | 2.2 | one-shot | A flat inked stamp pad slid out of a brass holder with a metal scrape, a fresh pad pressed in with a soft thump and a latch click, two slow leather bellows pumps, close, dry. | shotgun reload | D-4 | 3D |
| 116 | `iwz_dp_burst` | Burst: organ pedal cut by a wet slap, paper rain | 2.5 | one-shot | A deep organ pedal note cut off after half a second by a wet slap like a paper bag popped under water, then a light rain of paper scraps fluttering down for one and a half seconds, big hall. | grenade explosion | D+0 | 3D |
| 117 | `iwz_dp_up_burst` | FORWARDING ADDRESS burst, fuller | 3.0 | one-shot | A deep organ pedal chord of three notes cut off after a second by a heavier wet slap, followed by a longer rain of paper scraps, big stone hall. | nuclear blast | D+0 | 3D |
| 118 | `iwz_dp_return_whistle` | Forwarding Address: the surviving parcel's lower whistle on its way back | 1.2 | one-shot | A thin falling whistle of a small object travelling back along a tube, pitch sinking over one second and ending on a soft rubber heel squeak, close, dry. | cartoon slide whistle | P-4 | 3D |
| 119 | `iwz_dp_charge_chime` | Charging at the organ console: rising glass chime | 4.0 | one-shot | A glass harmonica style chime rising slowly in pitch over four seconds as a canister fills, delicate and smooth, large stone vault, close. | magic spell | P-3 | 3D |
| 120 | `iwz_dp_cylinder_rattle` | Message cylinder rattles out of a hatch | 1.0 | one-shot | An old brass message cylinder rattling out of a pipe hatch and rolling onto stone, clattering knocks then a slowing roll and a ring, close, dry. | bowling ball | P-3 | 3D |
| 121 | `iwz_dp_desk_drawer` | Dispatch desk drawer opens: the pistol | 1.2 | one-shot | A heavy walnut desk drawer unlocked with a key click then slid open with a wooden scrape, brass handle rattle and a soft leather and metal shift, dry salon. | treasure chest | P-3 | 3D |
| 122 | `iwz_tb_spray_start` | TOP TO BOTTOM spray begins | 0.3 | one-shot | A pressurised spray can nozzle pressed, a sharp quick hiss starting with a small pop, close, dry. | fire extinguisher | D-4 | 3D |
| 123 | `iwz_tb_spray_loop` | Spray hiss, held trigger | 3.0 | loop | A steady close dry spray can hiss with fine aerosol texture, no ring or pitch, constant level, seamless loop. | steam pipe | D-4 | 3D |
| 124 | `iwz_tb_spray_end` | TOP TO BOTTOM spray ends | 0.4 | one-shot | A spray can hiss cutting off with a tiny sputter and a drip tick, close, dry. | air release | D-6 | 3D |
| 125 | `iwz_tb_switch_magenta` | Can switch to MAGENTA, ball rattle | 0.5 | one-shot | The ball inside a spray can rattling three times, a lighter rattle than usual, plus a click of a collar snapping into place, close, dry. | ammo clip click | D-6 | 3D |
| 126 | `iwz_tb_switch_cyan` | Can switch to CYAN, ball rattle | 0.5 | one-shot | The ball inside a spray can rattling three times with a medium pitch, plus a click of a collar snapping into place, close, dry. | ammo clip click | D-6 | 3D |
| 127 | `iwz_tb_switch_yellow` | Can switch to YELLOW, ball rattle | 0.5 | one-shot | The ball inside a spray can rattling three times with a lower pitch, plus a click of a collar snapping into place, close, dry. | ammo clip click | D-6 | 3D |
| 128 | `iwz_tb_tag_slap` | Zombie tagged: wet slap (v3) | 0.4 | one-shot | A wet slap of thick paint hitting cloth and skin, a short splat with a small drip, close, dry. | water balloon | D-6 | 3D |
| 129 | `iwz_tb_allstand_whistle` | ALL STAND: platform whistle as the zombie turns | 0.5 | one-shot | A single short blast of a guard's metal platform whistle, a bright clean peep with the pea faintly rolling, station platform, mid distance. | referee foul whistle | P-3 | 3D |
| 130 | `iwz_tb_allstand_shuffle` | ALL STAND: feet shuffle to the waiting place and settle | 4.0 | loop | A few dozen feet shuffling slowly across a tiled platform, scuffing soles and cloth, no voices, steady and tired, a faint settle of bodies at the end of each pass, seamless loop. | marching army | F+6 | 3D |
| 131 | `iwz_tb_hazard_tick` | HAZARD: relay tick on the zombie | 2.0 | loop | Four dry electromagnetic relay ticks evenly spaced half a second apart, small and close, seamless loop of two seconds. | bomb timer beep | F+6 | 3D |
| 132 | `iwz_tb_hazard_burst` | HAZARD burst: pop, splat, flat ring | 1.0 | one-shot | A pop of paint bursting out of a body, a wet splat and a quick flat ring of paint thrown outward ending in a soft fwip, close, dry. | grenade explosion | D-2 | 3D |
| 133 | `iwz_tb_cyan_squeak` | WET PAINT (CYAN): slick squeaks under feet (v3) | 0.4 | one-shot | A rubber boot sole squeaking and slipping on a wet glossy painted floor, one short squeal and a skid, close, dry. | cartoon slide whistle | D-8 | 3D |
| 134 | `iwz_tb_cyan_fall` | Fall on the slick: splat, slide | 1.2 | one-shot | A heavy body slipping on a wet painted floor, a wet splat then a long sliding squeak and a thump into a wall, close, dry. | banana peel slip | D-4 | 3D |
| 135 | `iwz_tb_splash` | END TO END splash: hiss and flick | 0.8 | one-shot | A quick hiss of paint thrown from a spray lance and a flick of droplets landing around, close, dry. | water splash | D-4 | 3D |
| 136 | `iwz_tb_reload` | Pressure pot pump reload | 2.4 | one-shot | A hand pump on a pressure pot worked three times, a hiss of pressure and a final valve click, close, dry, metal and rubber. | rifle reload | D-4 | 3D |
| 137 | `iwz_tb_up_spray_loop` | END TO END spray, wider and fuller | 3.0 | loop | A fuller wider spray can hiss with a deeper body and more fine droplets, steady, close, dry, seamless loop, no pitch. | steam pipe | D-3 | 3D |
| 138 | `iwz_tb_stash_lid` | CYAN can stash lid opens | 1.0 | one-shot | A rusty metal tool chest lid lifted and propped open with a creak and a clunk, cans rolling slightly inside, close, dry, tunnel space. | treasure chest | P-3 | 3D |
| 139 | `iwz_tb_can_drop` | YELLOW can dropped by a Cleaner | 0.8 | one-shot | A metal spray can dropped onto concrete, a ringing clank then rolling away with a rattle of the ball inside, close, dry. | bottle drop | P-6 | 3D |

Count, group 3: **69**.

### 8.4 The four new perk machines

Source: `06-PERKS.md` and 3.8. Per machine: an idle loop, a purchase sound, the in-play effect sound(s) and a 1 to 2 s sting. The sting is an instrumental sound-design sting from the machine's jingle idea, played in the one jingle family of 3.8 (it overrides the instrument ideas of 06); the 8 to 10 s jingle itself is music (3.8) and is not here. The six stock perks and the Up 'N Atoms machine keep stock sounds. Hero lines on buying a perk are voice (5.2).

| # | Alias | What | Length (s) | Loop or one-shot | Generation brief | Must NOT sound like | Target level | 3D or 2D |
|---|---|---|---|---|---|---|---|---|
| 140 | `iwz_perk_bd_idle` | Baker's Dozens machine idle | 6.0 | loop | A doughnut-shop counter dispenser with a small motor humming softly, a glass drum of sugared drops rolling slowly and a mechanical flip-digit counter ticking over every few seconds, close, seamless loop. | carnival music | F+6 | 3D |
| 141 | `iwz_perk_bd_buy` | Baker's Dozens purchase: bag chute and counter ring | 1.5 | one-shot | A sugared drop sliding down a metal chute into a paper bag, the bag crinkled shut, and a small mechanical counter ringing once, close, dry. | vending machine beep | P+0 | 3D |
| 142 | `iwz_perk_bd_thirteen` | Baker's Dozens: the thirteenth hit, counter bell | 0.4 | one-shot | A small brass baker's bell struck once with a tiny mechanical counter click, a bright short ting, close, dry, for frequent repeat. | power-up chime | P-9 | 1P |
| 143 | `iwz_perk_bd_sting` | Baker's Dozens sting | 1.5 | one-shot | Four glockenspiel notes climbing a step each as if counting up, ending on one small baker's bell ring, bright and playful, no voices, dry. | heroic fanfare | P+0 | 2D |
| 144 | `iwz_perk_sg_idle` | Sour Grudges machine idle | 6.0 | loop | Hard sour drops tumbling slowly inside a glass gumball globe with a faint grumbling grind of a crooked crank mechanism, a rattle every second or two, close, seamless loop. | carnival music | F+6 | 3D |
| 145 | `iwz_perk_sg_buy` | Sour Grudges purchase: gumball down the chute | 1.5 | one-shot | A single gumball dropping through a metal chute with a rattle, landing in a flap tray with a clunk, then a quick sour lip-smack pucker, close, dry. | vending machine beep | P+0 | 3D |
| 146 | `iwz_perk_sg_mark` | Sour Grudges: a zombie is marked | 0.6 | one-shot | A short hiss of green fume with a dry sour tsk and a tiny rubbery squeak, close, quiet, only for the player. | poison gas cloud | P-9 | 1P |
| 147 | `iwz_perk_sg_payoff` | Sour Grudges: marked zombie killed, grudge settled | 0.8 | one-shot | A quick sharp zing of a sour sweet bursting with a wet pucker snap and a short falling tone, brief, bright, close, dry. | healing sparkle | P-4 | 1P |
| 148 | `iwz_perk_sg_forgive` | Sour Grudges: the next hit is forgiven | 0.5 | one-shot | A heavy blow absorbed by a thick cushion, a soft padded thump with a puff of air and a tiny rubbery squeak, close, dry, no voice. | shield block | P-6 | 1P |
| 149 | `iwz_perk_sg_sting` | Sour Grudges sting | 1.5 | one-shot | A cheap electric piano on a wheezing organ patch taunting two falling notes in a sweet major tune with a squeezed wrong note, ending on a wet blown raspberry, close, dry. | evil laugh | P+0 | 2D |
| 150 | `iwz_perk_bv_idle` | Bon Voyages machine idle | 6.0 | loop | A walnut and brass ticket cabinet with a brass destination dial ticking round slowly, round tins shifting softly behind a brass grille and a faint wooden creak, close, seamless loop. | fairground music | F+6 | 3D |
| 151 | `iwz_perk_bv_buy` | Bon Voyages purchase: dial spins, tin lid snaps | 2.0 | one-shot | A brass destination dial spinning on a spindle with a ratchet whirr and landing on a click, a round tin dropping into a tray and its lid pressed on with a tin snap, close, dry. | vending machine beep | P+0 | 3D |
| 152 | `iwz_perk_bv_dash` | Bon Voyages: arrival burst of speed | 0.5 | one-shot | A quick soft rush of air and a light scuff of running boots on tile as someone sets off, short, close, quiet, for frequent repeat. | sprint power-up | P-9 | 1P |
| 153 | `iwz_perk_bv_sting` | Bon Voyages sting | 1.5 | one-shot | Three bright rising electric piano notes in a guard's all-aboard call that leave the key and land back in it, ending with a tin lid snapping shut, dry, no voice. | circus clown | P+0 | 2D |
| 154 | `iwz_perk_dt_idle` | Double Takes machine idle | 6.0 | loop | A photo-booth shaped dispenser with a flash capacitor whining softly, a curtain rustling and an occasional small relay tick, close, seamless loop. | sci-fi machine hum | F+6 | 3D |
| 155 | `iwz_perk_dt_buy` | Double Takes purchase: flash bulb pop, strip falls | 2.0 | one-shot | A flash bulb popping with a bright pof, a camera whirr, and a strip of paper photographs sliding and falling into a metal tray, close, dry. | modern camera shutter | P+0 | 3D |
| 156 | `iwz_perk_dt_trigger` | Double Takes triggers: flash and still image | 0.6 | one-shot | A bright flash bulb pof with a quick shutter click and a faint capacitor squeal falling away, close, dry, a single event. | screen capture sound | P-3 | 3D |
| 157 | `iwz_perk_dt_ready` | Double Takes ready again after cooldown | 0.4 | one-shot | A tiny film advance click and a soft capacitor chirp as a camera reloads, quiet, close, dry, one short event. | level up chime | P-12 | 1P |
| 158 | `iwz_perk_dt_sting` | Double Takes sting | 1.5 | one-shot | A camera flash pof on the beat, a short bright electric piano phrase played twice with the second a half step higher, plucked bass note, dry. | advertising jingle voice | P+0 | 2D |

Count, group 4: **19**.

### 8.5 The Night Inspector

Source: 4.8, 3.4 and `07-ENEMIES.md` section 3 (short, wide, lamp-headed; he climbs out of inspection plates, never through a door). His voice lines (P1 to P8) are voice and are not here. The far whistle at -26 dB is made by filtering the arrival whistle. The marked player's blip is in group 11.

| # | Alias | What | Length (s) | Loop or one-shot | Generation brief | Must NOT sound like | Target level | 3D or 2D |
|---|---|---|---|---|---|---|---|---|
| 159 | `iwz_ni_plate_rattle` | Inspection plate rattles in the floor, lifts, he hauls out | 2.6 | one-shot | A heavy brass floor plate rattling on its frame for two seconds, a hinge clank as it lifts, then cloth and boots scraping on tile as a heavy body hauls itself out of the opening, mid distance. | monster emerging | P-3 | 3D |
| 160 | `iwz_ni_plate_down` | He climbs down and the plate settles | 2.0 | one-shot | A heavy body lowering itself into a floor opening with a scrape of leather and then a brass plate settling back on its frame with a hollow clank, tiled hall, mid distance. | haunted house door | P-3 | 3D |
| 161 | `iwz_ni_whistle_arrive` | Long low arrival whistle | 1.2 | one-shot | A single long low blast of a large brass guard whistle, deep and slow, with the pea faintly rolling, lower and heavier than a normal whistle, tunnel space. | referee whistle | Cue band | 3D |
| 162 | `iwz_ni_step` | Short quick step of a heavy waddle (v4) | 0.5 | one-shot | One short quick boot step on tile with a stiff cloth tunic creak and a wet leather squeak, a rolling weight, close, dry. | monster footstep | P-6 | 3D |
| 163 | `iwz_ni_scuttle` | Scuttle: fast steps and a satchel slap, 2 s | 2.0 | one-shot | Six very quick heavy steps on tile with a leather satchel slapping on each step and a dry paper rasp dragging behind, close, dry. | running horse | P-4 | 3D |
| 164 | `iwz_ni_ribbon_loop` | Paper ribbon of punched tickets dragging | 4.0 | loop | A long strip of stiff paper tickets dragging along a tiled floor, a dry continuous rasp with tiny confetti ticks, close, seamless loop. | snake hiss | F+4 | 3D |
| 165 | `iwz_ni_lamp_squeak` | Lamp wire handle squeaks on each step (v3) | 0.3 | one-shot | A thin dry squeak of a wire lamp handle in an iron ring, short, rising slightly, one swing, close, quiet. | rubber duck | P-9 | 3D |
| 166 | `iwz_ni_pulse_tock` | Inspector pulse tock (v3) | 0.35 | one-shot | A single wood block and relay click, a round dry tock with a small contact snap, no reverb, evenly weighted, close. A soft low tone is added later. | music metronome click | P-6 | 2D |
| 167 | `iwz_ni_punch_tell` | The Punch tell: hydraulic whine rising | 0.9 | one-shot | A hydraulic arm winding up, a whine rising smoothly from low to high pitch over nine tenths of a second with fluid hiss, close, dry. | robot servo | Cue band | 3D |
| 168 | `iwz_ni_punch_hit` | The Punch lands: clean metal chunk (v2) | 0.5 | one-shot | A single heavy clean metallic chunk of a large ticket punch closing on steel, tight, short ring, dry, close. | sword clang | Cue band | 3D |
| 169 | `iwz_ni_fine_stamp` | Fine taken: ticket torn off and rubber stamp | 0.7 | one-shot | A paper ticket torn from a pad with a sharp rip and a heavy rubber stamp thumped on it, close, dry. | cash register | P-3 | 3D |
| 170 | `iwz_ni_sweep_tell` | The Sweep tell: satchel arm creak | 0.6 | one-shot | A stiff leather satchel strap and a heavy arm drawn back with a long leather creak and a small paper rustle, close, dry. | door creak | P-6 | 3D |
| 171 | `iwz_ni_sweep_hit` | The Sweep: whoosh and thwack | 0.7 | one-shot | A heavy leather satchel swung through the air with a fast whoosh and a hard flat thwack against a body, close, dry. | karate chop | Cue band | 3D |
| 172 | `iwz_ni_notice_stomp` | Penalty Notice: feet planted | 0.5 | one-shot | A heavy boot stamping on a stone floor with a deep thud and a cloth coat flap, tight, close, dry. | earthquake rumble boom | Cue band | 3D |
| 173 | `iwz_ni_notice_whine` | Penalty Notice: rising whine, longest tell | 1.2 | one-shot | A hydraulic ram pressurising, a whine rising slowly from low to high over one and a quarter seconds with a pump pulse, close, dry. | robot servo | Cue band | 3D |
| 174 | `iwz_ni_notice_ring` | Penalty Notice: ring thud and 50 Hz swell | 1.5 | one-shot | A massive hydraulic punch hitting a stone floor with a deep thud then a low fifty cycle swell spreading and fading over one second, large hall. | shockwave blast | Cue band | 3D |
| 175 | `iwz_ni_whistle_blasts` | The Whistle: three blasts | 1.4 | one-shot | Three short blasts of a large brass guard whistle at 0.0, 0.5 and 1.0 seconds, each a third of a second, loud and sharp, tunnel space. | police siren | Cue band | 3D |
| 176 | `iwz_ni_lamp_open` | Lamp glass opens: hinge squeal and amber chime | 1.0 | one-shot | A tiny glass hinge squealing for a fifth of a second and a clean bright amber chime at C6 swelling softly for seven tenths of a second, close, dry. | video game alert | Cue band | 3D |
| 177 | `iwz_ni_lamp_shut` | Lamp glass shuts again | 0.3 | one-shot | A small glass cover snapping shut on a brass lamp frame, a short clicking glass tap, close, dry. | door slam | P-9 | 3D |
| 178 | `iwz_ni_hit_glass` | Shot on the lamp glass (v3) | 0.3 | one-shot | A bullet impact on thick lamp glass, a bright short ting and a tiny crack, no shatter, close, dry. | glass break | P-6 | 3D |
| 179 | `iwz_ni_hit_body` | Shot into the stuffed tunic (v3) | 0.3 | one-shot | A dull thud of an impact into a thick dusty wool tunic with a puff of dust, close, dry, no metal. | punch hit | P-6 | 3D |
| 180 | `iwz_ni_slip` | He slips on wet paint | 1.0 | one-shot | A heavy boot sliding on a wet floor with a squeal, then a metal arm clanging down to catch the body and a grunt-free heavy breath of cloth, close, dry. | banana peel slip | P-3 | 3D |
| 181 | `iwz_ni_stagger` | Stamped on the lamp: he reels, lamp held open | 1.5 | one-shot | A stout heavy body reeling back on short legs with a stumbling boot scuff, a brass lamp cage swinging with a squeal of its hinge and a punch arm clanking on the floor, close, dry. | monster roar | P-3 | 3D |
| 182 | `iwz_ni_death_burst` | Lamp bursts: glass pop, tinkle, dying flare | 1.2 | one-shot | A glass signal lamp bursting with a sharp pop, a tinkle of glass falling on stone and a dying flare hiss fading away, close, dry. | action film explosion | Cue band | 3D |
| 183 | `iwz_ni_death_collapse` | Tunic collapses: heavy thud, brass buttons clatter | 1.2 | one-shot | A heavy stuffed body collapsing in a heap with a dull thud, a clatter of loose brass buttons on stone and a stiff cloth whump settling, close, dry. | monster death | Cue band | 3D |
| 184 | `iwz_ni_death_cap` | Cap falls: flop and roll | 1.2 | one-shot | A peaked cap falling from a height to a stone floor with a soft flop, rolling in a short arc on its rim and settling, close, dry. | comic bonk | P-6 | 3D |
| 185 | `iwz_ni_reward_fines` | A fined player's pile of fines pours out | 3.0 | one-shot | A satchel emptying a large pile of metal coins onto a stone floor, a long cascade of clinks and rolling coins settling over three seconds, mid distance. | slot machine jackpot | P+0 | 3D |
| 186 | `iwz_ni_pile_pickup` | The fined player collects their pile: bright ting | 0.6 | one-shot | Many small brass tokens swept up into a hand with a bright ting and a short soft clatter, close, dry. | video game coin | P-3 | 1P |
| 187 | `iwz_ni_reward_punch` | Ticket punch ka-chunk for each player | 0.4 | one-shot | A conductor's hand ticket punch closing on cardboard, a crisp ka and a metal chunk, close, dry. | camera shutter | P-3 | 1P |
| 188 | `iwz_ni_ledger_drop` | Ledger slaps on the floor | 0.6 | one-shot | A thick leather bound ledger dropped flat on a stone floor, a heavy slap and the pages fluttering shut, close, dry. | book drop | P-3 | 3D |

Count, group 5: **30**.

### 8.6 The Rollers

Source: 4.9 and `07-ENEMIES.md` section 4. Four of the non-speech vocals of 5.6 (pain, crash "oof", laugh, death) stay in the voice todo; the three whoops are made here because the cue sheet needs them first. The Roller track and the Party Car teaser are music.

| # | Alias | What | Length (s) | Loop or one-shot | Generation brief | Must NOT sound like | Target level | 3D or 2D |
|---|---|---|---|---|---|---|---|---|
| 189 | `iwz_rl_chain_loop` | Chain of skaters rolling: moving loop | 6.0 | loop | Several polyurethane roller skate wheels rolling on hard tile, broadband rumble from low to high, a bearing whine and a regular tk-tk stride click every six tenths of a second, seamless loop. | train on tracks | F+10 | 3D |
| 190 | `iwz_rl_passby` | Skater pass-by, whine rising then falling | 2.0 | one-shot | A group of roller skaters rushing past, wheel rumble and a whine rising then falling by about four semitones over two seconds, left to right, tiled hall. | car fly-by | F+12 | 3D |
| 191 | `iwz_rl_whoop` | Chain leader's referee-style whoop (v3) | 0.8 | one-shot | A short loud cheerful whoop of a skater calling out, a rising half-second whoop without words, a cheering voice with a hint of a whistle, tiled hall. | wolf whistle | P-3 | 3D |
| 192 | `iwz_rl_swipe` | Swipe: satin fwip (v2) | 0.4 | one-shot | A quick swish of a satin jacket sleeve swung through the air, a soft fast fwip with a cloth snap, close, dry. | sword swing | P-4 | 3D |
| 193 | `iwz_rl_swipe_hit` | Swipe lands: thwap (v2) | 0.3 | one-shot | A flat open-hand thwap of a satin sleeve on a body, short and slappy, close, dry, layered over the stock hurt sound. | punch hit | P-4 | 3D |
| 194 | `iwz_rl_crash` | Wall crash: body whump and skate rattle | 1.2 | one-shot | A body hitting a concrete wall with a flat whump, roller skates rattling and wheels spinning down, a small scrape, close, dry. | car crash | P-3 | 3D |
| 195 | `iwz_rl_trip` | Trip: feet fly, lands on the back | 0.9 | one-shot | Skates slipping out from under a skater, a scuffle of wheels and a heavy back landing on a hard floor with a flat thump, close, dry. | banana peel slip | P-4 | 3D |
| 196 | `iwz_rl_slide_loop` | Slide on the back, wheels spinning | 2.0 | loop | A skater sliding on tile with skate wheels spinning in the air, a rattling whirr of loose wheels and a soft body scrape, seamless loop. | bowling alley | F+8 | 3D |
| 197 | `iwz_rl_getup` | Get up, wobble | 1.0 | one-shot | A skater struggling upright on wheels, a scuffle of hands and a knee, wheels rolling a little and a skate chirp on tile, close, dry. | cartoon wobble | P-6 | 3D |
| 198 | `iwz_rl_stop_skid` | Chain stops hard outside an opening: wheels skid | 0.8 | one-shot | A line of roller skaters stopping hard on tile, wheels skidding and squealing for half a second with a scatter of scuffs, hall, mid distance. | car braking | P-3 | 3D |
| 199 | `iwz_rl_skate_throw` | Skate throw: release, wheels in flight, impact (v2) | 1.5 | one-shot | A roller skate thrown overhand from a standstill, a quick release fwip, loose wheels whirring in flight for half a second, then a wooden thock against a wall or a flat thwap on a body, hall, close. | baseball pitch | P-3 | 3D |
| 200 | `iwz_rl_spin` | Spin on the spot | 0.9 | one-shot | A roller skater spinning once on the spot, a quick squeal of wheels turning on tile and a cloth whirl, close, dry. | ice skating | P-4 | 3D |
| 201 | `iwz_rl_pushoff` | Push-off from standing, three strides | 1.0 | one-shot | A roller skater taking three quick strides from standing, wheels clicking on tile with rising rolling speed, close, dry. | running footsteps | P-4 | 3D |
| 202 | `iwz_rl_pop` | Death: glitter-burst pop with bead shimmer (v2) | 0.8 | one-shot | A soft pop of a glitter burst with a shimmering scatter of tiny glass beads falling and tinkling on a floor, bright and short, close, dry. | balloon pop | P-3 | 3D |
| 203 | `iwz_rl_skate_roll` | Skate comes off and rolls away, taps a wall | 3.5 | one-shot | A single roller skate rolling away across a tile floor with one wheel spinning and ticking, slowing down and finally tapping against a wall, passing from close to far. | marble roll | P-4 | 3D |
| 204 | `iwz_rl_mirrorball` | Mirror-ball shimmer sweeps the platform | 3.0 | one-shot | A moving shimmer of tiny glittering high chimes and glass tinkles sweeping from one side to the other over three seconds, soft and airy, large hall, no melody. | fairy dust | P-4 | 3D |

Count, group 6: **16**.

### 8.7 Doors (one opening sound per door of `02-WORLD.md` section 3)

One-shot, positioned at the door, played when the purchase succeeds. The stock purchase sound plays as it does today and is not replaced; these are the door's own movement. Reason: each door is a different object and the player learns the map by ear.

| # | Alias | What | Length (s) | Loop or one-shot | Generation brief | Must NOT sound like | Target level | 3D or 2D |
|---|---|---|---|---|---|---|---|---|
| 205 | `iwz_door_d01_stair_debris` * | D1 Cordon to Fare Hall: debris cleared from the entrance stair | 3.0 | one-shot | Rubble, broken plank and sheet metal being dragged and tipped aside on a concrete stair, scraping, tumbling stones and a last timber thud, outdoors under a canopy, close. | building collapse | = P | 3D |
| 206 | `iwz_door_d02_hoist_stair` * | D2 Cordon to Police Post: hoist stair lowers | 3.5 | one-shot | A hydraulic steel stair section lowering on chains, a pump whine, chain clanks and a heavy plate landing with a boom on concrete, outdoors, close. | castle drawbridge chains | = P | 3D |
| 207 | `iwz_door_d03_fare_shutter` | D3 Fare Hall to Escalator Hall: fare gate roll shutter | 3.0 | one-shot | A corrugated steel roll shutter rattling up fast behind a turnstile, a ratchet click of the turnstile and a final bang at the top, big tiled hall. | garage door | = P | 3D |
| 208 | `iwz_door_d04_concertina` | D4 Fare Hall to Arcade: concertina gate | 2.5 | one-shot | A folding steel concertina security gate pushed open along a track, scissor links rattling and clacking, rollers rumbling and a last clang, tiled hall. | prison gate | = P | 3D |
| 209 | `iwz_door_d05_counter_flap` | D5 Fare Hall to Police Post: public counter door | 2.0 | one-shot | A wooden counter flap lifted and a glazed door latch released, a small bell on the door and a wood and glass rattle, small office. | saloon door | = P | 3D |
| 210 | `iwz_door_d06_hoarding` | D6 Fare Hall to the Breach: hoarding panels | 3.0 | one-shot | Plywood hoarding panels dragged aside from a frame, screws squealing, tape ripping and a final board falling flat on concrete, big hall. | wall smash | = P | 3D |
| 211 | `iwz_door_d07_blast_wind` | D7 Arcade to Shelter 7: blast door wound open | 4.5 | one-shot | A hand crank wheel turned with a ratchet clatter, a very heavy steel blast door grinding open on a stone threshold, groaning metal and a final boom, concrete. | sci-fi vault door | = P | 3D |
| 212 | `iwz_door_d08_welded_gate` | D8 Platform A West to Boneyard: welded track gate | 3.0 | one-shot | Weld seams popping and cracking, then a rusty steel gate dragged across gravel on squealing hinges and clanging against a pillar, tunnel. | castle gate | = P | 3D |
| 213 | `iwz_door_d09_brick_hole` | D9 Boneyard to Parlour: hole in the brickwork | 3.0 | one-shot | Loose bricks pulled and toppling out of a wall, stone clatter, mortar dust hiss and a last heavy brick thud, in a dead-end tunnel. | rock slide | = P | 3D |
| 214 | `iwz_door_d10_bronze_doors` | D10 Parlour to Bellows Vault: Vayle's bronze doors | 4.0 | one-shot | Two huge bronze double doors swinging open with a deep resonant hum, an old brass lock turning, a pneumatic hiss and a boom against a stone wall, marble hall. | dungeon door | = P | 3D |
| 215 | `iwz_door_d11_stair_gate` * | D11 Platform A East to Signal Cabin: steel stair gate | 2.0 | one-shot | A spring loaded steel stair gate unbolted and swung open with a bolt clack, a rattling latch and a hollow ring on an iron staircase, close. | gate creak | = P | 3D |
| 216 | `iwz_door_d12_gantry_door` * | D12 Signal Cabin to Converter Hall: gantry door | 2.5 | one-shot | A steel mesh gantry door rolling open on overhead rollers with a rumble, a clang of the stop and a rattle of mesh, big industrial hall. | garage door | = P | 3D |
| 217 | `iwz_door_d13_roller_door` | D13 Platform A East to Car Barn: depot roller door | 4.5 | one-shot | A big corrugated steel depot roller door cranked up by a chain hoist, rattling slats, chain clanks and a hard bang at the top, large steel shed. | garage door | = P | 3D |
| 218 | `iwz_door_d14_cable_door` | D14 Car Barn to Converter Hall: cable-way door | 3.0 | one-shot | A heavy sliding fire door on a rail with thick cables dragged along the floor, a rumble, a cable thump and a metal clunk, industrial space. | sci-fi door | = P | 3D |
| 219 | `iwz_door_d15_pit_grate` | D15 Car Barn to Sump: pit grate and catwalk door | 4.0 | one-shot | A heavy iron pit grate winched up on a chain with a clanking ratchet and set down, followed by a steel catwalk door banging open, echoing in a deep pit. | dungeon trapdoor | = P | 3D |
| 220 | `iwz_door_d16_keypad` | D16 Converter Hall to Exchange: jammed keypad door forced | 3.0 | one-shot | A numeric keypad pressed with dull clicks and a harsh relay buzz, then a solenoid forced open with a grunt of a metal bolt and a door swinging, computer hall. | sci-fi keypad | = P | 3D |
| 221 | `iwz_door_d17_cage` | D17 Exchange to Staff Stair: cage door | 3.0 | one-shot | A folding pull-cage lift door dragged open with scissor rattle, a padlock chain clattering against the cage and a final clang, brick stairwell. | elevator ding | = P | 3D |

Count, group 7: **17**.

### 8.8 The four traps

Source: 4.10. Each trap loop is at least 8 dB over its zone median and within 2 dB of the stock trap sound, measured the same way. The purchase sound is stock.

| # | Alias | What | Length (s) | Loop or one-shot | Generation brief | Must NOT sound like | Target level | 3D or 2D |
|---|---|---|---|---|---|---|---|---|
| 222 | `iwz_trap_decon_beacon` | Decon Foam start: three yellow beacon beeps | 1.5 | one-shot | Three evenly spaced dry electromechanical beeps from a yellow warning beacon, harsh buzzy tone not musical, outdoors under a tent, mid distance. | modern alarm beep | P+0 | 3D |
| 223 | `iwz_trap_decon_start` | Decon Foam: pump spin-up, four valve chunks | 2.5 | one-shot | An industrial pump spinning up over one second, then four heavy valve chunks opening one after another with a metallic clunk, tent and wet concrete, mid distance. | sci-fi pressure door | P+0 | 3D |
| 224 | `iwz_trap_decon_foam` | Decon Foam: thick foam hiss and gurgle | 4.0 | loop | A thick wet foam hissing and bubbling out of many nozzles, a soft heavy gurgle with sticky wet patter on concrete, constant level, no pitch, seamless loop, in a tented corridor. | rain shower | F+10 | 3D |
| 225 | `iwz_trap_decon_wade` | Decon Foam: a zombie wades in, sticky squelch (v3) | 0.6 | one-shot | A heavy body wading through thick foam, a slow sticky squelch and a soft wet drag with a muffled struggle, close, dry. | acid melt | P-6 | 3D |
| 226 | `iwz_trap_decon_end` | Decon Foam end: valves, pump runs down, drips | 3.0 | one-shot | Four valve chunks closing, an industrial pump winding down over a second and a half, then slow drips in a tent, mid distance. | machine shut down | P+0 | 3D |
| 227 | `iwz_trap_rail_start` * | Third Rail start: lever clunk, contactor, hum rises | 2.0 | one-shot | A fuse box lever thrown with a clunk, a big contactor ka-chunk, then a rising hum at fifty and one hundred and fifty cycles in a metro track pit, big space. | sci-fi power up | P+3 | 3D |
| 228 | `iwz_trap_rail_loop` * | Third Rail hum loop, 50 and 150 Hz | 4.0 | loop | A steady electrified rail hum with strong fifty and one hundred and fifty cycle components and a faint sizzle, wide underground platform space, seamless loop, no melody. | sci-fi energy field | F+12 | 3D |
| 229 | `iwz_trap_rail_kill` * | Third Rail kill: zzap (v3) | 0.4 | one-shot | A sharp electric zap of a body hitting a live rail, a snap and a short buzz, close, dry. | lightning bolt | P-3 | 3D |
| 230 | `iwz_trap_rail_arc` | Third Rail arc along the pit (v2) | 0.5 | one-shot | A crackling electric arc jumping between steel rails, a quick zip and two snaps, mid distance, tunnel. | lightning thunder | P-3 | 3D |
| 231 | `iwz_trap_rail_end` | Third Rail end: contactor clack, hum decays | 1.5 | one-shot | A contactor clacking open and a rail hum decaying away over one second with a last faint ticking, big underground platform. | power down whine | P+0 | 3D |
| 232 | `iwz_trap_arc_start` | Flashover start: switches slam, hall dark, rectifiers flash | 2.0 | one-shot | Knife switches slammed shut along a marble switchboard, then a sudden white crack of mercury arc rectifiers flashing with a rising capacitor whine and an ozone hiss, huge hall reverb. | sci-fi laser | P+3 | 3D |
| 233 | `iwz_trap_arc_loop` | Flashover flash loop, louder | 4.0 | loop | A fierce crackling arc buzz at a hundred cycles with violent snaps and a steady ozone hiss, aggressive, huge hall, seamless loop, no melody. | sci-fi energy field | F+14 | 3D |
| 234 | `iwz_trap_arc_blind` | Blinded zombie: stumbling scuff and a muffled groan (v3) | 0.6 | one-shot | A heavy body stumbling and scuffing on concrete with a muffled groan through its hands, as if covering its eyes, close, dry, no words. | monster scream | P-6 | 3D |
| 235 | `iwz_trap_arc_end` | Flashover end: lights strike back, buzz settles | 1.2 | one-shot | Fluorescent tubes striking back on one after another with buzzing ticks while a mercury arc buzz settles to a steady hum, big hall. | horror light flicker | P-3 | 3D |
| 236 | `iwz_trap_bel_start` | The Bellows start: lever, grating, air-draw roar | 3.0 | one-shot | A heavy lever ka-thunk, an iron intake grating clanking open, and a huge air-draw roar rising over two seconds into a vast stone vault, mid distance. | jet engine | P+3 | 3D |
| 237 | `iwz_trap_bel_note` | The Bellows: full organ chord held 15 s | 15.0 | one-shot | A huge organ pipe chord of deep C, G and E notes, steady and slow breathing, held for fifteen seconds in a vast stone vault, no melody, no vibrato. | church organ hymn | P+0 | 3D |
| 238 | `iwz_trap_bel_draw` | The Bellows air-draw loop under the Note | 5.0 | loop | A very large intake drawing air through iron gratings, deep steady roar with whistling edges and a slow pulse, seamless loop, enclosed vault. | wind storm | F+12 | 3D |
| 239 | `iwz_trap_bel_chop` | The Bellows: blades chop a zombie (v3) | 0.5 | one-shot | A heavy mechanical blade chopping into something with a chunk and a dull whump of displaced air, close, dry. | chainsaw engine roar | P-3 | 3D |
| 240 | `iwz_trap_bel_rush` | Player pulled by the draw: wind rush (v2) | 1.5 | one-shot | A sudden rush of strong wind pulling past the listener toward an intake, rising howl and flapping cloth, short, close. | storm tornado howl | P-3 | 1P |
| 241 | `iwz_trap_bel_exhale` | The Bellows exhales as the Note fades | 3.0 | one-shot | A giant bellows exhaling slowly, a long soft breath of air fading over three seconds with a faint leather creak, vast stone vault. | dragon breath | P-3 | 3D |

Count, group 8: **20**.

### 8.9 Ambience per zone (beds and emitters of 2.2 and 2.3)

Each bed is a 26 s seamless clip (24 s body plus 2 s head, F2), level = the zone median of 2.2. Emitter IDs (CO1 and so on) are those of 2.3. Emitters that share one source are made once: the shared rows come first. Lit twins (PE1) and second-cage copies (CH3) are made by the bank tools from the one file, by gain and by a pitch shift of 1.3 percent; they are not generated. The Terminus has one generated emitter, the clock's mechanism (TE1); the Departure Note pedal (TE2) is synthesis and the Voice (TE3) is voice. The stock fuse-box and tube-strike power sounds, and every music-like emitter other than the copier cycles and the cassette (the Party Car leaks PE3, the Needle Drop playlist), are not generated.

| # | Alias | What | Length (s) | Loop or one-shot | Generation brief | Must NOT sound like | Target level | 3D or 2D |
|---|---|---|---|---|---|---|---|---|
| 242 | `iwz_amb_shared_tube_buzz` | Shared: uneven fluorescent tube buzz and ballast ticks (FH4, PW2, PP3, EH sets) | 8.0 | loop | Row of old fluorescent tubes buzzing at a hundred cycles, uneven with one tube flickering, soft ballast ticks every few seconds, room tone of a tiled hall, seamless loop. | horror light flicker | F+6 | 3D |
| 243 | `iwz_amb_shared_lamp_buzz` | Shared: caged lamp and bare bulb soft 100 Hz buzz (SS2, S73, SU3, BO3, BR4) | 6.0 | loop | A few old incandescent bulbs in wire cages humming softly at a hundred cycles with a faint filament tick, quiet, close, seamless loop. | sci-fi hum | F+4 | 3D |
| 244 | `iwz_amb_shared_sodium_hum` | Shared: sodium lamp hum with ballast ticks (CO3, CB6) | 6.0 | loop | A tall sodium floodlight humming at a hundred cycles with a gritty ballast buzz and occasional ticks as it warms, outdoors or large shed, seamless loop. | horror light flicker | F+6 | 3D |
| 245 | `iwz_amb_cordon_bed` * | Cordon bed | 26.0 | loop | Heavy rain on a torn plastic canopy and wet concrete, gutter run-off splashing, far city traffic as a low bass rumble, seamless loop, no thunder, no voices, outdoor street shelter. | cinematic thunderstorm | -40 dBFS median | 2D |
| 246 | `iwz_amb_cordon_generator` | CO1 news van generator put-put with a stumble | 20.0 | loop | A small portable diesel generator running with a steady put-put and a slow stumble every twenty seconds, outdoors in rain, close, seamless loop. | motorbike idle | F+10 | 3D |
| 247 | `iwz_amb_cordon_mic_whine` | CO2 live microphone feeding back, wobbling | 8.0 | loop | A thin high microphone feedback whine at around 260 hertz pitch wobbling slowly at a third of a hertz, outdoor, faint and eerie, seamless loop. | alarm tone | F+4 | 3D |
| 248 | `iwz_amb_cordon_canopy_hum` | CO4 STATION 0 canopy transformer hum and sign tick | 6.0 | loop | A big sign transformer humming at a hundred cycles with an occasional neon tube tick, outdoors under a canopy in the rain, seamless loop. | sci-fi hum | F+6 | 3D |
| 249 | `iwz_amb_cordon_drip` | CO5 heavy drops from a canopy tear on a barrier slab (v3) | 0.5 | one-shot | One heavy water drop falling from a plastic canopy onto a concrete slab with a flat plop and a small ring, outdoors, close. | water tap drip | F+6 | 3D |
| 250 | `iwz_amb_cordon_canvas` | CO6 tent canvas flap and guy-rope creak (v2) | 3.0 | one-shot | A big canvas tent flapping in a gust, taut guy ropes creaking and a pole knocking, outdoors in wind, mid distance. | ship sails | F+6 | 3D |
| 251 | `iwz_amb_cordon_feedback_jump` | Van feedback jumps a fifth and settles at power-on | 2.0 | one-shot | A microphone feedback whine jumping up a fifth in pitch in a quick glide, wavering and settling, outdoors, faint, one event. | alarm tone | F+6 | 3D |
| 252 | `iwz_amb_fare_bed` * | Fare Hall bed | 26.0 | loop | Large tiled hall room tone, reverberant ventilation breath, distant drips returning from a stairwell, soft air movement, seamless loop, no voices, no machines. | cave ambience | -44 dBFS median | 2D |
| 253 | `iwz_amb_fare_board_motors` | FH1 split-flap board motors idling, soft ratchet purr | 6.0 | loop | Many small electric motors of a split-flap board idling, a soft ratchet purr with occasional faint flap taps, tiled hall, seamless loop. | slot machine | F+8 | 3D |
| 254 | `iwz_amb_fare_draught` | FH3 draught whistling through fare gates | 6.0 | loop | Cold air whistling softly through the bars of a row of turnstile gates, thin low whistle swelling and fading, tiled hall, seamless loop. | ghost wind | F+4 | 3D |
| 255 | `iwz_amb_fare_booth` | FH5 Announcer's booth breath and one paper rustle | 2.0 | one-shot | A small closed glass room breathing, faint air movement and one slow rustle of a sheet of paper, distant, quiet. | ghost whisper | F+3 | 3D |
| 256 | `iwz_amb_fare_bunting` | FH6 bunting flutter and fallen chair settling (v2) | 2.0 | one-shot | Paper bunting and ribbon fluttering in a draught and a wooden banquet chair creaking and settling on tile, tiled hall, mid distance. | party horn | F+4 | 3D |
| 257 | `iwz_amb_esc_bed` | Escalator Hall bed | 26.0 | loop | A long tiled shaft, air moving slowly down toward a platform, tile ring, a deep distant platform rumble below, seamless loop, no voices, no machines. | subway announcement | -46 dBFS median | 2D |
| 258 | `iwz_amb_esc_box_hum_a` | EH1 advertising box hum | 6.0 | loop | A lit advertising display box humming at a hundred cycles with a thin high whine, tiled hall, seamless loop. | sci-fi hum | F+5 | 3D |
| 259 | `iwz_amb_esc_box_hum_b` | EH2 second box hum, different pitch beating 2 Hz | 6.0 | loop | A second lit advertising display box with a slightly higher hum around a hundred and two cycles and a thin whine, tiled hall, seamless loop. | sci-fi hum | F+5 | 3D |
| 260 | `iwz_amb_esc_motor_cool` | EH3 escalator motor cooling, ticks slowing over 30 s | 30.0 | one-shot | Metal ticks of a cooling electric motor slowing from three a second to one every three seconds across thirty seconds, soft expansion pings, tiled hall, distant. | clock ticking | F+4 | 3D |
| 261 | `iwz_amb_esc_draught` | EH4 draught up the lanes with the train's air | 8.0 | loop | A low whistling draught moving up escalator lanes carrying warm tunnel air, soft moan and slow swell, tiled shaft, seamless loop. | ghost wind | F+6 | 3D |
| 262 | `iwz_amb_esc_rubber` | EH5 loose handrail rubber squeal and click (v2) | 1.5 | one-shot | A loose escalator handrail rubber squealing as it slides over a metal guide with a click, short, tiled hall, distant. | rubber duck | F+4 | 3D |
| 263 | `iwz_amb_esc_box_crackle` | EH6 advertising box tube crackle (v2) | 1.0 | one-shot | A burst of dry electrical crackle from a failing fluorescent tube in a box, quick sputter and a tick, tiled hall, close. | static noise | F+4 | 3D |
| 264 | `iwz_amb_arcade_bed` | Underpass Arcade bed | 26.0 | loop | A low ceiling underpass hush, dead ceiling panels humming at fifty cycles, dust and the faint thump and whir of copiers from far away through walls, seamless loop, no voices. | shopping mall | -42 dBFS median | 2D |
| 265 | `iwz_amb_arcade_copier_a` | AR1 Copy Stop photocopier, west row: lamp sweep and drum whir, cycle A, 8.0 s | 8.0 | loop | A photocopier cycling under its lid, a bright lamp bar sweeping with a soft hum, a drum whirring and a paper feed clacking, repeating every eight seconds, exactly eight seconds, seamless loop, shop interior. | modern office printer | F+8 | 3D |
| 266 | `iwz_amb_arcade_copier_b` | AR2 photocopier, centre: lid thunk and paper feed, cycle B, 10.0 s | 10.0 | loop | A second photocopier cycling, a heavy lid thunk, a roller feeding paper with a rattle and a warm fan, repeating every ten seconds, exactly ten seconds, seamless loop, shop interior. | modern office printer | F+8 | 3D |
| 267 | `iwz_amb_arcade_blueprint_c` | AR3 blueprint machine: ammonia fan and paper roller, cycle C, 12.0 s | 12.0 | loop | A blueprint machine with a slow fan and a long paper roller turning, a soft chuff of air once a cycle, repeating every twelve seconds, exactly twelve seconds, seamless loop, shop interior. | arcade game | F+8 | 3D |
| 268 | `iwz_amb_arcade_polisher` | AR4 floor polisher motor and brush swish, 12 s lap | 12.0 | loop | A floor polishing machine, steady electric motor drone and rotating brush swish on tile, the sound circling around the listener once in twelve seconds, seamless loop. | vacuum cleaner | F+10 | 3D |
| 269 | `iwz_amb_arcade_needle` | AR5 stuck needle in a run-out groove | 3.6 | loop | A record player needle stuck in a run-out groove, soft vinyl hiss and a dull thump every one and eight tenths of a second, seamless loop of two thumps. | vinyl crackle music | F+4 | 3D |
| 270 | `iwz_amb_arcade_coin` | AR6 coin-slot clatter (v2) | 1.0 | one-shot | Coins dropping through a coin slot mechanism into a metal tray, a quick rattle and clunk, arcade space, close. | slot machine jackpot | F+4 | 3D |
| 271 | `iwz_amb_arcade_coffee` | AR6 coffee machine gurgle | 3.0 | one-shot | An old espresso machine gurgling and hissing as it heats, bubbling water and a steam spit, small shop, mid distance. | cafe ambience | F+4 | 3D |
| 272 | `iwz_amb_arcade_capacitor` | AR6 photo booth flash capacitor whine | 2.0 | one-shot | A photo booth flash capacitor charging with a thin rising electronic whine and a tick, quiet, close. | sci-fi charge | F+4 | 3D |
| 273 | `iwz_amb_arcade_panel` | AR6 ceiling panel crackle (v2) | 1.0 | one-shot | A dead ceiling light panel crackling with a short dry electrical sputter and a tick, low ceiling, close. | static noise | F+4 | 3D |
| 274 | `iwz_amb_arcade_copier_fx` | Copy Stop copier events: lid slam, paper jam clatter, low-paper chirp, long scan sweep (v4) | 1.0 | one-shot | Short photocopier sounds one at a time: a heavy lid slam, a paper jam clatter, a small relay chirp, and a long lamp scan sweep with a hum, shop interior, mid distance. | arcade game effects | F+6 | 3D |
| 275 | `iwz_amb_s7_bed` | Shelter 7 bed | 26.0 | loop | A sealed concrete shelter, almost silent room tone, a faint forty cycle ear pressure tone, dry still air, seamless loop, no voices. | horror drone | -49 dBFS median | 2D |
| 276 | `iwz_amb_s7_ventilator` | S71 hand-cranked ventilator turning by itself | 4.8 | loop | A hand cranked air ventilator turning slowly on its own, one dry squeak per turn every two and four tenths of a second over a soft paper fan whirr, seamless loop. | haunted music box | F+8 | 3D |
| 277 | `iwz_amb_s7_hatch` | S72 escape hatch whisper of air | 6.0 | loop | Air moving very faintly in a long vertical shaft above a sealed hatch, a barely audible hollow whisper, seamless loop, concrete room. | ghost whisper | F+2 | 3D |
| 278 | `iwz_amb_s7_drip` | S74 water drum drip (v3) | 1.0 | one-shot | A single water drop falling into a large metal drum, a hollow plink with a short ring, concrete room, mid distance. | water tap drip | F+4 | 3D |
| 279 | `iwz_amb_s7_tins` | S75 cracker tins settling, bunk chain creak | 2.0 | one-shot | A stack of metal cracker tins shifting and settling with soft clanks and a bunk chain creaking once, concrete room, mid distance. | haunted house | F+4 | 3D |
| 280 | `iwz_amb_pp_bed` | Transit Police Post bed | 26.0 | loop | A small office room tone, a radiator ticking now and then, muffled street rumble from above, still air, seamless loop, no voices. | office ambience | -47 dBFS median | 2D |
| 281 | `iwz_amb_pp_typewriter` | PP1 one typewriter key struck (v2) | 0.8 | one-shot | One key struck on an old manual typewriter, a clack and a spring return, in a small quiet office, mid distance. | typing session | F+6 | 3D |
| 282 | `iwz_amb_pp_radio` | PP2 radio on a dead channel, carrier hiss | 8.0 | loop | A desk radio tuned to a dead channel, steady carrier hiss with faint crackle and no voice, small office, seamless loop. | police radio chatter | F+4 | 3D |
| 283 | `iwz_amb_pp_squelch` | PP2 squelch click on the dead channel | 0.4 | one-shot | One radio squelch click and a short burst of hiss, small speaker, quiet, no voice. | police radio chatter | F+4 | 3D |
| 284 | `iwz_amb_pp_cell` | PP4 slow drip and hinge tick | 1.5 | one-shot | A slow water drip and one small metal hinge tick in a holding cell, stone, close, quiet. | horror dripping | F+3 | 3D |
| 285 | `iwz_amb_pp_chain` | PP5 chain and padlock rattle (v2) | 1.5 | one-shot | A chain and padlock on a mesh cage rattling once as if bumped, metallic, small room, mid distance. | prison chains | F+4 | 3D |
| 286 | `iwz_amb_ss_bed` | Staff Stair bed | 26.0 | loop | A brick stairwell echo, a slow air column moving, a drip chain far down in the dark, seamless loop, no voices. | cave ambience | -48 dBFS median | 2D |
| 287 | `iwz_amb_ss_clock` | SS1 time clock thunk with no card (v2) | 0.8 | one-shot | An old time clock punching with a heavy mechanical thunk and a small bell ring, brick stairwell, mid distance. | cash register | F+6 | 3D |
| 288 | `iwz_amb_ss_draught` | SS3 draught breathing down the stair | 8.0 | loop | A soft draught breathing down a brick stairwell, slowly rising and falling hollow air, seamless loop, quiet. | ghost wind | F+4 | 3D |
| 289 | `iwz_amb_pw_bed` | Platform A West bed | 26.0 | loop | A wide underground platform, tunnel breath, long reverb tail, distant water, soft air, seamless loop, no voices, no trains. | subway station | -45 dBFS median | 2D |
| 290 | `iwz_amb_pw_wind` | PW1 wind before a train, no train | 9.0 | one-shot | A low-passed rush of tunnel wind swelling over six seconds along a platform with steel rails singing, then cut to two seconds of silence and a soft fall. | train arriving | F+14 | 3D |
| 291 | `iwz_amb_pw_rail_hum` | PW3 third rail live in the pit, 50 and 150 Hz | 6.0 | loop | An energised metro third rail humming at fifty and one hundred and fifty cycles with a faint sizzle, underground pit, seamless loop. | sci-fi energy field | F+8 | 3D |
| 292 | `iwz_amb_pw_rail_tick` | PW4 rails ticking as they settle (v3) | 1.5 | one-shot | Steel rails ticking and pinging as they settle, a few sparse metallic ticks, underground pit, mid distance. | clock ticking | F+4 | 3D |
| 293 | `iwz_amb_pw_shutter` | PW5 kiosk shutter rattling | 2.0 | one-shot | A rolled steel kiosk shutter rattling in a draught, loose slats chattering and a final bump, underground platform, mid distance. | garage door | F+6 | 3D |
| 294 | `iwz_amb_pw_ballast` | PW6 ballast drips (v2) | 1.0 | one-shot | A water drop falling on gravel ballast, a soft patter, tunnel pit, quiet, mid distance. | water tap drip | F+3 | 3D |
| 295 | `iwz_amb_pe_bed` | Platform A East bed | 26.0 | loop | Inside parked train carriages, ceiling fan whirr, subdued platform air, a muted bass thump from the far car, seamless loop, no voices, no music lyrics. | train interior | -42 dBFS median | 2D |
| 296 | `iwz_amb_pe_fluor` | PE1 lit cars fluorescent buzz | 6.0 | loop | Fluorescent carriage lights buzzing at a hundred cycles with a ballast tick and slight beating, inside a train, seamless loop. | horror light flicker | F+8 | 3D |
| 297 | `iwz_amb_pe_brake` | PE4 cab brake-release sigh | 2.5 | one-shot | A train brake releasing with a long breathy sigh of air and a soft metal settle, platform, mid distance. | steam locomotive | F+8 | 3D |
| 298 | `iwz_amb_pe_signal_tick` | PE5 east signal relay tick every 2 s while red | 2.0 | loop | A signal relay ticking once every two seconds with a dry click, tunnel mouth, seamless loop of one tick. | clock ticking | F+4 | 3D |
| 299 | `iwz_amb_pe_signal_buzz` | PE5 east signal steady buzz once green | 4.0 | loop | A signal relay holding a steady low buzz with a faint hum, tunnel mouth, seamless loop. | sci-fi hum | F+4 | 3D |
| 300 | `iwz_amb_pe_cess` | PE6 cess draught moan beside cars 5 and 6 | 8.0 | loop | A low draught moaning along a narrow tunnel walkway beside train cars, slow swell and fade, seamless loop. | ghost wind | F+4 | 3D |
| 301 | `iwz_amb_sc_bed` | Signal Cabin bed | 26.0 | loop | A wooden signal cabin, wind at window frames, old timber settling, a stove ticking, seamless loop, no voices. | cozy cabin | -46 dBFS median | 2D |
| 302 | `iwz_amb_sc_lever` | SC1 working lever settling in the frame (v2) | 1.5 | one-shot | One heavy iron signal lever settling in its frame with a creak and a small clack, wooden cabin, mid distance. | door creak | F+6 | 3D |
| 303 | `iwz_amb_sc_block_bell` | SC2 block bell, one stroke | 4.0 | one-shot | A single stroke of a railway block instrument bell, a bright brass ring decaying over four seconds, wooden cabin, mid distance. | church bell | F+14 | 3D |
| 304 | `iwz_amb_sc_stove` | SC3 stove tick and kettle on a low simmer | 8.0 | loop | A small iron stove ticking as it burns and a kettle on a low simmer with occasional pops, wooden cabin, seamless loop. | campfire music | F+4 | 3D |
| 305 | `iwz_amb_sc_diagram` | SC4 track diagram relay lamp-proving ticks | 4.0 | loop | Small relays ticking in a slow irregular pattern behind a track diagram board, dry bakelite clicks, wooden cabin, seamless loop. | computer beeps | F+4 | 3D |
| 306 | `iwz_amb_sc_desk` | SC5 grey desk fan and thin 8 kHz screen whine | 6.0 | loop | A small computer desk fan whirring with a very thin high screen whine, quiet, wooden cabin, seamless loop. | sci-fi computer | F+3 | 3D |
| 307 | `iwz_amb_cb_bed` | Car Barn bed | 26.0 | loop | A big steel shed, roof panels flexing slowly, far oil drips, high-bay air, seamless loop, no voices, no machines. | warehouse ambience | -43 dBFS median | 2D |
| 308 | `iwz_amb_cb_hoist` | CB1 chain hoist link ticking, 12 s | 12.0 | loop | A hanging chain hoist with a wheel set swaying, one link ticking through the pulley every second, steel shed, seamless loop. | clock ticking | F+6 | 3D |
| 309 | `iwz_amb_cb_compressor` | CB2 air compressor running (pump-up and hold) | 12.0 | loop | An industrial air compressor pumping up and holding pressure, rhythmic thudding motor with a steady hum, steel shed, seamless loop. | road jackhammer | F+10 | 3D |
| 310 | `iwz_amb_cb_relief` | CB2 compressor relief valve pfft | 2.0 | one-shot | An air compressor relief valve venting with a sharp pfft and a tail of leaking air, steel shed, mid distance. | steam locomotive | F+10 | 3D |
| 311 | `iwz_amb_cb_weld` | CB3 welding crackle bursts (v3) | 3.0 | one-shot | An electric arc welder crackling in bursts with hissing sparks and a buzz, steel shed, mid distance. | sci-fi laser | F+6 | 3D |
| 312 | `iwz_amb_cb_pit` | CB4 pit drips and work-lamp cable swinging (v2) | 2.0 | one-shot | Oil drips falling into an inspection pit and a work lamp cable swinging with a soft metal clink, steel shed, mid distance. | horror dripping | F+4 | 3D |
| 313 | `iwz_amb_cb_tool` | CB5 hung tool swinging on the shadow board | 1.5 | one-shot | A spanner hanging on a pegboard swinging and tapping softly against the board, steel shed, mid distance. | wind chimes | F+4 | 3D |
| 314 | `iwz_amb_ch_bed` * | Converter Hall bed | 26.0 | loop | A cavernous dead concrete hall, deep thirty cycle room resonance, louvre air whistling softly, seamless loop, no voices, no machines running. | horror drone | -38 dBFS median | 2D |
| 315 | `iwz_amb_ch_g2` * | CH1 G-2 diesel genset idling, four-cylinder tick-over | 8.0 | loop | A large four-cylinder diesel generator idling with a deep steady tick-over and a low exhaust throb, concrete hall, seamless loop. | race car engine | F+14 | 3D |
| 316 | `iwz_amb_ch_rect` | CH2 mercury-arc rectifier cage buzz | 6.0 | loop | A crackling hundred cycle buzz from a mercury-arc rectifier cage, violet arcing with dry crackle, concrete hall, seamless loop. | sci-fi energy field | F+10 | 3D |
| 317 | `iwz_amb_ch_switch` | CH4 marble switchboard meter ticks and knife-switch clack (v2) | 2.0 | one-shot | A marble switchboard with analog meters ticking and a knife switch clacking shut, concrete hall, mid distance. | sci-fi console | F+6 | 3D |
| 318 | `iwz_amb_ch_tag` | CH5 DO NOT RESTART tag tapping (v2) | 1.0 | one-shot | A paper tag on a string tapping against a metal engine housing in a draught, light dry taps, concrete hall, quiet. | knocking ghost | F+3 | 3D |
| 319 | `iwz_amb_ch_louvre` | CH6 wind howling in louvres | 8.0 | loop | Wind howling through steel ventilation louvres with a rising and falling moan, concrete hall, seamless loop. | storm wind | F+6 | 3D |
| 320 | `iwz_amb_ex_bed` | Exchange bed | 26.0 | loop | A raised floor computer hall plenum, air handling hush and faint relay flutter, seamless loop, no voices, no beeps. | server room | -44 dBFS median | 2D |
| 321 | `iwz_amb_ex_relay` | EX1 to EX3 relay wave: 40 clicks in 2 s (v2) | 2.0 | one-shot | Forty relay clicks rippling in a quick wave across a row of racks over two seconds, dry bakelite clatter, computer hall, mid distance. | computer beeps | F+8 | 3D |
| 322 | `iwz_amb_ex_printer` | EX4 line printer chatter, ratchet, paper feed | 8.0 | loop | An old impact line printer chattering with a ratchet and paper feed, rhythmic hammer bursts, computer hall, seamless loop. | modern printer | F+10 | 3D |
| 323 | `iwz_amb_ex_tape` | EX5 tape drive capstan whine and vacuum pump | 6.0 | loop | Reel tape drives spinning with a capstan whine and a slow vacuum pump thump, computer hall, seamless loop. | sci-fi computer | F+8 | 3D |
| 324 | `iwz_amb_ex_tape_spinup` | Tape drives spin up at power-on, rising whine | 2.0 | one-shot | A group of tape drive motors spinning up with a rising whine over two seconds, computer hall, mid distance. | sci-fi power up | F+10 | 3D |
| 325 | `iwz_amb_ex_fans` | EX6 cooling fans and screen hum | 8.0 | loop | Cooling fans blowing under a raised floor with a faint high screen hum, computer hall, seamless loop. | server room | F+5 | 3D |
| 326 | `iwz_amb_ex_names` | Printer prints the names of the riders | 3.0 | one-shot | A dot-matrix line printer printing a burst of text then a tractor paper feed with a ratchet, computer hall, mid distance. | modern printer | P-3 | 3D |
| 327 | `iwz_amb_su_bed` | The Sump bed | 26.0 | loop | Black water lapping slowly on concrete in a deep pit, hollow drain air, seamless loop, no voices, no machines. | swamp ambience | -42 dBFS median | 2D |
| 328 | `iwz_amb_su_pump` | SU1 running pump, shaking thud every 1.1 s | 4.4 | loop | A single submersible pump running with a shaking thud every one point one seconds and water slosh, deep concrete pit, seamless loop of four thuds. | film heartbeat thump | F+12 | 3D |
| 329 | `iwz_amb_su_culvert` | SU2 culvert gurgling with echo | 8.0 | loop | Storm water gurgling down a drain culvert with a hollow echo, deep concrete pit, seamless loop. | babbling forest brook | F+6 | 3D |
| 330 | `iwz_amb_su_drip` | SU4 echoing drips (v3) | 2.0 | one-shot | Water drips falling into a pool in a large echoing concrete pit, hollow, mid distance. | horror dripping | F+4 | 3D |
| 331 | `iwz_amb_su_catwalk` | SU5 catwalk steel creak (v2) | 2.0 | one-shot | A steel catwalk creaking and flexing, a long metallic groan and a ping, large concrete pit, mid distance. | ship creak | F+5 | 3D |
| 332 | `iwz_amb_su_bump` | SU6 floating debris bumps the wall | 1.5 | one-shot | A floating wooden crate bumping a concrete wall in dark water, dull knock and sloshing, pit, mid distance. | monster in water | F+4 | 3D |
| 333 | `iwz_amb_su_pump_fail` | Second pump coughs and fails at power-on | 3.0 | one-shot | A second pump motor trying to start, a labored cough and whine, a few failed attempts and a final dead clunk, deep concrete pit, mid distance. | machine shut down | F+8 | 3D |
| 334 | `iwz_amb_br_bed` | The Breach bed | 26.0 | loop | Cold air in a cut through rock, a low settling rumble, old wood creaking, seamless loop, no voices, no machines. | cave ambience | -47 dBFS median | 2D |
| 335 | `iwz_amb_br_boards` | BR1 scaffold boards creak and shift (v3) | 2.0 | one-shot | Scaffold planks creaking and shifting as if walked on, wood groans and a dull knock, rock tunnel, mid distance. | haunted floor | F+6 | 3D |
| 336 | `iwz_amb_br_drips` | BR2 drips on a steel plate, irregular 20 s | 20.0 | loop | Irregular water drips falling onto a steel plate over twenty seconds, rock tunnel, seamless loop. | horror dripping | F+4 | 3D |
| 337 | `iwz_amb_br_lamps` | BR3 work lamps on a cable, buzz and sway squeak | 6.0 | loop | Work lamps on a hanging cable buzzing softly with a slow sway squeak, rock tunnel, seamless loop. | horror light flicker | F+4 | 3D |
| 338 | `iwz_amb_br_trickle` | BR5 dust and pebble trickle (v2) | 2.0 | one-shot | Dust and small pebbles trickling down a rock face, soft dry patter, quiet, rock tunnel. | avalanche rockfall roar | F+3 | 3D |
| 339 | `iwz_amb_br_breath` | BR6 the Bellows breathing through the rock | 6.0 | loop | A deep breath through rock, a six second slow inhale and exhale low-passed at one hundred and fifty hertz, very low, seamless loop. | monster breathing | F+8 | 3D |
| 340 | `iwz_amb_pa_bed` | The Parlour bed | 26.0 | loop | A dry marble salon, warm still room tone of an old closed room, high ceiling reverb, tiny wood ticks, seamless loop, no voices, no music. | ghost ambience | -48 dBFS median | 2D |
| 341 | `iwz_amb_pa_tock` | PA1 long-case clock tick-tock | 2.0 | loop | A long-case clock ticking and tocking once a second, deep wooden tick with a soft brass spring, marble salon, seamless loop of two seconds. | bomb timer | F+6 | 3D |
| 342 | `iwz_amb_pa_gas` | PA2 gas hiss and sparker ticks | 8.0 | loop | Three gas chandeliers hissing softly with occasional small sparker ticks, steady dry flame hiss, no pitch, marble salon, quiet, seamless loop. | gas stove | F+6 | 3D |
| 343 | `iwz_amb_pa_fork` | PA3 one tuning fork of the fork wall rings by itself | 6.0 | one-shot | One steel tuning fork struck softly and ringing out a clear G4, a long slow decay over six seconds with a faint wooden frame resonance, marble salon, mid distance, nothing else. | music box | F+8 | 3D |
| 344 | `iwz_amb_pa_gauges` | PA4 dispatch desk pressure gauges ticking | 6.0 | loop | Several brass pressure gauges ticking at slightly different rates, dry small ticks, walnut desk, marble salon, seamless loop. | clock ticking | F+4 | 3D |
| 345 | `iwz_amb_pa_car` | PA5 creak from capsule No. 12 on its cradle, rare tap inside the glass (v2) | 3.0 | one-shot | A copper capsule on an iron cradle creaking slowly as old leather settles, and once a single soft knuckle tap on glass from the inside, marble salon, mid distance. | haunted house | F+5 | 3D |
| 346 | `iwz_amb_pa_whump` | Chandelier lights with a soft whump (v3) | 1.2 | one-shot | A gas chandelier lighting with a soft whump of ignition and a brief rush of flame, marble salon, mid distance. | action film explosion | F+8 | 3D |
| 347 | `iwz_amb_bv_bed` | The Bellows Vault bed | 26.0 | loop | A huge dark volume, pipe air with a faint shimmer of organ overtones, gratings wind, seamless loop, no voices, no melody. | horror drone | -41 dBFS median | 2D |
| 348 | `iwz_amb_bv_blower` | BV1 blower breathing, 6 s cycle | 12.0 | loop | A giant blower breathing slowly, a six second cycle of a deep inhale and exhale with a low organ-like hum, vast vault, seamless loop of two cycles. | dragon breath | F+14 | 3D |
| 349 | `iwz_amb_bv_pipes` | BV2 organ pipes ghost chord, swelling with breath | 12.0 | loop | Organ pipes sounding a quiet ghost chord of C and G, swelling slowly with each breath, vast stone vault, seamless loop, no vibrato, no melody. | church organ hymn | F+8 | 3D |
| 350 | `iwz_amb_bv_motor` | BV3 Lodestar motor and switchgear fifty cycle hum | 6.0 | loop | A large industrial motor humming at fifty cycles with contactor ticks in a yellow switchgear cabinet, vault, seamless loop. | sci-fi hum | F+8 | 3D |
| 351 | `iwz_amb_bv_gratings` | BV4 wind in the high gratings | 8.0 | loop | Wind blowing across iron street gratings high above, a thin whistle and moan with distant echo, vast vault, seamless loop. | storm wind | F+5 | 3D |
| 352 | `iwz_amb_bv_beacon` | BV5 yellow beacon motor tick (v2) | 1.0 | one-shot | A small beacon lamp motor ticking once with a mechanical click and a whirr, vault, mid distance. | emergency siren wail | F+4 | 3D |
| 353 | `iwz_amb_bv_bolts` | BV6 loose bolts rattling in the intake | 2.0 | one-shot | Loose bolts rattling inside a metal intake grille as air draws through, quick metallic rattle, vault, mid distance. | rattlesnake tail | F+5 | 3D |
| 354 | `iwz_amb_bv_motor_slam` | Lodestar motor slams in at power-on | 1.5 | one-shot | A huge electric motor contactor slamming in with a heavy thunk and a rising whine to a steady hum, vast vault, mid distance. | sci-fi power up | F+14 | 3D |
| 355 | `iwz_amb_bo_bed` | The Boneyard bed | 26.0 | loop | A dead-end tunnel, a low draught, metal ticks, far rail hum, seamless loop, no voices, no music. | abandoned tunnel | -44 dBFS median | 2D |
| 356 | `iwz_amb_bo_cassette` | BO1 dying cassette player breakbeat (generated 16 s, slowed to 48 s by tools) | 16.0 | loop | A cheap battery cassette player playing an original dusty breakbeat at ninety four beats per minute through a tiny speaker, drum machine only, no melody, seamless loop. | famous breakbeat | F+10 | 3D |
| 357 | `iwz_amb_bo_fire` | BO2 barrel fire crackle and wood pops | 8.0 | loop | A fire in a steel barrel crackling with wood pops and soft roar, tunnel, seamless loop. | campfire music | F+6 | 3D |
| 358 | `iwz_amb_bo_rats` | BO4 rats and mattress rustle (v2) | 3.0 | one-shot | Small animals scuttling over an old mattress, soft rustles and tiny scratches, tunnel, quiet, mid distance. | horror monster | F+3 | 3D |
| 359 | `iwz_amb_bo_trolley` | BO5 shopping trolley rolls a metre by itself | 4.0 | one-shot | A shopping trolley rolling slowly across concrete with a squeaking wheel and a rattle of its wire basket, tunnel, mid distance. | shopping cart commercial | F+6 | 3D |
| 360 | `iwz_amb_bo_wrecks` | BO6 wreck metal ticking and groaning (v2) | 3.0 | one-shot | Rusted car shells ticking and groaning as metal cools, slow creaks and a ping, tunnel, mid distance. | ship creak | F+4 | 3D |
| 361 | `iwz_amb_te_clock` | TE1 the Terminus clock's mechanism: one heavy tick a second | 2.0 | loop | A large station clock movement ticking once a second, a deep dry mechanical tick with a soft brass ring, in a large paper-walled room with a short dry reverb, seamless loop of two ticks. | bomb timer | F+8 | 3D |
| 362 | `iwz_amb_te_printer` | TE4 the line printer that never stops | 8.0 | loop | A big old impact line printer running without pause, a steady dry chatter of print hammers with a heavier carriage return every two seconds and the soft hiss of fan-fold paper feeding through, in a large paper-walled office room with a short dry reverb, seamless loop, no voices, no melody. | dot matrix modem | F+6 | 3D |

Count, group 9: **121**.

### 8.10 Activities and secrets

Source: 4.11, 3.9, 5.3 and `wiki/strand-tapes.md`. Strand's voice, the Voice's pay-phone lines, the booth's patter and the pay-phone oddities are voice and are not here; this group makes the sounds around them.

| # | Alias | What | Length (s) | Loop or one-shot | Generation brief | Must NOT sound like | Target level | 3D or 2D |
|---|---|---|---|---|---|---|---|---|
| 363 | `iwz_phone_ring` | Pay phone double ring | 2.0 | one-shot | An old electromechanical pay phone bell, a double ring brr-ring with a strong clanging bell and a case rattle, tiled hall, mid distance. Script repeats it three times. | modern phone ringtone | P+0 | 3D |
| 364 | `iwz_phone_pickup` | Handset lifted | 0.5 | one-shot | A heavy bakelite phone handset lifted from its cradle with a clack and a cord rustle, close, dry. | cell phone tap | P-6 | 1P |
| 365 | `iwz_phone_line` | Line hum with the Carrier faintly in it | 6.0 | loop | A dead telephone line hum, steady low hum with faint hiss and a very faint high tone at the edge, close, seamless loop. | dial tone | F+6 | 2D |
| 366 | `iwz_phone_hangup` | Hang-up clunk | 0.4 | one-shot | A heavy handset dropped back on a pay phone cradle with a dull clunk and a small bell tick, close, dry. | call end beep | P-6 | 1P |
| 367 | `iwz_phone_pulse_dial` | Car Barn phone lifted: a number pulse-dialled by itself | 2.0 | one-shot | A rotary telephone dial returning and clicking out pulses by itself, a run of dry ticks with a faint whir, as heard through a handset, close. | modern keypad beeps | P-6 | 1P |
| 368 | `iwz_phone_engaged` | Car Barn phone: engaged tone | 4.0 | loop | A steady engaged telephone tone, a single mid-pitched tone on for half a second and off for half a second, thin and flat as heard through a handset, seamless loop of four seconds. | ringtone | F+4 | 2D |
| 369 | `iwz_voice_splice` | Splice crackle between glued words (v3) | 0.3 | one-shot | A very short crackle and tick of an audio tape splice, a tiny dry pop and a puff of hiss, close, for layering between words. | glitch effect | P-12 | 2D |
| 370 | `iwz_tape_rec_click` | Micro-cassette record button click | 0.3 | one-shot | A small micro-cassette recorder record button pressed down with a mechanical clunk and a tape motor start, close, dry. | camera shutter | P-6 | 1P |
| 371 | `iwz_tape_stop_click` | Micro-cassette stop click | 0.3 | one-shot | A small micro-cassette recorder stop button clicking with a motor winding down to silence, close, dry. | camera shutter | P-6 | 1P |
| 372 | `iwz_tape_hiss` | Tape hiss bed under the voice | 4.0 | loop | Faint steady magnetic tape hiss with a tiny motor wow, very quiet, close, seamless loop, no voice. | vinyl crackle | F+0 | 2D |
| 373 | `iwz_tape_room_van` | Tape 1 room tone: the Channel 9 van | 1.5 | one-shot | The interior of a parked news van, soft electronics fan hum and rain on a metal roof, close, quiet. | news broadcast | F+0 | 2D |
| 374 | `iwz_tape_room_arcade` | Tape 2 room tone: Hole Number Nine | 1.5 | one-shot | A small coffee shop in an underpass, a quiet coffee machine hum and the distant whir of a photocopier, close, quiet. | crowded cafe | F+0 | 2D |
| 375 | `iwz_tape_room_post` | Tape 3 room tone: Police Post evidence cage | 1.5 | one-shot | A small metal evidence cage in a quiet office, a radiator tick and still air, close. | police station | F+0 | 2D |
| 376 | `iwz_tape_room_train` | Tape 4 room tone: a train seat | 1.5 | one-shot | Inside a parked train carriage, soft fan whirr and a faint fluorescent buzz, close, quiet. | train journey | F+0 | 2D |
| 377 | `iwz_tape_room_barn` | Tape 5 room tone: Car Barn | 1.5 | one-shot | A steel workshop shed at night, a distant compressor hum and a single slow drip, empty, quiet, close. | factory noise | F+0 | 2D |
| 378 | `iwz_tape_room_exchange` | Tape 6 and 7 room tone: Exchange | 1.5 | one-shot | A computer hall at night, a low fan wash and soft relay flutter, empty, quiet, close, no beeps. | data center | F+0 | 2D |
| 379 | `iwz_tape_room_cab` | Tape 8 room tone: the cab of the 23:47 | 1.5 | one-shot | The inside of a clean train driver's cab, soft electrical hum and a distant brass band muffled through glass, no melody. | brass band concert | F+0 | 2D |
| 380 | `iwz_notebook_page` | Page of Vayle's notebook | 1.2 | one-shot | An old paper notebook page turned and rustled, dry brittle paper, close, quiet. A low tone is added later. | magic book | P-9 | 1P |
| 381 | `iwz_mural_log` | Mural logged: spray rattle, hiss, register click | 1.2 | one-shot | A spray can rattled twice and hissed briefly, then a small mechanical cash register click, close, dry. | video game achievement | P-6 | 1P |
| 382 | `iwz_stud_knife` | Knife into the zero stud | 0.5 | one-shot | A knife blade pushed into a brass floor stud with a short metal scrape and a clink, close, dry. | sword draw | P-3 | 3D |
| 383 | `iwz_stud_clock_tock` | Six clocks tock once (v3) | 0.4 | one-shot | A single deep tock of a station clock movement, wooden and brass, dry, short, mid distance, used at six positions. | clock chime | P-3 | 3D |
| 384 | `iwz_stud_tick_low` | Low 2D tick for everyone | 0.4 | one-shot | A single low dull tick of a large clock mechanism, felt more than heard, close, dry, no ring. | film heartbeat thump | -18 dB under peak | 2D |
| 385 | `iwz_booth_flash_whirr` | Photo booth flash and whirr | 2.0 | one-shot | A flash bulb popping with a whine of a capacitor then a camera mechanism whirring and clunking, inside a small booth, close. | modern camera shutter | P+0 | 3D |
| 386 | `iwz_booth_strip` | Strip falls into the tray | 1.0 | one-shot | A strip of photographs sliding out of a slot and falling into a metal tray with a flap, close, dry. | printer output | P-6 | 3D |
| 387 | `iwz_booth_breath` | Fourth frame: a close breath behind the player | 1.2 | one-shot | A single slow close breath in an empty small space, quiet inhale and exhale, human, dry, very close, no words. | horror whisper | +5 dB over booth sounds | 1P |
| 388 | `iwz_lostprop_bell` | Lost Property service bell | 0.8 | one-shot | A brass service bell tapped once on a counter, a bright short ding with a small ring, close, dry. | hotel desk bell | P-3 | 3D |
| 389 | `iwz_lostprop_drawer` | Lost Property drawer slides | 0.8 | one-shot | A wooden drawer sliding open on rails with a rumble and a thump at the end, close, dry. | treasure chest | P-3 | 3D |
| 390 | `iwz_locker_clank` | Supply locker latch and clank | 0.8 | one-shot | A steel locker latch lifted and the door clanking open on its hinge, close, dry. | prison door | P-3 | 3D |
| 391 | `iwz_trophy_wheel` | Brass skate-wheel trophy spins down, click (v3) | 2.5 | one-shot | A brass skate wheel spinning on an axle, a bright whirr slowing down over two seconds ending with a click, close, dry. | slot machine spin | P-3 | 1P |
| 392 | `iwz_jukebox_coin` | Needle Drop coin in | 0.8 | one-shot | A coin dropped in a jukebox slot, a clink and a mechanical clunk, close, dry. | arcade coin | P-3 | 3D |
| 393 | `iwz_jukebox_change` | Record changer mechanism swaps the disc | 2.5 | one-shot | A jukebox record changer picking up a vinyl record, a motor whirr, arm swing and a clunk as it sets down, close, dry. | dj scratch | P-3 | 3D |
| 394 | `iwz_jukebox_needle` | Needle drop on the groove | 1.2 | one-shot | A record needle landing on a vinyl groove, a soft thump and a short burst of surface hiss, close, dry. | record scratch | P-6 | 3D |

Count, group 10: **32**.

### 8.11 UI sounds and server-drawn HUD notices

Source: 4.12, `10-EMOTES.md` 4.6 and `09-TAB-AND-HUD.md` section 3. One dry family of relay and solenoid clicks and sine blips on the C pentatonic (C, D, E, G, A). Peaks are those of 3.10 (open -34, tick -42, confirm -34, Tab open -36, Tab close -40 dBFS). Rows under 0.5 s are generated at 0.5 s and trimmed. If two attempts fail to give a clean sub-100 ms click, the family is built from the generated relay click plus a synthesised sine blip by the bank tools. All are 2D local sounds.

| # | Alias | What | Length (s) | Loop or one-shot | Generation brief | Must NOT sound like | Target level | 3D or 2D |
|---|---|---|---|---|---|---|---|---|
| 395 | `iwz_ui_wheel_open` | Emote wheel open: relay click then rising C5 to G5 | 0.18 | one-shot | A dry relay click followed at once by a soft two-note rising electronic chime, C5 to G5, very short, no reverb, quiet, plain. | modern ui chime | peak -34 dBFS | 2D |
| 396 | `iwz_ui_wheel_tick` | Emote wheel hover tick | 0.02 | one-shot | One tiny mechanical relay tick, extremely short and dry, a single crisp transient with no reverb and no tone, very quiet. | click track | peak -42 dBFS | 2D |
| 397 | `iwz_ui_wheel_confirm` | Emote wheel confirm: ticket-punch ka-chunk with C5 blip | 0.12 | one-shot | A ticket punch closing with a crisp ka-chunk and a short sine blip at C5, very short, dry, no reverb. | video game confirm | peak -34 dBFS | 2D |
| 398 | `iwz_ui_tab_open` * | Tab screen opens | 0.15 | one-shot | Short relay chatter followed by two quick data blips, E5 then A5, sine tones, dry, no reverb, quiet. | modern ui whoosh | peak -36 dBFS | 2D |
| 399 | `iwz_ui_tab_close` * | Tab screen closes | 0.10 | one-shot | Two soft quick data blips reversed, A5 then E5, with a tiny relay click, dry, quieter than the open sound. | modern ui whoosh | peak -40 dBFS | 2D |
| 400 | `iwz_ui_tab_page` | Tab page change tick | 0.08 | one-shot | A single dry solenoid click with a tiny low blip, very short, no reverb, quiet. | click track | peak -42 dBFS | 2D |
| 401 | `iwz_ui_ticker` | Timetable ticker: quest line appears | 0.20 | one-shot | A short burst of printer-like relay chatter ending in one soft blip at G5, dry, no reverb, plain. | notification ding | peak -36 dBFS | 2D |
| 402 | `iwz_ui_mark` | Inspector's mark: two blips, lamp pulse | 0.40 | one-shot | Two short low electronic blips and a dull lamp-relay pulse, serious, dry, no reverb, quiet. | danger alert | peak -30 dBFS | 2D |
| 403 | `iwz_ui_fine` | Fine taken: falling blip and stamp tick | 0.30 | one-shot | A short falling electronic blip with a small rubber stamp tick, dry, no reverb, quiet. | failure sting | peak -34 dBFS | 2D |
| 404 | `iwz_ui_handle_lockon` | Handle picked up: rising lock-on blip | 0.30 | one-shot | A short rising electronic blip ending in a firm relay click, dry, no reverb, quiet. | item pickup jingle | peak -34 dBFS | 2D |
| 405 | `iwz_ui_handle_blip` | Handle picked up: small blip to everyone | 0.15 | one-shot | One very small soft electronic blip around G5, short and dry, with no reverb, plain and very quiet. | notification ding | peak -42 dBFS | 2D |
| 406 | `iwz_ui_ticket_valid` | Validated Ticket earned: punch blip | 0.25 | one-shot | A ticket punch click followed by a short bright sine blip around E5, very short, dry, no reverb, plain and quiet. | reward fanfare | peak -34 dBFS | 2D |

Count, group 11: **12**.


### 8.12 Counts

| Group | Heading | Rows |
|---|---|---|
| 8.1 | Transport (the Capsule Post) | 32 |
| 8.2 | Power, quest steps, the Pack-a-Punch teleport and the Terminus | 38 |
| 8.3 | The four wonder weapons and their upgraded forms | 69 |
| 8.4 | The four new perk machines | 19 |
| 8.5 | The Night Inspector | 30 |
| 8.6 | The Rollers | 16 |
| 8.7 | Doors | 17 |
| 8.8 | The four traps | 20 |
| 8.9 | Ambience per zone | 121 |
| 8.10 | Activities and secrets | 32 |
| 8.11 | UI and server-drawn HUD notices | 12 |
| | **Total rows** | **406** |

Variants: 106 extra takes are needed on top of the rows (rows marked "(vN)"), so 512 files are produced.
97 rows are loops and the rest one-shots. 53 rows are 2D and 353 are 3D. This list replaces the estimate
of 6.2 for the sound-effect part of the bank (about 420 aliases there, with music and stock re-banked sources
counted in): music, voice and stock sources are not counted here.

### 8.13 Format the sound bank needs

The facts come from the research files and this chapter. Package SFX1 re-checks every one against the bank
tools' own documents before the first file is kept; a fact that no longer matches is corrected here, not worked
around. The bank holds FLAC (F9). Stock sources run at 12 to 48 kHz. The FLAC must use 1024-frame blocks, or the
sound is silent in game (F9). A mono source measures about 3.5 dB quieter in the game, because the game sums
channels (F4), so anything played as music, a 2D bed or a 2D cue is stored dual-mono, and spatial one-shots and
spatial loops are stored mono. A dedicated server returns 0 for the length of a mod-bank sound (F6), so every
row's length goes in the length table (6.4), filled from the final file. Loops are cut at zero crossings and
tested for a seamless join before they are kept.

- Generated files are converted, trimmed, loudness-normalised to their target and written with the project's
  bank tools (`iwz_audio_bank.py`, `iw7_sab.py`), never by hand. The generator's stereo output is downmixed to
  mono for 3D rows (a result whose level drops more than 1 dB in the downmix is regenerated) and duplicated to
  dual-mono for 2D rows. True peak -1 dBTP or lower, no DC offset.
- Level: a first pass sets each file's peak or RMS from its row; the in-game capture (P2) then sets the final
  gain. The manifest beside the files stores each file's measured length, peak, loudness, sample rate and channel
  layout, the row's target, the prompt-influence value used and the calibration offset found in game.
- Sample rates (starting values from the size basis of 6.2, to be confirmed by measuring): beds 22.05 kHz, loops
  and scatter sets 16 kHz, cues and UI 32 kHz, anything with a bright top (bells, whistles, glass, flash) 44.1 kHz.
- Rows shorter than 0.5 s are generated at 0.5 s with the sound at the start, then trimmed. Rows with a fixed
  length (the diesel at 2.65 s, the copier cycles at 8, 10 and 12 s, the 12 s polisher lap) are generated a little
  long and cut to the exact length, and a loop whose length is part of the design is verified to the sample.
- Loops: the generator's seamless-loop option is requested; the file is then cut at zero crossings and the join
  is tested (the 100 ms envelope across the join within 1 dB of its neighbours, and no sample step). A bed is a
  26 s clip (24 s body plus a 2 s head) used by the retrigger method of F2 with its twin alias on the second
  channel. A loop that fails the test twice is cross-faded by the tool and judged again.
- Pitched rows (the bells, the chimes, the door chime, the relay tone, the microphone whine, the tuning fork)
  are measured for pitch; more than 30 cents off is corrected by shifting.
- Prompt influence: starting values of 0.7 for exact physical one-shots, 0.5 for loops and beds, 0.8 for the UI
  family. These are first guesses. The first batch (8.15) records the value used for every kept file, and the
  starting values change only from measured results.

### 8.14 Credit estimate

The cost per generation is not known here and is not guessed. Before the first batch the package reads from the
service what one generation costs (per generation or per second of audio, as the service states) and the
remaining credits (the subscription call named in the project's notes; the key is never printed), then
multiplies.

| Quantity | Value |
|---|---|
| Rows | 406 |
| Files to produce (rows plus variants) | 512 |
| Assumed attempts per file | 1.6 (one first try, about three in five regenerated once) |
| Generations, one take per row | 406 x 1.6 = 650 |
| Generations, with variants (the figure to plan with) | 512 x 1.6 = 819 |
| Audio requested (minimum 0.5 s per file) | about 1,590 s for the files, about 2,544 s at 1.6 attempts (about 42 minutes) |
| Batches of 10 | about 82 |
| Cost in credits | generations (or seconds) times the price read from the service. Not estimated here |

The rule, from `12-BUILD-PLAN.md` (package SFX1): the plan gives 30,000 credits a month, renewed on the 9th.
Before every batch the package reads the remaining credits and stops if the batch would leave fewer than 5,000.
Batches of at most 10 sounds. Each result is measured for length, peak and loudness against the target in its
row, and judged by a second listener against "must NOT sound like". A rejected result is regenerated at most
twice; then the row's brief is rewritten. A call that may have succeeded (a timeout, a lost reply) is never
repeated until the account's generation history has been read to see whether it ran. If the monthly credits run
out the package stops and carries the rest to the next month, in the order of 8.15 first and then by group.

### 8.15 The 30 rows to generate first

The first playable build is the grey blockout of `12-BUILD-PLAN.md` (wave 1): the 19 zones with their doors,
power, the six stock perks, the Third Rail trap and the quest steps. These 30 rows (marked with an asterisk in the
tables; 32 files with the variants, about 51 generations, about 140 s of audio) give it its first complete sound
without any weapon or enemy work.

| Why | Rows |
|---|---|
| power, the first act | `iwz_power_breaker_slam`, `iwz_power_diesel_start`, `iwz_power_rectifier_strike`, `iwz_amb_ch_g2` |
| the clocks of step 1 | `iwz_clock_wind_ratchet`, `iwz_clock_hands_sweep`, `iwz_clock_bell_fare`, `iwz_clock_bell_platform`, `iwz_clock_bell_barn`, `iwz_clock_bell_parlour` |
| the board, the brightest object | `iwz_board_flap_round`, `iwz_board_flap_digit` |
| the levers and the cab | `iwz_lever_clack_right`, `iwz_lever_buzzer_wrong`, `iwz_cab_relay_slams`, `iwz_train_door_chime`, `iwz_train_doors_close`, `iwz_tele_arrive_chime` |
| the one trap of the blockout | `iwz_trap_rail_start`, `iwz_trap_rail_loop`, `iwz_trap_rail_kill` |
| the four doors on the shortest way to power (D1, D2, D11, D12) | `iwz_door_d01_stair_debris`, `iwz_door_d02_hoist_stair`, `iwz_door_d11_stair_gate`, `iwz_door_d12_gantry_door` |
| the three beds a first walk crosses | `iwz_amb_cordon_bed`, `iwz_amb_fare_bed`, `iwz_amb_ch_bed` |
| the Tab screen | `iwz_ui_tab_open`, `iwz_ui_tab_close` |

The first batch of ten is chosen from these and doubles as the test of the method: it covers a loop (a bed), a
pitched bell, a sub-second click, a long one-shot and a 2D row, so every rule of 8.13 is exercised before the
rest is generated.

### 8.16 Rows this list adds beyond the cue sheets

No chapter gave these a sound; they are needed for the mechanism to be heard, and each is a decision of this
section.

| Where | Added |
|---|---|
| 8.1 | the address dial's click, the junction clack, blowback suction, the hatch lamps ticking to amber, the plate arrow turning, the hatch ready tick, the empty-tube hoom and the six refusal tails of 4.6 (including REST) as separate files |
| 8.2 | the relay tone of the levers, the four board sounds as files, the lever springback and vent clang, the cooldown lamp-out thud, the car doors the Conductor pulls shut |
| 8.3 | Live Rail: build, stake into a body, player shock, reload, upgraded link, red chain; Dispatcher: stamped label, empty pad, puff, pad change, flight whistle, return whistle, message cylinder, desk drawer, the 3 s bellows refill after a send; Top to Bottom: ALL STAND whistle and shuffle, reload, stash lid, dropped can, upgraded spray; Exact Change: upgraded reload and token skip |
| 8.4 | each new perk machine's idle, purchase and effect sounds, the thirteenth-hit bell, the forgiven hit, the Bon Voyages dash, and the Double Takes ready tick |
| 8.5 | the plate lifting and going down, the scuttle, the paper ribbon, the lamp closing again, hits on the glass and on the tunic, the slip, the reel, the pile pickup |
| 8.6 | trip, slide, get-up, spin, push-off, the stop skid and the skate throw |
| 8.7 | one distinct opening sound for each of the 17 doors (the chapters gave only the stock purchase) |
| 8.9 | the copier events, the Terminus clock and line printer, the Cordon feedback jump, the second pump failing, the chandelier whumps, the tape drive spin-up, and the three shared hum sources |
| 8.10 | the tape recorder's clicks and hiss, the seven tape room tones, the notebook page, the zero stud's knife stroke, the Needle Drop mechanism, the locker, the trophy wheel, the Car Barn phone's pulse dial and engaged tone, the splice crackle for the Voice's glued words |
| 8.11 | the Tab page-change tick, the timetable ticker, the Inspector's mark, the fine, the Handle and Validated Ticket blips |

The Rollers' whoops (5.6) are moved here from the voice todo, because the round-start cue sheet needs them at
once; the other non-speech vocals of 5.6 stay in the voice todo.
