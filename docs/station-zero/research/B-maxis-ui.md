# B. Maxis UI design system and delivery routes (research, read-only)

Date of research: 2026-11-10. Repo read: `<server-worktree>`
(HEAD ddbae138, branch claude/heuristic-lamarr-b753dc, same content as main). Abbreviations: `MAXIS.md` = `docs/MAXIS.md`;
`LUA` = `src/mod/ui_scripts/maxis/__init__.lua`; `UIGSC` = `src/custom_scripts/cp/paris_ui.gsc`; `VOTE` = `src/custom_scripts/cp/iw7_map_vote.gsc`;
`ART` = `ops/maxis/make_art.py`. Sibling repos read from `origin/main` with `git show` only (iw7-mod-components, iw7-creator-sdk).

Headline finding: Maxis today has exactly four things: the terminal (`.menu`), the arrival briefing card, a reply toast, and the
map vote. There is **no scoreboard/Tab screen, no emote wheel, no HUD replacement, no radial widget** anywhere in the repo
(grep for scoreboard / emote / radial / wheel gives only stock retail references and the unrelated "magic wheel"). A Tab screen,
HUD elements and an emote wheel would be new work on one of the two existing delivery tiers.

---------------------------------------------------------------------------------------------------------------------------------

## 1. The Maxis design system, exact tokens

### 1.1 Identity and voice (MAXIS.md:16-31)

- Maxis = "Dr. Ludvig Maxis, Group 935 and Element 115". The interface is "a Group 935 field terminal that survived into Willard
  Wyler's films" (MAXIS.md:18-20).
- Logo = "an Element 115 periodic-table tile. Chamfered frame in Aether cyan, atomic number `115` top-left, symbol `Mx`, the name
  `M A X I S`, one electron orbit, amber terminal corner brackets" (MAXIS.md:22-25). Procedural, original, reproducible
  (`ops/maxis/make_art.py`, function `logo()`).
- Voice = "terse terminal labels in capitals (`MAXIS // TERMINAL 935`, `MAXIS // TRANSIT 935`), plain sentences for help text"
  (MAXIS.md:27-28).
- Map previews = retail theater posters of each film (Spaceland, Rave, Shaolin, Beast); Attack has none so a "1950s B-movie card built
  from its retail logo" ("IT CAME FROM MAYFIELD", "A WILLARD WYLER PICTURE", ART attack_card). "Graded with the Maxis tint and scanlines.
  Derived from game files, so never committed; the generator is." (MAXIS.md:29-31).

### 1.2 Colour tokens (MAXIS.md:35-47, mirrored in LUA:21-25 and ART:23-27, and GSC literals)

| Token | Hex | GSC vector | Use (quoted) |
| --- | --- | --- | --- |
| void | `#07090C` | none | "dimmers behind menus" |
| panel | `#0D1218` | `(0.05, 0.07, 0.09)` | "panel fills (86-94 % alpha)" |
| panel-2 | `#131B24` | none | "rows, tabs, buttons" |
| line | `#22303D` | none | "hairlines, idle card frames" |
| aether | `#34E8D2` | `(0.20, 0.91, 0.82)` | "primary accent, hover, `^5`" |
| amber | `#FFB238` | `(1, 0.70, 0.22)` | "data, own vote, brackets, `^3`" |
| blood | `#E5383B` | none | "round numbers, leading map, `^1`" |
| violet | `#A266FF` | none | "reserved: Pack-a-Punch / rare" (defined in LUA:22 but unused by any widget) |
| bone | `#EEE7D7` | `(0.93, 0.91, 0.84)` | "primary text, `^7`" |
| ash | `#8E949C` | none | "secondary text" |
| ok | `#6BE675` | none | "ON states, `^2`" |

Lua stores them as `0xRRGGBB` ints (`void = 0x07090C ... ok = 0x6BE675`, LUA:22-24) and applies with `SetRGBFromInt`.
Chat/HudElem colour codes map: `^1` blood, `^2` ok, `^3` amber, `^5` aether, `^7` bone (MAXIS.md table). `^4` and `^6` are not assigned
(one legacy string uses `^4`: `^5Maxis' ^4Pa^7r^1is` = server name, config/localization.json:2110).
Rounding note: the GSC float vectors are approximations of the hex (e.g. panel 0.09*255=23 vs hex 0x18=24); no doc says which is canonical.
Other colours seen in the HudElem tier (not in the table): vote row text bone `(0.93, 0.91, 0.84)`, hover aether, voted amber
(VOTE:587,626,627); AFK banner violet `(0.7, 0, 1)` (`AFK.gsc:199`, older, pre-Maxis).

### 1.3 Fonts and sizes (LUI tier)

"Type (LUI): `MainExtended` for titles, `MainBold` for labels and chips, `MainMedium` for body, `MainCondensed` for metadata, `Digital`
for clocks, counts and round numbers. All retail fonts; no font asset ships." (MAXIS.md:49-51). Resolved by
`FONTS.GetFont((FONTS[kind] or FONTS.MainMedium).File)` (LUA:125); sizes pass through `P(v) = v * (_1080p or 1)` (LUA:33), i.e. a
**1920x1080 design canvas** scaled by the engine's `_1080p` factor (LUA:242, 391, 526 root anchors 0..1920 x 0..1080).
(The BO3 HUD Lua uses `FONTS.MainBold.File` too, and stock `SWATCHES.HUD.warning` for the reserve warning, bo3 Lua:98,158.)

