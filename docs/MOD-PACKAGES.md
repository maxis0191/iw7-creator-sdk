# Versioned modules with client assets

`ops/Validate-ModPackage.py` is a read-only preflight for reviewed manifests.
It does not build a fastfile, import an external model, install a native client,
upload content, deploy to Main or run the game. Existing `config/modules.json`
continues to own server feature deployment. This separate contract describes an
asset-bearing module and the evidence still needed before delivery.

## Three gates

```powershell
# No assets: a structurally valid plan can contain explicit null payload facts.
python ops/Validate-ModPackage.py ops/mod-packages/hud-lua-plan.json

# Supply an actual ignored build root and matching provenance manifest first.
python ops/Validate-ModPackage.py <manifest.json> --stage package --root <build-root> `
    --client-source <reviewed-client-source-commit>

# Delivery additionally requires source-check/runtime-link evidence on all maps,
# and offline-load evidence when the package has client files.
python ops/Validate-ModPackage.py <manifest.json> --stage delivery --root <build-root> `
    --client-source <reviewed-client-source-commit> --server-source <server-pin>
```

Output is JSON. Plan exit 0 means the recipe is structurally valid; `ready` is
always false at that stage. Package exit 0 means local payload size/SHA-256,
declared closure/transport coverage and required source-pin declarations pass.
Delivery exit 0 adds the declared technical evidence coverage gate. `ready`
means this transport contract passed; it does not mean the game or installed
client version was evaluated. The JSON `readiness_scope` states this limit.
Neither stage is gameplay acceptance. A failed
evidence record leaves package readiness false and blocks delivery. Stage failures
exit 1. No dependencies beyond Python's standard library are needed.

Validation trusts the manifest's evidence references and the supplied source-pin
arguments as assertions. It does not fetch CI, authenticate the author, establish
the running executable's source provenance or interpret raw game evidence. The
supervising operations helper must correlate exact executable hash/build pin,
session identity, evidence and current server state before deployment. Revalidate
immutable staged payloads immediately before copying; this checker is not an
atomic installer and does not lock against concurrent path replacement.

## Contract `iw7.mod-package/1`

Unknown or missing fields fail closed. Duplicate JSON keys also fail.

| Field | Meaning |
| --- | --- |
| `schema`, `id`, `version` | Exact schema above, lowercase module ID, numeric major.minor.patch |
| `maps` | Nonempty distinct retail recipients from the five CP maps |
| `delivery` | `server-only`, `mod` or `usermap` |
| `native_requirements` | Exact optional server/client source pins, client capabilities and compatible source allowlist |
| `files` | ID, client/server role, contained source, destination, actual bytes/SHA-256, closure roots |
| `closure` | Status, roots, nodes, unresolved dependencies and traceable closure evidence reference |
| `evidence` | Distinct source-check/offline-load/runtime-link/render/gameplay records with status, reference, authority and map coverage |

See [the inert example](../ops/mod-packages/hud-lua-plan.json) for every required
field. Unknown payload `source`, `bytes`, `sha256` and closure-node hashes use
JSON null while planning. Never fill them with dummy hashes or claimed passes.
Positive integer sizes and actual SHA-256 are required for real package stages.

Each closure node has `id`, asset `kind`, `scope` (client/server/recipient),
`sha256` and `requires` node IDs. Asset IDs are logical names rather than filesystem
paths. Roots must exist; edges must resolve to nodes or explicit unresolved IDs;
unreachable inventory nodes are rejected. Cycles are allowed and traversed with
a visited set. Complete closures require declared inventory hashes for all nodes,
including reused recipient assets, roots, no unresolved dependency and an evidence
reference. Only the package-file hashes are measured by this validator; node hashes
are recorded claims from the independently produced inventory.

Every deliverable root must bind a declared file of its client/server scope.
Every client/server node must be covered by a payload of that same scope; graph
traversal cannot silently make a server file deliver a client model, or vice versa.
Only `recipient` nodes describe assets already present rather than delivered.
Cross-scope dependencies therefore require independent payload bindings of the
other role. Moving a missing custom asset to `recipient` without real inventory
proof is an incorrect manifest claim which the supervising asset verifier must
reject; this tool cannot inspect the running recipient database.

