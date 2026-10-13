# Community mod distribution: deterministic staging, explicit client compatibility

Source-only checkpoint, 2026-10-12. The preparation gate forbids game launches,
native builds, asset extraction, leases and publication. This work adds an offline
packager and compatibility preflight. It does not deploy or qualify a public
server. Main27016, the owner's client, bank, configuration and network are untouched.

Player projection added on 2026-10-13 under the owner's resumed feature work.
The dated source-only checkpoint above describes its original authorization.
The same ZIP writer now supports an explicit `--layout player`; default staging,
the common manifest, compatibility gates and package qualification are preserved.

## One contract, two delivery routes

The author supplies the architecture SDK's `iw7.community-mod/1` manifest from
`sdk/modding/manifest.py`. Its `package` field is the existing `iw7.mod-package/1`
transport object: one authoritative list of files, hashes, destinations, closure,
source requirements and evidence. Distribution creates no competing manifest.
See [SDK platform](MODDING-PLATFORM.md) and [transport contract](MOD-PACKAGES.md).

| Content | Route and boundary |
| --- | --- |
| Server GSC only | Reviewed dedicated deployment; empty `fs_game`; no client file transfer. |
| Mod client assets | One selected `mods/<package.id>`; real `mod.ff` required, optional `mod.sabl` and `mod.sabs`; automatic asset download at join on a compatible Aurora client. |
| Native client feature, executable or DLL | Explicit compatible community-client release/install before joining. Fast download cannot install it. The packager refuses these payload destinations. |
| Usermap, external PAK, arbitrary MP mod | Outside this SDK v1 distribution implementation. Later usermap source has a separate file list; its existence does not extend the mod list or establish runtime support. |

The v1 SDK is CP-only. The compatibility CLI accepts an observed `--mode mp` to
report the mismatch; that option does not enable MP support. Public CP dedicated
hosting is a future deployment decision, not something inferred from a valid ZIP.

## Source evidence, without a second upstream update check

The retained local Git objects were read, not fetched from upstream. The current
project native pin is `77e6d4d24e918ee363b3feee3735c3b889dff7d7`. The older pins
`36f7afedb9e4c8c665b6e29227e3f5c660ed63d6`,
`02a9aeeb89174812fb9a250e437f966239aeba26` and release
`1b76f04e55b7e01ffb9d5a6fd9053585beb5ba27` were also checked locally for the
three mod entries and `PROTOCOL 2`. They are the bounded transport allowlist in
`Distribution-Compat.py`, not a list of fully qualified gameplay builds.

