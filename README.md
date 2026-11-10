# IW7 creator SDK

The creator side of the IW7 products: tools to make and change maps and content, and the SDK that describes,
validates and packages a mod. The primary goal is deep, reusable control of IW7's own engine and rules; BO3 import
is one optional use case (see the [engine-modding strategy](docs/ENGINE-MODDING-STRATEGY.md)).

This repository is private. It complements the owner's public forks and does not publish private code into them.

- Where everything is: [docs/INDEX.md](docs/INDEX.md).
- Rules for agents: [AGENTS.md](AGENTS.md).

## What is in it

| Folder | What it holds |
| --- | --- |
| `tools-source/iwzmap` | Generated IW7 zombies maps (Station Zero): generator, collision and navigation, light bake, effects, art, audio, darkness, catalogue, offline checks, build and run scripts. See [docs/CREATION-TOOLS.md](docs/CREATION-TOOLS.md). |
| `tools-source/worldkit` | Reads a studio map as data and lifts prefabs from it. See [docs/WORLDKIT.md](docs/WORLDKIT.md). |
| `tools-source/mapents` | Changes a shipped map's entities with no build. See [docs/MAPENTS.md](docs/MAPENTS.md). |
| `tools-source/gsc-spawn-tip` | Offline audit profile of the server spawn tip example: whether its compiled GSC holds external or unresolved references. |
| `tools-source/gsc-consumption-tool` | Text-only patch series and manifest for the strict GSC consumption auditor; no executable. |
| `sdk/modding` | Author manifests (`iw7.community-mod/1`), validation, composition, author examples, and the dated records of their qualification. |
| `ops/` | Mod package validation and distribution (`ops/Validate-ModPackage.py`, `ops/modding`), the HUD lab runtime (`ops/hud-lab`) and its package plan (`ops/mod-packages`). |
| `tests/ops` | Tests of the `ops/` tools. |
| `docs/` | Living documents, contracts, and `docs/archive/` for history. |
| `migration/` | How this repository was extracted from the server repository in October 2026: [migration/README.md](migration/README.md), the path map and the commit map. Authors and commit messages were preserved. |

Native engine code and asset converters are not here. They are versioned dependencies named in `product.json`
(iw7-mod-components, x64-zt-extensions, iw7-paris-server at exact revisions).

## Prerequisites

Git, the GitHub CLI authenticated with read access to this private repository, PowerShell 7.4 or later,
Python 3.12 and Node.js 22. Native source checks also use Java 21; native compilation uses the existing
Visual Studio 2022 C++ toolchain. Per area, optional: the light bake needs numpy, numba, scipy, pillow and
DirectXTex texconv; the map build scripts need the machine locations listed in
[tools-source/iwzmap/README.md](tools-source/iwzmap/README.md).

## Run the checks

```powershell
./bootstrap.ps1 -Output "$PWD/runtime/source inputs"
./checks.ps1 -Workspace "$PWD/runtime/source inputs"
```

This local run on the exact committed head is the judge. GitHub's own checks do not run on this account and their
colour means nothing.

`bootstrap.ps1` refuses a checkout with uncommitted changes. It downloads only the immutable source dependency
archive named in `dependency-package.json` from this repository's private release and checks its SHA-256, length,
members, owners and commits. The archive holds selected text sources, never tools, game data or binaries. Offline:
pass `-DependencyArchive <downloaded dependencies.zip>`. A missing archive fails clearly; no fallback version is
selected.

The two commands do not install a game, copy retail assets, build native code, launch a process, deploy, publish or
change the public server. Build and run entry points inside the composed workspace keep their own input, identity,
resource and authorisation gates. To run one, use the composed workspace or
`bootstrap.ps1 -Entry ops/<entry>.ps1 -Arguments @(...)`.

## How it fits the other products

- Edit the tracked file here, never a composed workspace under `runtime/`. The relative layout of the sources is a
  compatibility contract used by tools that verify hashes.
- Dependencies contribute only their listed files to a fresh, bounded workspace; they are not vendored into this
  repository. The composition receipt records every owner, commit, Git blob and checkout-byte hash. It does not
  qualify a native build and does not inherit an older runtime receipt.
- Every tracked file is declared in the `exports` list of `product.json`; a file that is not declared fails the
  first check. The exceptions (root files, `.github/`, `migration/`) are listed in `AGENTS.md` section 3.
- Other products pin files of this repository by path and hash: iw7-paris-server and x64-zt-extensions pin files
  under `ops/hud-lab`, `ops/modding`, `ops/Validate-ModPackage.py` and `sdk/modding`; iw7-mod-components pins
  `tools-source/gsc-consumption-tool`. Those paths do not move.

## Evidence and rollback

Dated documents and pinned plans keep their original bytes and claims. A moved or rebuilt source needs a new plan
and a new qualification; an old receipt is not reused for a newly composed input. Failed results remain failed.
To roll back an integration, restore its earlier dependency revision in a new reviewed commit, compose a fresh
workspace and rerun the relevant tests. This never restores or deploys game data, banks or binaries.

## Licensing

Preserve upstream notices and per-file provenance. No blanket licence is granted to the private adaptations in
this repository. Public distribution requires its own licence and privacy review and the owner's decision.
Commercial game assets, dumps, installed SDKs, PDBs, executables, credentials and player data are excluded.
