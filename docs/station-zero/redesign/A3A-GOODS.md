# A3a: the goods of Needle Drop and Heel & Key (worker A3a, 27 Nov 2026)

Files: `tools-source/iwzmap/station_zero/film/goods_needle_drop.py`, `goods_heel_key.py`, the shared `goods_kit_a.py` (ids, flat goods,
authored meshes), `goods_score_a.py` (rules 5, 6, 7), `goods_pass_a.py` (one live pass), pictures `film/art_goods_a/make_goods_pictures.py`
(PIL) with the image prompts `art_goods_a/prompts/` and `gen_raw.sh`.
Document: `python film\arcade_doc.py C:\studio-data\sz\film\arcade\goods_a\doc --only needle_drop,heel_key` (STUDIO_ROOT=C:/studio).
Pictures (binary, not in git): `C:\studio-data\sz\film\art\arcade\goods_a\` (contact sheet `contact_goods_a.jpg`, in-game pixel preview
`preview_ingame_px.jpg`).

## What each shop holds

**Needle Drop** (layer `goods_needle_drop`), as Gil Amory left it at 23:30:
- Window: the film's one-sheet (`poster_station_zero.png`, FILM-LAYER item 2) and the rink's Roll-In poster (`lightbox_orbit.png` as paper)
  taped inside the glass at the two ends; a two-step "new this week" riser in black and orange with four new 45s (stock
  `cp_town_45_record_01..04`), three LPs and the card NEW 45s IN STOCK; behind it the window rack: three lipped rails of face-out sleeves;
  the card WEEKEND TAPE RENTAL on the glass.
- The record bins (the shell's island): four stacks of LPs read from above by their edges, a face-out sleeve at both ends of each stack
  (browsed from both sides), divider cards with orange tabs, two sleeves pulled half out.
- The sleeve wall (the shell's carcass): on each board a block of LPs filed spine out and two sleeves face out; two more on top.
- High rails of face-out sleeves on the west wall, two on the partition, one on the east wall over the counter.
- The rental shelf on the partition: three boards of VHS boxes (the six rental titles, the film's own box once, FILM-LAYER item 7),
  seven gaps: what was out on rent that night. The card WEEKEND TAPE RENTAL over it.
- The cassette wall: two racks of cassettes face out (the eight albums' cassette editions), the card BLANK C-90 CASSETTES, four 45s pinned.
- The counter: the register, the dubbing deck (a reel-to-reel), the EMPTY case of the party tape lying open with its J-card in the keeper's
  marker, the listening turntable and its headphones; the card USED LPs BOUGHT on the counter's face.
- One milk crate of records by the jukebox (a crate by its model name: counted as filler). The jukebox is the shell's (left as is).

**Heel & Key** (layer `goods_heel_key`), as Tomas Brill left it:
- Counter (what the hall sees through the slot under the shutter): the key carousel with stock keys on its hooks; the board of key blanks
  on its stand, one hook empty and tagged "0"; a pair of shoes and a pair of boots waiting with their claim tags; the price board
  (`board_heel_key.png`) on a stand; polish tins and a can of dressing; the four cards on the counter's face.
- Bench under the shell's work lamp: the key machine, the bench grinder, the plaster mould of the Dead-Man's Handle, hammer, pincers,
  glue brush, eyelet setter, a jar of nails.
- Pegboard over the bench: three shelves on brackets; four pairs never collected on the lowest, each with its claim tag (with the two on
  the counter: the six tags of the copy, one each); a row of six lasts; the drawers of heel tips (one drawer pulled, the tips in it) and a
  toolbox. Laces for sale and blanks on two hooks beside the bench. The marksman buy is left clear.
- Lasts shelf: nine lasts on three boards, polish tins, a can of dressing.

## Authored and simple (said plainly)
- LP sleeves, VHS boxes, cassette racks, the rails: a thin box with our picture on its face (decal). The stacks in the bins and the
  spine-out blocks: a black box with a picture of edges or spines.
- Key machine, bench grinder, key carousel, drawers of heel tips: boxes and cylinders (`goods_kit_a.py`), simple, a few dozen triangles.
- Shoe lasts: a lofted foot form and a leg cone, 260 triangles.
- The mould of the handle: two plaster blocks, the lower one built around its cavity (a grip channel, a knob pocket at one end, a boss
  pocket at the other, a brass-coloured stain in the channel), the upper one lying beside it. Simple: no handle is in it.
- All static. Nothing moves, nothing is usable.
- Heel & Key's front rail (round 2): three pairs hung by their laces from hooks under the shutter's bottom rail, each with its claim tag.
  With the two pairs on the counter and the one on the pegboard, the six tags of the copy hang one a pair.

## Proof

**Document** `C:\studio-data\sz\film\arcade\goods_a\doc` (shell + the two goods layers). `studio check` (check3.json): ok, reach 61 of 61,
networked entities 494 (the shell's 494: no record added), 48 distinct models all known, no emit problem; the 11 `WALKABLE_OFF_NAV`
warnings are the shell's own (same count on the shell alone, none in the Arcade). Every goods object is render-only except one clip
(the record crate, 16 x 16, in the dead corner by the jukebox).

**Score** (`python film\goods_score_a.py <doc> --md`; items = every object a player would name, authored ones included; props = stock
models only, as QUALITY-BAR part A counted):

| Shop | Count | Props | Rule 5 trade % (45+) | Rule 6 filler % (<8.8), most copied | Rule 7 distinct / 100 (19+) |
|---|---|---|---|---|---|
| needle_drop | items | 111 | 81.1 pass | 0.9, authored:vhs_box x29 pass | 57.7 (15 models / 26 props, shelf goods out) pass |
| needle_drop | props | 13 | 92.3 pass | 7.7, cp_town_45_record_02 x2 pass | 100.0 (5 models / 5 props, shelf goods out) pass |
| heel_key | items | 92 | 83.7 pass | 0.0, cp_disco_subway_locker_key x24 pass | 33.9 (21 models / 62 props, shelf goods out) pass |
| heel_key | props | 61 | 82.0 pass | 0.0, cp_disco_subway_locker_key x24 pass | 32.4 (12 models / 37 props, shelf goods out) pass |

Counts: Needle Drop 238 objects, 111 items, 13 stock props of 10 models, 28 pictures (26 new + A1's one-sheet and Roll-In); Heel & Key
130 objects, 92 items, 61 stock props of 13 models, 14 pictures (13 new + A1's price board). Lights added: 0. Records added: 0.

**Live passes** (`film\goods_pass_a.py`; frames, sheets `sheet_{on,off}_*.jpg`, blind crops under
`C:\studio-data\sz\film\arcade\goods_a\pass<N>\`):
- pass1: built with Studio's default SDK (the main checkout, without the darkness fix): ON equals OFF (mean 0.063 / 0.063). Not usable.
- pass2: the lit-vision variant (`arcade_litview.py`), labelled LIT.
- pass3, pass4, pass5: built with this worktree's SDK (`STUDIO_CONFIG=C:\studio-data\sz\film\arcade\goods_a\studio_goods_a.json`, `IWZ_SDK=`
  the worktree root), the REAL power-on, shot 10 s after the switch: ON 0.14 to 0.19 mean against OFF 0.03 to 0.07 at every camera
  (pass5: `arc_needle_drop_front` 0.170 / 0.067, `arc_heel_key_front` 0.155 / 0.053, `heel_key_counter_close` 0.186 / 0.040). pass5 is current.
- Cameras: the shell's `arc_needle_drop_front`, `_oblique`, `arc_heel_key_front`, `_oblique`, `arc_east_long`; mine
  `needle_drop_window_close`, `needle_drop_counter_view` (the shell's `arc_needle_drop_inside` looks out of the shop at the hall and shows
  none of the goods), `heel_key_counter_close`.

**The blind question** ("what does this shop sell?", fascia cut away, at the 800-unit size: `pass4\blind_pair.jpg`, `pass5\blind_hk_800.jpg`),
my own answer, to be checked by reviewers:
- Needle Drop: yes. A window of colourful square sleeves on three rails, four 45s with coloured labels on a riser, two posters, the
  jukebox glowing behind.
- Heel & Key: weak, not reliably answerable. The hall sees a red counter under a shutter half down: a lamp glow, the key board, small
  tags on dark hanging pairs, a price board too small to read. The goods are there (`heel_key_counter_close` reads plainly: tagged shoes
  and boots, the row of lasts, the key board with the "0" tag, the price board, the work lamp), but the slot between the counter (z 42)
  and the shutter rail (z 72) is 30 units high and the stall has one lamp.

## Differences from the target (`concept\arcade.png`), pass5, largest first

Needle Drop: (1) the target's shop is lit bright and warm inside, ours is dim beyond the window (the shell's light; rule 9 leaves no light
for me); (2) the target's records fill tall shelves seen through a full-height window, our shutter a quarter down cuts the view at z 112;
(3) the bins read as dark boxes from the hall (their face sleeves are low, behind the plinth); (4) the posters glow (emissive 0.6) where
the target's paper is lit by the room; (5) the high rails are seen only from inside.
Heel & Key: (1) the shutter: the target's front is a tall lit window of shoes on shelves; (2) one lamp: the target is lit warm across the
back wall; (3) our shoes are dark models (the only shoe models in the five dumps: a dark pair and black boots), the target's are tan;
(4) the target's pegboard and key carousel stand in the open window, ours sit behind the counter; (5) the lasts shelf faces west and its
south end panel hides its lasts from the hall.
Rounds: round 1 (pass4): posters glow, card moved off the window mullion, Heel & Key shelves lowered into the visible band, one pair moved
to the counter; round 2 (pass5): the tagged pairs hung from the shutter rail. A third round in my layer would not change the Heel & Key
read: what is left is the shell's.

## Requests to the shell owner (A2)
1. **Heel & Key shutter**: `SHUTTER_STOP['heel_key']` 0.5 -> 0.2 (curtain bottom z 120; `hk_stall_clip` to the same height). Purpose:
   the pegboard's lower shelves (z 54, 76: heel-tip drawers, lasts) and the bench (machine, grinder, mould) come into the hall's view.
2. **Heel & Key light**: one warm downlight over the stall, e.g. `fix(m, 'downlight', (-1480, 4365, UNIT_H), kelvin=2600, intensity=1.0,
   radius=0.9)`. The stall has 1 light of its 5 (0.0104 per 1,000). Purpose: the pegboard and counter goods read from the hall.
3. **Heel & Key lasts shelf**: turn it to face south, or drop its south end panel (`hk_lasts_end_a`, y 4350), which hides the lasts.
4. Needle Drop: no change needed. The sleeve-wall carcass is short (62, behind the door leaf); I used the partition for the rental
   shelf and two high rails. The jukebox is left as placed; no light requested.

## What does not exist
- Painted sleeve and tape art: the image tool was out of quota (TOOL-FAULTS FE-A3a-1); the art is procedural graphic design. After the
  quota returns: `art_goods_a\gen_raw.sh`, then `make_goods_pictures.py` (it puts `raw\<prompt>.png` under the same words).
- Nothing moves or is used: the turntable does not turn, the carousel does not spin, the jukebox is silent (no script models from a layer).

## Decisions the brief did not dictate
- Words beyond the copy file: the party tape's J-card says PARTY TAPE / CAR 6 (words of the Needle Drop door card, recomposed); the quest
  tag says "0" (canon). No placed stock model carries words (the stock DISCO HITS / PUNK HITS sleeves and the HORROR magazines were looked
  at and not used).
- The posters inside the glass are emissive signs (0.6) set 0.4 in front of the glass: as lit decals they came out black (pass3), and a
  light would break rule 9 (the unit has 4 of 5).
- Rule-6 filler words: cardboard box, carton, crate, pallet, trash (a VHS box or a toolbox is not filler); the record crate counts as filler.
- Item classes in the ids (`<shop>_<T|S|F|X|P>__<item>__<n>`) decide the score; shelf goods (S): sleeves, tapes, keys on hooks, heel tips,
  the laces card; shoes left for repair are the trade's goods (T).
- The dubbing deck is the stock reel-to-reel: no cassette deck model exists in the five dumps.
- Real-ON frames use a Studio config of my own (the coordinator's route); `goods_pass_a.py` sets it on every call.

## Every model used
Needle Drop: `cp_town_45_record_01..05` (45 singles), `park_cash_register` (1980s register), `cp_town_tape_recorder` (reel-to-reel, the
dubbing deck), `cp_rave_turntable_01` (turntable), `misc_interior_headphones_01_variation` (headphones), `cp_disco_record_milk_crate`
(milk crate of records). The shell's `cp_town_jukebox`.
Heel & Key: `cp_disco_subway_locker_key` (key with fob: the blanks on the carousel and hooks), `p7_54i_gear_shoes` (a pair of shoes),
`boots_civ_miner_01_static` (a pair of boots), `p7_jar_glass_short` (lidded tin: polish), `cp_town_motor_oil` (plain can: dressing),
`dns_tool_hammer01_iw6` (hammer), `dns_tool_pliers01_iw6` (pincers), `p7_tools_jar_glass_bolts` (jar of nails), `misc_paint_brush_01`
(glue brush), `equipment_industrial_rivet_tool_01` (eyelet setter), `toolbox_small01_iw6` (toolbox), `square_hook` (shelf bracket),
`cp_rave_tiki_key_hook_01` (peg hook). Each looked at with `store show` (sheets `C:\studio-data\sz\film\arcade\goods_a\show\`).
