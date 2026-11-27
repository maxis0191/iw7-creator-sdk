# A3b: the goods of COPY STOP and HOLE NUMBER NINE (worker A3b, 27 Nov 2026)

Status (27 Nov, end of the work package): both shops dressed and checked offline (`studio check` ok, reach 61/0, records 494);
**one live pass (pass 1)** shot ON and OFF with the darkness fix; round 1 of fixes is built and checked but **not shot**: the second
live start was refused twice by Studio's disk floor (C: 31.5 GB free, floor 34.8 GB; nothing of mine to sweep, the space is other
workers' live work folders younger than 12 h). Next step: `python film\goods_pass_b.py C:\studio-data\sz\film\arcade\goods_b\pass2`
once the disk allows it.

## Files
- `tools-source/iwzmap/station_zero/film/goods_copy_stop.py`, `goods_hole_nine.py`: `add(m, anchors)`, one layer `goods_<shop>` each,
  ids `<shop>__<kind>__<nn>[__part]` (one id stem = one ITEM a player would name).
- `film/goods_kit_b.py`: the kit (items, our materials, flush signs and decals, oriented boxes as meshes, paper stacks, reams, doughnut rings).
- `film/goods_score_b.py`: QUALITY-BAR rules 5, 6, 7 per shop from the document's layers.
- `film/goods_pass_b.py`: one live pass in one command (start, power on, shots, power off, shots, stop, sheets, blind crops, luma).
- `film/art_goods_b/make_pictures_b.py`: every picture of ours, drawn with PIL (period fonts of `C:\Windows\Fonts`), into
  `C:\studio-data\sz\film\art\arcade\goods_b` (binary, not in git).
- Document: `C:\studio-data\sz\film\arcade\goods_b\doc` = `python film\arcade_doc.py <doc> --only copy_stop,hole_nine`.

