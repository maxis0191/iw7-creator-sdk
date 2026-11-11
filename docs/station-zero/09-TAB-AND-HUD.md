# 09 · THE TAB SCREEN AND THE HUD

In the Maxis design system (`docs/MAXIS.md` of the server repository; exact tokens and their file lines are in
`research/B-maxis-ui.md`). Nothing here invents a second style: the station flavour comes from *content*
(a departure board's words, a network diagram, clocks), the look is Maxis.

## 1. Tokens taken from Maxis (and how each is used here)

| Token | Value | Use on this map's screens |
|---|---|---|
| void | `#07090C` | dimmer behind the Tab screen, 88 % |
| panel | `#0D1218` | panel fills, 90 to 94 % |
| panel-2 | `#131B24` | rows, zone boxes on the diagram, chips |
| line | `#22303D` | hairlines; closed doors on the diagram; idle frames |
| aether | `#34E8D2` | primary accent: top rules, open doors and links, the player's own row, hover |
| amber | `#FFB238` | all data: points, counts, clocks, quest progress; the corner brackets |
| blood | `#E5383B` | the round number; the Night Inspector's mark; downed players |
| violet | `#A266FF` | reserved in Maxis for "Pack-a-Punch / rare": here the Terminus, upgraded weapons, wonder-weapon glyphs |
| bone | `#EEE7D7` | primary text |
| ash | `#8E949C` | secondary text, hints |
| ok | `#6BE675` | done states: power on, a clock wound, a hatch unsealed |
| Fonts | MainExtended (titles), MainBold (labels, chips), MainMedium (body), MainCondensed (metadata), Digital (clocks, counts, round) | as in Maxis; no font ships |
| Canvas | 1920 x 1080, scaled by the engine | |
| Shapes | rectangular panels, 4 px aether top rule, 2 px amber corner brackets (arm 24), 2 px hairline frames that recolour on state | |
| Motion | hover 120 ms, small state changes 80 to 100 ms, cards in 450 ms and out 400 ms | easing is not defined in Maxis; linear is used |
| Voice | terse capitals for labels in the `MAXIS // …` form; plain sentences for help | header: `MAXIS // STATION 0` |
| Languages | every label in English, French and Spanish per player; names, commands and numbers are never translated | |

Not defined in Maxis and decided here: an icon style (single 3 px stroke pictograms in bone with one amber
accent, the same rule as the emote wheel in `10-EMOTES.md`), and a disabled state (text in `line`, 60 % alpha).

## 2. The Tab screen

One screen, three pages. It opens on the Tab key and replaces the stock scoreboard on this map.

### Page 1 · DEPARTURES (the default)

```
+--------------------------------------------------------------------------------------------------+
| [Mx]  STATION ZERO                                   DEPARTURE          23:47      MATCH 00:41:07 |
|       MAXIS // STATION 0 · HALCYON RAPID TRANSIT        12  (blood, Digital 70)  (amber)          |
|==================================================================================================|
|  PASSENGERS                      |  NETWORK                              |  TIMETABLE             |
|  # NAME        POINTS  K  D  R   |   [ zone diagram: 18 boxes joined     |  POWER  G-2      ON    |
|  1 Ana         12 450  88 1  2 * |     by lines, drawn like a transit    |  CLOCKS          2/4   |
|    perks: ● ● ● ● ○ ○            |     map: only horizontal and vertical |   o o . .              |
|  2 Malik        9 020  61 0  4   |     strokes ]                         |  ROAD            --    |
|    perks: ● ● ○ ○ ○ ○   [lamp]   |                                       |  HANDLE          --    |
|  3 …                             |   legend: you, squad, wheel, perk,    |  047 TERMINUS    --    |
|  (up to 8 rows)                  |   Capsule Post and its direction, power     |  POST  BLOW    3/4   |
|                                  |                                       |  ------------------    |
|                                  |                                       |  FOUND                 |
|                                  |                                       |  TAPES 3/8  PAGES 1/6  |
|                                  |                                       |  MURALS 0/5  WHEELS 1/3|
|--------------------------------------------------------------------------------------------------|
|  [1] DEPARTURES   [2] JOURNAL   [3] CARRIED            server name · language · ping               |
+--------------------------------------------------------------------------------------------------+
```

- **Header.** Logo tile 72 px; title MainExtended 40 bone; subtitle MainCondensed 18 aether; the round as
  "DEPARTURE" with the number in Digital 70 blood; the station clock in Digital 46 amber, which reads 23:47
  for the whole match and changes only while a clock is being wound and during the Terminus visit (it then
  shows the Terminus clock); match time in MainCondensed 18 ash.
- **PASSENGERS** (x 120 to 700). One row per player, up to eight (the stock scoreboard has four rows; this
  one is the first place where players five to eight are listed). Row height 76: line 1 = number, name
  (MainBold 24), points (Digital 30 amber), kills, downs, revives (MainCondensed 20); line 2 = six perk
  pips (filled bone if owned, the four new perks have their own pictogram), a wonder-weapon glyph in violet
  if carried, a small lamp in blood if marked by the Night Inspector, a key in amber if carrying the Handle.
  The viewer's own row has an aether 2 px frame. A downed player's name is blood; a spectator's is ash.
- **NETWORK** (x 740 to 1360). The map as a transit diagram, never a floor plan: each zone is a labelled box
  in panel-2; links are 4 px lines (line colour while the door is closed, aether when open); the Capsule Post ring
  is a thin amber loop through its four hatches with one arrowhead showing BLOW or DRAW; small pictograms in
  the boxes: perk (a sweet), wheel (a star, only on the active position), trap, wall weapon, clock (amber
  when wound). Players appear as pips inside the box of the zone they are in (the viewer aether, others
  bone): zone-level only, which is all a team needs and costs almost no data.
- **TIMETABLE** (x 1400 to 1800). The road to Pack-a-Punch as five lines that fill in (`04-PAP-QUEST.md`):
  each line is a label in MainBold 22 and a state in Digital 26 (ash "--" pending, amber in progress, ok
  done). Under CLOCKS, four clock pips in the order Fare Hall, Platform, Car Barn, Parlour. Then POST with
  the direction and the number of hatches unsealed. Then FOUND: the four collections as counts.
- **Footer.** Page chips; server name, the viewer's language and ping in MainCondensed 18 ash.

### Page 2 · JOURNAL (lore fragments found)

Left: a list grouped STRAND'S TAPES 1 to 8, VAYLE'S NOTEBOOK 1 to 6, ZERO KINGS MURALS 1 to 5, OTHER (the
Inspector's ledger, the typed police report, the manifest). Found entries are bone with their title; missing
ones are a `line`-coloured row "NOT FOUND" with the zone name as a hint only after round 15. Right: the
reader, a panel 900 wide with the fragment's text in MainMedium 22, 34 px leading, the date in Digital
amber. What is found is shared by the whole team for the match, and remembered per player across matches
(a per-player file on the server, like the language setting) so the journal fills up over time; a counter
"17 / 25 ever found" sits under the list. Texts are the wiki's (`wiki/strand-tapes.md`,
`vayle-notebook.md`), in three languages.

### Page 3 · CARRIED (what I have and what it does)

Two columns. PERKS: each owned perk with its pictogram, name and one line of effect; for Double Takes the
cooldown as a draining amber bar; for Baker's Dozens the 1 to 13 counter; for Sour Grudges the forgiven-hit
state. WEAPONS: both weapons with upgrade level
(violet tag "PaP 1" / "PaP 2"); for a wonder weapon its variant state: Live Rail's fuse (a red, amber or
green block), Top to Bottom's cans owned, the Dispatcher's stamps out, Exact Change's current fare. Below:
the Validated Ticket if held; the Handle if carried. A player who has never seen a perk or weapon learns it
here, not from a wiki.

