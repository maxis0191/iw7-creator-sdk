# Original sound: neutral SDK plan

This private research example implements the [sound SDK contract](../../../../docs/SOUND-SDK-CONTRACT.md).
It is a source plan, not a measured or deployable sound package. The three client
payloads are absent; every file size/hash, node hash and network protocol is
unknown. Closure is incomplete and all evidence is pending. There is no new
`custom-sound/1` capability or package format.

| Package source | Installed destination | Closure roots |
| --- | --- | --- |
| `client/mod.ff` | `mods/sdk_original_sound_v1/mod.ff` | Bank + rawfile |
| `client/mod.sabl` | `mods/sdk_original_sound_v1/mod.sabl` | Bank |
| `client/mod.sabs` | `mods/sdk_original_sound_v1/mod.sabs` | Same bank, including an empty streamed bank |
| `server/sdk_original_sound_v1.gsc` | `iw7-mod/custom_scripts/cp/sdk_original_sound_v1.gsc` | Canonical server ScriptFile |

The generic node kinds are `sound`, `other` and `scriptfile`. The bank and rawfile
IDs preserve native inventory names, without treating those native types as SDK
kinds. The neutral script does not request the bank, so its node has no sound
dependency; all three asset nodes are explicit package roots.

## Neutral lifecycle

The canonical `custom_scripts/cp/sdk_original_sound_v1.gsc::init` entrypoint runs
only on a dedicated isolated lab, `cp_zmb`, this exact `fs_game`, a private port
27100–27999, a nonempty password, LAN-only mode and `sv_cheats=0`. Repeated init
is ignored while its level state exists. It creates one shutdown thread, clears
its own state on `game_ended`, then returns. Map unload discards the level VM.
Hot reload is disabled. It allocates no player state; the declared `player-state`
cleanup obligation therefore has nothing to release.

It logs lifecycle markers only: no sound playback/precache, Beacon, model, HUD,
input, Use or weapon action. Protection and input remain the external lab's
responsibility. A lifecycle marker proves neither audio loading nor readiness.

## Source checks

Run from the repository root:

```text
python -B sdk/modding/manifest.py sdk/modding/examples/original-sound/manifest.json --stage plan --target native
python -B sdk/modding/examples/original-sound/test_example.py -v
```

The real SDK Plan result must be `valid=true`, `ready=false`,
`runtime_ready=false`, `owner_accepted=false` and `checked=[]`. Tests use only
source, synthetic JSON representations, temporary copies of the reviewed GSC and
rejected modified variants; they never create or inspect FF/SAB/sample payloads.
Materializer tests require PowerShell 7 and the repository's existing `python`
command. Without PowerShell they are explicitly skipped, not reported as passed.

The GSC source passed the existing `gsc-tool -m parse -g iw7 -s pc -y` check on
2026-10-12. This was syntax parsing only, not runtime compilation or gameplay.

## Materialize a plan from completed production

Use the completed StandardMod execution plan and `state.local.json` from the
qualified producer described in [Sound Agent Lab](../../../../docs/SOUND-AGENT-LAB.md).
Their pinned SHA-256 values must come from that retained run's evidence. A failed,
quarantined, unrestored or incompletely closed run is not eligible. Keep output
outside the closed producer run in an existing owned directory, with a fresh name.

```powershell
$materialize = @{
    BuildPlanPath = $qualifiedPlanPath
    BuildPlanSHA256 = $qualifiedPlanSHA256
    BuildReceiptPath = $qualifiedStatePath
    BuildReceiptSHA256 = $qualifiedStateSHA256
    OutputPath = $freshAbsoluteManifestPath
}
& ./sdk/modding/examples/original-sound/Materialize-Plan.ps1 @materialize
```

These variables are required operator inputs, not example measurements. The
adapter calls the existing `Read-IW7SoundProducerEvidence` gate, including its
bounded pinned phase metadata and actual producer semantic validators. It copies
only the three client sizes/hashes asserted by the receipt. It separately enforces
the existing sound HTTP caps (1600/131072/4096 bytes) and runs the real SDK Plan
without a payload root. In this default mode it never reads/hashes/copies a
payload. It never measures a native binary, opens a lease, starts a producer/game,
or grants package/audio readiness. The summary binds the output manifest hash to
the plan/state hashes; retain it with the qualification record. Synthetic test
receipts are never production evidence.

The output intentionally retains the unknown server measurement, node hashes,
protocol, native source declarations, incomplete closure and pending evidence.
The three producer file measurements alone cannot complete those fields.

## Complete the static closure with exact representations

For a producer receipt containing the new
[`Reader.closure_evidence`](../../../../docs/SOUND-CLOSURE-REPRESENTATIONS.md),
stage the reviewed canonical GSC at `server/sdk_original_sound_v1.gsc` in a fresh
private package directory. Then explicitly request the additional bounded source read:

