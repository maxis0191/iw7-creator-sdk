# Where things are

One page that routes a reader. Paths are relative to the repository root. The check names are the `id` values in
`checks.json`; `checks.ps1` runs all of them.

| I want to | Read | Tools | Check |
| --- | --- | --- | --- |
| make or change a generated map (Station Zero and after) | [CREATION-TOOLS.md](CREATION-TOOLS.md), then [tools-source/iwzmap/README.md](../tools-source/iwzmap/README.md) | `tools-source/iwzmap` | `tools-source-iwzmap-tests`, `tools-source-iwzmap-volume-check`, `tools-source-iwzmap-audio`, `tools-source-iwzmap-catalog`, `tools-source-iwzmap-art` |
| read a studio map as data, lift a prefab | [WORLDKIT.md](WORLDKIT.md) | `tools-source/worldkit` | `tools-source-worldkit-tests` |
| know what a captured frame of the game shows, as data (what is at a pixel, is a thing visible, floating, sunk, missing) | [SEE.md](SEE.md) | `tools-source/worldkit/iw7_see.py` | `tools-source-worldkit-tests` |
| change a shipped map's entities with no build | [MAPENTS.md](MAPENTS.md) | `tools-source/mapents` | `tools-source-mapents-tests` |
| describe, validate and package a mod | [MODDING-PLATFORM.md](MODDING-PLATFORM.md) (the contract), [MOD-PACKAGES.md](MOD-PACKAGES.md), [COMMUNITY-MOD-DISTRIBUTION.md](COMMUNITY-MOD-DISTRIBUTION.md), [sdk/modding/CREATOR.md](../sdk/modding/CREATOR.md) | `sdk/modding`, `ops/modding`, `ops/Validate-ModPackage.py` | `sdk-modding-tests`, `mod_package_test`, `community_distribution_test`, `beacon_ff_test`, the `sdk-modding-examples-*` checks |
| touch the HUD lab (showcase cancelled, files pinned by the server) | header of `tests/ops/hud_lab_test.py` | `ops/hud-lab` | `hud_lab_test` |
| describe sound in a mod | [SOUND-SDK-CONTRACT.md](SOUND-SDK-CONTRACT.md) | `sdk/modding/examples/original-sound` | `sdk-modding-examples-original-sound-test_example` |
| audit what a compiled GSC consumes | [sdk/modding/gsc-consumption-audit.md](../sdk/modding/gsc-consumption-audit.md), [tools-source/gsc-consumption-tool/README.md](../tools-source/gsc-consumption-tool/README.md) | `sdk/modding/audit_gsc_consumption.py`, `tools-source/gsc-consumption-tool` | `tools-source-gsc-consumption-tool-verify_archive` |
| build the server spawn tip example | [tools-source/gsc-spawn-tip/README.md](../tools-source/gsc-spawn-tip/README.md) | `tools-source/gsc-spawn-tip` | `tools-source-gsc-spawn-tip`, `Test-SpawnTip`, `Test-SpawnTipHost` |
| know that every script still parses after an edit | header of `tools-source/compile_check.py` | `tools-source/compile_check.py` | `tools-source-compiles` |
| know what is proven and what is not | [MODDING-CAPABILITIES.md](MODDING-CAPABILITIES.md) (evidence as of 2026-10-16), [CREATION-TOOLS.md](CREATION-TOOLS.md) (the map tools) | | |
| read the design of the custom map Station Zero (lore, world, quest, weapons, audio, build plan, client needs) | [station-zero/README.md](station-zero/README.md), then [station-zero/12-BUILD-PLAN.md](station-zero/12-BUILD-PLAN.md) | | |
| know why and in what order | [ENGINE-MODDING-STRATEGY.md](ENGINE-MODDING-STRATEGY.md) | | |
| test in the game, measure, find a tool | server repository (iw7-paris-server): `docs/DEVKIT.md`, `docs/TOOLS-INDEX.md` | | |
| know the rules for working here | [AGENTS.md](../AGENTS.md) | | |

## Kinds of document

