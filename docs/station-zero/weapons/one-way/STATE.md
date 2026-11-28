# ONE WAY: state of the work (28 Nov 2026, resumed after the owner's pause)

Branch `claude/sz-wonder-1`. Nothing of this weapon has run in the game yet.

| Done | Where |
|---|---|
| Design, reviewed once and corrected (the corrected version was not re-reviewed) | `DESIGN.md` |
| Owner's choice: mechanic kept, look = direction A (the conductor's machine) | `DESIGN.md` section 14; images in `C:\studio-data\sz\weapons\one-way\concept\final`, prompts and manifest in `concept/` |
| Fallback copy and names (Gemini 4 Hydrogen; Neon refused for this account) | `DESIGN.md` section 12 |
| The mechanic's game script and its test driver | `tools-source/iwzmap/weapons/one_way/cp_sz_oneway.gsc`, `szoneway_driver.gsc`: compiled by the pinned compiler inside the plan fixture (`forge check` accepts both plans), link check 0 unresolved. **Never run** |
| Plans | `tools-source/iwzmap/weapons/one_way/plans/sz-oneway-core.json`, `sz-oneway-upgraded.json`, with `make_gamelab.py` |
| The weapon's own skeleton as data | `skeleton.json` (20 bones; the root's name and the standard tags wait for a stock view model dump) |

## Blocked: no game session can start on this machine (28 Nov)

The disk clean of 28 Nov removed the retained test stock (`IW7-Runtime\private-test-server`: Forge answers
"Stock root not found", class infra, `C:\studio-data\sz\weapons\one-way\runs\core-1.json`), `C:\IW7-Cache\tools`
and the stock weapon dumps. Ledger: `test-stock-root-gone`, `forge-library-dir-gsc-tool`. The lead session was asked
who restores it; this session does not touch the stock.

## In work (helpers, no game needed)

| Item | Where |
|---|---|
| Blender generator of direction A, with preview renders | x64-zt-extensions branch `claude/sz-oneway-model` (worktree `worktrees\xzte-oneway`); renders in `C:\studio-data\sz\weapons\one-way\model` |
| Own-skeleton mode of the model writer (`build_model.py --skeleton`), offline tests only | x64-zt-extensions branch `claude/own-skeleton-writer` (worktree `worktrees\xzte-ownskel`) |

Not started: sounds (ElevenLabs has 191 credits left of 40,000 until the reset of 9 Dec 2026), effects, animations
(they need the hands' skeleton from a stock dump), the upgraded form at the machine, the quest hooks.

## The exact next steps

1. When a stock root exists again: `python -B make_gamelab.py --server <iw7-paris-server checkout> --out C:\studio-data\sz\weapons\one-way\gamelab`,
   then `python -B C:\forge\forge.py run plans\sz-oneway-core.json --gamelab C:\studio-data\sz\weapons\one-way\gamelab\ops\gamelab --json`
   in the background, then the upgraded plan. Read the probes against the expectations; fix the script.
2. Read the helpers' work: the five renders of the model against the two reference images; the writer's diff and tests.
3. When stock dumps exist again: the root name and tags of a stock view model into `skeleton.json`; the hands' skeleton
   for the animation rig; then, in the order of `DESIGN.md` section 11, the moving-bone measure on a Black Ops 3 port,
   the model on its own skeleton in the game, the first authored first-person clip.

Open, for the lead session or the owner: who restores the test stock; who runs zone builds (the Coordinator rule).
Hook facts and the engine's state: the shared notes file `wonder-weapon-one-way.md`.