## What each shop holds
**Copy Stop** (paper is the goods). West window, a display strip along the glass (one clip, y 4307..4342): the drawing-tube rack
(blueprint rolls and kraft tubes), the light table lit from below with a pencil elevation of this row of shopfronts on vellum and her desk
lamp (the shop's one practical, baked, `emergency`), a pyramid of wrapped reams and more under the easel, the easel with a white-on-blue
station section print; two of her cards on the glass. East window: reams along the glass, three spiral-bound sample books standing open,
a sample board hung on chains from the transom (copies, a card, a programme), the two other cards. Blueprint bay: the diazo machine on
the plan chest with a long print out of its feed lying on the chest and hanging down the drawers, rolls on the machine, a paper stock shelf
on the west wall (no floor footprint). Copiers: copies in both output trays, an original on each lid, eight reams and an opened ream
between them, the TONER drum west of copier 1. Counter, west to east: guillotine (blade raised) with cut sheets, spiral binder, the gala
programmes (Zero Line roundel, 047) in three stacks and one loose, the wire tray of jobs with her ticket, the rubber-stamp tree, stapler,
laminator with a card half out, the blue till; behind it the price board (A1's) and her two notices pinned. Pigeonholes: five dividers,
one job a hole (envelopes and stacks), a few already collected; in the front hole of the third shelf the forty-copy job, its top sheet
the memo (our own material: typewriter texture, the LODESTAR dial mark, red COPY 1 OF 40). Photo booth: lettering band on its front
and its curtain side (lit), the price plate by the slot, the sample strip of four painted faces in its frame, the stool seat inside, a
strip face down on the floor at the curtain.

**Hole Number Nine.** Serving counter (open to the hall), west to east: a cake stand with honey rings under a glass dome, the napkin
dispenser, two sugar pourers, Strand's order (a pink dozen box, the kraft bag on it with the shop's sticker, the hand-written ticket
taped on), the bell, two stacks of paper cups and a stack of saucers, the till, the four gala trays stacked under film with a card with the
Zero Line roundel and 047 propped against them; two cards on the counter's front (eye level) and two hanging in the hatch. Display case:
a three-tier glass rack (chrome posts, glass shelves and front) with seven trays of rings, chocolate (the stock `food_donut`), pink and
honey (our authored rings), some gone; the steel urn and the second pot on its end. Back wall: A1's menu and today boards, the
television on Channel 9. Inside counter: a plate with a ring left on it, a mug, sugar, napkins, the pink boxes folded flat and stacked, two
made up. East wall: a bakery rail rack, six rails, five trays of what did not sell, three made-up boxes on its top.
Round 1 added: Copy Stop's paper tower (four shelves of white and pastel reams in the west window), a ten-bin sorter on copier 1,
three drawings pinned over the copiers; Hole Number Nine's countertop pastry case at the hatch and white liners under every tray.

## Proof
- `python -m studio check C:\studio-data\sz\film\arcade\goods_b\doc` (`goods_b\check2.json`): ok true, reach 61 sources 0 failures,
  the arcade one nav region (1,461 cells, no island), no WALKABLE_OFF_NAV in the arcade, `build.networked_entities.total` **494** (= the
  shell). Warning of mine: CAMERA_BLOCKED on the shell's `arc_hole_nine_inside` (its eye stands 17 behind the glass rack: request 1).
- Pass 1, live, real power-on (Studio pointed at this worktree's SDK: `goods_pass_b.py` writes `studio_goods_b.json` with `sdk` = this
  worktree's `tools-source/iwzmap` and sets `IWZ_SDK` = the worktree; `live power on` settles 15 s before the shots): sheets
  `C:\studio-data\sz\film\arcade\goods_b\pass1\sheet_on_{0,1,2}.jpg`, `sheet_off_{0,1,2}.jpg`, blind crops `blind_on.jpg`, `blind_off.jpg`,
  mean luma of every frame in `pass1\pass.json`. ON is clearly brighter than OFF at every camera (mean luma of 255): arc_copy_stop_front
  42.1 / 16.0 (0.165 / 0.063), arc_hole_nine_front 40.4 / 13.1, arc_east_long 36.7 / 15.9, copy_stop_memo_close 64.0 / 5.4. Live start 251 s.
- Pictures: 33 of ours (Copy Stop 23, Hole Number Nine 10; the programme cover also serves the gala trays' card), under 30 a shop;
  contact sheet `C:\studio-data\sz\film\art\arcade\goods_b\sheet_pictures.jpg`. Own materials 13 (B.material).

## Score (`python film\goods_score_b.py`, round-1 document)
| shop | items (stock / authored) | rule 5 trade share (stock props only) | rule 6 most copied; filler stock models | rule 7 distinct per 100, shelf goods excepted (all) |
|---|---|---|---|---|
| copy_stop | 160 (14 / 146) | 82.5 % pass (85.7 %) | authored ream x64 (40.0 %); 0 pass | 64.8 pass (25.6) |
| hole_nine | 171 (125 / 46) | 93.0 % pass (98.4 %) | food_donut x114 (66.7 %); 0 pass | 68.4 pass (17.5) |

Definitions in the script's header: an item = one id stem; shelf goods = rings, reams, jobs, rolls, tubes, programmes, ring trays,
made-up boxes. The most copied model of each shop is its own trade good (as the stock market's bottles), never a carton.
Objects: Copy Stop 330 (73 boxes, 195 meshes, 14 props, 21 signs, 18 decals, 1 light, 8 materials); Hole Number Nine 365 (145 boxes,
82 meshes, 125 props, 8 signs, 5 materials, no light). Distinct models (items): 41 and 30.

## Stock models used (each looked at with `store show`)
`cp_town_blueprint_teleporter_roll` (a plain blue print roll: rack, machine, shelves), `cp_town_cash_register` (old blue register, Copy
Stop's till), `p7_light_lamp_desk_vintage_01_on` (the desk_lamp fixture), `food_donut` (cp_town's chocolate ring with sprinkles, 2.4
across, scaled 1.6), `park_cash_register` (Hole Nine's till), `p7_diner_table_napkin_clean`, `ma_cup_stack`, `cup_paper_open_iw6`,
`p7_cup_coffee_mug`, `misc_coffee_machine_pot` (the second pot), `ng_plate_03` (plate with crumbs), `zmb_tv_crt_01` (our Channel 9
picture over its screen, emissive). Looked at, not used: the iw6 snack-packet doughnuts (a wrapper), `office_paper_stack01_iw6` (aged
manila), the flat `cp_town_blueprint_*` sheets (stock quest drawings), `food_trash_bag_paper_01` (a trash model), `metal_serving_tray_01`
(compartment tray), `container_food_coffee_shop_flavor_01` (a modern syrup rack). No stock copier, ream, stapler or urn exists.

## Authored, simple (static, render-only; a clip box where it stands on the floor)
Reams (an oriented box, wrapper material in white and three pastels), paper stacks (edge material, printed top sheet), the forty-copy
job (memo material on its top face), programmes, envelopes, the diazo machine, the light table (emissive top, vellum drawing), guillotine,
spiral binder, laminator, stapler, stamp tree, toner drum, sorter tower, tube rack, paper tower, easel, sample books and board,
pigeonhole dividers, the booth stool seat, the face-down strip; doughnut rings (a 144-triangle torus in our honey and pink glazes), trays
with white liners, the glass rack, the countertop pastry case, the urn, sugar pourers, the bell, saucers, the order (box, bag, ticket),
the gala trays under film, the rail rack, pink boxes flat and made up.

## Pass 1: what the frames show, and the round-1 fixes (built, checked, NOT yet shot)
Blind question, fascias cut away (`pass1\blind_on.jpg`): Copy Stop reads as a bright white office with a carved chair (the wheel), a lit
table and an easel: **not** a copy shop. Hole Number Nine reads as a pink cafe counter with menu boards; its rings do not show from the
hall. Neither passes from 800 units in pass 1. Five largest differences from the target per shop, and round 1:
- Copy Stop: (1) everything under z 14 hides behind the window riser (the ream pyramid was invisible) -> the paper tower, reams up to
  z 100; (2) the copiers show no paper -> the sorter, copies in every bin; (3) white empty walls -> three drawings pinned over the copiers;
  (4) the easel print small and low -> 56 x 28 at z 47..75; (5) window cards illegible from the hall -> 20 x 12.5. The memo camera re-aimed.
- Hole Number Nine: (1) rings invisible from the hall (back of the shop, pink on pink) -> the countertop pastry case at the hatch, eye
  height, honey and chocolate rings, a lit strip; (2) pink rings vanish in the pink light -> white liners; (3) the back rack in shadow ->
  request 4; (4) the counter's small goods crowded -> respaced; (5) the TV small on the back wall: kept (the shell's shelf).

## Requests to the shell owner (A2)
1. `arc_hole_nine_inside` (-1810, 4440, 60) stands 17 behind the display case at the glass rack's height: move it to (-1730, 4440, 66)
   yaw 200, or use `hole_nine_interior` of my layer.
2. Photo booth: remove `pb_seat` (a rubber box 0..20); my stool seat (z 20..23) then stands on its own post instead of on the box.
3. `cs_planchest` reaches y 4420, 45 from the wheel (the brief's 64 rule): shorten it to y 4392.
4. Hole Number Nine's racks are in shadow: turn the downlight at (-1830, 4412) into a spot aimed at the rack front; no new light
   (the shop is at 4 lights, a fifth fails rule 9).
5. The copier bodies read as beige boxes behind the window riser: a taller body (z 0..44) with a document feeder, or the green bar raised.
6. The signed publicity photograph (later lot): its space is left free on Hole Number Nine's partition between the menu (x -1949..-1897)
   and the OPEN neon: x -1893..-1868, z 100..126.

## Decisions the brief did not dictate
- The four passport photographs are painted with PIL (invented, cartoon-simple faces): the image generator was out of quota until
  28 Nov 01:00. Its prompt is ready (`art_goods_b/prompts/booth_faces.prompt.txt`) for a photographic redo.
- PLACEHOLDER words, marked in the file names: `mat_cs_memo_PLACEHOLDER.png` (COPY 1 OF 40), `mat_h9_ticket_PLACEHOLDER.png`
  (STRAND - TO COLLECT), `cs_toner_PLACEHOLDER.png` (TONER). Every other word is the copy file's, or canon (047, the marks).
- Small paper that must read close up (memo, programme, ticket) is a world material on a box face (512 px), not a sign (8 px a unit).
- No light in Hole Number Nine (rule 9); Copy Stop's one practical is the desk lamp on the light table (baked, emergency).
- The gala trays carry a card with the programme cover (Zero Line roundel, 047): caterer and printer worked the same night.
- Extra cameras in my layers: `copy_stop_far`, `hole_nine_far` (776 from the fronts: the blind question), `copy_stop_window_close`,
  `copy_stop_interior`, `hole_nine_interior`, `hole_nine_back_wall`.