### Behaviour

- Opens while Tab is held, as the stock scoreboard does; pages change with 1, 2, 3 or left and right on a
  controller; the mouse is free on pages 2 and 3 for the lists.
- Opening and closing: the panel fades in 120 ms and out 100 ms (short on purpose: Tab is hit in combat);
  no slide. The diagram's player pips move between boxes in 200 ms.
- Never blocks play: no control is frozen.

## 3. The HUD elements the map needs

The stock HUD stays (round, points, ammo, the perk row, revive prompts). The map adds only what its
mechanics need. Positions are in the server-drawn tier's virtual units where that tier draws them.

| # | Element | When shown | What | Elements used (server tier) |
|---|---|---|---|---|
| H1 | **Timetable ticker** | 6 s after any quest state change | one line, top centre under the round: "CLOCKS 2/4", "ROAD SET FOR 047", "047 · TERMINUS · BOARDING" | 1 |
| H2 | **Inspector's mark** | while the viewer is the marked player | "TICKET, PLEASE · FINE 870" in blood, centre top, with a lamp pictogram; pulses once on being marked | 2 |
| H3 | **Fine taken** | 2 s after a penalty fare | "−870 PENALTY FARE" in blood under the points | 1 |
| H4 | **Handle carried** | while carrying the Dead-Man's Handle | a key pictogram, amber, beside the weapon name | 1 |
| H5 | **New perk icons** | while owned | up to four pictograms to the right of the stock perk row | up to 4 |
| H6 | **Weapon read-out** | while a wonder weapon is in hand | Exact Change: "FARE 30" (amber, turning blood as surge pricing climbs). Live Rail: fuse colour block and fences alive "1/2". Dispatcher: stamp pips 0 to 4 (6 upgraded). Top to Bottom: the chosen can's colour block | 1 or 2 |
| H7 | **Baker's Dozens counter** | while owned | a number 1 to 13 beside the ammunition, amber at 12 | 1 |
| H8 | **Capsule Post refusal** | 2 s | the plate text: "TUBE SEALED", "NO CAPSULE", "CHANGEOVER", "INSPECTION" | 1 |
| H9 | **Validated Ticket** | while held | a small punched-ticket pictogram beside the points | 1 |
| H10 | **Double Takes ready / recharging** | while owned | its perk icon (H5) dims and refills; no extra element | 0 |
| H11 | **Zombie count** | always (the servers' existing counter) | "ALIVE 41 / 62" so that the cap is visible and provable | existing |

Worst case at once for one player on the server tier: 1 + 2 + 1 + 1 + 4 + 2 + 1 + 1 + 1 = 14, rounded to 15, plus the servers'
own counter and timers (about 5) = 20 of the project's budget of 24 owned elements per player. Elements are
destroyed when not shown, never hidden (hidden ones still count).

**One allocator for the whole map** owns the 24. Screen states and what each may hold:

| State | Holds | Released while in this state |
|---|---|---|
| playing | H1 to H9 as triggered, counter (20 at most) | |
| emote wheel open (13 elements, `10-EMOTES.md`) | wheel 13, counter 5, H2 and H4 if active (3) = 21 | H1, H3, H5 to H9 |
| terminal or STATION page open (up to 15) | page 15, counter 5 = 20 | all of H1 to H9 except H2; the wheel cannot open |
| map vote | the vote's own elements | everything else, as today |

Admission is by priority (vote, terminal, wheel, mark, the rest); a request that does not fit is refused, never
drawn half. Proof 1 of section 5 reads the count in each state.

Use prompts at machines, doors, clocks, levers and hatches are the game's own hint strings; their texts are
added to the localisation table in three languages. The Terminus has no HUD timer: its clock is in the room.

## 4. What reaches players today, and what needs the Lua route

Facts from `research/B-maxis-ui.md`: server-drawn elements reach every player with no download (text, tinted
rectangles, and images that ship in a zone the client loads; about 24 elements per player; no mouse; the
script can read fire, aim, melee, use and the view direction, nothing else). Lua screens are drawn by the
client and are loaded from a mod only by clients built from the client project's development line (the lab
client, the owner's build); the official client does not load them until that project releases its merged
change, which is outside this project's control. Maxis's own Lua tier has been parse-checked but has never
been rendered on a client.

| Piece | Tier 2: server-drawn, every player, today | Tier 1: Lua, as designed above |
|---|---|---|
| Tab screen | **not possible as a Tab overlay**: the script cannot read the Tab key, and three columns exceed 24 elements. Instead: a fifth page **STATION** in the existing Maxis terminal (`.menu 5`, also `.tab`): the TIMETABLE lines and the FOUND counts as text rows (about 12 elements). The stock scoreboard stays on Tab | the full three-page screen. First thing to prove: replacing the stock scoreboard's menu on Tab (find its menu name with the Lua dump tool; the project's other Lua HUD already restyles stock HUD parts, which shows the approach) |
| Network diagram | not drawn; `.where` prints each player's zone in one line | drawn from rectangles only (no arcs needed: a transit diagram is all straight strokes) |
| Journal | `.journal` lists what is found; `.journal 3` shows a fragment in the reply panel, paged at 6 rows of 44 characters (a tape is 2 to 3 pages) | the reader page |
| Carried | `.carried` prints perks and weapon state as rows | the page |
| HUD H1 to H9 | **all of them**, as listed (text and tinted rectangles; pictograms are small 2D materials shipped in the map's own zone, which every player loads with the map) | the same information as proper Maxis widgets: a card with the aether rule and amber brackets for H1, a blood banner for H2, icons in the stock perk row for H5 |
| Scores for players 5 to 8 | the terminal's SQUAD page already lists all players | PASSENGERS shows eight rows |
| Data from server to a Lua client | n/a | the existing Maxis channel: one new client variable `maxis_t` with a stamped payload written only on change: round, quest states, door bits (17), Capsule Post state, found bits (25), each player's zone index. Scores, kills, downs and revives are read by the client from the stock scoreboard data, so nothing is streamed. Budget: under 1 KB; coalesced to at most one write per player per 5 s, and one server-wide token bucket shared with Maxis's other writes and the wheel's so that the total never passes the project's limit of 24 writes per 10 s with eight players (8 players at one per 5 s is 16) |
| Data from a Lua client to the server | n/a | none needed for Tab (it only displays) |

**Order of delivery.** The server-drawn HUD and the STATION terminal page ship with the first playable map
(they are what the official client can show). The Lua Tab screen is built and proven on the lab client in
parallel and reaches players the day their client can load it; nothing in the map depends on it.

**Said plainly**: on today's official client the owner's "full Tab screen" is **not** delivered. Those players
get the STATION page and the chat commands above, which carry the same information as text. The designed
screen exists for them only when their client can load Lua from a download (capability 1, package CF1).

## 5. Proofs

1. Every server-drawn element: a plan that triggers it and reads back the element count per player (the
   existing `hud_max` measure) staying at or under 24 in the worst case of section 3.
2. Text in three languages for every string, through the existing localisation generator and its check.
3. The Lua screen: layout read as data by the UI dump tool (package U1) with no overlap, clipping or
   off-screen element at 1280 x 720, 1920 x 1080 and 2560 x 1080, for 1, 4 and 8 players; then frames
   judged by independent reviewers against the Maxis tokens.
4. The diagram agrees with the map: generated from the same door list as the map source, not drawn by hand.
5. No reliable-command overflow in a one-hour soak with eight players and the payload changing at its
   fastest rate.
