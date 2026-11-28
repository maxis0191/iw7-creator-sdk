# A3b: the goods of COPY STOP and HOLE NUMBER NINE (worker A3b, 27-28 Nov 2026)

Status: both shops dressed, three rounds of fixes shot live with the real power-on (passes 2, 3, 4) plus one corrective pass (pass 5:
the ream wall's light). `studio check` ok, reach 61/0, records 494. Not reached: the 800-unit blind test for Copy Stop (its ream wall
still reads dark from the hall: request 7). The passport photographs: see the last section.

## Files
- `tools-source/iwzmap/station_zero/film/goods_copy_stop.py`, `goods_hole_nine.py`: `add(m, anchors)`, one layer `goods_<shop>` each,
  ids `<shop>__<kind>__<nn>[__part]` (one id stem = one ITEM a player would name).
- `film/goods_kit_b.py`: items, our materials, flush signs and decals, oriented boxes as meshes, paper stacks, reams and ream stacks, rings.
- `film/goods_score_b.py`: QUALITY-BAR rules 5, 6, 7 per shop from the document's layers.
- `film/goods_pass_b.py`: one live pass in one command (start, power on, shots, power off, shots, stop, sheets, blind crops, luma). It points
  Studio at this worktree's SDK (`studio_goods_b.json` `sdk` = this worktree's `tools-source/iwzmap`, `IWZ_SDK` = the worktree): the
  darkness fix e9af6d9 is here, not in the main checkout. `live power on` settles 15 s before the shots.
- `film/art_goods_b/make_pictures_b.py`: every picture of ours (PIL, period fonts of `C:\Windows\Fonts`) into
  `C:\studio-data\sz\film\art\arcade\goods_b` (binary, not in git); `prompts/booth_faces.prompt.txt` for the image generator.
- Document: `C:\studio-data\sz\film\arcade\goods_b\doc` = `python film\arcade_doc.py <doc> --only copy_stop,hole_nine`.

## What each shop holds (final)
**Copy Stop** (paper is the goods). West window, built up to eye height behind the riser (one clip, y 4307..4342): the ream wall (open
white shelving, four boards of ream stacks in blocks of canary, salmon, green, blue and white, lit strips under the boards, rolls on top)
which also screens the wheel's stock model from the hall; a full-height diazo print (white on blue: the escalator hall in section)
pinned on a board; the light table (lit top, a pencil elevation of this row of shopfronts on vellum, her desk lamp, unlit); a rack of
tall rolled drawings by the door; a line of finished jobs in bulldog clips across the top of the glass (copies, programmes, prints); two
of her cards on the glass. Over the window head a display light bar (the shop's one practical, baked, `emergency`). East window: reams in
colours along the glass, three spiral-bound sample books open, a sample board on chains, the other two cards. Blueprint bay: the diazo
machine on the plan chest, a print out of its feed over the drawers, rolls, a paper stock shelf on the wall. Copiers: copies in both
trays, an original on each lid, a ten-bin sorter full of copies on copier 1, reams and an opened ream between them, the TONER drum.
Three drawings pinned on the partition over the copiers. Counter: guillotine with cut sheets, spiral binder, the gala programmes (Zero
Line roundel, 047), the wire tray of jobs, stamp tree, stapler, laminator, the blue till; behind it A1's price board and her two notices.
Pigeonholes: dividers, a job a hole; in the front hole of the third shelf the forty-copy job (top sheet the memo: typewriter texture,
the LODESTAR dial mark, red COPY 1 OF 40), a red rubber band and a red tag hanging over the shelf edge (the one red thing in the
pigeonholes: it reads from 140 units, `copy_stop_memo_walkby`). Photo booth: lit lettering band on its front and curtain side, the price
plate, the sample strip of four photographs in its frame, the stool seat, a strip face down on the floor.

**Hole Number Nine.** Serving counter, west to east: a countertop pastry case at the hatch (two trays of honey and chocolate rings
tilted to the hall, a warm lamp strip under its top), napkins, sugar, Strand's order (a pink dozen box, the kraft bag with the shop's
sticker, a canary order ticket "STRAND - TO COLLECT": it reads from 150 units, `hole_nine_order_walkby`), the bell, cups and saucers, the
till, the steel urn (the hatch's foreground), the four gala trays under film with the Zero Line card; a warm lamp strip under the hatch
head; two cards on the counter's front, two hanging in the hatch. Display case: a three-tier glass rack, seven trays of rings (stock
chocolate, our pink and honey), the second pot. Back wall: menu, today board, the television on Channel 9. Inside counter: a plate with a
ring left on it, mug, sugar, napkins, pink boxes flat and made up. East wall: the rail rack, five trays of what did not sell, boxes on top.

## Proof
- `studio check C:\studio-data\sz\film\arcade\goods_b\doc` (`goods_b\check5.json`, final document): ok true, reach 61 sources 0 failures,
  the arcade one nav region (1,460 cells, no island), no WALKABLE_OFF_NAV in the arcade, `build.networked_entities.total` **494** (= the
  shell). Warning of mine: CAMERA_BLOCKED on the shell's `arc_hole_nine_inside` (request 1).
