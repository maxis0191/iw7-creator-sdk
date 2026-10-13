# Spawn-tip Run C — 2026-10-13

One authorized native attempt qualified the exact original spawn-tip's offline
GSC compilation under the pinned V8 community IW7 decoder: both buffers were
fully consumed, every instruction was independently checked, and no encoded
external, unresolved or dynamic script-reference blocker remained.

This is **offline encoded-reference evidence only**. Native builtin semantics,
asset dependency closure, Aurora runtime recompilation/linking, package readiness
and owner gameplay acceptance remain unverified. No game, package, installation,
native rebuild or second Run was performed. The server payload remains the
original `.gsc`; the `.gscbin` is an audit artifact.

## Exact scope and measurements

- Reviewed clean source: `732951a41db6816c8eeeac0582500ea605f14f03` (PR #199).
  The original host-argument P2 in `3de35aa` was corrected by `f91cc497`
  before integration and before this attempt.
- Plan C SHA256:
  `61d4621adcec5be8bc7c8d7b7ad14b5c997b9d8e6439b3a793bcd0fc41a138b7`.
  Default validation passed with 23 text/source bindings, including eight actual
  physical table files. Binary pins were expectations at Plan time and were
  verified during admitted execution, not inferred from metadata alone.
- GSC source: 894 bytes,
  `eb574a8da461b6e38024a985264b0cf7dd91cf230afc793c73c3c8f4da962e23`.
- Compiled container: 327 bytes,
  `42b3591a8618041c67f2ecea6187a56d08b49cfea1a6e0fb881a49b65365adf4`.
- The independent text-evidence review matched **63 instructions**, bytecode
  **148/148 bytes** and decompressed stack **269/269 bytes** consumed, complete
  instruction coverage, encoded-reference absence and an empty blocker list.
- Runner result: `OfflineReferencesQualified`, original root exit 0,
  `TreeClosureConfirmed=true`, `LeaseReleased=true`, no quarantine or forced
  termination. The child reverified source/tool inputs; the parent guarded and
  reverified inputs and output identities before releasing admission.
- Runner timestamps: `2026-10-13T08:36:47.0589295Z` started and
  `2026-10-13T08:36:47.8844310Z` finished. The observed owned-stage elapsed value
  was 411.4568 ms; this is not a separately measured compiler/auditor duration
  or a new resource estimate.

The retained official compiler pin is
`1adfd67414a9b886cbad57ee0378f622eed485bcef7711322aee478e298fadcb`.
The retained V8 auditor pin is
`fbaeff90961d1c5c3aec5f293c6dcb7b9dd92ab049e6aebe3ea399b47a007211`,
source revision `03d3956d648b7aa4637fe1007f9d69ea463631e9`.
The exact source/table/validator and helper bindings remain in Plan C; no Beacon
artifact was substituted for this newly compiled input.

## Preflight, admission and storage

Both other operational chats were read immediately beforehand: not loaded, with
their latest turns completed. Fresh inventory found no IW7/T7/build process,
relevant UDP listener or lease. The separately identified pre-existing Python
process was preserved. Full 4 GiB physical / 6 GiB commit projection fit current
capacity, without a smaller RAM budget or reserve-policy change.

The first preflight command refused **before admission and native execution**
because its comparison mixed local and UTC `DateTime` representations. Raw CIM
identity inspection confirmed the same existing Python creation tuple. Comparing
the canonical UTC value corrected that transient inventory check; the reviewed
runner, source and Plan C remained unchanged. This was not a native retry.

Admission retained 4/6 GiB and the reviewed 180-second outer deadline,
20-second compiler / 60-second auditor bounds and H1 5-second owned cleanup.
The 65 MiB storage allocation remained 1 MiB preparation plus 64 MiB outputs,
including the reserved receipt space. At closure, run outputs used **23,870
bytes / 15 entries**, preparation and local evidence used **42,485 bytes**,
total **66,355 bytes**. The observed pre-receipt output high-water value was
19,638 bytes. No allowance was exceeded or waived; polling is not an OS quota.

## Original host and actual exit

The original `-NoExit` host retained the in-memory runner result, owner, guards
and verified host contract after the native work. Inspection observed
`ContextClosed=true`, `OwnerClosed=true`, owner exit 0, `CanExit=true`, both guard
counts 0, no context lease, registry lease count 0 and no active/quarantine
context. Exact host, parent and root-child tuples are in the ignored receipts.

The dot-sourced close helper wrote an exit request but returned to the same
interactive host. That host's identity and original context were reobserved;
the fresh in-memory exit guard followed by direct interactive `exit 0` then
closed PTY **3765**. The tool returned **exit code 0**, chunk **`f9b9b7`**, with
the expected normal-exit marker. Neither an exit request nor process absence
was substituted for this actual terminal completion. No recovery incident or
second host was used.

The independent absence witness passed at `2026-10-13T08:46:54.0430224Z`.
Four pinned receipts and the actual completed terminal command agreed. The
three recorded host/parent/root-child identities and observable descendants
were absent, with no lease, heavy/game process or UDP 27016/27116/27117 listener.
Main remained stopped and the original unrelated Python identity was preserved.
The compiler/auditor process names were absent; their individual historical
identity tuples were **not recorded**, so no separate exact-tuple absence is
claimed for them. The witness relied on the original lifecycle/host receipts;
it did not inspect old in-memory contexts/handles or treat the child-only report
as sufficient closure proof. No opaque binary or asset was reread/hashed after
release; subsequent work used bounded JSON receipts and file metadata only.

The inventory worktree retains
`runtime/spawn-tip-offline-c-independent-absence.local.json`, 6,261 bytes,
SHA256 `33f39fab1d6a5f9ef5f65f533a6673b000db3d2939c1c97768e49d26b77e32b0`.
Adding that witness to the producer's 66,355-byte accounting gives **72,616
bytes arithmetically**; it is not an independent complete-scope disk recount.

## Retained evidence pins

Paths below are relative to the producer worktree's ignored `runtime/`.
Only this sanitized checkpoint is tracked; tools, binaries and local receipts
remain outside Git. Product hashes come from the guarded original run receipts.
An earlier wrapped-terminal transcription added one character to the container
digest; the correct 64-character digest above is the structured receipt value.

| Evidence | Bytes | SHA256 |
| --- | ---: | --- |
| `spawn-tip-plan-source-c.local.json` | 9672 | `61d4621adcec5be8bc7c8d7b7ad14b5c997b9d8e6439b3a793bcd0fc41a138b7` |
| `spawn-tip-run-c-preflight.local.json` | 1828 | `41ac47037be48ea1833e4aa229bbcda9e831f58cb3b0ebedb083413b6d590eaf` |
| `spawn-tip-offline-c/receipt.json` | 4232 | `8b28ec0d2aa9011fdedd6b20658c856e90da0764909abbf88a86ebc3fcf5741d` |
| `spawn-tip-run-c-host-postflight.local.json` | 2567 | `d8a5e077d3f30ba88a5a237d83ce0607b61ffbc9958d01fe4cc0026879fc07c2` |
| `spawn-tip-run-c-host-exit-request.local.json` | 1603 | `be514965f8b2f86ecf325e0f9a4651d1591beb3ed6726c4fb71d060355f1ccad` |
| `spawn-tip-run-c-actual-host-exit.local.json` | 2901 | `fefa62065b7aacbd3091f4e6261d90e33759f679cd4787a6c8cd15073fc85443` |
| `spawn-tip-offline-c/phase/audit.stdout.json` | 10337 | `77ca05d1228bacff2d03374b0a3967e843272a250ebd081954f2ee40b133a04e` |
| `spawn-tip-offline-c/phase/references.bound.json` | 3977 | `5f292a8917c22f414572948c180949caa356f9bfbdea2f9963ffbf42411f408c` |
| `spawn-tip-offline-c/phase/disassembly.gscasm` | 1645 | `4dcaedfe5a10051fc1f5a840c53ddfdbcd03369f131771fe2537b87e5cb31d5a` |

Next action: review how Creator can consume this exact evidence without asserting runtime
or package readiness. Changing the source or tools requires fresh qualification;
the existing output root and obsolete Plans A/B are preserved, not reused.
