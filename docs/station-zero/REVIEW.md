# REVIEW of the STATION ZERO bible

Two independent reviewers, fresh context, told to find what is generic, filler, incoherent, overpowered or
unbuildable. Each reviewed twice: a first pass on the first complete bible, then a verification pass on the
corrected one. Their full texts are in `review/` (`reviewer-A.md`, `reviewer-B.md`, `final-A.md`,
`final-B.md`); the author's decisions are in `review/CHANGES-AFTER-REVIEW.md`. This page is the summary: what
they found, what was changed, their final remarks, and what is still open. Nothing here was tested in the
game: this is a review of a design on paper.

## Reviewer A (creative, originality, coherence, balance)

**First pass.** Scores between 3 and 7 of 10 per chapter. Main findings:

| Finding | What was done |
|---|---|
| All four wonder weapons dealt a share of the zombie's health, so they never weakened | every effect now has a flat damage rated by round (the health of a round-R zombie); nothing kills "at any round" |
| The token gun made money at every round | hit points withheld for it, pierced kills pay half, refund only for a one-token head kill (base fare, once per 1.5 s); the sums are written out and checkable |
| The yellow paint set off a whole crowd; density 78 untested | one burst generation, six targets a burst; every weapon and perk is tested at 24 and at 78 alive |
| Three weapon ideas were borrowed (dancing zombies, inhale-and-fire, a film title as a name) | the magenta can now sends the dead to wait behind the yellow line (the map's own joke); the pistol stamps an address and sends; the paint rig is TOP TO BOTTOM |
| The mini boss's mark could be dodged and used to grief; he resembled another game's stalker | mark by points earned over two rounds, away players skipped, fines returned only to the fined player; redesigned as a short, wide, lamp-headed inspector who climbs out of floor plates |
| The Parlour copied a real 1870 pneumatic subway; the Terminus echoed a film's ballroom | the Atmospheric is now a parcel post with one season of "passenger dispatch", its salon has a fork wall and a listening horn; the Terminus is a platform made of printer paper |
| The Roller round and the Terminus could be exploited | Rollers throw skates at players who hide out of skating reach; the Terminus visit is 40 s with a 150 s cooldown, downed players travel, spawning pauses |
| The quest resolved the main-quest hook every match; two "Graffiti Kings"; an impossible handle | the clock stops at 23:59:59 and no arrival is logged; the dead painter is Undercoat; the handle is ceremonial |
| The transport read as a loop line with stops and fares | renamed and re-themed as post (hatches, an address dial, postage); the rider chooses the destination; distance costs time and points; the lever swaps near and far and cannot trap a team |
| Two new perks dull or copied; 28 of 40 dances were library clips with puns | Baker's Dozens (every thirteenth hit) and Bon Voyages (the Post and traps) replace them; Sour Grudges forgives the next hit instead of healing; 21 dances are now animated from the map |
| Real brands and phrases; the chime used a broadcaster's notes; the setting leaned on two shipped maps | a transit phrase, a news brand, two titles and a call sign removed; the chime is three notes that are not a chord; the arcade became a copy shop; the gang became the authority's sacked painters |
| 27 contradictions between files | fixed, and the wiki, audio and emote chapters brought into line twice |

**Final remarks of reviewer A** (verification pass, before the last round of fixes): of its ten main findings,
one resolved and nine partly. Scores 5.5 to 8 per chapter (weapons and emotes lowest at 5.5; client
capabilities highest at 8). Verdict: *"Yes, with conditions. The bible is now creative, largely coherent and
mostly its own: the commuter dead, the board as the interface, the clock quest, stamp-and-send, ALL STAND, the
lamp-headed Inspector, the new Three-Tone. The layout, quest, Capsule Post version 1, HUD and audio can go to
build teams now. The weapon and perk work should wait until chapters 05 and 06 are fixed."* Its three
remaining changes: close the Dispatcher and Exact Change loops and cap wonder-weapon damage on the Inspector;
remove the Capsule Post shelter and the foam safe room; give the Terminus a look of its own, rename borrowed
titles and clear the contradictions.

**After those remarks, changed:** a send uses up its stamps and has a cooldown; the refund is limited and the
sums redone; bursts hit six; wonder-weapon hits on the Inspector are capped at 2,000 with no lamp bonus; a
rider must rest 45 s between rides and keeps the Inspector's mark; the foam only halves attacks; the Terminus
became printout; the Atmospheric became a parcel post; five names changed. These last changes were **not**
re-reviewed.

## Reviewer B (buildability, plan, player delivery)

**First pass.** 44 findings; chapter 07 (enemies) "not buildable as written". Main findings:

| Finding | What was done |
|---|---|
| Nothing proves bullets can hit a script-driven body; the only known collision route crashes a match | stated as unproven; first probe of package E1 with three routes and a clone counter; the stand-in enemies ship until it passes |
| A crowd body is at least two entities; nobody counted entities | package TF8 keeps an entity ledger and counts the template map's pools; the cap is derived from it |
| "6,000 compiled static props" ignored that models without a twin in the template map crash or stay entities | package TF10 before any dressing; budgets count such models as entities until it passes |
| No system knows crowd bodies exist | one enemy registry in E1; every weapon, perk and trap is tested against a mixed crowd |
| The map's fallback was a manual install; deployment choices were written as decisions | no manual install is offered as acceptable; the map stays on private servers until it can install itself; every such choice is now a recommendation to the owner |
| The stair lesson was read backwards | the stock stair construction everywhere, with a new file check of navigation against the surface |
| The order broke "tool first" | build time, the meters, the ledgers and the delivery test moved to wave 0; the crowd probe and a stress test to wave 1; culling before dressing |
| Budgets could not be measured; two chapters disagreed | package TF9 builds the meters; one figure (85 % of the shipped map's frame rate), fixed measuring points, 1080p |
| Layout errors (a door between rooms that do not touch, an unbuildable chute, a walkable pit under walkable cars) | rooms moved, the chute removed, the pit under the train closed; the generator must refuse such a door |
| Water, rain, fog, changing screens designed with no tool | each has a first probe and a written fallback (`02-WORLD.md` 8.1) |

**Final remarks of reviewer B** (verification pass): 75 items checked: 52 resolved, 22 partly, 1 not resolved
(this file was listed and did not exist yet). Verdict per chapter: buildable as written for the lore and
wiki, camos, Tab and HUD, audio; buildable with named fixes for the rest; chapter 07 "was not buildable
before" and now is with fixes. Final paragraph: *"Can build sub-threads execute 12-BUILD-PLAN.md without
inventing or asking? No, but it is close. The first review's blockers are now early first probes with
fallbacks, the order puts tools first, and 14 is honest."* Its three first changes: give the plan one voice
(complete the delivery table, remove stale lines, fix two proofs, give two tool packages their inputs, name
the stress test's machine); fix the numbers that drive budgets and geometry; write the missing rules of the
redesigned mechanics.

**After those remarks, changed:** the Fare Hall extended so that door D1 joins touching rooms; 60 bodies and
120 entities; the dial's input defined (tap and hold of Use); the mark kept through rides; sends snapped to
walkable floor; ALL STAND with no free place; the Terminus pause as a probe with a fallback; a skate mask in
the scene description; the stand-in boss's rules; the delivery table completed and corrected; inputs and
method for TF9 and TF10; a stated stand-in machine for the stress test; stale lines removed. These last
changes were **not** re-reviewed.

## What is still open (said plainly)

1. **Nothing is proven.** Every number in the bible is a design value. The unproven mechanics are listed with
   their first probes and fallbacks in `12-BUILD-PLAN.md` section 4, `05-WONDER-WEAPONS.md`, `06-PERKS.md`,
   `07-ENEMIES.md` 2.2 and `02-WORLD.md` 8.1. The three that decide the most: the stress number (ST1), the two
   finished rooms (W2), the one crowd body that can be shot (E1).
2. **Seventy-eight zombies** on the official client depends on E1. If its probes fail, the official-client cap
   stays 24 and the real 78 waits for the client change (CF2), which is deep.
3. **The map cannot yet reach a player by itself.** TF6 measures it first; CF3 builds what is missing.
4. **Reviewer A's partly-resolved items that the author kept on purpose**: the Capsule Post is still four
   hatches on a ring (argued in `03-TRANSPORT.md` section 8); Baker's Dozens is a number whose worth is where
   the thirteenth hit is placed; the city keeps the name Port Halcyon; nineteen library dance clips remain.
5. **The second round of fixes has had no independent reading.** The first act of the sub-thread that picks
   up weapons and perks (WW1, P1) should be one more adversarial read of chapters 05, 06 and 07 section 3.
6. **Balance needs play.** The plans check arithmetic at rounds 10, 25, 40 and 50 with 24 and 78 alive; only
   the owner's play decides whether it is fun.
