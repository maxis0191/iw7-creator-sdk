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
