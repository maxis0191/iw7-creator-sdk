# Original two-bone animation: author plan

This example describes a retained original animation fixture through the ordinary
Creator contract. It includes planning files and the opt-in DISPLAY/ANIMATE GSC
experiment, not the fastfile, retail material or a qualified animation launcher.
`AnimationProbe` remains an unconnected named adapter. `ModelLabV2` accepts
resident rigid geometry and must not be used for this two-bone fixture.

From an exact prepared SDK source workspace:

```powershell
./sdk/modding/Creator.ps1 -Action Plan -Adapter None `
  -Project ./sdk/modding/examples/original-rig-probe `
  -ClientSource 77e6d4d24e918ee363b3feee3735c3b889dff7d7 `
  -ServerSource 77e6d4d24e918ee363b3feee3735c3b889dff7d7 -Protocol 2 -Json
```

Plan checks names, roles, graph structure and declared compatibility. It writes
nothing and retains all package/runtime/owner readiness flags as false. The
source pins above are operator assertions, not an installed binary measurement.
The existing `skeletal-animation-import/1` capability is explicitly **blocked**:
it permits an honest experimental Plan, and refuses package/delivery stages.
The tested rigid-cube/NCS capabilities are not substituted for this rig.
The SDK contract step passes, but the complete Creator command currently exits
1 because Distribution has no qualified client-source proof for that blocked
capability. The report states this exact environmental blocker. No source-proof
entry is invented to obtain exit 0, and `AnimationProbe` remains unconnected.
The supplied `sdk_original_rig_probe.gsc::init` source is bound to its actual
4,866 bytes and SHA-256
`49f7e1aa336bb2fdb73e5c36be03c213311ead4555fc9bca0d7b4e69ccdc219b`.
[SDK PR9](https://github.com/maxis0191/iw7-creator-sdk/pull/9) supplied and reviewed
it, including the early stop watcher and teardown marker ordering. Parse and dry
IW7/PC compilation passed with gsc-tool 1.5.1.359 (tool SHA-256
`1adfd67414a9b886cbad57ee0378f622eed485bcef7711322aee478e298fadcb`),
with no GSC import. This binds the source only; whole-package source evidence,
static asset closure and engine behavior remain pending. Package is refused.
See [the private scenario](SCENARIO.md) for protection, DISPLAY/ANIMATE phases
and restoration. The SDK does not implement or run that native supervisor.

## Observed assets and representations

The asset worker's pinned handoff is
`iw7.original-rig-asset-handoff/1`, SHA-256
`b9b5aff6f17d9682e0c902b319f3b061d6090f892ae7a91fd2ab5a3507f325a8`,
on assets product `d2d72a72f24eea0c5b64b61728e6d58be8a5f886`
([asset CPU reader PR4](https://github.com/maxis0191/x64-zt-extensions/pull/4)).
Its retained inventory CSV hashes to
`fa764dc0f975eb3d48339d2353a335d21deee6749484b9d9634065aa97206951`.

The seven entries are two original models, their two surface assets,
`paris_original_probe_bend`, the zone rawfile `sdk_original_rig_probe`, and the
IW7 recipient material reference `,mopw/character_park_clown_zombie_shoes`.
The comma marks a reference; the logical material node omits it. Historical
`paris_doom_skin_two_bone_*` names are preserved asset identities, not Doom or
BO3 content claims. No NCS, animation tree or GSC is present in this fastfile.

The retained FF is 1,064 bytes with SHA-256
`ea7ba4be1d5e6f0878431b51e7b9b1ba9d2b10bf74b1ad21da14d55c414e145d`.
The animation node hash refers specifically to the 281-byte **FF redump**,
`a9cd7a3de12b805f5f3e73e5442980a714e39294912f689992f55e3d65576444`.
It is different from the native source XAB hash. Neither hash describes an
engine registry entry, a rendered pose or the entire recipient material.
Unknown representation hashes remain null. The manifest does not turn an empty
dependency list into a qualified terminal boundary; closure stays incomplete.

The CPU reader observed eight vertices, six triangles, two bones (`tag_origin`
and `tag_probe`) and the child bind pivot `(0, 0, 8)`. The clip has four authored
keys across 30 frames at 30 fps, an authored loop flag and a `probe_contact`
notetrack at normalized time 0.5. The two weight profiles have the same bind pose
and must be compared in the engine to determine weight direction. CPU readback
passed over 22 retained inputs / 15,143 bytes; rendered motion remains unverified.
The historical native run remains **FailedRestored**, with its original jobs
closed. These observations do not promote its run status to successful.

## Next private runtime step

The demo worker owns the protected GSC scenario, installation and rollback.
Observe the supplied experiment's actual CP precache and script-model animation
route with this exact FF. Do not invent a NCS or
animation tree to make a plan appear complete. Add either only if the observed
loading/registration behavior establishes that dependency.

Then bind the retained FF source, representation inventory and
static closure in the same contract. Runtime linking, GPU resources, material
resolution, skinning, cadence, notetrack delivery and owner acceptance need their
own observations. The existing original CPU reader remains the asset consumer;
this example adds no validator, runner, receipt schema or resource supervisor.

The first author-plan candidate exposed an existing SDK limitation: every client
XModel required the tested rigid-cube and NCS capabilities, including this
explicit skeletal experiment. That failed candidate is retained in history.
The SDK now accepts the existing blocked skeletal capability for an experimental
Plan, and requires it for client animation nodes. Ordinary rigid plans keep their
previous requirements. The blocked capability still refuses package/delivery;
this correction does not qualify skeletal runtime support.

A second check exposed the separate Distribution source-proof blocker above.
That check remains enforced; the example's tests assert the precise blocked CLI
result and its unchanged files, rather than disguising it as an executable plan.
