# Bounded beacon FF build

`Build-BeaconFF.ps1` defaults to a **read-only plan**. No helper with top-level
native loading is imported before explicit `-Run`. Planning can run while the
H1 owner holds the single heavy slot; execution cannot. The candidate EXE is
unavailable/unqualified until the H1 owner's final receipt passes.

## Why the existing command cannot run unchanged

`ops/model-lab/Build-ModelFF.ps1` binds `paris_model_probe` in its five source
paths, output name, verify/dump arguments and inventory. It also requires the
old two-test tool provenance and loads a native identity helper even on DryRun.
`Hud-Process.ps1` can accept other arguments, but has no byte cap for logs and
its `IW7LabProcess` owner terminates only the original process. Calling either
unchanged would not establish the requested new zone, provenance or tree cleanup.

The SDK adapter retains the existing Base-Client transaction, ModelFF NTFS/source
identity/restoration checks and machine resource admission. It imports the H1
owner's **final** `tools-source/asset-bridge/model/BuildJob.cs` from its existing
path with an explicit SHA256; no new native process owner is copied or invented.
The job assigns its root suspended, disallows breakaway and kills on close.
The coordinator must supply the final reviewed job hash after H1 corrections.
Before Resume, the wrapper also requires a positive PID, a valid UTC creation
time, the exact resolved Python image and BelowNormal priority from that owner.

## Exact inputs and output

The already prepared beacon folder is used in place. Its ten-file receipt is
rehashed; exactly these five ZoneTool inputs get temporary hardlinks:

```
xmodel/paris_model_probe.xmb
xsurface/paris_model_probe_lod0.xsb
zone_source/sdk_beacon.csv
zone_source/paris_model_probe_recipient.csv
netconststrings/ncs_mdl_paris_model_probe.json
```

`sdk_beacon.gsc` stays outside the FF and is separately deployed by Agent-Lab.
The complete stock list comes from the SHA-pinned, completed/restored historical
`model-lod1m-ff-build-20261007/state.local.json`, with every relative path matched
to an absolute source under the explicit StockRoot. The current read-only plan
found72 entries totaling839,210,257 logical bytes. FFs, PAK1, engine/DLLs and the
new candidate executable use hardlinks, not copies. The mutable77B filesystem
sentinel alone is copied. No stock attributes are changed. Source read guards
remain open through the job; target NTFS identities are checked before execution
and restoration. No source folder, stock, EXE or PDB is duplicated now.

Phases, in order, all inside one complete8GiB RAM/11GiB commit reservation:

```
zonetool.exe -headless -unbuffered-io -strict-content-sources -buildzone sdk_beacon
zonetool.exe -headless -unbuffered-io -strict-content-sources -verifyzone sdk_beacon
zonetool.exe -headless -unbuffered-io -strict-content-sources -dumpzone sdk_beacon
model-writer.exe --verify-existing <absolute RunRoot/roundtrip>
```

Retain `zone/sdk_beacon.ff` as `RunRoot/mod.ff` before later gates, size1..1MiB.
Expected inventory is exactly:

```
material,,mopw/character_park_clown_zombie_shoes
xmodelsurfs,paris_model_probe_lod0
xmodel,paris_model_probe
netconststrings,ncs_mdl_paris_model_probe
rawfile,sdk_beacon
```

Dump from `dump/sdk_beacon`; retain only the two original geometry dumps (each
at most8192B). The retained B77B422E… reader must confirm24 vertices,12 triangles,
one bone/LOD, LOD1M and the recipient material. No `cp_zmb` preload is added.
Bootstrap inventory/geometry cannot establish actual recipient material binding,
pixels, native Use, rejoin or multiplayer. Successful output keeps `Ready=false`.

## New EXE provenance and launch

The coordinated H1 producer is `runtime/zt-full-a`; EXE is
`bin/zonetool-community.exe`. The wrapper requires the SHA-pinned
`build-artifact.local.json` schema `iw7.zonetool-community-candidate/1`, exact
EXE path/bytes/hash, linked preparation/result hashes and `macro_compiled=true`.
It also verifies the real compiler-command tlog bytes/hash and the
`EXPERIMENTAL_IW7` token. Preparation must name pin `fab9358`, exactly three
patches with their pinned names and SHA256 values, five exact patched CPP source
identities, 413 units and 18 libraries; final result must show successful last attempt,
zero job members, unchanged inputs and released build lease. Compilation alone
is never renamed `TestsPassedReviewedBinary`. PDB/symbol suitability and runtime
remain separate evidence owned by the producer/coordinator.

