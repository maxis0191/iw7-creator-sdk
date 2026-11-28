# ONE WAY: state of the work (28 Nov 2026, resumed after the owner's pause)

Branch `claude/sz-wonder-1`. The mechanic is measured in the game on a stand-in weapon; the weapon itself has not been in the game.

## Measured in the running game (28 Nov 2026, Forge, headless server, one engine bot, compressed time, cp_zmb)

The mechanic on a stock stand-in weapon (`iw7_fhr_zm`), by the two plans of `tools-source/iwzmap/weapons/one_way/plans`
(`forge run <plan> --library-dir tools-source/iwzmap/weapons/one_way`). Both pass on the final script: core 37 of 37
expectations (`C:\studio-data\sz\weapons\one-way\runs\core-7.json`), upgraded 13 of 13 (`upgraded-7.json`). A third plan,
`sz-oneway-carry-joined.json`, passes 8 of 8 with a real client joined (`forge run --joined`, `carry-joined-4.json`).

| Rule | Measured |
|---|---|
| A ticket is a real bullet through the stock damage callback and takes no health | 12 bullets in the trunk of 12 round-10 zombies: 12 second-class tickets, health 1,045 each before the bell |
| Taken on the bell, kill paid to the owner | 12 taken on one bell; points +60 a kill (23 kills: 500 to 1,880). A first-class kill pays 60 too, not the head reward |
| Full train | 12 taken: 6 tickets to the reserve (10 to 16); 8 taken: 4. Upgraded: 12 taken: 8 |
| Flat rated damage | round 25: 4,365 to 395 on all eight (3,970 exactly); round 34 after one first-class ticket: 10,292 to 372 |
| Six cars | eight round-25 zombies, one ticket each: six carried, two stayed; all eight alive |
| Put back, the 12 s rule | all six back on the platform at the next bell, counted immune; a second ticket then takes all eight |
| First class | one bullet in the head: taken at round 33 (9,357), carried at round 34 |
| Three tickets a zombie | four bullets on one round-35 zombie: three tickets, one wasted, taken |
| Doors closing | a ticket issued with 250 ms left is not taken at that bell and is taken at the next |
| Carried over, with a real client joined | hidden alone, hidden + `notsolid`, and hidden + contents 0 each still stopped a bullet where the zombie stood (41 % of the trace, the same as a zombie on the platform; three runs). So a carried zombie leaves: no-clip physics and 400 units under its place. Then a bullet passes its place (100 %; 41 % on one that stayed), it is 399 units under, and all eight are alive and back at the next bell with 395 health. Frames of the client: `C:\studio-data\sz\weapons\one-way\runs\frames\joined4_*.png` (dark; the proof is the probes) |
| The calm | four zombies asked to sprint: 186 units a second; ticketed: 70 units a second, move mode walk |
| Arrival (upgraded) | 12 and 3 arrivals one bell after 12 and 3 taken; unbooked round-30 zombies fall from 7,030 to 3,060 (one arrival) or die (two) |

Learned in these runs: a stock bullet goes on through zombies standing together and hits the hook several times
(62 hits for 12 bullets), so the script books only the first zombie of a shot; a script `dodamage` reaches the stock
callback as a HEAD hit; round 30 health is 7,030 and round 34 is 10,292 in the game.

**Not measured yet:** that a PLAYER walks through a carried zombie's place (`playerphysicstrace` does not see agents
at all, so it proves nothing here), the calm seen on a client, real time, with 24 and with about 55 zombies alive, four players and two weapons in the game (the
logic tests cover them outside it), the specials, frame time. Nothing of the weapon itself (model, animations,
effects, sounds, its own definition) has been in the game.


| Done | Where |
|---|---|
| Design, reviewed once and corrected (the corrected version was not re-reviewed) | `DESIGN.md` |
| Owner's choice: mechanic kept, look = direction A (the conductor's machine) | `DESIGN.md` section 14; images in `C:\studio-data\sz\weapons\one-way\concept\final`, prompts and manifest in `concept/` |
| Fallback copy and names (Gemini 4 Hydrogen; Neon refused for this account) | `DESIGN.md` section 12 |
| The mechanic's game script and its test driver | `tools-source/iwzmap/weapons/one_way/cp_sz_oneway.gsc`, `szoneway_driver.gsc`: both plans pass in the game (below); 20 logic tests outside it |
| Plans | `tools-source/iwzmap/weapons/one_way/plans/sz-oneway-core.json`, `sz-oneway-upgraded.json`, with `make_gamelab.py` |
| The weapon's own skeleton as data | `skeleton.json` (20 bones; the root's name and the standard tags wait for a stock view model dump) |

## History: the game was unavailable for part of 28 Nov (restored the same day by the lead session)

The disk clean of 28 Nov removed the retained test stock (`IW7-Runtime\private-test-server`: Forge answers
"Stock root not found", class infra, `C:\studio-data\sz\weapons\one-way\runs\core-1.json`), `C:\IW7-Cache\tools`
and the stock weapon dumps. Ledger: `test-stock-root-gone`, `forge-library-dir-gsc-tool`. The lead session was asked
who restores it; this session does not touch the stock.

## Built since the resume, without the game

