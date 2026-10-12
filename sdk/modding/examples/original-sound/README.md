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
source and synthetic JSON metadata; they never create or inspect FF/SAB payloads.
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
without a payload root. It never reads/hashes/copies a payload, measures a binary,
opens a lease, starts a producer/game, or grants package/audio readiness. The
summary binds the output manifest hash to the plan/state hashes; retain it with
the qualification record. Synthetic test receipts are never production evidence.

The output intentionally retains the unknown server measurement, node hashes,
protocol, native source declarations, incomplete closure and pending evidence.
The three producer file measurements alone cannot complete those fields.

## Later packaging with the existing SDK

After real production and under the applicable authorized resource workflow:

1. Prepare a fresh private package root with exactly the four source paths in
   the table. Copy only `artifacts/mod.ff`, `artifacts/mod.sabl` and
   `artifacts/mod.sabs` from the qualified run, plus this canonical server source.
   Do not recurse over producer work/stock directories or alter the closed run.
2. Verify those files against retained evidence, measure the server source, and
   establish node identity hashes and dependency closure from traceable inventory
   evidence. Whole FF/SAB file hashes are not substitutes for bank/rawfile node
   hashes. Keep closure incomplete until those facts exist. Record the measured
   protocol and reviewed source declarations; source pins do not prove the native
   executable or its R2 overlays.
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
