## Current workflow for every agent - owner rule 2026-11-10

This section replaces older test, build and delegation instructions wherever they differ (they are kept below
as history). The owner's keys: best quality, speed, light weight, total efficiency. A result is a measured run,
never a prediction.

Start here, in the server repository (iw7-paris-server): `docs/DEVKIT.md` says which tool answers which question; `docs/TOOLS-INDEX.md` (when it lands) lists every tool on every branch, merged or not; `docs/DEVKIT-PLAN.md` lists what exists, the holes and the open work; `docs/QUALITY-OBSERVATORY.md` says how problems are found without the owner.

1. Check the files first. Before any build or launch run the file checks for your kind of content (weapon audits
   and mod preflight for weapons; `iwz_emitcheck.py check|diff|route|at` for a map source; the build-log gate and
   the loader readback after a build). A build or a launch made to learn what a file check can say is waste.
2. Never copy the game, and never test in the owner's game folder. Make a bench root (`ops/bench/New-BenchRoot.ps1`,
   2 seconds, hard links); remove it only with `ops/bench/Remove-BenchRoot.ps1 -RunFiles`.
3. Test without a game client whenever no screen is needed: `ops/gamelab/Invoke-GameLabHeadless.ps1` runs a test
   plan on a private server with a bot in about 40 seconds and 1.1 GB. Use a client plan
   (`ops/gamelab/Invoke-GameLab.ps1`) only for frames, frame rate or key presses. One plan answers many questions;
   write expectations; the exit code is the verdict.
4. Sessions queue themselves: pass `-WaitForSlotSeconds`; never write retry loops; never stop a game process you
   did not start; never touch a game instance another application started. The scheduler admits sessions by free
   memory, several at once; builds stay exclusive.
5. Need a lab client: `ops/enginelab/Get-LabClient.ps1`. Changed native code: `ops/enginelab/Invoke-EngineLab.ps1`
   (commit, build in about 70 seconds, plans, verdict).
6. Engine questions: the engine map (what is at an address, who calls it, which function mentions a text, console
   variables), the memory watch (where the game keeps a value), the performance recorder with `iw7_perf.py`
   (frame rate and the functions that cost the time; a change under about 5 % needs three runs a side), the freeze
   reporter, the crash reader. All in iw7-mod-components `ops/engine-map` and its `docs/`.
7. Network questions: `ops/netlab/Invoke-NetLab.ps1` (chosen ping, jitter and loss; key-to-server time).
   Long runs: `ops/soak/Invoke-Soak.ps1`. Every place of a map: `ops/atlas/atlas.py` with the `survey` step.
8. Problems go into the ledger (`ops/quality/ledger.py`), not only into a chat; read its `list` before starting.
9. Landing: the local `checks.ps1` run on the exact head is the judge; GitHub's own checks do not run. Do not run
   a live session while a check run is in progress (some checks need the build slot). Nothing is deployed to
   players without the owner, then to both public servers.
10. Delegation in Claude Code sessions (owner, 2026-11-10): the most capable model designs, writes precise briefs,
    reviews and makes or validates the live proofs; Sonnet subagents write code, tests and documents and land
    branches; Opus for the hardest pieces. Briefs name exact paths, commands, limits and what proves the work.

Older lines this replaces: testing in the owner's base game folder; one heavy session on the whole machine;
waiting for GitHub checks; per-test game copies; launching once per question.

# iw7-creator-sdk: instructions for agents

The section above is the owner's current workflow and wins wherever anything else differs. The sections below are
the standing rules of this repository, each written once. `docs/TOOLS-INDEX.md` named above has landed in the
server repository. The `ops/bench`, `ops/gamelab`, `ops/enginelab`, `ops/netlab` and `ops/quality` paths named above
are not in this repository: they live in the server repository (iw7-paris-server) or in iw7-mod-components; that
index says which.

## 1. What this repository is

- The creator side of the IW7 products: map and content creation tools (`tools-source/iwzmap`,
  `tools-source/worldkit`, `tools-source/mapents`), the mod manifest, validation and packaging SDK (`sdk/modding`,
  `ops/`), GSC audit adapters (`tools-source/gsc-consumption-tool`, `tools-source/gsc-spawn-tip`) and author
  examples.
- Primary objective (owner, 2026-10-16): deep, reusable control of IW7's own engine and rules. BO3 import is an
  optional use case, never the destination and never a prerequisite. Read
  [the engine strategy](docs/ENGINE-MODDING-STRATEGY.md). Kino and the Ray Gun are requested demos; they do not
  block other useful IW7 work. Rhino is retired and the HUD showcase is cancelled.
- What it is not: server logic (iw7-paris-server), native engine code (iw7-mod-components), asset converters
  (x64-zt-extensions). Native engine and asset conversion implementations are versioned dependencies named in
  `product.json`.
- Where to read next: [docs/INDEX.md](docs/INDEX.md).

## 2. Rules that never change

1. This repository is the canonical owner only of its declared exports. Do not add server logic, another product's
   full tree, game assets, binaries, symbols, credentials, player data or decompiled dumps.
2. One canonical implementation per component: extend an explicit interface or dependency instead of copying
   another product's implementation.
3. Keep author and licence notices and exact upstream pins.
4. Never force-push. Never rewrite published history.
5. Preserve unrelated work, other sessions' worktrees and branches, ignored evidence and frozen plans. Never archive
   or delete a live worktree.