| Item | Where | Proven how |
|---|---|---|
| The mechanic's rules | `tools-source/iwzmap/weapons/one_way/test_oneway_logic.py` | 13 tests in 0.1 s in Forge's script interpreter (gscvm), no script error: tickets, the beat, flat sums, taken / carried / stayed, six cars, the 12 s rule, refund, arrivals, two owners. Not the game: the stock damage callback is a stand-in |
| Blender generator of direction A | x64-zt-extensions branch `claude/sz-oneway-model` (7aa3358): `tools-source/asset-bridge/t7-weapons/authored/one_way_gun.py`, `one_way.params.json` | 37,386 triangles, 148 parts, each tagged with its bone key; five preview renders per round in `C:\studio-data\sz\weapons\one-way\model\r10` read by the lead (product, left, fp). The helper's unwrap and bake ran to the end on Blender 5.2 with no game data (an earlier round, 540 s). Left: chips too heavy on the grip, the strap hidden behind the body; never exported, never in the game |
| Own-skeleton mode of the model writer | x64-zt-extensions branch `claude/own-skeleton-writer` (776320f): `tools-source/iw7-skinned-writer/skeleton.py`, `build_model.py --skeleton <spec.json>` | 34 tests of the folder pass (16 new), the old path's bytes unchanged, `skeleton.json` of this weapon loads. Unverified against stock data: the quaternion scale (32767 or 32768), the per-bone bounds, three records copied from the base |

| The two meet: the model written on its own skeleton | `C:\studio-data\sz\weapons\one-way\model\r11\dump` (`weapon_iwz_oneway_vm.xmb`, `_lod0.xsb`), built by `build_model.py --skeleton` from the generator's bake model and its own `one_way.skeleton.json` (x64-zt-extensions `claude/sz-oneway-model` 9a15fbd, which now holds the writer too) | read back by the lead: 20 bones, 20 surfaces, 37,386 triangles, every surface on its bone, positions within 2e-7 inch of the spec. The header is a SYNTHETIC base, so this file is not a game asset: the same command with a stock view model as `--base-xmodel` is the next step when dumps exist |
| The mechanic's script, after a read of the whole stock damage callback | `cp_sz_oneway.gsc` (6cee926) | 19 logic tests: the bell's damage is never left on a zombie when the callback returns early, a special that stays is not stunned, a leaving player cancels his tickets, Insta-Kill makes any ticket enough |

**Found on the model, the owner's call:** held straight in first person the six lamps line up one behind the other and
cannot be counted (`model\r11\fp_straight.png`, `fp_cant10.png`); they read only with the weapon turned toward the
player (`model\r10\fp.png`, 22 degrees). **The owner chose (28 Nov): the inclined desk.** Done the same day
(x64-zt-extensions `claude/sz-oneway-model` 67d2876): a fare desk at the rear of the top, its face at 55 degrees toward
the holder's eye, the six lamps across it (lamp 1 on the holder's left). Read by the lead on `C:\studio-data\sz\weapons\one-way\model\r13\fp_straight.png`:
six lamps side by side, each its own disc, in the same straight hold that hid them before. 37,798 triangles, 148
parts. Also left on the model: the grip is chipped almost bare (`r13\rear.png`); no world model yet.

| The model on a STOCK view model header, its own 20 bones | `C:\studio-data\sz\weapons\one-way\model\r12\dump` (`build_model.py --skeleton`, `--base-xmodel weapon_ftlpistol_vm_fallback.xmb` of the restored cp_zmb dump; x64-zt-extensions `claude/sz-oneway-model` 3fd0e59) | read back by the lead: root `j_gun`, 20 bones, 20 surfaces, 37,386 triangles, no problem reported, the three unknown counts 0. Stock conventions checked on real view models the same day (notes of the writer): quaternion scale 32767, transWeight 2.0, part class 0, the weapon joins the hands at the bone `j_gun`, and a stock wonder weapon has bones of its own (`j_dischord_wire_*`). Still a file, not in the game: it has no materials, images, definition or animations yet |

The skeleton now holds the stock hand locators too (22 bones: `tag_ik_loc_ri` mid-grip, `tag_ik_loc_le` under the
belly; first placements, to tune on the hands). The `r12` dump predates the desk and the locators: the next build
rewrites it. To reduce later: 20 surfaces (one a bone and atlas) against 5 or 6 on a stock weapon.

Not started: the world model, sounds (ElevenLabs has 191 credits left of 40,000 until the reset of 9 Dec 2026), effects (they are cloned from
stock emitters), animations (they need the hands' skeleton from a stock dump), the upgraded form at the machine, the quest hooks.

## The exact next steps

1. Next proofs of the mechanic: a player walking through a carried zombie's place; 24 and about 55 alive; the stock specials; real time. (Old note, kept for the command) When `--library-dir` fails for a missing tool cache: `python -B make_gamelab.py --server <iw7-paris-server checkout> --out C:\studio-data\sz\weapons\one-way\gamelab`,
   then `python -B C:\forge\forge.py run plans\sz-oneway-core.json --gamelab C:\studio-data\sz\weapons\one-way\gamelab\ops\gamelab --json`
   in the background, then the upgraded plan. Read the probes against the expectations; fix the script.
2. The model: lighter chips on the grip, the strap where it can be seen; then its export on its own skeleton (needs a stock view model as the header template).
3. Dumps and compilers are back (28 Nov, the lead session's `C:\studio-data\sz\film\restore\RESTORE.md`). Next: the authored chain (`build_authored_weapon.py`) with `--skeleton` for materials and images, a weapon definition and a donor animation package as a marked stand-in, a mod zone under the Build lease, the weapon in the hands at fixed camera frames. Then the hands' skeleton
   for the animation rig; then, in the order of `DESIGN.md` section 11, the moving-bone measure on a Black Ops 3 port,
   the model on its own skeleton in the game, the first authored first-person clip.

Open, for the lead session or the owner: who restores the test stock; who runs zone builds (the Coordinator rule).
Hook facts and the engine's state: the shared notes file `wonder-weapon-one-way.md`.
