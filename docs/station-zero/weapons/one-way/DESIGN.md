# ONE WAY: a wonder weapon for Station Zero (design, 28 Nov 2026)

Working id `one-way` (asset prefix `iw7_szoneway`). "ONE WAY" is the lead's working title; the names a player reads
are in section 12 and are fallback copy. Nothing in this page was run in the game: it is a design, with the
state of the engine and of our tools checked on 28 Nov (section 10). Canon: `../../01-LORE.md`.

## 1. The fantasy, in one sentence

**You do not shoot the dead: you sell each of them a ticket, and on the guard's bell the train that is not there
comes through and collects every ticket holder at once.**

It is a token clerk's ticket-issuing machine, rebuilt as a gun by someone who worked the Fare Hall window on the
night of the Midnight Service. Card tickets, a date press, a guard's bell, six small lamps. The dead of this
station are commuters: they are not hungry, they are late. A commuter who holds a ticket and a departure is no
longer late. He stops running. He waits for the bell.

Why this one, and not one of the bible's four (`../../05-WONDER-WEAPONS.md`): the reviewers named "the commuter
dead" and "ALL STAND" as the things that are this map's own, and scored the weapon chapter lowest (5.5 of 10).
ONE WAY takes the map's central joke (the dead wait for a train that is already there, `00-PITCH.md`) and its
central line of canon (the 23:47 "does not move and takes them anyway") and makes them the whole weapon instead
of one paint can out of three. Section 9 says what it does that the four do not.

## 2. The mechanic

The verb is **issue**. The station does the rest, on time.

| Step | What happens | Rule |
|---|---|---|
| **Issue** | each pull prints one card ticket and fires it (instant hit, a pale spinning card as tracer, reach 1,500 units). The dead it hits is **booked** on the next departure: the ticket is seen stuck to its chest | no damage on the hit. A body hit is a second-class ticket, a head hit a **first-class** ticket. A zombie holds at most 3 tickets |
| **Calm** | a booked dead flinches for 0.6 s (it looks down at the ticket), then **walks** until the departure, whatever the round's speed | it still comes at the player and still hits; it has stopped running. A zombie that was carried over (below) cannot be calmed for 12 s |
| **The headway** | six lamps on the machine go out one a second. The departure is every **6.0 s**, on one beat shared by the whole station (server time, not the weapon): it does not wait, cannot be rung early, and is the same for every ONE WAY in the match | the lamps and their ticks run only while this player has a ticket out. A ticket issued in the last 0.5 s ("doors closing") is valid for the departure after |
| **The bell** | the guard's bell rings twice. Bars of warm window light sweep through the room with the sound of a train that is not there. Every booked dead takes the sum of its tickets | flat rated damage, section 3. Kills and points go to the ticket's owner |
| **Taken** | a booked dead whose health is covered is pulled sideways off its feet into the light and is gone; its tickets flutter down where it stood | a kill, with the stock kill reward |
| **Carried over** | a booked dead with more health than its tickets takes the damage and is **carried one stop**: it leaves with the train and is put back where it stood at the next departure, down for 1.5 s | it stays alive for the round count; at most 8 carried at once per weapon (12 upgraded); a returned zombie takes ticket damage but is not carried again for 12 s |
| **Full train** | 6 or more taken for good on one bell (six cars) | 4 tickets go back to the reserve; the bell rings a third time |

**What the player does every five seconds.** Reads the lamps. Puts three to six tickets on the front rank, heads
when he can. Walks back through dead that now walk. Bell. The rank is gone; the unbooked ones behind it arrive
at a run. Again.

**What skilled play looks like.**
- *Issuing late.* A ticket issued with one lamp left kills in a second; issued with six it calms for six. The
  same shot is a kill or a hold, and the lamps decide which.
- *Doors closing.* A ticket in the last half second books the departure after: 6.5 s of a walking zombie, bought
  on purpose, to carry a team mate's revive or to hold the last zombie of a round.
- *Exact fare.* One second-class, one first-class, two, three: issuing what a zombie needs and not one more
  (twelve tickets a stack).
- *Full trains.* Six on one bell pays four tickets back: a player who batches plays almost for free up to the
  rating; a player who issues one at a time runs dry.
- *Reading the carry.* Past the rating a bell clears the platform for six seconds instead of killing: the
  skilled player uses the empty six seconds to move, and stands off the spot where the carried will be put back.

