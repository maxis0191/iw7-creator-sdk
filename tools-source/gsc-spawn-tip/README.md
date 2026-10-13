# Spawn-tip offline profile (source candidate)

This profile qualifies one question about the exact 894-byte original
`sdk/modding/examples/server-spawn-tip/sdk_spawn_tip.gsc`: whether its complete
offline compilation has encoded external or unresolved/dynamic script references
under the retained V8 community IW7 profile. **No native run has qualified this
profile.** Source tests and Plan verification do not establish import absence.

Ownership is limited to this directory. Creator, manifests, common runners and
server files are unchanged. The coordinator owns integration and native GO.

## Reused implementation and evidence

`Run-SpawnTip.ps1` uses the same unchanged H1 functions as d468's
`asset-bridge/t7-bridge/Run-T7Catalogue.ps1`: `Invoke-H1OwnedStage`,
`Register-H1Original`, `Test-H1Budget`, `Complete-H1Stage`, `Open-H1Pin` and
`Write-H1Receipt`. The existing witnessed `Probe-NativeJob.dll` owns the child
and descendants from creation, sets BelowNormal and disallows breakaway.
No native helper or compiler is built. Stage `GscAudit` does not enter the H1
MSVC telemetry exception. There is no vctip classification or residual waiver.

One pinned Python child runs exactly two native invocations, sequentially:

1. `gsc-tool.exe -m comp -g iw7 -s pc SOURCE`, with the fresh `RUN/phase` as cwd.
   Exit status, error text and exactly one `compiled iw7/` marker must agree.
2. `iw7-gsc-audit.exe --stdin-gscbin-references`, using the exact compiled
   container bytes over binary stdin. Its nested consumption witness supplies
   the disassembly; a separate historical `disasm` invocation is unnecessary.

The child reuses `audit_gsc_consumption.run_bounded` and `validate_witness`, then
`audit/references.py:validate` from the retained independent auditor source.
The latter independently redecodes every instruction and stack operand and
compares native symbols/partitions with its own parse. Neither Beacon's fixed
artifact pins nor Creator's Beacon adapter are repurposed. Original source,
compiler, auditor, validators, all eight physical table files, Python, host and
the existing Job DLL are bound in the plan and reverified during admitted work.

Expected identities are in `spawn_tip.py`: official compiler SHA starts
`1adfd674`, V8 tool `fbaeff90`, source revision `03d3956d`, and Job DLL `5f613ebb`.
The V8 build/supervision receipts are pinned to `7279357c` / `f1a1f3e4`.
These historical expected tool identities are **not freshly observed binary
hashes** during Plan. Source tables are hashed as actual physical bytes,
including the retained CRLF bytes. No retail assets are read or needed.

## Source-only preparation and review

Use existing paths from the retained receipts; no installation or clone:

```powershell
& $Python -I -B "$Repo/tools-source/gsc-spawn-tip/spawn_tip.py" plan `
  --repo $Repo --audit-source $AuditSource --compiler $Compiler `
  --python $Python --host $HostImage --job $JobAssembly `
  --run "$Repo/runtime/spawn-tip-offline-a" --output $PlanPath
& $HostImage -NoProfile -File "$Repo/tools-source/gsc-spawn-tip/Run-SpawnTip.ps1" `
  -PlanPath $PlanPath -PlanSHA256 $ReviewedPlanSHA256
```

Preparation creates only the requested fresh JSON plan, outside the future run
root. Default Plan opens bounded text/source only: no binary contents, native
types, child process, lease or run directory. Review the exact plan hash and
text pins. Source edits invalidate the plan; generate a fresh one instead of
overwriting a prior receipt. The bound source hash is
`eb574a8da461b6e38024a985264b0cf7dd91cf230afc793c73c3c8f4da962e23`.

Only after a separate coordinator GO, from an original interactive host:

```powershell
& $HostImage -NoProfile -NoExit -File "$Repo/tools-source/gsc-spawn-tip/Run-SpawnTip.ps1" `
  -PlanPath $PlanPath -PlanSHA256 $ReviewedPlanSHA256 -Run
```

The `child` Python verb is internal to the admitted runner. A child report alone
never proves supervision, resource release or whole-job closure.

## Budget, stop and closure

- Admission retains the historical conservative **4 GiB physical / 6 GiB commit**
  estimate. It is not a measured minimum. No reduced profile is implied.
- The unchanged account-wide scheduler admits one Build group. Binary reads and
  Job DLL loading occur after admission. Main and the owner client are untouched.
- Overall admitted setup/execution/verification deadline: 180 seconds. Compiler:
  20 seconds; audit: 60 seconds, through the existing bounded pipe helper. Its
  failure cleanup can use an additional 5 seconds, still within the outer budget.
- Per compiler pipe: 64 KiB; per auditor pipe: 4 MiB. Compiled container: 64 KiB;
  declared/decompressed stack: 128 KiB. Assembly/bound report: 1 MiB each.
- Total output: 64 MiB, with 1 MiB reserved for the final receipt, at most 64
  filesystem entries, using the unchanged H1 100 ms polling loop. This is a
  measured refusal threshold, **not an OS disk quota**; an overshoot fails.
- `RUN/stop.request` stops through the original H1 owner. Deadline, output,
  commit high-water, child and validation failures use the same path. Never kill
  a PID or delete a lease. No automatic retry or failed-root reuse occurs.
- Natural success requires the original root exited and original job active
  count zero. H1 failure cleanup uses `StopAndConfirm(5000)`. The V8 *build*
  recipe's two-second residual policy is not claimed by this H1-based profile.
- Release occurs only after proven closure. Any uncertain owner, membership or
  scheduler release retains the in-memory context, handles/guards and lease in
  the original `-NoExit` host. Keep that host open for coordinator recovery.
  `IW7.SpawnTip.Active` and H1's existing quarantine slot retain the context.
- A forced stop never grants success. Final source/artifact revalidation is
  performed under input guards and admission; publication is bounded separately.
  The actual host/session exit must be observed by the coordinator afterward;
  it is not inferred from the native run receipt or process absence.

On success, `receipt.json` may report only `OfflineReferencesQualified` and bind
the child/run/plan identities, original-job closure and lease release. Its
container, complete native witness, independent bound report, assembly and logs
remain ignored evidence. New blockers are preserved as failures. All asset,
builtin semantics, runtime, package and owner-acceptance gates remain false.

The distributable payload remains the original `.gsc` source, which Aurora
recompiles at load. The offline `.gscbin` is audit evidence only. No manifest is
updated and no claim is made that the offline compiler matches runtime linking.

## Source tests

```powershell
& $Python -I -B "$Repo/tools-source/gsc-spawn-tip/test_spawn_tip.py"
& $HostImage -NoProfile -File "$Repo/tools-source/gsc-spawn-tip/Test-SpawnTip.ps1"
& $HostImage -NoProfile -File "$Repo/tools-source/asset-bridge/h1-fixture/Test-H1Native.ps1"
```

Mocks cover compiler exit-zero errors, strict witness failure, unresolved
references, output/stack bounds, existing-output refusal, two-validator input
binding, admission refusal, partial failure, stop, late completion, unknown job
closure, release failure and receipt failure. They do not execute native tools.