Sizes actually used (LUA line : role -> font size, px at 1080p):
- Vote header title 54 MainExtended (249); transit subtitle 20 MainCondensed aether (250); countdown clock 70 Digital amber (251);
  "N / M VOTED" 20 MainCondensed ash (252); card name 26 MainBold (274); card count 48 Digital amber (275); "VOTES" unit 18 MainCondensed ash (276);
  YOUR VOTE tag text 22 MainBold void on amber (280); LEADING 18 MainBold blood (282); hint 20 MainCondensed ash centred (305).
- Terminal title 40 MainExtended (398); status line 18 MainCondensed aether (399); tab labels 24 MainBold (412); row chip 22 MainBold amber (425);
  row description 20 MainMedium bone (426); RUN pill text 18 MainBold void (428); footer 18 MainCondensed ash (444); close label 24 MainBold (402).
- Welcome briefing: title 30 MainExtended (537); map line 18 MainCondensed aether (538); small labels 16 MainCondensed ash (539, 542, 544);
  record/best numbers 46 Digital blood / amber (540, 543); names 18 MainMedium (541).
- Toast rows 22 MainMedium bone, row pitch 26 (555).
HudElem tier has no font choice: engine default font, `fontscale` 0.68 to 1.35 (see 3a). No `.font =` assignment exists in src/.

### 1.4 Shape language, spacing, components

Quoted (MAXIS.md:53-57): "chamfer-free rectangular panels with a 4 px aether top rule, amber corner brackets (the signature), 2 px hairline
frames that recolour on state, chips (amber command text) with a RUN pill, film cards (300x600 poster, bottom shade, Digital count, voter pips,
`YOUR VOTE` amber tag, `LEADING` blood tag). States: idle `line`, hover `aether` + 14 px lift + glow, selected `amber`."
The chamfer exists only in the logo art (ART chamfer()), not in panels.

Exact geometry from code (1080p design px):
- Brackets: 2 px thick, arm length 18 default, 24 (terminal), 28 (vote), 20 (welcome) (`brackets()` LUA:167-175; calls 306, 396, 535).
  Placed 8 px outside the panel on the terminal (396), 6 px on welcome (535).
- Hairline frame: four 2 px rects (LUA:159-165). Top accent rule: 4 px (terminal 395, welcome 534), 6 px full-width on vote (246).
- Vote menu (LUA:239-342): full-screen dimmer void@0.88 (245); header logo 96x96 at (140,70) (248); rule line 2 px at y=190 (253);
  draining bar amber 4 px at y=188-192, width 1640 * time-left (254, 337); 5 cards W=300 H=600 GAP=35 X0=140 Y0=240 (257);
  glow rect +/-10 px aether alpha 0 (261); card shade last 150 px void@0.78 (273); count + "VOTES" unit (275-276); voter pips 12x12, pitch 18,
  max 8, aether (278); tag bar 34 px amber (279); outer brackets rect (120,50)-(1800,940) len 28 (306).
- Terminal (LUA:386-494): dimmer void@0.55 (392); panel (410,170)-(1510,910), 1100x740, panel@0.94 (393-394); logo 72 (397); close button
  140x46 panel-2, hover blood (400-405); 4 tabs 250x48, pitch 262, tab bg panel-2, hover line, active text bone + 4 px aether underline, inactive ash
  (407-418, 450-452); 10 rows, pitch 50, height 44, zebra alpha 0.6 on even rows (421-443, 483); chip column x+48 (width 372), description x+430,
  RUN pill 116x32 aether (427-428); footer at Y2-40 (444).
- Welcome card (LUA:523-545): 800x220, panel@0.92, aether 4 px rule, logo 110 at (26,30); on screen at y=60..280, x=560..1360 (588), parked
  off-screen y=-260..-40 (530).
- Toast (LUA:547-556): x=1340..1880, y=250..330 base, width 540, height `24 + rows*26`, up to 9 rows, panel@0.9, aether left bar 5 px; comment
  "upper right, below the minimap area" (546).
- Logo fallback when the material is missing: text "Mx" aether MainBold (183); card fallback "Mx" (272). Every `RegisterMaterial` use is wrapped in `pcall`.

### 1.5 Motion and animation (LUI tier; easing is not stated anywhere)

| Effect | Timing | Source |
| --- | --- | --- |
| card hover lift 14 px up | 120 ms (`SetAnchorsAndPosition(..., 120)`) | LUA:288, return 294 |
| card glow alpha 0 -> 0.22 | 120 ms | LUA:289, 295 |
| voter pip alpha | 80 ms | LUA:320 |
| YOUR VOTE tag / LEADING alpha | 100 ms | LUA:322-324 |
| frame recolour alpha | 120 ms | LUA:163 |
| terminal row hover alpha | 80 ms | LUA:431, 434 |
| terminal tab underline alpha | 100 ms | LUA:452 |
| welcome card slide + fade in | 450 ms | LUA:588-589 |
| welcome card slide + fade out | 400 ms | LUA:570-571 |
| toast fade in / out | 150 ms / 300 ms | LUA:607, 612 |
| vote clock/bar tick | every 100 ms (`UITimer interval=100`, event `maxis_vote_tick`) | LUA:330 |
| global heartbeat | every 100 ms (`maxis_tick`) | LUA:558 |
| clock turns blood red | when < 10 000 ms left | LUA:335 |
Easing curve: "not stated" (the engine call only takes a duration in ms). HudElem tier: `fadeovertime(0.4)` in, `fadeovertime(1)` out for the briefing
(UIGSC:701, 707); no `moveovertime`/`scaleovertime`/pulse/glow use anywhere in src/.
Server-driven lifetimes: briefing 12 000 ms (UIGSC:389); toast 7 000 ms (UIGSC:372); HudElem page auto-close 15 000 ms (UIGSC:97, docs/UI-COMPACT-REPLIES.md:23-26);
vote window 40 s and unanimous hold 5 s (MAXIS.md:112 "Unchanged: deadline, five-second unanimous hold"; AGENTS.md "Vote windows doubled" 20 -> 40 s);
terminal click rate limit 400 ms (UIGSC:290).