6. Never stop a game process you did not start, and never touch a game instance another application started.
7. Never copy the game, and never test in the owner's game folder.
8. Preserve the public Main server (UDP 27016), bank data and occupied clients. Anything that changes a running
   system needs its identity, backup and ownership checks first.
9. Do not edit the resource scheduler here and never delete its lease. Keep its telemetry and shared leases. Builds
   and heavy groups stay serialised through it; game sessions are admitted by free memory, several at once (this is
   what the first section's "several at once" means).
10. Nothing is deployed to players without the owner, and then to both public servers.
11. The repository is private. Do not publish private code into public forks. Do not change visibility, billing,
    protection or credentials.
12. Nothing is sent to any public upstream project (the game client iw7-mod, ZoneTool or any other) without the
    owner: no issue, no pull request, no message. Contribute only to the owner's forks, never with private code.
13. Historical results do not qualify moved or rebuilt inputs. A failed result stays recorded as failed.
14. Keys, passwords, bank data and player identifiers are never read, printed or committed.
15. Game tests follow the server repository's test-server privacy rules: a password, `sv_lanOnly 1`, loopback, absent
    from the public server browser.
16. Do not change another agent's or tool's memory or configuration automatically.
17. Specific stops, prohibitions and refusals the owner has given remain in effect; a new tool, a strategic
    correction or a rewrite of these instructions does not erase them.

## 3. How to work here

- Tool first. Real work in the game is also the test of the tools. Whenever a tool, the workflow or the environment
  is seen to be slow, unoptimized, buggy or blind, or a new tool would be a real jump, fix or build that FIRST,
  prove it with a measured run, document it, then return to the job. Never grind: the same build or launch repeated
  more than about three times for one question, a cause that is guessed instead of read from data, minutes of
  waiting for what a file check answers in seconds, a result judged by looking at a picture, a manual step done
  twice: each of these means stop and improve the tool. (Owner rule, 2026-11-10.)
- Delegation (owner, 2026-11-11): in Claude Code sessions the lead session plans and orchestrates; helpers run
  Opus 5.5 at medium effort for real work and Sonnet 5.5 at medium effort for cheap and easy tasks (searches,
  inventories, mechanical edits, landing a finished branch). Other agent programs follow their own program's
  equivalent: the strongest model plans, a cheaper one does routine work. Briefs name exact paths, commands,
  limits and what proves the work. Where this differs from point 10 above, this rule is the current one (owner,
  2026-11-11).
- Before editing, classify the change by product and read `product.json`, `README.md` and `docs/INDEX.md`.
- Every tracked file is declared. Adding, moving or deleting a file means editing the `exports` list of
  `product.json` in the same commit; the first gate of `checks.ps1` fails otherwise. The exceptions are the root
  files (`README.md`, `AGENTS.md`, `product.json`, `checks.json`, `dependency-package.json`, `bootstrap.ps1`,
  `checks.ps1`, `.gitignore`, `.gitattributes`) and what is under `.github/` and `migration/`.
- Paths other products pin (`ops/`, `sdk/modding/`, `tests/ops/`, `tools-source/gsc-consumption-tool/`,
  `tools-source/gsc-spawn-tip/`): do not move or rename. Changing their bytes is allowed; the consumer then pins
  the new revision.
- Do not edit a composed source workspace (`runtime/...`); edit the tracked file here.
- Map tools: commands run from `tools-source/iwzmap`. Machine locations come from parameters or from the `IWZ_*`
  variables listed in `tools-source/iwzmap/README.md`, never from a new hard-coded path.
- Testing a map-tool change in the game: set `IWZ_GAME_ROOT` to a bench root (a stopped test server's folder, see
  the server repository's `docs/DEVKIT.md`), never the owner's game folder; without it `run-sz2.ps1`,
  `new-work.ps1`, `pipeline.ps1` and `fx/agent/run-fx.ps1` stop with an error by design.
- A result is a measured run. Report source checks, build, game run and owner acceptance separately.

## 4. How to land

- A branch, coherent commits, a private pull request, a merge commit.
- The judge: on the exact head, `./bootstrap.ps1 -Output runtime/<short>` then
  `./checks.ps1 -Workspace runtime/<short>`, once, in the background; post the result on the pull request; merge.
  `bootstrap.ps1` refuses a checkout with uncommitted changes and composes the workspace from the committed head.
  GitHub's own checks do not run and their colour means nothing.
- A check that fails is fixed at its cause. It is never removed, skipped or weakened to get a passing run.
- Exit code 3221225794 on several checks at once means Windows could not start the processes (machine under load):
  run again once before reading it as a failure.
- Leave the main checkout clean and synchronised.

## 5. What needs the owner

- Anything deployed to players (then to both public servers).
- Anything sent to a public upstream project.
- Making the repository or any private code public; a licence statement; changing visibility, billing, protection
  or credentials.
- Resuming a retired effort (Rhino, the HUD showcase), or recreating a retired lab, an access bridge or deleted
  game stock.

## 6. History

Older instructions and the record of the extraction: [docs/archive/AGENTS-2026-10.md](docs/archive/AGENTS-2026-10.md).
They are history, not instructions. This is the history that the first section says is kept below.