| Evidence | Consequence |
| --- | --- |
| [party.cpp at the project pin](https://github.com/auroramod/iw7-mod/blob/77e6d4d24e918ee363b3feee3735c3b889dff7d7/src/client/component/party.cpp), `mod_files`, `check_download_mod`, `infoResponse` | `mod.ff`/`mod_hash` required; `mod.sabl`/`sabl_hash` and `mod.sabs`/`sabs_hash` optional. Empty required hash blocks join. Both empty `fs_game` values skip mod download. |
| Same source, path and protocol checks | Advertised path starts `mods/`, contains neither a dot nor `::`. A dotted semantic version must not be pasted into `fs_game`. Protocol equality is checked, but does not negotiate capabilities or identify a native build. |
| [download.cpp](https://github.com/auroramod/iw7-mod/blob/77e6d4d24e918ee363b3feee3735c3b889dff7d7/src/client/component/download.cpp) | Requests `<sv_wwwBaseUrl>/<destination>`; rejects missing URL/curl errors/HTTP >=400/hash mismatch; saves bytes and reconnects. A mod change can require `vid_restart`. It does not read this SDK manifest or resolve its dependencies. |
| [hash.cpp](https://github.com/auroramod/iw7-mod/blob/77e6d4d24e918ee363b3feee3735c3b889dff7d7/src/client/utils/hash.cpp) and [dump_hex](https://github.com/auroramod/iw7-mod/blob/77e6d4d24e918ee363b3feee3735c3b889dff7d7/src/common/utils/string.cpp) | Generic FF/audio transport hash is CRC32, serialized as the four little-endian Windows `uLong` bytes in uppercase hex. `123456789` therefore gives `2639F4CB`, not `CBF43926`. Package/archive SHA-256 remains separate; CRC equality does not authenticate a publisher. |
| [fastfiles.cpp](https://github.com/auroramod/iw7-mod/blob/77e6d4d24e918ee363b3feee3735c3b889dff7d7/src/client/component/fastfiles.cpp), `sys_create_file_stub` | Opens the three mod filenames through the selected `fs_game`. Client FF/audio also need to exist on the dedicated side for load/hash advertisement. |
| `ops/Download-CacheOverlay.Core.ps1` in this project | The reviewed overlay changes only the client cached-hash call to a fresh file hash. The upstream source pin alone cannot identify whether an executable includes this overlay. Server pathname hash caching remains. |

The inspected protocol does **not** advertise SDK version, asset namespace,
dependency graph or client build identity. The CLI checks the supplied environment
facts; it does not add handshake enforcement. A source pin is an operator assertion
until correlated with the exact executable/build manifest. See also
[existing client evidence](CLIENT-COMPATIBILITY.md) and the earlier
[one-time upstream inspection](UPSTREAM-2026-10-06.md).

## Author to package

1. Author original or authorized content in a private staging root. Produce the
   asset dependency closure and actual pack through the reviewed SDK/ZoneTool
   workflow. Names in packed databases are global: filesystem namespaces alone
   cannot isolate two identical material/script/model names.
2. Fill the common manifest's exact version, measured bytes/SHA-256, closure,
   lifecycle and native requirements. The mandatory `mod.ff` must be a genuine
   engine-compatible fastfile; this packager cannot establish its internal format.
3. Supply the exact expected client/server source pins, observed network protocol,
   and **every other intended active mod** with its local payload root. There is
   no dependency network fetch, package manager, version-range solver or hidden
   installation. Dependencies are separately packaged/deployed by the operator.
4. Run the packager from a checkout containing the SDK and distribution commits:

```powershell
python ops/modding/Package-CommunityMod.py <community-manifest.json> `
  --root <private-build-root> --output <fresh-staging-path.zip> `
  --client-source <reviewed-client-commit> --server-source <reviewed-server-commit> `
  --protocol 2 --mode cp --max-bytes 67108864
# Repeat for every other active mod, including dependencies/conflicts:
# --active <dependency-manifest.json> <dependency-payload-root>
# Only for an explicit custom native client requirement: --target native
```

`--sdk-root` can temporarily point to the architecture chat's **reviewed local
source directory** before integration. It imports that Python implementation; it
is never read from a package manifest or fetched from a URL. Normal integrated
use needs no override. Python 3.11+ standard library is sufficient; this task used
the existing Python3.12 and installed no tools.

The preflight first uses SDK plan validation, then bounds declared/actual sizes
before any package hashing. SDK package validation measures every listed payload
and active dependency. Distribution additionally refuses missing/wrong exact
dependency versions, dependency cycles, conflicts in either direction, duplicate
IDs/namespaces, Windows-case destination collisions, and duplicate delivered
asset kind/name pairs. Recipient inventory nodes can be shared. It refuses a
second client mod because only one `fs_game` is selected: combine required client
assets into one complete closure/FF and revalidate, rather than pretending multiple
downloaded mods are composed automatically.

The capability-to-source table is reviewed code, never supplied by the manifest.
The original model/NCS/script-model and Lua witnesses are conservatively restricted
to the project pin. This is a recorded verification boundary, not a claim that
all older clients lack those engine types. Unknown/unproven capability source
pairs fail closed. SDK capabilities marked blocked cannot become packaged by
claiming a protocol match.

## Archive layout and integrity

```text
manifest.json                       exact common manifest, canonical JSON
fastdl/mods/<id>/mod.ff              client entries only, web-root-relative
fastdl/mods/<id>/mod.sabl             present only if declared
fastdl/mods/<id>/mod.sabs             present only if declared
server/mods/<id>/mod.*               client payloads also required by dedicated
server/iw7-mod/custom_scripts/cp/... declared server scripts, if any
server/zone/...                      declared server fastfiles, if any
```

The default ZIP is a staging layout, **not an archive to extract over the game root**.
The authoring `source` paths inside the manifest are unchanged. The operator maps
archive entries by declared `destination`; the packager provides no extractor or
automatic installer. Never expose the `server/` subtree through fast download.
Only explicit manifest entries are copied, so unrelated files in a build root are
not swept into a package. Script/FF content still needs review: path filtering is
not an analysis of proprietary or secret data inside author-supplied payloads.

Archive names are sorted, JSON object keys canonicalized, timestamps fixed at
1980-01-01, permissions fixed at0644, and entries stored without compression. The
same manifest (including array order) and payloads yield identical archive bytes,
independent of local input mtimes. No ZIP compression implementation variability
is involved. Client payload duplication is charged twice to the output budget.
The default archive/aggregate-input limit is64MiB; this is an operational bound,
not a reason to package oversized content for the user's installation.

Payload SHA-256 and sizes are verified again **while writing**, including both
server and HTTP copies. Path links/reparse points are rejected; file identity,
mtime and size changes are checked. A same-directory temporary output is published
with a no-replace hardlink only after validation. Existing output or a publication
race fails without replacing the other file. A failed write removes only the new
temporary output. Filesystems without hardlink support fail rather than silently
falling back to an unsafe overwrite. This is a bounded trusted-staging workflow,
not an atomic installer resistant to hostile concurrent directory replacement.

## Copyable player archive

After the complete author package passes the existing SDK package and compatibility
checks, run the same command with `--layout player` and a separate fresh output:

```powershell
python ops/modding/Package-CommunityMod.py <community-manifest.json> `
  --root <private-build-root> --output <fresh-player-path.zip> --layout player `
  --client-source <reviewed-upstream-client-commit> --server-source <reviewed-upstream-server-commit> `
  --protocol 2 --mode cp --target native
```

The exact archive layout is:

```text
PLAY.txt
mods/<id>/mod.ff
mods/<id>/mod.sabl    only if declared
mods/<id>/mod.sabs    only if declared
```

This projects the manifest's client files without changing their destinations or
bytes. Server GSC, `server/`, `fastdl/`, author manifests, PS1, source trees and
unlisted files are absent. The client executable and its release notices are
supplied separately by the native release owner; no executable is inferred from
the mod or copied from the build root. `PLAY.txt` tells the player to close the
game, back up an existing `mods/<id>`, copy the `mods` directory into the legitimate
game installation, start the compatible community client and join the intended
server. An existing `mods/<id>` must first be moved outside the game installation
as a backup, leaving an absent destination. To roll back, close the game, remove
only the newly installed `mods/<id>` and move the original folder back. Do not
merge either folder: this prevents old optional SABL/SABS files surviving a release
that omits them, or newly added files surviving restoration.

Server-only packages have no player assets and are refused in this layout. The
existing operator ZIP remains the input for `Install-CommunityMod.Package.py`
and the backed-up server/FastDL installer; the player archive is a manual copy
route and is not accepted as operator staging. Do not feed it to that installer.
Source and creator tooling remain separate downloads.

The complete author package, including server files omitted from the player ZIP,
still passes the real SDK and compatibility gates before projection. An incomplete
closure, changed server script or wrong protocol still blocks output. No additional
manifest or qualification gate is introduced. The writer reports
`archive_layout: "player"`, exact delivered hashes/CRC32, archive size and SHA-256;
`ready_to_deploy` remains false. It reuses deterministic entry metadata, streaming
integrity checks and no-replace publication. The output budget charges only the
copies actually delivered in the chosen layout.

Compatibility SourcePin values retain their upstream Aurora meaning, including
`77e6d4d24e918ee363b3feee3735c3b889dff7d7`. A private product commit must not replace
that value in the old reviewed source table. Correlate the exact executable hash
separately with its build manifest's upstream revision, product/project commit,
profile/modules, overlays and source-identity receipt where present. A migrated
source checkout or an older binary does not automatically acquire the other's
qualification. Actual client/server handshake, mod load and rejoin remain runtime
checks on the intended private releases and real FF output.

Targeted source validation on 2026-10-13: 23 distribution tests, 22 passed and one
Windows symlink case skipped because this token cannot create symlinks. New cases
cover a copyable FF/SABL/SABS layout, omission of scripts/tools/local files,
determinism, overwrite/tamper refusal, server-only/invalid layouts, layout-aware
byte accounting and real SDK rejection of changed server files, incomplete closure
and protocol mismatch. Fixtures use synthetic CRC vectors, never engine-loadable
content. No genuine BO3 player archive or installation/rejoin is claimed by these
source tests; those await the qualified demo outputs and native release.

JSON stdout records the final archive SHA-256/size and derived payload transport
hashes. It always says `ready_to_deploy: false`. The SDK/closure/evidence records
are declarations and local integrity checks, not runtime observations. A synthetic
9-byte `mod.ff` deliberately passes the transport test and must never be served
to a game. This demonstrates why package validity is distinct from FF/engine validity.

## Package to server to client join

After the parent lifts the heavy-test gate, validate the genuine candidate on a
retained separate dedicated and the base client with the resource reservation and
protection rules. Obtain offline FF load, runtime-link, render where relevant,
and actual client-join evidence for every supported map before a delivery claim.
Inspect the exact native build and overlays, not just its upstream commit.

For a future authorized public rollout, publish only the immutable `fastdl/`
contents beneath a versioned HTTP(S) base, and deploy matching `server/` files
through the existing backed-up/guarded operations. Verify fetched bytes against
the package and the dedicated's advertised hashes before announcing availability.
Set `sv_wwwBaseUrl` to that base, `fs_game` to `mods/<id>` only for the asset mode,
and let the engine derive the hashes from real files. Do not invent a `mod_hash`.
Use an existing appropriate host only after publication authorization; no host,
URL, firewall or router change was made here.

Keep versions immutable. A compatible update under the same ID still requires a
controlled dedicated restart because server hash caching is pathname-based.
The client cache overlay's presence must be verified for loaded-update tests.
For revisions that change/remove optional audio, use a new safe ID/path such as
`author_mode_v1_2_0` (never dots), or an explicit stopped-client cleanup/reinstall
process: missing optional hashes make the downloader skip those files, not remove
stale local audio. The packager does not rename IDs, silently delete old payloads,
or enforce immutability across past releases. Retain old release package/checksum
and config for guarded rollback; bank data remains outside all these archives.

An ordinary compatible client can then join, download the advertised FF/audio,
reload assets and reconnect. A wrong SDK dependency/version is caught in offline
preflight; it is **not** newly negotiated by the current engine at join. A native
feature needing client changes therefore follows the explicit route below.

## Explicit community-client route

Maintain a separately reviewed community-client release with its exact source
commit, build/overlay identity, file SHA-256, protocol, capability support, source
and applicable notices. The existing split player/source packaging is precedent,
not automatic compatibility evidence. No client release was built or published
in this lot.

The player intentionally obtains that release from the chosen trusted project
release channel, verifies its checksum against that channel, closes the game,
keeps the official launcher, and installs/launches the named sidecar client in
their legitimate game installation. The owner-facing instructions must name the
compatible dedicated release. Do not execute a URL/script/executable supplied in
a mod manifest, infer trust from `sv_wwwBaseUrl`, or replace the running client.
The native route grants no asset-download install powers. CRC32/SHA-256 integrity
without a trusted release channel is not publisher authentication.

Before joining, correlate installed executable hash with the reviewed build
record and run the same exact source/protocol/capability preflight. The current
tool does not hash a client executable or interrogate a live server. A future
community launcher/handshake can enforce build/capability policy, but this task
does not pretend one exists. Sharing a network protocol number is insufficient
for Lua loaders, native voice, hooks, custom assets or other engine changes.

## Verification and next decisive experiment

Run `python tests/ops/community_distribution_test.py` after integrating the SDK.
Before integration, set the task-local `IW7_MODDING_SDK_ROOT` to its reviewed SDK
directory. The real CLI calls the real SDK; no success mock replaces the contract.
The17 cases pass16 and skip1 real symlink case because this Windows token cannot
create symlinks. The26 pre-existing transport cases pass25 and skip1 for the same
host limitation. They cover deterministic output, source changes, no-overwrite
publication races, byte budget, strict JSON, mismatched native target, mode/protocol,
unsupported executable paths, corrupt active dependency and compatibility graph.
No Windows symlink runtime acceptance is claimed from that skip.

A retained ignored synthetic archive is2494bytes, with SHA-256
`1410915f54ccd5827c12487408ebbc3d17139135629b6f50e428b9a479bb373b`.
Its only payload is the original CRC check vector `123456789`; all engine/render/
gameplay records remain pending. It contains no proprietary asset and is not
engine-loadable. The whole new source checkout was approximately6.4MB before
this small implementation, well under this chat's100MB preparation ceiling.

Next, under the parent's single heavy reservation, reuse the SDK vertical's
small genuine FF with original model/Lua assets and its dedicated script. Cap
new pack+staging+logs at64MiB for this distribution experiment; reuse installed
tools, stock and base client. Budget the full dedicated+client through current
[resource](RESOURCE-WORKFLOW.md), [instance](INSTANCE-WORKFLOW.md) and
[storage](STORAGE-WORKFLOW.md) workflows; a12GiB full-quality client plus the
greater2–4GiB dedicated estimate is the starting physical/commit estimate, not
proof of admission. Compile/extract only in a separately admitted phase.

Observe: absent mod first join, cached rejoin, loaded update, corrupt/absent HTTP
file, wrong native source/capability, optional-audio removal/version path, rotation
and restoration. Record hashes and actual loaded/rendered state separately. A
second authorized remote machine is needed before WAN/multiplayer-public claims.
No new copies/services are justified by this plan. Parent owns the private
PR/exact-head CI/merge, common STATE/BUGS/VALIDATION/PLAN integration and the next
admitted experiment; this chat supplies a coherent source commit without a separate
competing PR or deployment.