**Why four players want it differently.** The runner wants the front of his train walking. The one who holds a
window wants full trains on a choke, for the refund. The one who revives wants a single ticket on each of the
three dead standing over a team mate: 0.6 s of flinch, then they walk. The marksman wants first-class tickets,
which are the only ones that still kill past round 33.

## 3. Numbers

Flat damage rated by round, the bible's rule: rating **R** is the health of an ordinary zombie of round R (150 at
round 1, +100 a round to round 9, then 950 x 1.1^(round - 9)). Nothing here kills at any round.

| Property | ONE WAY | Upgraded (section 4) |
|---|---|---|
| Second-class ticket (body) | **R24**: 3,970 at the bell | **R32**: 8,510 |
| First-class ticket (head) | 2.5 x: 9,920 (one ticket takes to round 33) | 21,270 (to round 41) |
| Tickets on one zombie | 3 at most; they add (3 first-class: 29,760, round 45) | 3 (63,810, round 53) |
| Stack, reserve, rate | 12 in the stack, 60 in reserve, one ticket every 0.4 s | 18, 90, every 0.35 s |
| Reload | 2.4 s (2.8 s from empty) | same |
| Headway | 6.0 s, shared; "doors closing" 0.5 s | same |
| Calm | 0.6 s flinch, then walk until the bell | same |
| Carried at once | 8 | 12 |
| Full train | 6 or more taken: 4 tickets back | 6 or more: 6 back |
| Points | a ticket pays no hit points; a kill pays the stock reward (first-class as a head kill) | same |
| Max Ammo | refills the reserve. Wall ammo: none | same |

By round (ordinary zombie; one bell):

| Round (health) | What one stack of 12 does |
|---|---|
| 10 (1,045) | twelve dead taken on one or two bells; two full trains pay 8 tickets back |
| 25 (4,365) | second class no longer kills alone: two a zombie, or one first-class. Six to twelve taken a stack |
| 35 (11,320) | two first-class or three second-class a zombie: four to six taken a stack; refunds become rare |
| 45 (29,350) | three first-class a zombie: four taken a stack by a perfect shot; everything else is carried over |
| 50 (47,300) | nothing is taken by the base weapon. It calms, and each bell empties the platform for six seconds |

