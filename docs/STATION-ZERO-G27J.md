# Station Zero g27j: release candidate 2 (21 Nov 2026)

The nine-zone Station Zero (`station_zero2.py`, `cp_iwz2.gsc`, `build-g.ps1`) after the finish pass of 21 Nov 2026.
Package: `<runtime>\iwz-release\cp_iwz-g27j-rc2` (usermap files, `manifest.json` with hashes and the measured results).
Not accepted by the owner, not deployed. Evidence: `<runtime>\iwz-stage2\finish\` (run folders, frames, logs).
The 19-zone bible map (`scenegen.py`, `docs/station-zero/`) is a separate, larger redesign; what it has and g27j lacks is
listed at the end as "does not exist".

## What changed

| Change | Cause, found by measurement | Result |
|---|---|---|
| Door blocker tiles are no longer hidden at load (`cp_iwz2.gsc`) | `hide()` on a brush model removes its player collision on this map (Forge `szf_phys_vis`: shown tiles stop a player-physics line across the door plane, hidden ones do not; stock cp_zmb blockers keep it hidden). Players walked through all five doors and the PaP shutter | all 24 tiles block (g27f); `accept_doors` 70 of 70: each door seals, charges its cost and opens. Shown tiles draw nothing a player sees (0.09 to 0.16 % pixels change) |
| West well moved to -2112..-1904, mirroring the east one, with a `deck_west` strip | its bottom landing was flush with the pit end wall beside the service tunnel door: with the door closed, zombies from the pit wandered there (0 of 10) | wells 9 of 9 with every door closed (`accept_wells_stairs_wells`, g27h and g27j) |
| Stair A in the stock construction by default (`WELL_FIX` default `stair_a=stock`) | with the g27 flight 2 of 5 zombies went under the treads at (-608, 2673) (`iwz_probe_forensics`: sub_surface) | stair A 5 of 5 up and down, stair B 5 of 5, twice |
| Capsule Post (package T1, `modules/post.gsc`) on the nine-zone map: hatches HALL, OLD_STATION, GENERATOR, SIGNALS, lever in the control room | the map had no transport | `post_routes` 128 of 128: all 12 routes both lever settings, every rider sample in the destination zone |
| `build-g.ps1 -Darkness -DarkZoneFill` | the darkness work was not wired into the g27 build | builds (g27g, g27h); NOT DIAGNOSED in game: the module initialises (72 lights, 9 banks), but in every client run the lab's generator `use` left power off (probe after it: `power=0`; headless runs get `power=1`), so its power-on sequence never ran. Not used in g27j |

## Measured on g27j (classic headless runner, compressed time 10x unless said; only the joined door walk ran at real time)

| Plan | Result |
|---|---|
| accept_doors | PASS 70/70 |
| door walk, joined (a real client on a dedicated server, real time, the forward key held 3 s; Forge) | the player stops at x -2386.4 against the closed tunnel door and at y 3986.4 against the PaP shutter, as against a plain wall |
| rounds 1-4 from the start of a match, every door closed, player in the ticket hall | every round starts, ends and reaches the player (6, 8, 13, 17 arrivals); 1 zombie idles at a spawner in rounds 3 and 4; none walked into a closed door |
| accept_economy: power, 9 perks at their prices, six-perk limit, 5 wall buys, 3 wheels, Third Rail before and after power | PASS 76/76 |
| accept_wells_stairs (wells, stairs) | PASS 9/9 and 9/9 (stairs twice) |
| post_routes | PASS 128/128 |
| post_rules | 34/39: a downed player and blowback were not exercised (the plan's quiet preset keeps the bot from going down and removes the zombies blowback needs) |
| accept_pap | 16/20: relays, shutter, gate state and the upgrade pass; the lab's `use` step calls the machine directly and skips the stock `.disabled` check a player's trigger goes through, so "refused while closed" is not shown by this plan |
| accept_rounds 1-15 (g27h, same gameplay as g27j) | every round starts and ends, 1 stall (round 11); zombies reach the player every round, but 1 to 13 a round idle 50 s or more, many at their spawner's origin (all 45 ground spawners are on the floor and the navmesh) |
| look frames, 13 cameras, three independent reviewers | 6, 6, 6 of 10 against the shipped IW Zombies maps; one said not shippable |

## Open (not done)

1. Look, 6 of 10 against a target of 7.5. Reviewers agree on: flat ambient fill and glows with no fixture; a blown-white
   strip along the platform edge (well views); hard-edged floor patches on platform B; floors and walls too clean and sparse;
   a floating blue dot (control room), a red cross and a blue streak (stair A); black train windows; the PaP look camera
   faces the shutter.
2. Darkness: not diagnosed. First a client run must actually switch the power on (the lab's generator `use` does not in a
   client cell); then the bank sequence and the lit look can be measured. The client exits seen on 21 Nov fell inside a
   window when three Forge daemons were running at once (platform lane, fixed in iw7-forge 71951a3), so they are not
   attributed to the map.
3. Idle zombies in rounds (above) and the round-11 stall.
4. post_rules and accept_pap test gaps above (plans, not the map, as far as measured).
5. Does not exist on the nine-zone map: the bible's 19 zones, the Terminus quest (Q1), the four wonder weapons, the Night
   Inspector and the Rollers, the Tab pages, camos, emotes, most of the audio direction.