```powershell
$materialize.PackageRoot = $freshAbsolutePackageRoot
$materialize.OutputPath = $anotherFreshAbsoluteManifestPath
& ./sdk/modding/examples/original-sound/Materialize-Plan.ps1 @materialize
```

The same pinned producer gate must pass first. The internal
`Complete-StaticClosure.py` adapter calls the producer reader's pure
`validate_closure_evidence` API on the retained Reader object. It verifies embedded
bytes, sizes and SHA-256, exact bank JSON references, original alias and dumped
alias values, empty auxiliary exports, rawfile contents and their artifact
bindings. It does not call the reader's FF/SAB inspection path. Embedded bytes
alone prove their semantics and hashes, not native provenance; the separate
completed producer gate binds them to the pinned run. The internal adapter is
not a replacement for `Materialize-Plan.ps1` or that producer gate.

Only the exact canonical GSC under `PackageRoot` is read from disk, with a 16 KiB
limit and rejection of linked paths. It must match the fixed reviewed neutral
source: **1266 bytes**, SHA-256
`88934abec9af1ac1af54f9831f967b9cfafa3144e3cae19c28f93b5bb36cc1af`.
This independent pin is not derived from the delivered file or refreshed from a
mutable repository template. Every byte matters: CRLF conversion, a BOM, added
whitespace, an include or a changed call is refused. No GSC parser or silent
normalization is used. A source variant requires its own reviewed dependency
proof, outside this fixed fixture's qualification.

The accepted delivered bytes are measured twice as sequential snapshots, not
held under a persistent lock. The resulting hashes are:

| SDK node | Exact hashed representation |
| --- | --- |
| Bank `sound` | Original dumped JSON bytes, including formatting |
| Branding rawfile `other` | Exact dumped rawfile contents |
| Server `scriptfile` | Bytes of the GSC staged for delivery, required to match the reviewed fixed source pin |

The FF hash remains a separate payload measurement. Alias, sample and auxiliary
records are internal bank evidence, not invented native asset callbacks or new
SDK nodes. The closure reference binds the producer state hash and the delivered
GSC hash. An old receipt, malformed representation or missing GSC cannot produce a
complete closure. The fixed source identity supplies this fixture's reviewed
absence of additional script dependencies. It does not establish runtime
compilation, behavior, installation or a server asset lookup.

On success, `closure.status=complete`, `StaticClosureComplete=true`,
`RepresentationsRevalidated=true` and `ServerSourceMeasured=true`.
`PayloadMeasured=true` means only that server source; `ClientPayloadMeasured`
remains false. The client files need not be present at this stage. The protocol
and native source declarations remain unknown, every evidence record remains
pending, and `PackageReady`, `RuntimeReady` and `OwnerAccepted` stay false.
The real SDK still validates Plan without reading its payload root.

## Later packaging with the existing SDK

After real production and under the applicable authorized resource workflow:

1. Prepare a fresh private package root with exactly the four source paths in
   the table. Copy only `artifacts/mod.ff`, `artifacts/mod.sabl` and
   `artifacts/mod.sabs` from the qualified run, plus this canonical server source.
   Do not recurse over producer work/stock directories or alter the closed run.
2. Use the explicit static-closure mode above with the qualified new receipt and
   the exact GSC to deliver. Keep closure incomplete if those proofs are absent.
   Verify all four files against retained evidence. Record the measured protocol
   and reviewed source declarations separately; source pins do not prove the
   native executable or its R2 overlays. Packaging remeasures every file, so a
   later change to the staged GSC cannot reuse its earlier measurement.
3. Populate a separate complete manifest only with established values. Leave
   runtime/audio/owner evidence pending until its own tests establish it. Use the
   existing static packager, with the complete intended active set supplied through
   `--active` if applicable:

   ```powershell
   python -B ops/modding/Package-CommunityMod.py $completeManifestPath --root $packageRoot --output $freshArchivePath --client-source $reviewedClientSource --server-source $reviewedServerSource --protocol $measuredProtocol --mode cp --target native
   ```

The packager enforces SDK package/compatibility/integrity gates and creates the
standard server/FastDL archive; this example adds no zipper or copy framework.
Successful static packaging still reports `ready_to_deploy=false`. Delivery
validation additionally requires genuine source-check, offline-load and
runtime-link evidence for each declared map. Native lookup, playback, audibility,
owner acceptance and any deployment remain separate gates. Do not turn pending
records into passes to bypass them. No package or runtime test was performed for
this source example.

## GSC closure correction

The first static-closure adapter (`39c4ab8`) accepted any bounded GSC at the
canonical path and incorrectly treated its measured hash as enough to declare no
script dependencies. Independent review reproduced acceptance of an injected
include/call. Three real-materializer regression cases also reproduced exit 0 for
an injected include, an absent thread call and an unrelated source before this
correction. The adapter now requires the pinned reviewed bytes before completing
closure. Tests also reject same-size changes, CRLF, BOM and an extra newline;
the positive case stages and measures the exact approved source.