- Live passes, real power-on, sheets `C:\studio-data\sz\film\arcade\goods_b\pass<N>\sheet_on_{0,1,2}.jpg`, `sheet_off_{0,1,2}.jpg`, blind
  crops `blind_on.jpg`, luma per frame in `pass<N>\pass.json`: pass 1 (first dressing), 2 (round 1), 3 (round 2), 4 (round 3), 5 (the
  practical moved to the ream wall). ON is clearly brighter than OFF at every camera of every pass; pass 5, mean luma of 255 ON / OFF:
  arc_copy_stop_front 42.3 / 15.0 (0.166 / 0.059), copy_stop_window_close 55.8 / 19.1, copy_stop_far 37.8 / 16.1; pass 4:
  arc_hole_nine_front 40.6 / 12.9, hole_nine_order_walkby 41.9 / 14.6, arc_east_long 37.0 / 15.7. Live start 183 to 251 s (65 s once).
- Pictures: 38 of ours (Copy Stop 26, Hole Number Nine 12), under 30 a shop; contact sheet
  `C:\studio-data\sz\film\art\arcade\goods_b\sheet_pictures.jpg` (round-0 set). Own world materials 15 (Copy Stop 9, Hole Nine 6).

## Score (`python film\goods_score_b.py`, final document)
| shop | items (stock / authored) | rule 5 trade share (stock props only) | rule 6 most copied; filler stock models | rule 7 distinct per 100, shelf goods excepted (all) |
|---|---|---|---|---|
| copy_stop | 164 (11 / 153) | 92.1 % pass (72.7 %) | authored ream_stack x33 (20.1 %); 0 pass | 77.8 pass (26.2) |
| hole_nine | 151 (104 / 47) | 92.1 % pass (98.1 %) | food_donut x93 (61.6 %); 0 pass | 69.2 pass (20.5) |

Definitions in the script's header: an item = one id stem; shelf goods = rings, reams, ream stacks, jobs, rolls, tubes, programmes,
ring trays, sorted copies, made-up boxes; signs and lamps count in the denominator only. The most copied model of each shop is its own
trade good (as the stock market's bottles), never a carton. Objects: Copy Stop 356 (88 boxes, 193 meshes, 11 props, 37 signs, 17 decals,
1 light, 9 materials); Hole Number Nine 345 (132 boxes, 87 meshes, 104 props, 10 signs, 6 materials, no light). Distinct models: 43 / 31.

## Stock models used (each looked at with `store show`)
`cp_town_blueprint_teleporter_roll` (a plain blue print roll), `cp_town_cash_register` (old blue register, Copy Stop's till),
`p7_light_lamp_desk_vintage_01_on` (her desk lamp, unlit), `ind_light_fixture_led_wall_01_on` (the wall_led fixture: the window light bar),
`food_donut` (cp_town's chocolate ring with sprinkles, 2.4 across, scaled 1.6), `park_cash_register` (Hole Nine's till),
`p7_diner_table_napkin_clean`, `ma_cup_stack`, `cup_paper_open_iw6`, `p7_cup_coffee_mug`, `misc_coffee_machine_pot`, `ng_plate_03`,
`zmb_tv_crt_01` (our Channel 9 picture over its screen, emissive). Looked at, not used: the iw6 snack-packet doughnuts (a wrapper),
`office_paper_stack01_iw6` (aged manila), the flat `cp_town_blueprint_*` sheets (stock quest drawings), `food_trash_bag_paper_01` (a trash
model), `metal_serving_tray_01` (compartment tray), `container_food_coffee_shop_flavor_01` (modern syrup rack). No stock copier, ream,
stapler or urn exists in the five dumps.

## Authored, simple (static, render-only; a clip box where it stands on the floor)
Reams and ream stacks (an oriented box, the wrapper repeating every ream, white and four pastels), paper stacks (edge material, printed
top), the forty-copy job (memo material on its top face), programmes, envelopes, the diazo machine, light table, guillotine, binder,
laminator, stapler, stamp tree, toner drum, sorter, ream wall, window print board, roll rack and rolled drawings, the job line, sample
books and board, pigeonhole dividers, booth stool seat, face-down strip; doughnut rings (a 144-triangle torus, our honey, pink and chocolate
glazes; tilted trays in the pastry case), trays with white liners, the glass rack, the pastry case, urn, sugar pourers, bell, saucers, the
order, gala trays, rail rack, pink boxes; warm and white lamp strips (emissive pictures: they glow, they are not lights of the count).

## The rounds: what each pass showed, what changed
- Pass 1 (first dressing). Blind, fascias cut away: Copy Stop a white office with a carved chair (the wheel) and an easel, not a copy
  shop; Hole Nine a pink cafe counter, rings not visible. Largest differences: goods under z 14 hidden by the window riser; copiers without
  paper; white empty walls; small easel print; illegible cards; Hole Nine's rings deep in the pink room.
- Round 1 (pass 2): a paper tower of pastel reams, the sorter, drawings on the partition, bigger print and cards; Hole Nine's countertop
  pastry case and white liners. Result: colour reams and the blue drawings read; the wheel still the first thing in the west window; the
  pastry case dark inside.
- Round 2 (pass 3), with the lead's reading: the ream wall in colour blocks screening the wheel (screened: yes, at `arc_copy_stop_front`
  and `_oblique`), a full-height diazo print, a roll rack by the door, the line of finished jobs; the red tag on the forty-copy job (reads at
  140); Hole Nine's urn to the counter, warm strips, bigger canary ticket (reads at 150), open case front. Result: the ream wall read black.