A standalone `.gsc` binds exactly one ScriptFile root and cannot cover imported
ScriptFiles merely because they appear in its dependency graph. Imports require
another delivered source or server FF. FF is a multi-asset container; SABL/SABS
cover sound nodes and PAK covers image nodes. An audio or texture container cannot
cover a missing model. These are transport-format checks rather than inspection
of actual packed asset inventories.

These checks catch inconsistent manifests; they cannot discover an omitted
dependency by examining packed proprietary bytes. ZoneTool dependency manifests,
effective ScriptFile catalogs, native token mapping, reachable-function graphs,
retail callbacks and recipient verification must establish the closure beforehand.
The Slasher registration graph is useful precedent, not a universal importer or
proof that every phase/audio/FX path is covered.

Source and destination paths use relative forward slashes. Traversal, drive/UNC
paths, ADS, Windows device names, invalid filename characters, trailing dots or
spaces, empty segments, backslashes, symlink/reparse ancestors and case collisions
are rejected. Duplicate source paths, destinations, file IDs and node IDs fail.
Local package files are streamed for size/SHA-256 verification with a check for
size/time/file-identity changes during the read. Missing and nonregular files fail.

## Transport and compatibility

For `mod`, the client destination must be `mods/<id>/mod.ff`, or optional
`mod.sabl`/`mod.sabs`; the FF is mandatory. Separate PAK, executable, DLL, ZIP,
raw Lua or arbitrary scripts are not mod-downloader entries. Use resident textures
or a separately reviewed transport rather than assuming a PAK is fetched.

For `usermap`, the reviewed current-develop layout is
`usermaps/<id>/<id>.ff`, optional `_load.ff`, `_art.ff`, `.pak`, `.sabl`, `.sabs`.
The main FF is mandatory. This is a source-backed allowlist, not a successful
custom-map runtime or a compatibility promise for older clients. Localized
usermap FF variants are intentionally outside this initial contract.

Server files use `iw7-mod/custom_scripts/cp/*.gsc` or `zone/*.ff` and are never
client-downloader files. The required scripts/native source remain separately
reviewed and deployed through current operations. A custom native `client_source`
requirement fails with `--target stock`; `--target native` additionally requires
the exact supplied client source pin. A native server requirement always requires
its exact server source pin at package/delivery stages. Source pins do not describe
an executable installer.

`lua-fastfile` is the first declared client capability. It requires an exact
compatible client source pin from the independently reviewed `CAPABILITY_SOURCES`
catalogue in the validator. A manifest cannot invent a compatible 40-character
revision and make itself ready. Adding a revision requires a reviewed source
proof and code change, not just a manifest entry. The catalogue points to PR #697,
our verified project ancestry and the dated official develop source. No version
range or inferred ancestry is silently accepted. The example's two pins are
source-level compatibility observations, not measured installed binary hashes.
The caller must still establish actual executable provenance independently.
Official release main `1b76f04` predates the loader.
Our pinned `77e6d4d` contains it. See the upstream evidence (server repository: `docs/UPSTREAM-2026-10-06.md`).

## Minimal LuaFile recipe, still unbuilt

`ops/mod-packages/hud-lua-source/zone.csv` declares one original diagnostic
LuaFile, `ui_scripts/paris_hud_probe/__init__.lua`. The Lua source only prints an
initialization marker and is outside active `ui_scripts`/deployment locations.
It creates no HUD, loads no retail asset, writes no game state and is not installed.

Next: verify the pinned ZoneTool's LuaFile input format; stage this tiny source in
an ignored admitted build area; build a distinct real `mod.ff`; replace null
manifest facts with measured inventory/hash/size and closure evidence. Then test
zone initialization, teardown/reload, reconnect and missing-client-version behavior
on the separate dedicated/base observer route. Add one stock LUI text element only
after startup works, and capture a frame to establish rendering. A log marker
cannot establish a visible HUD or multiplayer delivery.

`declared_owner_gameplay_accepted` becomes true only for an explicitly supplied
owner-authority passing gameplay record covering every declared map. Agent gameplay,
static checks, runtime linking and rendered frames cannot substitute for that
record. The field reports declared evidence, not acceptance produced by this tool.

All generated packs, proprietary payloads, raw inventories, profiles and private
evidence stay outside Git. Only recipes, original diagnostic source, sanitized
contracts and tests belong here. No current module defaults, parked feature or
retired texture effect is activated by this work.