The third patch is `zonetool-fab9358-h1-map-layout.patch`, SHA256
`75c26c4eb9d2260dc71a722d4e54aaa49fea03a4e8c0e8554f3643231d0e3cd7`.
Its `map-layout-source.json` binds the historical field rename and fifth CPP,
`h1/converter/iw7/assets/clipmap.cpp`, with status
`experimental_runtime_unvalidated` and `runtime_validation=false`. The SDK
requires preparation to retain the corresponding unvalidated capability; it
does not qualify maps, collision or scriptables. Both the preparation and final
artifact must contain the exact same three pinned patches; missing, substituted
or additional patches are refused. The source plan may report only
`SourcePreparationContractVerified`, with `BuildValidated=false` and
`MapRuntimeValidated=false`; it cannot manufacture a passed build receipt.

The local, ignored `runtime/beacon-v1-ff-parameters.local.json` contains actual
absolute paths for this machine; `runtime/beacon-v1-ff-plan.local.json` lists
every exact stock entry. They contain no server password. Planning command:

```powershell
$beaconArgs = Get-Content runtime/beacon-v1-ff-parameters.local.json -Raw | ConvertFrom-Json -AsHashtable
./sdk/modding/Build-BeaconFF.ps1 @beaconArgs
```

Only after the coordinator GO, successful final H1 receipt and an available heavy
slot, add `CandidateArtifactSHA256` and `JobSourceSHA256` from their verified
receipts, then invoke the same command with `-Run` in a fresh PowerShell host.
Never fill either hash with a guessed value. No `RunRoot` may already exist.

`beacon_tool_phase.py` is a small output adapter inside that job, not a new
ownership API. Both stdout and stderr are drained, each capped at2MiB; excess
bytes or pipe/disk errors mark failure. Native phase timeout is240s (reader30s),
outer allowance245s/35s. New generated files have a64MiB stop threshold, checked
every100ms; that filesystem threshold can overshoot between samples. Stock links
are excluded from that count. A fresh measurement after every phase and before
success includes all logs, receipts and retained artifacts, even when the phase
finished between polls. The receipt records maximum and final observed bytes.
No automatic large dump/CDB capture is added.
`stop.request`, timeout, memory pressure or output failure terminates the original
job. The wrapper requires root exit and active members0 before restoration and
lease release. Unconfirmed closure/restoration retains inputs, receipt and lease;
do not recursively remove work or delete scheduler state to retry.

No dedicated/client is launched by this script. Future Agent-Lab sessions retain
the mandatory private/password/loopback/heartbeat-suppression privacy gate.

## Source-only validation

Default planning completed against the real prepared source, original reader
and72 stock metadata records with `CandidatePending=true`, native job type absent
and work directory still absent. The live H1 preparation contract reports three
patches, five CPPs, 413 compile units and 18 libraries; build and map runtime
validation remain false.21 standard-library tests pass (including bounded
pipe tests without a subprocess). PowerShell parsing, six inventory fixtures,
complete-identity refusals, final-output boundaries and twelve malformed source
contract refusals pass without Add-Type.
This does not test native job closure, actual hardlink
staging/restoration, EXE execution, FF serialization or readback of the new FF.
Those require the separately admitted first execution; no source-only test is
reported as its successful result.

## First native execution, 2026-10-12

After the coordinator's explicit GO, the first actual build, verify, dump and
native reader phases all exited 0 with zero remaining job members. The new
`sdk_beacon` FF is **1,048 bytes**, SHA256
`76ed0701dc1480c501604db04999f300394c65877aa24a70dfe7afc2cd662d4a`.
The exact five-asset inventory passes. Native readback confirms 24 vertices,
12 triangles, one bone/surface/LOD and the retained LOD1M metadata.

The full 8 GiB RAM/11 GiB commit admission was used. Maximum observed outputs
were 1,198,238 bytes; 1,197,187 bytes remain as evidence after restoration,
principally two generated TOC cache files. All 78 staged input entries are gone,
source identities/metadata are preserved, and the lease was released; the fresh
registry read was empty. Each stdout was at most 1,212 bytes; all stderr streams
were empty. Bootstrap logs mention missing English language zones;
this did not prevent the required inventory or geometry checks.

The [sanitized execution record](beacon-ff-validation-2026-10-12.json) binds the
source, final H1 tool receipt, shared job implementation and retained local state.
The actual FF is retained in ignored `runtime/beacon-v1-ff-build-20261012/mod.ff`.
No client or dedicated was launched. Recipient material resolution, pixels,
Use/HUD/rejoin, multiplayer and H1 map conversion remain unvalidated. `Ready`
remains false; the next game test belongs to a separate coordinator allocation.

At the 2026-10-12 03:36:51 UTC availability refresh, the old
`doom-negative-textures` stock worktree/root was absent. The completed beacon
`mod.ff` and `state.local.json` remain present with their final hashes unchanged.
Do not replay the old stock parameters: a future build needs a verified suitable
retained root and a fresh provenance plan. Historical receipts were not edited.
