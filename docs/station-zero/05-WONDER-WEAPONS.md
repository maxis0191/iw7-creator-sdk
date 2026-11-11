# 05 · THE FOUR WONDER WEAPONS

Four weapons, four verbs: **pay**, **place**, **send**, **paint**. None is a bigger gun; each changes what the
player does and where they stand. All four are original to this map. (The weapons ported from another title
that exist on the servers are a separate module and are not part of Station Zero's set.)

| Weapon | Verb | How it is obtained | Variants |
|---|---|---|---|
| **EXACT CHANGE** | pay: every shot is bought with points | mystery wheel | none (one upgraded form) |
| **LIVE RAIL** | place: two stakes, a standing arc between them | built from three parts | three signal fuses: RED, AMBER, GREEN |
| **THE DISPATCHER** | send: stamp an address on the dead, then post them | the Parlour's small quest | none (one upgraded form) |
| **TOP TO BOTTOM** | paint: the colour tells the dead what to do | mystery wheel; cans found in the map | three cans: MAGENTA, CYAN, YELLOW |

Two come from the wheel, one is built, one is earned.

## Common rules

- **Damage is flat and rated by round.** Every damaging effect has a rating **R**: it deals the full health of
  an ordinary zombie of round R by the stock formula (`research/E-shipped-map-numbers.md` section 5: 150 at
  round 1, plus 100 a round to round 9, then 950 x 1.1^(round - 9)). Up to round R it kills in one
  application; after R it takes more and more. Nothing in this chapter kills "at any round".

  | Rating | Damage | | Rating | Damage |
  |---|---|---|---|---|
  | R24 | 3,970 | | R32 | 8,510 |
  | R28 | 5,810 | | R34 | 10,290 |
  | R30 | 7,030 | | R36 | 12,450 |
  | | | | R38 | 15,070 |

  For scale: a round-40 zombie has 18,230 health, a round-50 zombie 47,300. The shipped map's own wonder
  weapons deal a flat 2,000 (a one-shot to round 16). Ours are rated higher on purpose, because this map puts
  up to 78 zombies in the fight where the shipped map puts 24, and each also carries a second brake that is
  not damage (a price, charges, a count of stamps, paint).
- **Specials and the mini boss** are never killed outright; each weapon states its effect. On the Night
  Inspector every wonder-weapon hit is capped at **2,000** (the stock rule for the shipped mini boss) and gets
  no bonus on the open lamp: the triple damage there belongs to bullet weapons. What the wonder weapons give
  against him is the *opening* of the lamp, each in its own way (`07-ENEMIES.md`).
- **One per slot**: a wonder weapon takes a normal weapon slot; a player may hold two different ones, never two
  copies. The Lost Property window never returns a wonder weapon.
- **Where the assets ship**: in the map's own zone, delivered with the map, so that nothing changes for players
  of the other maps. Putting them in the servers' global mod instead is a recommendation left to the owner.
- **Animations.** There is no path today from Blender to a game animation (package C1 is running). Each weapon
  first ships on the first-person animation set of a **donor stock weapon**, with our model built to that
  donor's grip and bones. "Animations wanted" is what replaces the donor set once C1 and C2 are proven.
- **Behaviour scripts.** Three families exist in the project (`src/bo3wpn/paris_bo3wpn.gsc`): the cone push
  with knock-down, the chain between targets from a tracked impact point, and the re-fired bullet for
  piercing. Each weapon says what it reuses and what is new.
- **One enemy registry.** Every weapon script reads enemies only through the registry of package E1
  (`07-ENEMIES.md` 2.2), so that it acts the same on engine zombies and on crowd bodies, and is tested against
  a mixed crowd, with 24 alive and with 78 alive.
- **Sounds and effects** are made for this map; none is taken from a game. Effects are stock particle systems
  re-timed and re-coloured, because authoring an effect from nothing is not a documented path.

---

## 1. EXACT CHANGE

**Fantasy.** A fare box rebuilt into a carbine by a sacked paint-shop hand who was tired of paying. Brass
hopper on top, a coin chute for a barrel, a turnstile arm for a lever. It fires transit tokens. It has no
ammunition: it has your money.

**Obtained.** Mystery wheel, in the normal pool.

| Property | Value |
|---|---|
| Type | single shots, lever-cycled, 110 a minute; visible brass tracer; instant hit |
| Hopper | 12 tokens; reload 2.4 s; no reserve: the hopper refills for free |
| Fare per shot | **30 points**, taken when the shot leaves. Under 30 the trigger clicks and the HUD reads "EXACT FARE ONLY" |
| Surge pricing | each further shot within 0.6 s of the last costs 10 more (30, 40, 50 … capped at 100); back to 30 after 1.5 s without firing |
| Damage | body **R24** (3,970); head 2.5 times that (9,920: one head shot kills to round 33) |
| Penetration | passes through 2 zombies, full damage to each |
| Points | its hits pay **no** hit points (the stock 10 a hit is withheld for this weapon). A kill on the first zombie pays the stock kill reward (60, or 100 for the head); kills on zombies behind it pay half |
| Refund | a kill by **one** token to the head of the first zombie returns the base fare of 30 (never the surge), at most once every 1.5 s; nothing else refunds |
| Max Ammo, wall ammo | no effect |
| Rollers | one token trips a Roller; a second kills it |
| Night Inspector | like every wonder weapon, at most 2,000 a hit on him (`07-ENEMIES.md`); while he lives every fare is doubled ("penalty fare") |

**The sums** (so the claim can be checked; zombie health by the stock formula). One body token kills to round
24: +60 for 30 paid. Two body tokens (7,940) kill to round 31: 60 or 70 paid for 60. One head token (9,920)
kills to round 33: 100 for 30, refunded. Two head tokens kill to round 40: 70 paid for 100, no refund. Three
head tokens kill to round 45 (100 or more paid for 100): break-even. From round 46 every kill loses money,
and by round 50 (47,300 health) a zombie costs five perfect head shots. A line of three pierced by one token
at round 20 pays 60 + 30 + 30 for 30. So: profitable for anyone to round 24, for a good shot to round 40, for
nobody after 45.

**Upgraded: KEEP THE CHANGE.** Body **R32** (8,510), head 21,270 (one head shot to round 41); hopper 18;
passes through 4; a kill drops a brass token worth **25 points to whoever picks it up** (12 s on the floor, at
most one drop a second per shooter, at most 12 lying). Sum at its best: six kills in a few seconds give about
150 points in tokens to the team for 180 or more paid in surging fares: it shares money, it does not print it. With perfect head shots the upgraded form stays near break-even to about round 52.

**Why it is not overpowered.** It is the only weapon that makes you poorer when you miss; sustained fire is
dear; it gains nothing from Max Ammo; past round 31 it pays only for head shots and past round 45 for nothing.

**Look.** Brushed brass and worn HRT green enamel; a glass-fronted hopper in which the tokens drop one by one;
the lever is a chromed turnstile arm; a fare plate riveted on the side: "FARE 30".

**Sounds.** Coin into a steel chute with a spring crack on every shot; turnstile ratchet for the lever; a
rejected coin for the empty click; a till bell for the refund; one bright "ting" for a picked-up token.

**Effects.** Brass tracer with a short spark trail; a spray of coins on impact; dropped tokens spin on edge.

**Animations.** Donor: a stock pump-action shotgun set. Wanted later: lever cycle with the turnstile arm, hopper
top-up, first raise with a token flipped and caught, inspect.

**Scripts.** Reuses the fire event hook and the piercing re-fire. New: fare and surge on the stock score
functions, withholding hit points for this weapon, token pickups (the stock power-up drop pattern).

---

## 2. LIVE RAIL

**Fantasy.** A track gang's tool turned outward: a collector shoe from under a train on an insulated
hot-stick, fed by a cable drum on the hip. It throws stakes. Two stakes make a piece of third rail standing in
the air.

**Obtained.** Built at the Car Barn workbench from three parts; each part is in one of three places per match:

| Part | Possible places |
|---|---|
| Collector shoe | Car Barn (on the jacked car's bogie), Platform A West (the open pit just west of car 1), the Boneyard (wreck pile) |
| Hot-stick | Transit Police Post (evidence cage), Signal Cabin (behind the lever frame), the Sump (catwalk) |
| Cable drum | Converter Hall (beside G-2), Lodestar Exchange (printer room), Shelter 7 (stores) |

The builder receives the weapon. Afterwards any other player may take one from the bench for 2500 points, once
per player per match.

| Property | Value |
|---|---|
| Type | one stake per pull; flies at 3000 units per second; sticks in any world surface |
| Load | 2 stakes; reload 2.0 s; reserve 12 (6 pairs) |
| The fence | when the second stake lands within 600 units of the first with a clear line between them, an arc stands between the two for 14 s |
| Fences alive | at most 2 per player; a third pair collapses the oldest |
| Crossing | a zombie within 20 units of the line takes **R30** (7,030) and is stunned 1.5 s and **pushed 48 units back off the line**. One hit per zombie per fence per 2 s |
| Charges | each fence gives 24 hits, then burns out |
| Direct hit | a stake that hits a zombie deals **R34** (10,290) and does not plant |
| Players | touching the arc: 15 damage per half second and slowed |
| Failed pair | too far or no line of sight: both stakes spark for 1 s and die; the pair is spent |

**Variants: the three signal fuses.** The weapon carries one fuse; the fence takes its colour. AMBER is fitted
when built; RED is in the Signal Cabin's relay cupboard once the road is set for Pack-a-Punch; GREEN is in the
Converter Hall's fuse board once all four Capsule Post hatches are unsealed (the board has one lamp per hatch,
so the condition can be read). Swapping at any of the map's three fuse boxes takes 2 s and is free.

| Fuse | Aspect | Fence | Its own job |
|---|---|---|---|
| **AMBER** | caution | 14 s, 24 charges, R30 | **the only fuse that acts on specials**: it trips Rollers (they fall and slide, alive) and stuns the Night Inspector for 1 s on his first crossing of each fence |
| **RED** | danger | 7 s, 12 charges, R30; each zombie it kills arcs to 2 more within 160 units at R24 (no further jumps) | the short, violent clearing tool; does nothing to specials |
| **GREEN** | proceed | 20 s, no charge limit, no damage; zombies that cross are slowed by 60 % for 6 s and marked: a marked zombie pays 20 extra points to whoever kills it (at most 40 marks alive) | the team's training and income fence; does nothing to specials |

**Upgraded: THE FOURTH RAIL.** Load 3 stakes; stakes of one load link to each other (three make a triangle);
durations plus half; charges 40 (RED 20); ratings **R38** and R32 for RED's jumps.

**Why it is not overpowered.** It does nothing where the player has not prepared a line. One hit per zombie
per 2 s and the push-back mean a fence holds a crowd, it does not grind it; 24 charges end a fence that is
doing too well; twelve stakes are six fences a refill; it hurts its user; past round 30 a crossing no longer
kills. Named test cases: a fence across a Capsule Post hatch at arrival; a Double Takes image inside a
triangle; RED with 78 alive in a corridor.

**Look.** A yellow fibreglass hot-stick with a pistol grip, a bronze shoe at the muzzle, a ceramic insulator
stack, a cloth-wrapped cable to a small drum, a fuse holder with a window that glows red, amber or green.
Stakes are ceramic-collared copper spikes. The fence is a taut white core with a fringe in the fuse colour.

**Sounds.** A contactor slam and cable whip to fire; a ceramic knock to land; a substation breaker's "thunk,
hum" as the fence forms; a 50-cycle hum that crackles faster as charges run low; a fuse pop at burn-out.

**Effects.** Stake trail; sparks at a planted stake; the arc; a flash at each crossing; a ground glow in the
fuse colour.

**Animations.** Donor: a stock single-shot launcher set. Wanted later: break-open reload, fuse swap, first raise.

**Scripts.** Reuses the tracked impact point and the chain (RED). New: the "segment" family (two points, a line
test, per-zombie hit timers, charges, owner limits) and the fuse state.

---

## 3. THE DISPATCHER

**Fantasy.** Ambrose Vayle's dispatch pistol: brass, bellows, a rubber address stamp where the muzzle should
be. Every parcel on the Atmospheric was stamped with its destination and the tube did the rest. The pistol
still works. It does not ask what the parcel is.

**Obtained.** The Parlour's small quest, "Undelivered":

1. Be dispatched by the Capsule Post to three different hatches. The first time a player arrives at each of
   three hatches, a **message cylinder** from 1897 rattles out behind them (three in the match, shared; the
   hatch lamp blinks white while one is waiting).
2. Bring the three to the dispatch desk in the Parlour: its drawer opens. In the drawer, the pistol and a card
   in Vayle's hand: "Charge at the organ. Hold on."
3. Hold Use at the organ console in the Bellows Vault for 20 s while the Bellows breathes on the pistol; the
   console lamp fills amber to green; zombies come (a burst as for a quest clock).

The player who charges it keeps it. The desk then offers one more for 2500 points. Two exist in a match at most.

| Property | Value |
|---|---|
| Fire | **STAMP**: a short-range shot (reach 400 units, instant) that stamps the zombie it hits: 600 damage and a glowing address label on its chest. Up to **4** zombies can carry your stamp at once; a stamp lasts 12 s |
| Ink | 12 stamps per pad; 36 in reserve; changing the pad 2.2 s |
| Aim button, held 0.4 s | **SEND**: the bellows fires. Every zombie carrying your stamp is posted to the point under your crosshair (up to 1,200 units away, in sight). The point is snapped to walkable floor within 64 units; if there is none (a ledge, the closed pit, a wall high up) the send is refused with a dry click and no ink is used, so a sent zombie can never be stranded where the round cannot end: it is snatched off its feet and flies there in under a second |
| What happens to a sent zombie | if its remaining health is **R30** (7,030) or less it is sent for good: it bursts at the destination. If it has more, it takes R30 and lands there knocked down for 2 s. **Either way the stamp is used up by the send**, and the bellows needs 3 s before it can send again |
| The burst | each zombie that bursts at the destination deals **R24** (3,970) to zombies within 140 units of that point; bursts from the same send do not add on one target beyond two |
| Send with no stamps out | a puff of air: zombies within a 200-unit cone are knocked down, no damage; costs one stamp of ink |
| Sending into a Capsule Post hatch | stamped zombies sent at an unsealed hatch are posted away and come out of the hatch one segment on, 3 s later, knocked down for 2 s. No kill, no points: it moves a problem |
| Rollers | can be stamped; a sent Roller is thrown to the point and falls for 2 s (alive); stamps on Rollers last 6 s |
| Night Inspector | cannot be sent. A stamp on his lamp glass holds it open for 3 s (once every 15 s) |
| Self | sending onto your own feet knocks you down for 1 s |

**Upgraded: FORWARDING ADDRESS.** 6 stamps out at once; pad 16, reserve 48; send rating **R38** (15,070) and burst
R32; and its signature: a sent zombie that survives walks back toward the place it was stamped for 4 s before
it remembers the player (unproven: steering a stock zombie to a point; fallback: it stays down for 4 s).

**Why it is not overpowered.** A kill takes two actions on the same zombie, and the first must be done inside
400 units. Four stamps a send is the ceiling: twelve stamps are three full sends a pad. Past round 30 a send
moves and wounds, it does not kill: a send uses its stamps, so a tough zombie must be stamped again (one of twelve) for every 7,030 it takes. The burst is small and capped. Its real strength is position: it takes
four zombies off a teammate and puts them somewhere else, which is support, and it is meant to be.
Named test cases: stamp, then Sour Grudges (wonder-weapon kills do not count for that perk); sends into a
Live Rail fence; sends with 78 alive.

**Look.** Polished brass and oxblood leather bellows; where a barrel would be, a round rubber stamp in a brass
collar, wet with violet ink; an ivory-coloured grip; a little wheel of address rings above the stamp that
spins when it fires. Engraved: "HALCYON ATMOSPHERIC DISPATCH Co. · No. 12". The label on a stamped zombie is a
glowing paper tag reading "FORWARD".

**Sounds.** Stamp: a post-office "thump" with a wet edge. Send: a bellows cough, then a rising whistle for
each parcel and a thud of arrival. A burst is a paper bag popped under water. Empty pad: a dry stamp.

**Effects.** A violet ring where the stamp lands and a tag that flutters; a pale streak along each parcel's
flight; scraps of paper at the destination.

**Animations.** Donor: a stock heavy pistol set. Wanted later: pad change, the bellows squeeze with the off
hand, first raise with the stamp tested on the back of the hand.

**Scripts.** Reuses the cone knock-down (the puff). New: stamp state per zombie with timers and an owner cap;
reading the aim button as a second trigger (unproven while a pistol is aimed: the fallback is melee held);
moving a zombie through the air to a point (a real zombie is killed or relocated by the stock spawner calls
and its flight is drawn by a short-lived model and a streak; a crowd body is simply moved); the capped burst.

---

## 4. TOP TO BOTTOM

**Fantasy.** The paint rig of Undercoat, the last of the Zero Kings: a pressure pot on a strap, a spray lance,
three sockets for cans. The Kings were the authority's own livery painters; they knew the colour code of the
railway better than its managers. Undercoat found out in 1985 that the Carrier reads colour as a signal. Paint a
dead commuter the right colour and he does what the colour says. ("Top to bottom" is what a painter calls a
car covered from roof to sill.)

**Obtained.** Mystery wheel, in the normal pool, with the MAGENTA can. The other two cans are found, per player,
per match:

| Can | Where | Feedback so that nobody has to guess |
|---|---|---|
| **CYAN** | the Zero Kings' stash in the Boneyard; the lid opens for a player who has stood before three of the five murals | each mural logs with a rattle-and-click and a can icon; the stash lid shows three paint dots that fill |
| **YELLOW** | dropped by the first Lodestar Cleaner (the yellow-suited zombie) that the player has tagged with any colour, whoever kills it | the tagged Cleaner's suit visibly bulges with a can outline |

| Property | Value |
|---|---|
| Type | continuous spray while the trigger is held; a cone 380 units long and 24 degrees wide; applied ten times a second |
| Paint | each can has its own tank: 100 units, used at 10 a second (10 s of spray), 200 in reserve |
| Switching can | the weapon's alternate-mode key cycles the cans the player owns; 0.5 s |
| Direct damage | none worth counting (5 a tick). It marks; it does not shoot |
| "Tagged" | after 0.5 s of exposure a zombie drips that colour. A zombie holds one colour; a new colour replaces the old |

**Variants: the three cans.**

| Can | Railway meaning | What a tagged ordinary zombie does | Limits |
|---|---|---|---|
| **MAGENTA · "ALL STAND"** | the colour of "wait here" boards | turns away, walks to the nearest free waiting place (platform edge, bench, queue rail; within 400 units and not within 150 units of a player) and stands behind the line facing the track for 6 s. With no such place it stands where it is for the 6 s. When the 6 s end it takes **R28** (5,810) | it is not removed, it is parked: a place holds 6. Shooting a parked zombie wakes it: it loses the tag and takes no end damage. Every zone has waiting places (placed by W1a: at least one per 600 units of walkable length) |
| **CYAN · "WET PAINT"** | the colour of "caution, slippery" | sprayed on the **floor**: a slick up to 200 units long for 12 s. Zombies crossing fall (1.5 s) and are slowed by half for 4 s. Rollers fall and slide (alive) | no damage; at most 3 slicks per player |
| **YELLOW · "HAZARD"** | the colour of "danger, do not approach" | carries on normally, striped yellow, for 10 s. If it dies in that time by a **player's** weapon it bursts: **R28** to the six nearest other zombies within 160 units. The burst does not tag, and a zombie killed by a burst does not burst | useless alone; trap kills do not set it off; one generation only |

| Against | Effect |
|---|---|
| Rollers | MAGENTA: they circle once and keep coming. CYAN: trip. YELLOW: tagged as normal |
| Night Inspector | MAGENTA: none. CYAN: he slips once every 20 s and his lamp is open for 1.5 s. YELLOW: bursts near him deal 2,000 at most, as every wonder-weapon hit does |

**Upgraded: END TO END.** Cone 480 units; tanks 150; ratings **R36** (12,450); and the signature: when a tagged
zombie dies, its colour splashes on untagged zombies within 120 units for 2 s (one hop; a splash of YELLOW
tags but those zombies still burst only if a player's weapon kills them).

**Why it is not overpowered.** Short reach, half a second of held stream per target, no damage of its own.
MAGENTA parks six per waiting place and wounds late; CYAN only controls; YELLOW needs a second gun and stops
after one generation, so a crowd of 78 cannot be set off by one kill. Named test cases: YELLOW with 78 alive
packed in the tunnel cess; YELLOW with a trap; MAGENTA with every waiting place full.

**Look.** A dented steel pressure pot under layers of HRT livery colours and the Kings' crowns, a brass lance
with a fan nozzle, three real spray cans in a rotating collar (the chosen can clicks to the top). The paint is
thick, glossy and too bright for the station: the only saturated colour on the map.

**Sounds.** A spray can's hiss, close and dry, with the ball rattle on every can switch; a wet "slap" for a
tag; a platform whistle and shuffle for ALL STAND; a relay tick for HAZARD; a squeak underfoot on the slick.

**Effects.** A coloured aerosol cone; drips on tagged zombies (an effect on the body, not a new skin); a glossy
slick; a flat ring of yellow thrown outward by a burst.

**Animations.** Donor: a stock sub-machine-gun set held at the hip. Wanted later: can rotation, pot pump, a
shake-and-rattle inspect, first raise with a test burst.

**Scripts.** Reuses the cone test. New: the "status" family (per-zombie colour state with timers, effects on a
body tag), sending a zombie to a waiting place and holding it (the stock idle-spot structs that the map's
"commuting" already uses), the slick (a timed box that trips), the burst-on-death hook.

---

## Mechanics that are unproven (first probes of their packages, each with a fallback)

| Weapon | Unproven mechanic | Fallback |
|---|---|---|
| LIVE RAIL | a launcher whose projectile sticks in any world surface and reports where | a sticky grenade-type projectile; if no impact point can be read, the stake plants at the end of a script trace from the eye |
| LIVE RAIL | an arc drawn between two arbitrary points | a row of small arc effects every 48 units |
| THE DISPATCHER | reading the aim button as a second trigger while a pistol is held | SEND moves to the melee button held; the weapon then has no melee |
| THE DISPATCHER | a zombie flown to a point | the zombie is hidden where it stands, a streak effect flies, and it is placed (or its burst happens) at the point |
| TOP TO BOTTOM | a continuous spray (no flame-type weapon is in the stock tables) | a full-automatic weapon with no bullet damage and a script cone, the spray drawn as its muzzle effect |
| TOP TO BOTTOM | holding a zombie at a waiting place from script; a three-way alternate-mode chain | a 6 s stun where it stands; two cans on the base weapon, the third on the upgrade |
| all four | **flat rated damage**: a script-set amount applied to a zombie regardless of the weapon file's damage | the weapon file's damage is set to 1 and the script applies the rated amount on the hit event; if the hit event gives no victim for a weapon type, that weapon falls back to a stock damage value near its rating at round 20 |
| EXACT CHANGE | withholding the stock 10 points a hit for one weapon | first probe of WW1; fallback: the points stand and the fare is 40 |
| EXACT CHANGE, LIVE RAIL | tokens and stakes are entities | their worst case is written in the entity ledger (TF8): 12 tokens in all, 6 stakes per player; if the ledger is tight, tokens become an effect plus a script pickup radius |

## Balance view across rounds (ordinary zombies)

| Round (zombie health) | EXACT CHANGE | LIVE RAIL (AMBER) | DISPATCHER | TOP TO BOTTOM |
|---|---|---|---|---|
| 10 (1,045) | one token a zombie; +30 a kill | a fence holds a doorway alone | stamp and send kills four at a time | ALL STAND parks and kills; CYAN makes a lane |
| 25 (4,365) | two body tokens (break-even) or one head (+100) | still one crossing a zombie; charges run out in seconds with 78 alive | still kills on send | ALL STAND still kills; YELLOW pairs are the strong play |
| 40 (18,230) | five body tokens (a loss) or two head tokens (a small profit) | three crossings a zombie: it holds a line for others | a send throws four away and wounds them: rescue, not kill | control only; the upgrade's ratings give a few more rounds |
| 50 (47,300) | five head tokens a zombie: a loss on every kill | seven crossings: a stun line | position only | position only |

Each weapon stops being a solution at a different round and stays a tool after it. No round plays like the
one twenty rounds earlier.

## The proofs every weapon must pass (measured)

1. File checks: weapon audits and mod preflight (seconds).
2. Behaviour in a plan with placed zombies: counts of killed, stunned, tagged, parked, sent against the numbers
   above, at rounds 10, 25, 40 and 50 (health set by script), with 24 and with 78 alive, engine zombies and
   crowd bodies mixed.
3. Economy for EXACT CHANGE: score before and after 100 scripted shots for each row of "the sums".
4. The named test cases of each weapon and the combinations: each perk with each weapon; fence and slick at a
   hatch; a trap with each weapon.
5. The mini-boss numbers on a scripted Inspector.
6. Sound measured as audible from the game (the audio witness); frames of each effect, the first-person model
   and both camos judged by independent reviewers.
7. Two clients: the second player sees the fence, the paint, the flight and the tokens.