### 1.6 Iconography

Not stated beyond: logo tile, amber corner brackets, "voter pips", chips, the RUN pill. No icon set, no glyph rules, no emoji. Retail materials in use:
`white` (tinted by colour) and previously `black` (git history of paris_ui.gsc: "Retail "black"/"white" materials only: no client asset or download");
retail `scoreboard_mic_talk` / `scoreboard_mic_mute` are used only by the separate BO3 HUD Lua (bo3 Lua:1205).
Mod-shipped art: `maxis_logo` (256x256 RGBA TGA) and `maxis_map_<cp_zmb|cp_rave|cp_disco|cp_town|cp_final>` (256x512 RGB TGA), materials built with technique set
`2d` (Build-ParisMod.ps1:267-301). Note ART draws the logo text with the Windows fonts Bahnschrift/Arial (`font()` in make_art.py), even though MAXIS.md:23 says "no font ... inside";
the licence of baking that raster is not stated.

### 1.7 Sound of the UI

**Not stated.** No UI sound, `playlocalsound` or alias exists in `paris_ui.gsc`, `iw7_map_vote.gsc` or the Lua; MAXIS.md has no audio section.

### 1.8 Do / don't rules found in the docs and code

Do:
- Use retail fonts only; ship no font asset (MAXIS.md:50-51).
- Keep one palette in three places in sync: "Keep in sync with the Lua and GSC palettes" (ART:22).
- Never write an unchanged payload: "Writes happen only on change: client dvars and chat share the 128-entry reliable ring" (MAXIS.md:135-136).
- Release HudElems (destroy) instead of hiding with alpha 0: "Hidden elements still consume the engine HUD budget" (UIGSC:439-441; UI.md:10-11).
- Allocation order is admission priority: "the five choices, then the highlight, title, timer and hint; decoration last" (VOTE:577-578).
- Mark temporary elements `archived = false` (VOTE:667, 685; docs/MAP-VOTE-HUD.md:27-34).
- Vote has priority over every private panel (`blocked()` UIGSC:54-59).
- Vote must survive Esc: "Esc does not lose the vote: the menu returns while the vote runs" (MAXIS.md:102-103; LUA:350-353).
- Private pages: only the latest reply, wrap at spaces within 44 visible chars, colour codes zero width, continuation inherits colour, at most 6 rows, auto-close 15 s
  (docs/UI-COMPACT-REPLIES.md:13-26).
Don't:
- Don't commit generated art or anything derived from game files (MAXIS.md:31-32).
- Don't put a newline, double quote or `%` in a client-dvar payload; `|` separates fields, `~` separates rows (MAXIS.md:136-138; `clean_text` UIGSC:232-243).
- Don't invent client-to-server message names: only four retail names are reusable (see 3b).
- Don't assume stock clients run Lua: "older clients simply never run this file and keep the server's HudElem tier" (LUA:3-4).
- Don't use new identifier-shaped GSC names carelessly: Beast's canonical-string table has 4095 slots and the catalog budget is 1130 dynamic identifiers with 64 free slots required
  (`config/canonical-budget.json`; docs/BEAST-CANONICAL-STRINGS.md:21-29; MAXIS.md:172-176). Existing code hides names with `#define` aliases of retail tokens and delimited string literals (UIGSC:1-20, 26-30).

---------------------------------------------------------------------------------------------------------------------------------

## 2. What exists, how it is drawn, where it lives