- Living documents, kept true: this page, `README.md`, `AGENTS.md`, `docs/CREATION-TOOLS.md`, `docs/WORLDKIT.md`, `docs/SEE.md`,
  `docs/MAPENTS.md`, `docs/ENGINE-MODDING-STRATEGY.md`, the READMEs under `tools-source/`.
- Contracts, stable formats that change with the code: `docs/MODDING-PLATFORM.md`, `docs/MOD-PACKAGES.md`,
  `docs/COMMUNITY-MOD-DISTRIBUTION.md`, `docs/SOUND-SDK-CONTRACT.md`, the `*.md` files in `sdk/modding/`.
- Dated records, history and never instructions: `docs/archive/`, `docs/MODDING-CAPABILITIES.md` (a record kept in
  place because a pinned file names its path), the dated `*.json` files in `sdk/modding/` listed below, `migration/`.

## Paths other products pin

`ops/`, `sdk/modding/`, `tests/ops/`, `tools-source/gsc-consumption-tool/` and `tools-source/gsc-spawn-tip/` are
named, and partly verified by hash, by iw7-paris-server, x64-zt-extensions and iw7-mod-components. Nothing there is
moved or renamed. Changing the bytes of a file is allowed; the consumer then pins the new revision.

Recorded decisions (2026-11-10), not to be reopened without a reason that is new:

- Nothing moves under those five folders. The dated records in `sdk/modding/` would read better in a folder of their
  own, but other products' documents and deployment records name them where they are.
- `tools-source/iwzmap` is not restructured now. Its Python files import each other by bare module name, its
  PowerShell scripts call their siblings by folder, `checks.json` discovers a test in the folder root, and the
  server's documents name the flat paths. Revisit when a second map exists and the generic tools must be separated
  from Station Zero. Until then `tools-source/iwzmap/README.md` lists every file directly in the folder and
  describes each sub-folder.

## Dated records in `sdk/modding/`

Evidence of 2026-10-12, kept where other repositories' records name them:
`beacon-ff-validation-2026-10-12.json`, `creator-composition-v8-validation-20261012.json`,
`creator-composition-validation-20261012.json`, `creator-materialize-validation-20261012.json`,
`creator-validation-2026-10-12.json`, `gsc-consumption-native-20261012.json`, `gsc-qualified-closure-20261012.json`,
`gsc-reference-collector-correction-20261012.json`, `gsc-reference-qualified-v8-20261012.json`,
`gsc-reference-source-20261012.json`, `gsc-reference-v7-failure-20261012.json`,
`gsc-residual-diagnostic-20261012.json`, `integration-bo3-bootstrap-validation-20261012.json`,
`integration-bo3-native-validation-20261012.json`, `integration-bo3-prepatch-validation-20261012.json`,
`integration-bo3-tooling-validation-20261012.json`, `integration-native-dumps-20261012.json`,
`integration-native-followups-validation-20261012.json`, `recipient-export-budget-2026-10-12.json`,
`recipient-recovery-2026-10-12.json`, `self-contained-runtime-plan-20261012.json`,
`self-contained-runtime-plan-b-20261012.json`, `self-contained-startup-a-20261012.json`,
`self-contained-startup-b-20261012.json`, `self-contained-use-rejoin-b-20261012.json`.

Live inputs in the same folder that code reads, not records: `capabilities.json`, `manifest.schema.json`,
`creator_beacon_self_contained.manifest.json`, `recipient-material-requests.csv`, `recipient-script-requests.txt`.

## Names that point at another repository

Documents written in October name `docs/STATE.md`, `docs/HUD-LAB.md`, `docs/MODULES.md`, `docs/ENEMY-PORTING.md`,
`docs/MODEL-LAB.md`, `docs/INSTANCE-WORKFLOW.md`, `docs/STORAGE-WORKFLOW.md`, `docs/CLIENT-COMPATIBILITY.md` and
`docs/UPSTREAM-2026-10-06.md`. Those are documents of the server repository (iw7-paris-server);
`docs/RESOURCE-WORKFLOW.md` belongs to iw7-mod-components. The `reference` fields of `sdk/modding/capabilities.json`
name several of them too; that file is pinned by two products and is not edited for it.