- Round 3 (pass 4): lit strips under the boards, no back panel; tilted trays of honey and chocolate rings in the pastry case. Result: Hole
  Nine's rings now read in rows from the hall at the hatch (`arc_hole_nine_front`, `hole_nine_order_walkby`); the ream wall still dark.
- Pass 5 (correction): the practical moved from the desk lamp to a light bar on the window head. Result: the ream wall's boards and tops lit,
  the stack fronts (facing the hall) still dark grey. The cause is light, not goods: the fronts face the hall, and the north lane in front
  of Copy Stop has only dead tubes (`tube_dead_n_0` at x -2620); a light from the hall side is the shell's (request 7).
Blind question now: Hole Number Nine, yes from the front camera (the pastry case's rings, the urn, the menu, the pink boxes). Copy Stop:
from the front, the blue print, the lit light table, the line of papers and the drawings read; the colour of the ream wall does not.

## Requests to the shell owner (A2)
1. `arc_hole_nine_inside` (-1810, 4440, 60) stands 17 behind the display case at the glass rack's height: move it to (-1730, 4440, 66)
   yaw 200, or use `hole_nine_interior` of my layer.
2. Photo booth: remove `pb_seat` (a rubber box 0..20); my stool seat (z 20..23) then stands on its own post instead of on the box.
3. `cs_planchest` reaches y 4420, 45 from the wheel (the brief's 64 rule): shorten it to y 4392.
4. Hole Number Nine's back racks are in shadow: turn the downlight at (-1830, 4412) into a spot aimed at the rack front; no new light.
5. The copier bodies read as beige boxes behind the window riser: a taller body (z 0..44) with a document feeder, or the green bar raised.
6. The signed publicity photograph (later lot): its space is left free on Hole Number Nine's partition between the menu (x -1949..-1897)
   and the OPEN neon: x -1893..-1868, z 100..126.
7. Copy Stop's ream wall (x -2604..-2500, y 4312..4334, z 16..104) is lit from behind only: one of the dead north-lane tubes over Copy
   Stop (`tube_dead_n_0`, x -2620, y 4120) made live, or a panel of the grid near (-2552, 4200) lit, so the wall's colour reads from the hall.

## Decisions the brief did not dictate
- PLACEHOLDER words, marked in the file names: `mat_cs_memo_PLACEHOLDER.png` (COPY 1 OF 40), `mat_h9_ticket_PLACEHOLDER.png`
  (STRAND - TO COLLECT), `cs_toner_PLACEHOLDER.png` (TONER). Every other word is the copy file's, or canon (047, the marks).
- Small paper that must read close up (memo, programme, ticket) is a world material on a box face (512 px), not a sign (8 px a unit).
- No light in Hole Number Nine (rule 9: a fifth would be 0.052 per 1,000); its warmth comes from emissive lamp strips. Copy Stop's one
  practical is the window light bar (moved from the desk lamp in pass 5; the lamp stays as a model).
- A fifth pass beyond the three rounds: a correction of the light only, no change of goods.
- The gala trays carry the programme cover (Zero Line roundel, 047): caterer and printer worked the same night.
- Extra cameras in my layers: `copy_stop_far`, `hole_nine_far` (776 from the fronts), `copy_stop_memo_walkby` (140), `hole_nine_order_walkby`
  (150), `copy_stop_window_close`, `copy_stop_interior`, `hole_nine_interior`, `hole_nine_back_wall`.

## The passport photographs
Passes 1 to 5 carry painted faces (PIL): the image generator was out of quota until 28 Nov 01:00. At 01:02 it made the 2 x 2 grid
`C:\studio-data\sz\film\art\arcade\goods_b\gen\booth_faces.png` (prompt `art_goods_b/prompts/booth_faces.prompt.txt`: four invented,
unremarkable adults, flat booth flash, grey-blue curtain, no text; looked at: no likeness intended or recognised). `make_pictures_b.py`
cuts it into the strip `cs_booth_strip.png`. Pass 6 (`goods_b\pass6`, the same document with the new strip, live start 75 s):
`copy_stop_booth_close` shows the four photographs in the frame under the lit AUTO PASSPORT PHOTOS band; ON 74.2 / OFF 13.7.
