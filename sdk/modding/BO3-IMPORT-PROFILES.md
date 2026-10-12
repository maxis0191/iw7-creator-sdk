# BO3/T7 import profiles

The product objective remains broad BO3-like creative freedom in IW7: imported
and original models, materials, animation and gameplay, with community delivery.
The first static model is a **pilot for one complete proof**, not the permanent
scope of the SDK. H1 work was stopped by the owner on 2026-10-12; its retained
checkpoints are history, not BO3 provenance.

## First pilot and source route

The conversion workstream identified existing T7-to-IW7 `xmodel` and
`xmodel_mesh` converters at ZoneTool source
`fab935826c898806855376662a8a03317b3ad8f1`. Reuse those converters and the existing
IW7 builder, reader, finalizer and distribution contracts where their measured
scope permits. Do not start a second import framework merely for this pilot.

The proposed initial selection is one real T7 static prop, one selected LOD,
one surface and one resolved root bone, using resident payloads. Cosmetic bones,
skinning, physics, collision and submodels are outside this pilot's acceptance
profile. These are selection criteria for its first controlled experiment, not
universal limitations of the T7 source format, IW7 destination or SDK.

The donor asset and its exact names remain unknown before an admitted catalogue
and selective export. The current loader targets
`BlackOps3_UnrankedDedicatedServer.exe`; the observed downloading installation
contains `BlackOps3.exe`. Source addresses alone do not prove compatibility with
that client executable. Selective CLI execution, the exact executable identity
and an observed export are still pending.

The current source route writes:

- `dump/<fastfile>/xmodel/<T7-model-name>.xmb`
- `dump/<fastfile>/xsurface/<T7-mesh-name>.xsb`

These are typed `assetmanager` streams without a global magic/version field.
Identify the serialized format by the pinned converter, ABI and serializer
source hashes. Current source reconnaissance gives IW7 structure sizes of
736 bytes for XModel, 256 for XSurface and 56 for XModelSurfs. Sizes alone do not
validate the stream, its pointers, names, dependencies or geometry.

The source uses the T7 string resolver when dumping bone names. A successful
export must still demonstrate the actual resolved names; subsequent IW7 parsing
and zone preparation must separately demonstrate their re-interning. Materials
currently follow this model route as name references. That is not proof of T7
material conversion, dependency closure or correct rendered appearance.

## Profiles extend independently

| Profile direction | Evidence required before enabling its delivery |
| --- | --- |
| Initial static resident pilot | Bound donor/export provenance, resolved strings, full typed-stream readback, explicit binding changes, actual FF build/readback and protected rendering |
| Multiple surfaces and LODs | Complete surface/LOD ranges and material-slot mapping; readback and runtime selection for the supported counts |
| Skinned models | Bone identities and hierarchy, bind pose, weight/index representation, supported influence groups, matching geometry and observed deformation |
| Animation | Compatible rig, decoded track representation and timing, root motion/notetracks where supported, observed playback and teardown |
| Materials and images | Explicit material/technique/image conversions or qualified recipient references, texture residency/transport and full dependency closure, rendered verification |
| Larger or combined content | Measured byte/count/resource bounds, namespace and asset collisions, actual build, delivery and recipient behavior for that profile |

These rows describe extension work, not available or `Ready` capabilities.
Existing T7 converter implementations should be assessed and reused for each
row; their presence in source does not establish successful native execution.
Weapons, enemies and maps remain part of the wider objective and require their
own behavior, animation, audio, collision and networking evidence as applicable.

Each implemented profile needs an explicit versioned identity, source/destination
formats, supported counts and representations, measured byte bounds and separate
source/native/runtime evidence. Adding a reviewed profile must not require
weakening a prior profile or relabeling its receipts. Unknown profiles and input
outside the selected profile fail explicitly until the appropriate extension
exists. Do not clamp, discard unsupported data or substitute a synthetic cube.

Profile-specific limits belong in that profile's validator. Keep the general
SDK manifest, composition and delivery contracts extensible through reviewed
profiles. In particular, do **not** introduce a global `numsurfs <= numBones`
invariant: surface count and bone count describe different domains. Validate
actual references and index ranges under the selected representation. The
historical Beacon checks for 24 vertices, 12 triangles and small dump sizes are
evidence for that original asset, not ceilings for future BO3 models.

## Composition and evidence boundary

Keep original T7 names, sources, export bytes and receipts immutable. A binding
to Beacon names such as `paris_model_probe` and `paris_model_probe_lod0` must be a
separate, named derivation with explicit before/after names, material policy,
LOD selection and hashes. Its reader must validate the actual T7-derived
geometry, not the original Beacon cube oracle. Replacing a material reference
or selecting a LOD must not be described as full retail fidelity.

Keeping Beacon's model identifiers can preserve the exact SelfContained GSC
source and its offline V8 witness. New asset bytes still require a separate
composition and new asset/provenance/closure/runtime evidence. Preserve the
existing V8 candidate. A fresh runtime compilation of the source does not prove
that runtime bytecode equals the offline witness.

Use the existing build transaction and finalizer after an export/profile has
been reviewed. Do not issue an executable BO3 recipe while the selective CLI,
supported executable and actual donor are unresolved. No new native run, lease,
stock copy or installation change is authorized by this profile document.
