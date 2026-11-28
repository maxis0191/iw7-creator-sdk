# ONE WAY: where the work stopped (paused by the owner, 28 Nov 2026)

Branch `claude/sz-wonder-1`. Nothing of this weapon was ever compiled, built or run in the game. No game session,
build or image generation of this session is running or queued.

| Done | Where |
|---|---|
| Design, reviewed once and corrected (the corrected version was not re-reviewed) | `DESIGN.md` |
| Owner's choice: mechanic kept, look = direction A (the conductor's machine) | `DESIGN.md` section 14; images in `C:\studio-data\sz\weapons\one-way\concept\final`, prompts and manifest in `concept/` |
| Fallback copy and names (Gemini 4 Hydrogen; Neon refused for this account) | `DESIGN.md` section 12 |
| The mechanic's game script and its test driver: **written, never compiled** | `tools-source/iwzmap/weapons/one_way/cp_sz_oneway.gsc`, `test/szoneway_driver.gsc` |

## The exact next step

1. Write `tools-source/iwzmap/weapons/one_way/make_gamelab.py`: `git archive origin/main ops/gamelab` of the server
   repository into a private folder, append `cp_sz_oneway.gsc` + `test/szoneway_driver.gsc` as `lib/szoneway.gsc`.
2. Write the plans (cp_zmb, player at (1467.65, 4134.45, 0.2) yaw 0, zombies at (1767, 4134, 0), stand-in weapon
   `iw7_fhr_zm`, `"libraries": ["szoneway"]`, conditions `quiet` plus `ignore on`): round 10, twelve one-ticket
   zombies taken on one bell, refund 6; round 25, eight booked: six carried, two stayed, back at 395 health, then
   taken; one head ticket at round 33 (taken) and 34 (carried); a ticket with 400 ms left (valid for the bell
   after); four tickets on one zombie (one wasted); upgraded arrivals. Issue tickets with the driver's `owt_issue`,
   not with the `shoot` step (`via: auto` adds a second hit when a hit does 0 damage).
3. `python -B C:\forge\forge.py check <plan> --gamelab <folder>`, then one `forge batch` in the background.
4. Then, in the order of `DESIGN.md` section 11: the four probes, the moving-bone measure on a Black Ops 3 port, the
   model of direction A in Blender, the new-bone writer (`build_model.py:319`), the first authored first-person clip.

Open, for the lead session or the owner: who runs zone builds (the Coordinator rule), and the disk (33 GB free on
28 Nov, under the 35 GB build floor). Hook facts and engine state: the shared notes file `wonder-weapon-one-way.md`.
