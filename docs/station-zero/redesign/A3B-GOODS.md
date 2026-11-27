# A3b: the goods of COPY STOP and HOLE NUMBER NINE (worker A3b, 27 Nov 2026)

Status: DRAFT, filled in as the passes run.

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