**Against the specials** (the bible's common rule: never killed outright, at most 2,000 a hit on the mini boss).
Any agent that is not an ordinary zombie: no calm, no carry, 2,000 at most per bell. *Rollers*: a booked Roller
brakes, falls and slides (alive). *The Night Inspector*: a ticket shown to him is a ticket to check. He stops for
2 s to punch it and his lamp is open for 3 s, once every 15 s. It is the only weapon he answers to as an
inspector. Until those two enemies exist the rule is tested on the stock stand-ins.

**Edge cases that are rules.** Tickets pass through players and do nothing to them. A booked zombie killed by
anyone before the bell is an ordinary kill; its tickets are lost. Two ONE WAYs in a match share the beat; a
zombie holds 3 tickets in all, each credited to its owner, the kill to whoever issued most. A carried zombie
whose place is no longer walkable is put back at the nearest walkable point within 64 units, or at a spawner of
its zone. If the last zombie of a round is carried, the round waits for it. A player who goes down keeps his
tickets out; a player who leaves cancels his.

**Why it is not overpowered.** It never kills at once: every kill waits for the bell, three seconds on average.
Twelve tickets a stack; past round 24 a zombie costs two; past 33 only heads count; past 45 it kills nothing.
The calm is a walk, not a stop. The carried come back. Each brake is a different kind, and each bites at a
different round, so the weapon stops being a solution and stays a tool, as the bible asks of all four.

## 4. Upgraded: the return half

In kind, not only in number: **every dead that is taken for good comes back one bell later as an arrival.** At
the place it was taken, the doors that are not there open: a burst of pale carriage light and a spill of
tickets. Every unbooked ordinary zombie within 120 units takes **R24** (3,970) and flinches. An arrival makes no
arrival; a zombie takes at most two arrivals a bell.

So the upgraded weapon has two beats a bell: who leaves, and who comes back where the last ones left. The player
now leads the next rank over the place he emptied six seconds ago. Pack-a-Punch camos: the map's two
(`../../08-CAMOS.md`); the tickets of the upgraded weapon are printed on the return stock (a second colour).

## 5. How it is obtained

A short build quest in the concourse. Each part is in one of its places per match; the place is told by the
station, not by a marker (a shelf light, a bell that rings by itself once).

| Part | Where (one per match) | State of the place on 28 Nov |
|---|---|---|
| **The machine** (issuing machine No. 0, under a token window) | Fare Hall token booth · Transit Police Post evidence shelf | Fare Hall: the generator's version exists; Police Post: not built |
| **The ticket stock** (a carton: 312 commemorative singles for the inauguration, never collected) | Copy Stop, the uncollected jobs | built (Arcade, `redesign/PLAN.md` section 3) |
| **The bell** (a counter bell that comes away in the hand when it is rung) | Hole Number Nine, the serving counter · Needle Drop, beside the till | built (Arcade) |
| **Fitting** (hold Use 3 s at the bench; Brill's key machine cuts the issuing key) | Heel & Key, the stall counter | built (Arcade); the stall is not entered, the counter is reached from the hall |

The player who fits it receives it. Afterwards the stall offers one more for 2,500 points, once per player; two
exist in a match at most. It takes a weapon slot; the Lost Property window never returns it.

The weapon does not depend on the quest to be proven: the script exposes one call (`give to player`) and three
part hooks; the map section that hosts the quest declares the places. Until the map base is rebuilt it is proven
on a mod zone on a stock map (section 11).

## 6. Animations (all its own: none is a donor's)

The parts that move, the same in every visual direction: the **issuing lever**, the **ticket stack and its
follower**, the **ticket tongue** in the slot, the **stock door**, the **bell striker**, the **six lamps**, the
**carrying strap**.

| Animation | Length | Intent |
|---|---|---|
| First raise | 2.2 s | pulled up by the strap; the left hand gives the bell one test stroke and damps it with the palm; the six lamps come on in a row. The player learns in two seconds that this thing rings and counts |
| Raise, drop | 0.5 s | brought up like a tool, not like a rifle: weight in the right hand, the left steadies the body |
| Idle | loop | weight, breath; the ticket tongue trembles in the slot; the strap swings a little after every move |
| Issue (fire) | 0.4 s | the lever snaps down and forward with the date press's thump, the ticket leaves the slot, the follower climbs one ticket, the next tongue appears. Short hard kick to the left: a stamp, not a shot |
| Issue, last ticket | 0.5 s | the same, then a red flag drops in the stock window |
| Dry issue | 0.3 s | the lever goes half way and springs back; the flag shivers |
| Reload | 2.4 s | thumb opens the stock door; the empty tube drops out; a banded stack goes in, the band is torn off with the teeth of the door; door shut; lever once |
| Reload from empty | 2.8 s | the same, and the flag is pushed back up with a finger |
| Sprint in, loop, out | | carried low and tilted in one hand by the strap, like a cash tin; the bell damped by the thumb |
| Aim up, down | 0.25 s | lifted to the eye: the clerk's window frame around the slot is the sight |
| Melee | 0.7 s | struck bell-first; the bell gives a dull stroke |
| Inspect | 3.5 s | turned over: the fare plate on the back; a finger flicks the bell; the thumb riffles the stack |
| Bell (overlay, at each departure) | 0.5 s | the striker hits twice by itself and the hand takes the jolt |
| Full train (overlay) | 0.6 s | third stroke; four tickets drop back into the stock window |

The world model (what the other players see) uses the stock third-person holding poses: a player's third-person
animations are not in this package's scope, and that is said in the report.

## 7. Effects

| Effect | Intent |
|---|---|
| Issue (first person and world) | a puff of card dust and a spark from the press: no muzzle flame |
| Ticket in flight | a pale card spinning flat, a short white streak; it must read in the dark vision |
| Ticket on a zombie | the card stuck to the chest, its edge catching light; second class buff, first class with a red band, return stock (upgraded) pale green |
| Ticket on the world | the card stands in the surface for a second, then falls |
| Lamp out (first person) | one lamp of six dies with a relay's blue pinpoint |
| The passing train | bars of warm carriage-window light sweeping across walls, floor and bodies for 1.2 s, with dust pulled along the same way: the light of a train with no train in it. It is the weapon's signature and the only large effect |
| Taken | the body snatched sideways into a streak; two or three tickets left turning in the air |
| Carried over, put back | the same streak run backwards; the body arrives on its knees |
| Full train | the light is whiter and the bars closer together |
| Arrival (upgraded) | a tall pale door-shaped burst, a spill of tickets on the floor |

## 8. Sounds (all made for it; no voice, by the owner's freeze of 26 Nov)

| Sound | Intent |
|---|---|
| Issue | a cast-iron date press: one dry thump with the snap of stiff card; never a gunshot |
| Dry issue, last-ticket flag | a sprung lever with nothing under it; a small tin flag |
| Reload set (door, tube out, stack in, band torn, door, lever) | sheet steel and card; the torn band is the loudest thing in it |
| Raise, drop, strap | a leather strap and a kilogram of cast metal |
| Lamp tick, six pitches falling | a relay; the last second is a double tick. Heard by the owner only |
| The bell | a guard's dome bell struck twice, 0.35 s apart, pitched on E5: the first note of the Three-Tone, twice. ZERO owns the three notes; the weapon only ever starts them |
| The passing train | 1.2 s: a pressure wave, wheel beats, the hum of lit cars, gone. No horn, no brakes |
| Taken | a rip of paper and an intake of air |
| Carried over put back, arrival (upgraded) | a door engine's hiss; for the arrival the car-door chime of the map (`../../11-AUDIO-DIRECTION.md`, PE2) |
| Full train | the third bell stroke over a cash drawer |
| First raise, inspect, melee | the test stroke damped by the palm; a finger on the bell; a dull struck bell |

Levels are measured against the stock weapons with the weapon audio witness before any is called done.

## 9. What it does that the bible's four do not

"Mark now, resolve later" exists twice in the bible: THE DISPATCHER (stamp, then send where the player points) and
TOP TO BOTTOM's magenta can (tag, wait 6 s, rated damage). The difference in kind:

- **The player never decides when.** The Dispatcher resolves on the player's button, magenta on each zombie's own
  timer. ONE WAY resolves on a beat that belongs to the station and that the whole team can hear and plan on.
  The decision is who is on the list when it falls.
- **It moves the dead in time, not in space.** Past its rating the Dispatcher throws four zombies somewhere else;
  ONE WAY takes them out of the next six seconds and puts them back in the same place.
- **The calm is not a hold.** Magenta parks a zombie at a waiting place; a booked zombie keeps coming, at a walk.

If ONE WAY is built, the magenta can of TOP TO BOTTOM should get another job: two "wait, then rated damage"
effects in one map are one too many. That is a change to chapter 05, recommended here, not made.

Checked against other games: no cone of force, no chain between targets, no pull to a point, no decoy, no
changed size, no dance. One fresh adversarial read was asked of an independent reviewer (section 13).

## 10. What each part needs from the engine (checked 28 Nov 2026)

Three words, used strictly: **proven** (seen or measured in the running game, with where), **built** (the tool or
the call exists, the result was never proven in the game), **missing** (with the limit and the place).

| Part | State | Evidence, or the limit |
|---|---|---|
| A weapon with a new definition, given, fired, reloaded, upgraded at the machine | proven | four Black Ops 3 ports, 6 to 8 Nov (server `docs/BO3-WONDER-WEAPONS.md`) |
| Detecting the shot and its victim, hit location | proven | `weapon_fired`, `weapon_hit_enemy` (`paris_bo3wpn.gsc:349, :379`); the chained `onzombiedamage_func` of the EXACT CHANGE prototype was never run |
| Flat damage from script, credited to a player | proven for the kill; the points of such a kill are not measured | `dodamage(..., player, player, "MOD_UNKNOWN", weapon)`, 11 Nov |
| Per-zombie state, the list of live zombies, health by round | proven | `getaliveagentsofteam`, `calculatezombiehealth` |
| Flinch | proven | the ported Thundergun's stun fields, 7 Nov |
| **Calm: one zombie forced to a walk** | built | `scragentsetanimscale`, `asm_setmoveplaybackrate` are called in `paris_doom.gsc:510`, `paris_kino.gsc:1668`; no per-zombie slow was measured. First probe |
| **Carried over: an agent hidden, frozen, and put back** | built | `scripted_mode`, `setorigin` exist in lab libraries; "a script-moved agent snaps back to the navmesh". First probe. If it fails, the part is an engine job (agent suspend and resume), and the weapon ships without it only as "not done" |
| An effect on a zombie's tag, an effect at a point | built | called in the ported DG-2; counted by kills, never by frames |
| A new effect | proven by cloning a stock emitter and rewriting its fields (`iw7_vfx.py`, `t7_fx_to_iw7.py`; Thundergun muzzle, 7 Nov). An effect authored from nothing: missing (no authoring tool; the limit is the emitter template) | the passing light is built from stock emitters with our textures; lit particles read black in a dark map, so it uses unlit or emissive ones |
| First-person effects | only from an animation's notes or the definition's flash slots | no client-timed view effect exists in this engine's assets |
| New sounds in the bank, played to their owner | proven | 22 Nov capture (`docs/STATE.md:81`): `playlocalsound`, loops |
| A new one-shot heard by the others at a place | built, and failed once | 4 of 4 weapon-type one-shots were not heard on 22 Nov. First probe: the bell for the team |
| A weapon's fire sound, its level against stock | proven | audio witness, 9 Nov (-17 to -25 dBFS against -16 stock, gains set; the recheck is not recorded) |
| The lamps as a HUD element | proven route, tight budget | server elements, 24 a player, the map plans 20. ONE WAY takes **one** element (seven fixed strings) and reuses the stock ammo counter |
| **The lamps on the weapon itself, driven by the script** | missing | nothing in the project drives a view model's part from script. Candidates to probe: a scriptable part state on the weapon, a view-model gesture. Until one passes, the lamps on the gun animate with the idle and the true count is the HUD element and the ticks |
| The bell overlay on the weapon | built | `forceplaygestureviewmodel` exists (stock perk gestures use it); never played over a weapon of ours |
| A view model authored in Blender, in the hands | built | the authored chain of `x64-zt-extensions` branch `claude/sz-ww1-model` (11 Nov): proven offline only, on a **donor's** skeleton; never built into a zone |
| **Our own skeleton** (lever, follower, striker, door, tongue) | missing in the tool, not in the engine | the model writer refuses a bone the base skeleton lacks: `tools-source/iw7-skinned-writer/build_model.py:319`. The engine draws weapons on foreign skeletons (the ports keep the Black Ops 3 gun's bones). Whether a gun-only bone **moves** in first person was never measured |
| **Our own first-person animations** | missing | no animation authored by us has ever played in first person. The glTF route (`docs/ANIM-GLTF.md`) is proven on a zombie body (0.007 unit) and was never run on a view-model skeleton; additive clips cannot be authored (which slots of a weapon package are additive is the first file check) |
| Inspect | the slot exists (`WEAP_ANIM_INSPECTION`); no trigger found in Zombies | to probe; otherwise a gesture on a key |
| Filming an animation as frames | missing | `capture` takes stills; a sequence at a fixed camera is a tool job for the Platform lane (ledger) |
| Third-person animations of the holder | out of scope | stock poses |

Not found anywhere: a finished wonder weapon of this map. EXACT CHANGE (the two prototype branches) was never run
in the game: its script, its model on the 1887 shotgun's skeleton and its plans are unproven; its animations and
sounds are the donor's and marked so.

## 11. Risks, and the order of proofs (cheapest first)

1. **The mechanic on a stock stand-in gun** (Forge, server plans, seconds): tickets, the beat, rated damage at the
   bell at rounds 10, 25, 35, 45, 50, stacking, the refund, the points of a script kill, two weapons, a leaving
   player, with 24 alive (the official cap) and about 55 (the owner's working target, on the capacity build).
2. **The four probes** of section 10: calm, carried over, an effect on a tag seen in frames, the bell heard by a
   second player. Each answers in one plan.
3. **Does a gun-only bone move in first person**: measured on an existing port (frame difference in the part's
   box across a reload). It decides whether the engine or only our writer stands between us and our own skeleton.
4. **The authored model on a donor skeleton, drawn in the game**: the existing chain, never run. Still a stand-in.
5. **The new-bone writer** (`build_model.py:319`), then our skeleton in the hands at fixed camera frames.
6. **One authored first-person clip** (the issue stroke) through the glTF route onto that skeleton, played by the
   weapon, measured in frames; then the set of section 6. This is the largest unknown of the package.
7. Effects seen in frames; sounds measured; the upgraded form at the real machine; the quest hooks.
8. One real-time run with a joined client, then four players; frame time against the same scene without it.

Risks said plainly. (a) Steps 5 and 6 are tool work nobody has done; if a part cannot be finished it is reported
as "not done" and the donor's animation is never presented as the weapon's. (b) The carried-over rule rests on a
probe. (c) Proven outside the map: the map base is being rebuilt, so the weapon lives in a mod zone on a stock map
until a section hosts it. (d) Builds belong to the Coordinator and the disk is under the build floor (33 GB free
on 28 Nov): who builds, and where, is a question for the session that started this one. (e) The canon holds one
running clock, in the Terminus: ONE WAY carries no clock, no dial and no hour; it counts six lamps.

## 12. Copy (fallback)

Written by Gemini 4 Hydrogen on 28 Nov 2026 because Gemini 4 Neon is refused for this account ("not available");
to be rewritten by Neon when a route exists. The lead checked canon and fit and did not rewrite the prose.

| Key | English | French | Spanish |
|---|---|---|---|
| name, option 1 (its pick) | CARD TICKET ISSUER | DISTRIBUTEUR DE BILLETS | EXPENDEDOR DE BILLETES |
| name, option 2 | THE BOARDING STAMP | TAMPON DE QUAI | SELLO DE ANDÉN |
| name, option 3 | SINGLE FARE PUNCH | COMPOSTEUR ALLER SIMPLE | PICADOR DE IDA |
| name, option 4 | PLATFORM CLERK | GUICHETIER DE QUAI | TAQUILLERO DE ANDÉN |
| name, option 5 | SCHEDULE ENFORCER | CONTRÔLEUR DE QUAI | REVISOR DE TURNO |
| upgraded name, option 1 (its pick) | RETURN TICKET ISSUER | ÉMETTEUR ALLER RETOUR | EXPENDEDOR DE REGRESO |
| upgraded name, option 2 | ROUND TRIP STAMP | TAMPON ALLER RETOUR | SELLO DE RETORNO |
| upgraded name, option 3 | THE RETURN DISPATCH | LE RETOUR GARANTI | DESPACHO DE VUELTA |
| pickup_line | Clerk on duty. Issue fares to clear the platform. | Guichet ouvert. Délivrez les titres pour libérer le quai. | Taquilla abierta. Emita billetes para despejar el andén. |
| description | Issues a card ticket to each late commuter, slowing them to a walk until the double bell clears the platform. Heavy fares survive one stop hurt, and six on a bell pay tickets back. | Délivre un billet aux usagers en retard, les calmant au pas jusqu'à la double cloche. Les plus coriaces reviennent blessés après un arrêt, et six sur une cloche remboursent des titres. | Emite un billete a cada viajero retrasado y lo calma al paso hasta la doble campana. Los más duros vuelven heridos tras una parada, y seis en un toque devuelven billetes. |
| hud_booked | TICKET ISSUED | BILLET ÉMIS | BILLETE EMITIDO |
| hud_first_class | FIRST CLASS | PREMIÈRE CLASSE | PRIMERA CLASE |
| hud_departure | NOW DEPARTING | DÉPART IMMÉDIAT | SALIDA INMEDIATA |
| hud_full_train | FULL TRAIN | TRAIN COMPLET | TREN COMPLETO |
| hud_carried_over | CARRIED ONE STOP | REPORTÉ UN ARRÊT | UNA PARADA MÁS |
| hud_sold_out | SOLD OUT | STOCK ÉPUISÉ | AGOTADO |
| quest_title | Open the Ticket Office | Rouvrir le guichet | Reabrir la taquilla |

Ticket face: `HRT - ZERO LINE` / `STATION ZERO SINGLE` / `DEP 23:47 NO RETURN`.

Lead's reading: canon holds (HRT, ZERO LINE, 23:47; no real brand or slogan). The HUD words and the ticket face
fit. The five names describe the object instead of naming it; a second brief for names only was sent (below).
The working title ONE WAY (French: ALLER SIMPLE; upgraded: RETURN, ALLER-RETOUR) is the lead's and is not copy.

(names, second brief: inserted below)

## 13. Review

(one independent adversarial read of sections 2 to 4 and 9; inserted below)
