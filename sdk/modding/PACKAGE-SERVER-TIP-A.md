# Server spawn-tip Package A — 2026-10-13

One authorized `Creator -Action Package -Adapter None` invocation returned
**exit 0** and produced a **3,561-byte ZIP** containing exactly the manifest
and the original 894-byte server GSC. This records a real local package, with
payload integrity verified separately from runtime linking and gameplay.
`ready_to_deploy`, `runtime_ready` and `owner_accepted` remain false.

## Source and qualification

The operation used clean source
`7f23ae5c19a71e09d382026449a66c9c632e90ed` (PR #200). It created a fresh ignored
author project under `runtime/spawn-tip-package-a/project` in the retained
`modding-sdk-contract` worktree. The tracked
[example manifest](examples/server-spawn-tip/manifest.json) and
[original GSC](examples/server-spawn-tip/sdk_spawn_tip.gsc) stayed unchanged.

The GSC was copied byte for byte and matched both the working example and its
Git blob: **894 bytes**, SHA256
`eb574a8da461b6e38024a985264b0cf7dd91cf230afc793c73c3c8f4da962e23`.
The 327-byte compiled container from [Run C](../../tools-source/gsc-spawn-tip/RUN-C.md)
is an audit artifact and was not read, copied or packaged by this operation.

Only the separate author manifest received measured source bytes/hash, the
source node hash, `closure.status=complete` with pinned evidence references,
and `source-check=pass` for `maps=[cp_zmb]`. The reviewed declaration covers the
standalone source inventory and encoded script-reference absence. It does not
claim native builtin semantics, native asset dependency closure or runtime
compatibility. `runtime-link` and `gameplay` remain pending, with null references
and empty evidence map lists. The package map remains `cp_zmb`.

Seven bounded existing JSON files were checked against their recorded sizes and
hashes before preparation: Plan C, runner receipt, references report, host
postflight, exit request, actual exit and the independent absence witness.
Their paths and full pins remain in `preparation.local.json`; no evidence files
were duplicated into this package directory. The manifest references bind:

| Evidence | Bytes | SHA256 |
| --- | ---: | --- |
| Run C `spawn-tip-offline-c/receipt.json` | 4232 | `8b28ec0d2aa9011fdedd6b20658c856e90da0764909abbf88a86ebc3fcf5741d` |
| Run C `spawn-tip-offline-c/phase/references.bound.json` | 3977 | `5f292a8917c22f414572948c180949caa356f9bfbdea2f9963ffbf42411f408c` |
| Independent `spawn-tip-offline-c-independent-absence.local.json` | 6261 | `33f39fab1d6a5f9ef5f65f533a6673b000db3d2939c1c97768e49d26b77e32b0` |

These are reviewed evidence declarations prepared before invocation. Creator
checks the declared contract and payloads; it does not authenticate or re-audit
Run C by following those references. `GscAuditEvidence` was not supplied to
Package, which rejects that adapter input. No shared gate or schema was changed.

## Actual command and result

Both `ClientSource` and `ServerSource` were explicitly asserted as
`77e6d4d24e918ee363b3feee3735c3b889dff7d7`, with `Protocol=2`. These are operator
compatibility assertions for the intended target. The current installed
client's provenance was not verified, and no installed EXE was read or hashed.

The invocation below is the recorded command with worktree paths made relative
for this sanitized document. The exact absolute command array is retained in
both preparation and verification receipts. It is historical evidence, not an
instruction to rerun against the already-existing output:

```powershell
pwsh -NoProfile -NonInteractive -File ./sdk/modding/Creator.ps1 `
  -Action Package -Adapter None `
  -Project ./runtime/spawn-tip-package-a/project `
  -Output ./runtime/spawn-tip-package-a/sdk_spawn_tip-0.1.0.zip `
  -ClientSource 77e6d4d24e918ee363b3feee3735c3b889dff7d7 `
  -ServerSource 77e6d4d24e918ee363b3feee3735c3b889dff7d7 `
  -Protocol 2 -ToolsRoot . -Json
```

The single invocation started at `2026-10-13T09:01:23.753235Z` and finished at
`2026-10-13T09:01:24.258112Z`, exit 0. There was no retry or gate override.
Standard output was 2,887 bytes; standard error was empty. Creator reported:

| Field | Observed value |
| --- | --- |
| `plan_valid`, `packaged` | `true` |
| `package_result.valid`, `package_result.packaged` | `true` |
| `build_executed`, `build_verified`, `materialized` | `false` |
| `runtime_ready`, `owner_accepted` | `false` |
| `package_result.ready_to_deploy` | `false` |
| `errors` | `[]` |

Creator's successful package report does not clear the manifest's pending
runtime-link/gameplay evidence. No Install Plan/Apply, native build, heavy Run,
game launch or deployment occurred during this package operation.

## Archive verification

After Creator returned, the ZIP was reopened and verified to contain exactly
these two regular, stored entries, with no CRC error:

| ZIP entry | Bytes | SHA256 |
| --- | ---: | --- |
| `manifest.json` | 2347 | `12bdf90cb04dfb211169f766d92a726120af0f3958808c5786973eb53a171197` |
| `server/iw7-mod/custom_scripts/cp/sdk_spawn_tip.gsc` | 894 | `eb574a8da461b6e38024a985264b0cf7dd91cf230afc793c73c3c8f4da962e23` |

The ZIP manifest matched the canonical serialization of the author manifest
and had identical parsed content. The GSC matched the original bytes; its
packager-reported Aurora CRC32 was `6EB20A34`. The ZIP's path, byte count and
SHA256 matched the Creator receipt. The tracked worktree remained clean.

## Retained files and storage accounting

The following inventory is exhaustive for ignored
`runtime/spawn-tip-package-a/` at verification time
`2026-10-13T09:02:32.886367Z`. Full local paths remain in the ignored receipts.
No artifact or raw receipt is committed to Git.

| Relative file | Bytes | SHA256 |
| --- | ---: | --- |
| `project/sdk_spawn_tip.gsc` | 894 | `eb574a8da461b6e38024a985264b0cf7dd91cf230afc793c73c3c8f4da962e23` |
| `project/manifest.json` | 3137 | `12382afc98d5e3847b14130a8488129d8c633cbe1a208e4da1b0e1fe14e68a6f` |
| `sdk_spawn_tip-0.1.0.zip` | 3561 | `3569da056162689b8a559d3040ab88110b97cb3f9964c4b2170f46fe15862a55` |
| `preparation.local.json` | 5280 | `2505d5ee659b768cf7b80449b4cc3f8014b80fb417d5161abf4c2d7ab12a5a65` |
| `creator-package.stdout.json` | 2887 | `eb7e73bd741a0f9b31d9d1cdc5648077b2854b4ff2eb5bad7bd873673c15122b` |
| `creator-package.stderr.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `verification.local.json` | 4719 | `3cbac9c492d963a2bee47bf0e61c6873539aff2fed6b93ad458e0881ca522d09` |

Final usage was **7 files / 20,478 bytes**, within the additional 1 MiB allowance.
The project used **4,031 bytes** against 17 KiB; the ZIP used **3,561 bytes**
against 32 KiB. The conservative preflight ZIP estimate was 5,645 bytes.
Each trace remained below 256 KiB and the complete directory stayed below the
eight-file cap. These are preflight and final accounting checks, not an OS quota.

The author ZIP and receipts are preserved for the separately coordinated
installation preparation. The next stage must keep package integrity, candidate
installation, runtime linking/message visibility and owner acceptance distinct;
this checkpoint authorizes none of those later transitions by itself.