| Screen / component | Tier | How drawn | Files |
| --- | --- | --- | --- |
| Terminal `.menu` (tabs PLAY / BANK / SQUAD / SERVER; rows are commands with RUN pills; roster rows with #IDs; module ON/OFF list; map record) | LUI | LuaFile menu type `MaxisTerminal`, mouse buttons, replays 15 allowlisted commands via notify | LUA:386-494, 496-519 |
| Terminal | HudElem | right-top panel, `newclienthudelem`, 8-15 elements, text rows from `page_lines()` | UIGSC:393-571 |
| Latest-reply "status" panel / toast | LUI toast; HudElem status page | toast 540 px wide upper right; HudElem panel | LUA:547-556, 592-614; UIGSC:436-489 |
| Arrival briefing (map, record, personal best, Easter egg line, `.menu` hint) | LUI overlay card; HudElem centre-top card with 40x40 logo | LUA:523-545, 562-590; UIGSC:622-720 |
| Map vote | LUI full-screen `MaxisVoteMenu` with five poster cards, mouse cursor, click votes | LUA:219-362 |
| Map vote | HudElem: 5 text rows (static labels + `setvalue` counts), highlight bar, 110x220 poster preview, timer, hint; **virtual cursor = view pitch** (7 degrees per row), left click = Fire | VOTE:550-697, 699-728 |
| Rush label ("Rush ON \| Double Points \| Round 15 health cap") | HudElem x=10,y=90 fullscreen, scale 0.8 | UIGSC:795-819 |
| Zombie counter, two timers, personal record | HudElem x=10, y=40 (scale 1), 54 and 66 (0.8), record y=78 (0.8) | `zombie_counter.gsc:41-65` |
| Spawn blessing timer | HudElem x=10,y=102 | `paris_spawn_blessing.gsc:61` |
| AFK countdown / banner | HudElem centre, y=-50, scale 1.3 | `AFK.gsc:81-87, 192-199` |
| Maxis art (logo, 5 poster materials) | mod.ff materials | `ops/maxis/make_art.py`, `ops/Build-ParisMod.ps1:262-301` |

Not existing: scoreboard / Tab, emote wheel, perk or ammo HUD, damage numbers, notifications queue, any gamepad focus navigation.

Separate (not Maxis-styled) Lua HUD: `iw7-mod-components` `src/ui_scripts/bo3_zombies_hud/__init__.lua` (1467 lines) restyles the **retail** HUD leaves (round, ammo, portrait,
perks, Fate cards) in a BO3 look with `0xF5F1E7` text, `FONTS.MainBold`, 18-60 px sizes (bo3 Lua:1016, 1231-1234). Per `docs/CREATION-CORE.md:105` "359 offline tests,
one real run with a wrong layout" - not accepted. It is the only evidence of how to edit stock HUD widgets from Lua.

Module switch: `ui` module in `config/modules.json`/`paris_modules` (docs/MODULES.md:92 "ui | paris_ui.gsc | stock HudElems, registry"); `paris_ui_art` server cvar
(`config/server_modules.cfg:26`, `art()` UIGSC:49-52) gates the mod art: art is used only when `fs_game == mods/paris` and `paris_ui_art != 0`.
Per-map profile: Station Zero (`cp_iwz`) default-disables bank, rush etc. (docs/MODULES.md:9-22); UI itself is not in that disable list.

Status in docs (MAXIS.md:9-14): merged (PR399, `eba9d29b`), deployed 2026-11-08 on Main (staged, stopped) and Canada (staged, process frozen); later STATE.md says Canada runs
`fs_game mods/paris` publicly since 2026-11-09 and Main is closed by the owner. "**No in-game test yet**" of the LUI tier; see section 6.
(`docs/TOOLS-INDEX.md:159,171` still labels the Maxis scripts/tests "unmerged, 40 ahead"; stale versus MAXIS.md:9 and the files present on main.)

---------------------------------------------------------------------------------------------------------------------------------

## 3. The two delivery routes

### 3a. Server-drawn (GSC HudElem), no client change

What exists and is proven in game (E2E 33/33, protected client witness; docs/deployments/2026-11-08-maxis-ui-e2e.json; briefing frame with logo, terminal, toast, vote with posters,
agent mouse-look moved selection 2 -> 3, Fire voted map 4):
- Per-player elements: `newclienthudelem(player)` (UIGSC:398, VOTE:666).
- Fields used: `x`, `y`, `alignx` (left/center/right), `aligny` (top/middle), `horzalign` ("right", "center", "fullscreen"), `vertalign` ("top", "middle", "fullscreen"),
  `fontscale`, `sort`, `foreground`, `alpha`, `color` (RGB vector), `archived`, `label` (static string prefix for counters), `fadeovertime`.
- Methods used: `setshader(material, w, h)` (rectangle or image), `settext`, `setvalue(n)`, `settimer(s)`, `settimerup(s)`, `destroy()`.
- Stock materials: `white` (tintable rectangle; every panel, rule, bar) (UIGSC:422, VOTE:591-607). Rectangles only: no rotation, arc, ring, gradient or rounded-corner primitive
  is used or documented ("not stated").
- Mod materials (images): `maxis_logo`, `maxis_map_<map>` loaded with `precacheshader`; "precacheshader of a material no loaded zone defines raises a script error" (UIGSC:32-34).
  They exist **only** when the server runs `fs_game mods/paris` (they are in `mod.ff`, auto-downloaded). Without a mod, only retail materials are available. New custom images
  need the 2D material recipe in `Build-ParisMod.ps1:267-301` (TGA + materials/<name>.json with `techniqueSet->name = '2d'`, per-material state and constant buffer files) and the
  owner-fork ZoneTool that reuses captured stock shaders (MAXIS.md:203-211); the community ZoneTool fails with `pixelshader "68aefedcc8d5dfde" not found`.
- Fonts: engine default only, only size via `fontscale`. Sizes seen: 0.68 footer, 0.72 tab bar, 0.78 rows, 0.8 status/timers, 0.85 hint/briefing, 1.0 counter, 1.05-1.1 titles, 1.15 vote rows,
  1.2 timer, 1.3 AFK, 1.35 vote title (UIGSC:458-468, 690-691; VOTE:583-602). Colour inside text via `^N` codes.
- Layout anchors in use: terminal `x=-6` right-anchored `horzalign right`, y=80, width 312, text x=-306, row pitch 13 (14 for replies) (UIGSC:399, 457-467); briefing centre-top y=92, width 360, row pitch 15,
  logo 40x40 at (-150,100) (UIGSC:677-682); vote centre/middle, backdrop 480x296 at y=-150, rows pitch 30, preview 110x220 at x=150,y=-112 (VOTE:583-611).
  Coordinates are HudElem virtual units (not the 1920x1080 LUI canvas); the vote uses `vertalign "middle"` offsets.
- Limits:
  - Count: "a small per-client element budget" (MAXIS.md:64); the engine maximum is not stated. Project budget: "HudElems we own per player <= 24" measured by `[Paris perf] hud_max`
    (MAXIS.md:160; `ops/Analyze-ServerPerf.py:38` notes "the engine budget is shared with retail"). Measured: briefing 8, terminal 13/10/9/15 (Play/Bank/Squad/Server), vote 12 (E2E record).
    Earlier incident: vote labels disappeared under retail death/spectator elements; "the frame does not prove a specific engine limit" (docs/MAP-VOTE-HUD.md:15-19).
  - Strings: "every distinct text costs an engine string" (MAXIS.md:65) -> use static labels + `setvalue` counts (VOTE:214, 645-648).
  - Reply text: 264 chars input cap, 6 rows x 44 visible chars, UTF-8 aware (UIGSC:127-159, 821-834; UI-COMPACT-REPLIES.md:17-21).
  - Private/per-player only; no shared-language elements (LOCALIZATION.md:57-60).
- Update rate: terminal monitor 4 Hz (`wait 0.25`, UIGSC:225); vote cursor/buttons thread 20 Hz (`wait 0.05`, VOTE:726); vote row refresh 20 Hz (VOTE:636). Text is rewritten only on change (UIGSC:477-481).
- **Input a server script can read** (proven in repo): `attackbuttonpressed` (Fire), `adsbuttonpressed`, `meleebuttonpressed`, `usebuttonpressed`, `getplayerangles()` (view pitch/yaw),
  `getvelocity`, `freezecontrols(true/false)`. Not available: "inspected IW7 `buttonpressed` is constant false" and raw keyboard/arrow keys need a native extension; owner declined arrows to avoid
  updating clients (docs/CONTEXT.md:801-803). **No mouse cursor position and no click events** on this route: the proven workaround is the "virtual cursor": mouse-look moves the view, the pitch
  maps to a row (7 degrees per row, edges re-anchor), left click = Fire (VOTE:650-660, 704-724). A spectator (view follows someone else) can only step with Fire (VOTE:719-723).
  Controller: the pitch cursor reads view angles so any look device moves it (inference; only agent mouse-look was tested). Chat commands (`.menu`, `.close`) are the other input path.
- Server -> player text commands: `setclientdvar` only; chat reply `tell`.

### 3b. Lua / LUI route (client draws)

Capabilities proven by the code and the HUD lab (not by a rendered Maxis frame): LUI menus via `MenuBuilder.registerType` + `LUI.FlowManager.RequestAddMenu(name, true, controller, false)` /
`RequestLeaveMenuByName` / `IsInStack`; elements `LUI.UIElement`, `UIImage`, `UIText`, `UIButton`, `UITimer`; `SetAnchorsAndPosition(l,r,t,b, ms)`, `SetAlpha(a, ms)`, `SetRGBFromInt`,
`setImage(RegisterMaterial(name))`, `setText`, `SetFont`, `SetFontSize`, `SetAlignment`; events `button_over`, `button_up`, `button_action` (mouse hover/leave/click); overlay root `Engine.GetLuiRoot()`;
timing `scheduler.once`, `Engine.GetMilliseconds`, `Game.GetTime`; dvar read `Engine.GetDvarString`; map `Game.GetMapName`; `Engine.InFrontend()`; scoreboard data `Game.GetCPNumScoreboardPlayers`,
`Game.GetCPScoreboardRowData` (bo3 Lua:1215-1224). Mouse cursor, images, animation and "no HudElem" cost (MAXIS.md:70-71).

Data path (MAXIS.md:130-154): server -> client `setclientdvar` ("the client creates unknown dvars, iw7-mod `patches.cpp`") on five dvars, each payload starting with the server time:

| Dvar | Payload |
| --- | --- |
| `maxis_k` | handshake answer: server time |
| `maxis_v` | `t|until|kind|sel|c0,c1,c2,c3,c4|players|lang` (until 0 = closed) |
| `maxis_m` | `t|seq|tab|lang|flags|rush|record|names|best|modules|roster` (tab 0 = close) |
| `maxis_w` | `t|until|seq|lang|map|record|names|best|rush` |
| `maxis_n` | `t|until|seq|row~row~...` |

Client -> server: `Engine.NotifyServer(name, value)`; "sends an **index** into a fixed retail name table (iw7-mod `cmd_lui_notify_server`: 161 is `end_game`), so custom names are impossible. We reuse
four retail names that no CP script listens to: `intel_tab` (handshake, protocol 1), `map_select` (card 0-4), `boss_set` (terminal row 1-15), `boss_reset` (terminal closed)" (MAXIS.md:149-152). Server
side: `self waittill("luinotifyserver", channel, value)` (UIGSC:266); index > 15 or inside 400 ms is ignored (UIGSC:290). Every payload is dropped by the client if newer than its clock or past its deadline
(LUA:209-212, covers dvars surviving a map change). Per-payload cap about 1 KB (one reliable command); feature list dropped first (UIGSC:344). Write budget `<= 24 per 10 s` (all players), reliable ring 128 entries;
a past incident `EXE_SERVERCOMMANDOVERFLOW` disconnected a player (docs/SERVER-COMMAND-OVERFLOW.md). Lua polls dvars on a 100 ms timer (LUA:558, 617-634).
Handshake: client sends `intel_tab 1` every 2 s until the server answers `maxis_k` (LUA:622-629); the server marks `paris_ui_observed = 2` (UIGSC:273) and then draws no HudElem for that player.
For stock clients (observed == 1) the server rejects LUI events (E2E: "server rejection of LUI events from a stock client").

Who can run Lua today:
- **Official updater client v1.1.0 (main, 26 Sep 2026): no.** "The official v1.1.0 client does not load zone Lua" (MAXIS.md:232-233); it loads LUI only from `cdata/ui_scripts` (E2E record Findings). Client reported `lui=0`.
- The release awaited: **auroramod/iw7-mod PR #697** ("load raw Lua/LUI from fastfiles, drop Lua callbacks on teardown"), merged to `develop` 30 Sep 2026 (merge `7c8fe47d`), not in `main`/any release; the updater serves `main`
  (`files.json`), `develop` only to opted-in players (`files-dev.json`) (docs/DISCORD-BUTTON.md:16-21; MAXIS.md:72-77; UPSTREAM-2026-10-06.md:11,22-31). "Checked 10 Nov" still unreleased (docs/CREATION-CORE.md:105).
  A drafted issue "Release request: ship PR #697 (zone Lua) in a main release" exists, **not posted**; posting is "left to the owner" (MAXIS.md:239-253; memory: nothing posted to Aurora).
- Clients built from `develop` / the owner's native builds / lab and bench clients: yes. Our native pin `77e6d4d2...` already contains the loader (UPSTREAM-2026-10-06.md:31-35). HUD lab proved the route: a 1360-byte `mod.ff` with
  `luafile,ui_scripts/paris_lab_hud/__init__.lua` downloaded fresh into a lab client, evaluated, rendered two text rows in the retail font (docs/HUD-LAB.md:1-18, 367-379).
  The owner's habitual client (`iw7-cb-aurora.exe`, CB + official develop `37abcb26`) is documented but not stated to load zone Lua; Maxis never ran its LUI tier on any client.
- On-disk Lua always works: `iw7-mod/ui_scripts/<folder>/__init__.lua` or `cdata/ui_scripts/` (a disk folder of the same name overrides the zone one; zone Lua runs after disk scripts) (HUD-LAB.md:26-29). Raw `.lua` is **not** in the
  mod downloader's file list, so a server cannot push a loose file (MAXIS.md "Architecture"; DISCORD-BUTTON.md:20-22; HUD-LAB.md:161).

How a mod delivers Lua to players: put the file in the mod zone as `LuaFile` asset named exactly `ui_scripts/<single-folder>/__init__.lua`; ZoneTool's shared importer stores raw bytes, no Lua compiler needed
(HUD-LAB.md:38-44). `Build-ParisMod.ps1:262-266` always adds `luafile,ui_scripts/maxis/__init__.lua` to zone `mod`. The server advertises `fs_game mods/paris`, `mod_hash` (CRC32), optional `sabl_hash`/`sabs_hash`;
the client downloads `<sv_wwwBaseUrl>/mods/paris/mod.ff|.sabl|.sabs` (Canada OVH host, TCP 8767), then `vid_restart` restarts the Lua VM (CLIENT-COMPATIBILITY.md:20-30). Delivery works only for a client whose executable
loads zone Lua. The file runs once per LUI state, guards `Engine.InFrontend()` and `rawget(_G, "MaxisUI")` (LUA:15-18), attaches to the LUI root by polling every 500 ms up to 240 times because PR697 discards scheduled callbacks of a torn-down state (LUA:638-652).
Usermap zones: PR697 enumerates LuaFile assets of "loaded zones" (DISCORD-BUTTON.md:16-17; UPSTREAM-2026-10-06.md:22-24); whether a custom-map FF can carry such a LuaFile and be run is **not stated** (usermap delivery is party-join only,
dedicated `connect` download unproven: CLIENT-COMPATIBILITY.md:55-57).
Environment limits: Lua is Lua 5.1/HavokScript; checked offline by `tests/ops/maxis_lua_test.cjs` (109 checks; allowed globals list, no `io`/`os`/`require`; parse only). Lab packages cap Lua at 1600 bytes (hud-lab) and 131 072 bytes
(BO3 HUD profile) - these are tool limits, not engine limits. No UI-as-data tool exists yet: "UI review still needs eyes" (CREATION-CORE.md:105; package U1 "running").

---------------------------------------------------------------------------------------------------------------------------------

## 4. Stock Zombies Tab / scoreboard, input capture, controller

What the docs and source actually say about the stock scoreboard (very little):
- Rendered by retail LUI/CP; its data is queryable from Lua: `Game.GetCPNumScoreboardPlayers()` and `Game.GetCPScoreboardRowData(i)`, a row table including `clientNum`, `isMicOn`, `isMuted`
  (bo3 Lua:1205-1226); the retail PlayerCash grid uses `GetCPScoreboardRowData(row, target, true)` (docs/BO3-ZOMBIES-HUD.md:147, 1052, 1076). The BO3 Lua itself guards `count <= 4`.
- It is sized for four: "LUI HUD portraits, the CP scoreboard, the end-of-game (EoG) DDL rows and omnvar definitions are sized for four. Players 5 to 8 would get no teammate portrait or EoG row unless the client is updated.
  The owner earlier declined forcing client updates." (docs/PLAYERS8-AUDIT.md:110-113); "portraits/scoreboard/EoG keep four rows, while server statistics retain all eight" (docs/PUBLIC-SERVER.md:6).
- "The native scoreboard/leaderboard writes remain authoritative and unchanged" (docs/PLAYER-STATS.md:18); stats flow through `scripts\cp\cp_persistence::setcoopplayerdata_for_everyone("EoGPlayer", slot, name, total)` with names
  kills, deaths, downs, revives, headshots (`paris_stats.gsc` stat_update ~lines 191-229).
- Whether or how Tab can be **replaced or extended**: not stated. No doc proposes replacing the retail scoreboard. The retail menu/widget names, the Tab binding and stock layout are **not stated** (GrayWolf does not index luafiles,
  DISCORD-BUTTON.md; an `iw7-dump` decompilation `deshayu/iw7-dump ui/ingame/cp` pinned at `2305708` is cited as a reference by BO3-ZOMBIES-HUD.md but is not in this repo). Local tooling that could answer: `@luadump` of the LuaFile
  inventory and the console-driven `iwzmap_menu_probe.lua` (docs/IWZ-CUSTOM-MAP.md:116-123).
- Data the server can already show on its own Tab-like screen: `#ID` (`getentitynumber()+1`), name, ping (`paris_get_ping`, native server method, dedicated only, -1 if unavailable; docs/PING.md:15-24), language/country, per-player
  EoG-style stats via `paris_stats` (time, connections, kills, headshots, deaths, downs, revives, best round, maps), bank balance (`.balance`, private), round record (`level.paris_stats.highest`). These are written to the LUI client by the existing
  `maxis_m` roster/record fields (only `id~name` pairs and record are in the payload today).

Input capture conventions already used by Maxis:
- LUI tier: mouse `button_over` / `button_up` / `button_action` on `LUI.UIButton`; menu requested on the first active controller (`Engine.GetFirstActiveController`, LUA:195-198, 358, 511). No key-binding (Tab, Esc, wheel,
  gamepad button) handler exists in the Maxis Lua; no gamepad focus/dpad navigation is implemented (not stated). Esc closes a menu without telling the module, so presence on the flow stack is polled (LUA:129-133, 350).
- HudElem tier: view-pitch virtual cursor + Fire (see 3a). Earlier vote used Fire/ADS stepping (removed; "Fire/ADS stepping is gone", MAXIS.md:105). UI.md:30-31 (superseded text) says the old private page "does not freeze controls or read Fire, ADS, Use or melee".
  Vote freezes/unfreezes controls (`freezecontrols(false)` so the view can move; `true` afterwards, VOTE:562-574).
- Commands: `.menu 1-4`, `.close`, `.players`, `.mods`, `.help` aliases; the LUI terminal replays clicks as chat text, allowlist of 15 (MAXIS.md:84-97).

---------------------------------------------------------------------------------------------------------------------------------

## 5. Localization rules UI copy must follow (docs/LOCALIZATION.md, MAXIS.md, code)

- Owner decision 2026-10-19: "Every maintained dedicated command, menu, HUD, announcement ... uses EN/FR/ES per recipient. Stock game strings keep the game's own localization. Map, weapon/perk names, commands,
  player names and numeric values remain identifiers; chat written by players is never translated." (LOCALIZATION.md:3-8). Command tokens (`.lang`, `yes/no`, `all`) stay identical in every language (LOCALIZATION.md:11-12).
- Language per player: `.lang fr|es|en|auto`, saved per GUID at `mods/paris_beta/language/<sanitized-guid>.txt`; auto = GeoIP country default (ES: 20 Spanish-speaking states + PR, Canaries, Ceuta/Melilla, Andorra; FR: France + overseas,
  Monaco, Belgium, Switzerland, Luxembourg, Haiti, French-official Africa, Maghreb, Mauritius; **Canada = EN**; everything else EN) (LOCALIZATION.md:14-45). Resolved by `player custom_scripts\cp\paris_country::array_contains()` (paris_country.gsc:43-57).
- HudElem tier: write the English template (exact key, with colour codes) into `config/localization.json` with complete `fr` and `es`, run `python ops/Generate-Localization.py` (`--check` verifies), which regenerates a `switch` in
  `paris_country.gsc`; call `self custom_scripts\cp\paris_country::array_combine("template {0}", a, b, c)`. Rules: placeholders `{0}..{2}` must match in all languages; no tab/CR/LF in a translation; single-pass substitution so names cannot become
  translation keys; no runtime JSON (LOCALIZATION.md:53-62; Generate-Localization.py generated()). 596 templates today. Missing language falls back to English text.
- LUI tier: strings live in the Lua `COPY` table (`en`, `fr`, `es`, UTF-8 escapes such as `\195\137` = E acute, `\194\183` = middle dot), selected by the `lang` field the server sends in every payload (`L(lang)` LUA:110). Test enforces that every
  key in `en` exists in `fr`/`es` and every static terminal row has EN/FR/ES text (maxis_lua_test.cjs). Row descriptions are `en`/`fr`/`es` fields on each ROWS entry (LUA:79-107). Brand strings stay untranslated (`MAXIS // TERMINAL 935` same in FR/ES;
  `TRANSIT 935` -> ES `TRÁNSITO 935`).
- Text conventions from the existing FR/ES: uppercase terminal labels keep accents ("EQUIPE" is written `\195\137QUIPE`); spaced colons in French ("Solde bancaire : {0}").
- Payload safety: strip `| ~ " % \n` from any dynamic text (names) before it goes into a client dvar (UIGSC:232-243).
- Wrapping/width: HudElem rows use 44 visible characters and count UTF-8 multi-byte characters correctly (UIGSC:821-834). Rendered accented glyphs on a real client are **not established** ("These models do not establish ... rendered glyphs", LOCALIZATION.md:66-69).
- Canonical catalog: new GSC strings should be delimited literals to avoid growing the identifier budget (LOCALIZATION.md:72-75).

---------------------------------------------------------------------------------------------------------------------------------

## 6. Unproven, broken or open (verbatim where possible)

1. "**No in-game test yet**: startup with this set, owner gameplay and the LUI tier (needs an iw7-mod release with PR #697) are not proven. Every runtime item below stays pending" (MAXIS.md:13-14). Later: "Not done: client LUI rendering,
   clicks and `NotifyServer` indices ... companion revive in a real co-op match, HudElem cursor feel for a human, owner acceptance." (MAXIS.md:234-237).
2. The LUI tier has only been parse-checked (maxis_lua_test.cjs: "Parsing is not execution: rendering, input and the engine's own LUI remain runtime questions"). The `NotifyServer` index mapping (161 = end_game) is read from source, unverified at runtime.
   `Engine.NotifyServer` events from a LUI client, `LUI.FlowManager.IsInStack` semantics, `_1080p` scaling and font names were never executed by Maxis code on a real client. The E2E client ran with `lui=0` (official v1.1.0 style client),
   so the Lua tier visuals are unseen. The HUD lab shows a lab client can run zone Lua, but the Maxis witness did not use it (reason not stated).
3. The only visual evidence is the HudElem tier on a protected base client (frames hashed in the E2E record; no independent visual review is recorded). Owner acceptance: false.
4. `setclientdvar` to a new name read by `Engine.GetDvarString` is described as "unproven end to end" (DISCORD-BUTTON.md:34-37) for a similar per-player language route; Maxis relies on the same mechanism.
5. HudElem cursor feel for a human, spectator stepping, controller input, and the 24-element budget under real retail HUD load: not verified; "the frame does not prove a specific engine limit" (MAP-VOTE-HUD.md:18-19).
6. Reliable-command overflow is an unresolved class of disconnect (Issue 129; SERVER-COMMAND-OVERFLOW.md:1-8); Maxis keeps writes on change, <= 24 per 10 s; any chatty Tab (per-second ping/score streaming) would add risk.
7. Mod art needs the owner-fork ZoneTool (community build fails on 2d shaders), takes the mod.ff size up, and never reaches servers without `fs_game mods/paris` (MAXIS.md:203-216).
8. Canonical-string headroom on Beast is tight; any new GSC UI code must re-run the cold Beast capacity check (MAXIS.md:172-176; config/canonical-budget.json).
9. The retail scoreboard is four rows only; players 5-8 get no row (PLAYERS8-AUDIT.md:110-113). The owner accepted four-row legacy portraits/scoreboard/EoG for eight-player (AGENTS.md "Eight-player delivery candidate"). A custom Tab on the Lua tier could show all slots; on HudElem tier it competes with the 24-element budget.
10. No emote system, no UI sound design, no icon set, no easing spec, no gamepad navigation exists; Maxis tokens do not define a typographic scale below 16 px or any disabled-state colour.
11. Doc inconsistencies to be aware of: MAXIS.md says panels are 4 px top rule but the vote screen uses a 6 px full-width aether rule (LUA:246); UI.md still describes an old eight-element, right-upper panel (marked superseded); `docs/TOOLS-INDEX.md` lists Maxis rows as unmerged; GSC float colours differ from hex by 1 unit.
12. Project rules that bind any new UI claim: never say the UI looks right without independent reviewer agents judging real frames first; never CUA-drive IW7 clients (memory files visual-claims-need-unbiased-review, game-tests-via-codex); agents must not deploy; Main/Canada deployment needs owner approval then both servers (AGENTS.md).

---------------------------------------------------------------------------------------------------------------------------------

## 7. Design consequences for Tab, HUD elements and an emote wheel (inference, clearly separated from the sources)

- Authoring against the Maxis tokens is straightforward in Lua (reuse `rect`, `label`, `brackets`, `frame`, `button` helpers LUA:135-198) at the 1920x1080 canvas. A Tab screen should be a `MenuBuilder` type or an always-attached overlay element toggled by a server flag; Tab key capture in Lua is not
  implemented anywhere (no key handler exists); an emote wheel needs mouse angle from button regions (8 wedges as UIButtons is possible but wedge shapes need a mod-shipped ring image, as rotation/arc primitives are not documented) and a `NotifyServer("boss_set"-like retail name, index)` per choice; with only 4 usable
  retail names and 15 indices per `boss_set`, allocate one or two names for wheel use and keep indices small.
- Server-only fallback (every player, no download): view-pitch/yaw virtual pointer + Fire like the vote; wedge highlighting by yaw angle is possible with `getplayerangles()`; labels via `setvalue`/static text; ring art needs mod.ff; budget <= 24 elements per player, destroy not hide.
- Any server -> client state (scores, ping, wheel set) should follow the existing protocol rules: stamped payload, only on change, one reliable command about 1 KB, `|` and `~` separators, no `"`/`%`/newline.
- Release dependency: players on the official updater client cannot see any Lua Tab/wheel until PR #697 ships; the Tier-2 (HudElem) version is the only no-download path today.
