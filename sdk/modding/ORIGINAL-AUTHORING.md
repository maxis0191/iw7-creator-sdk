# Original author inputs through Creator

The creation objective extends beyond BO3 imports. These are editable original
source projects, using the existing community manifest, ModelLabV2 selector and
producer ownership. No engine hook, per-asset allowlist or new runtime framework
is introduced by this source selection.

| Project | Geometry source | Original RGBA8 source | Authored behavior |
| --- | --- | --- | --- |
| `examples/original-authoring/turn-prism` | Triangular prism, 18 vertices / 8 triangles | 4 x 4 navy/cyan bands | Use rotates through four orientations |
| `examples/original-authoring/step-lantern` | Two stacked boxes, 48 vertices / 24 triangles | 8 x 4 orange/cream/brown pattern | Use arms or cancels a four-second pulse |
| `examples/original-authoring/platform-contact` | Fixture-specific box, 24 vertices / 12 triangles | 8 x 8 yellow/dark pattern | One armed retail trigger; fixture owns contact/withdrawal |

Their names, geometry, pixels and GSC are separate editable files. The second
project is not a renamed singleton plan. All retain one rigid root, one surface
and one LOD. Geometry bounds are declared source inputs, awaiting the producer's
independent validation; no collision or physics follows from them.

`authoring.json` has schema `iw7.creator-authoring/1` and exactly namespace,
zone, model_name, mesh_name, material_name, image_name, geometry_source,
script_source, texture, material_template and placement. Namespace/zone equal the existing
community package ID. Asset names use that namespace prefix, not a fixed demo
identity. `geometry_source` uses the existing `iw7.original-mesh-source/1`
format with the declared material reference. `script_source` is the editable
`<namespace>.gsc`; no template hash is imposed.

Placement contains `offset_forward_right_up`, `angles` and scale 1. It describes
the intended player-relative source scene, not an observed engine transform.
The two examples use forward 96/right 0/up 32. A platform project can instead
use forward 0/right 0/up 96 without changing an SDK API or imposing its box
dimensions on every project. World/physics callers consume these explicit data;
the SDK neither drives Use nor adds a second fixture coordinator. The examples'
GSC states `level.<namespace>.model` and `.uses` are conventions of those example
scripts, not a new universal VM/ABI or event bus.

`texture` contains kind (`rgba8` or `dds-dx10`), relative source and integer slot.
RGBA8 source JSON contains width, height and a flat pixels array of four integer
bytes per pixel. It is text, not a generated bitmap or measured DDS. The real
producer's `rgba8_dds` uses its existing encoder; the SDK adds no image serializer.
DDS inputs use its existing strict single-2D/one-mip DX10 subset. Plan never
opens DDS bytes. The material producer alone validates the actual DDS/layout.
The examples declare slot 1 for the retained Material C template layout: index
0 is its normal (semantic 15), index 1 its diffuse (semantic 14). Supply and pin
the actual template/sidecars under their applicable admission before preparation;
the declaration does not authenticate a template or prove CBT/render behavior.
Other templates need their own explicit correct slot; no binding is reordered.

`material_template` maps explicit roles to relative author project paths.
The general producer requires `material`, `statebits`, `statebitsmap`; `cbi` and
`cbt` are required when the actual material has constants. `stateinfo` is
required when the actual state fields need it. The examples explicitly declare
all six paths for retained Material C: its two constants require `cbi`/`cbt`,
while its present stateFlags makes `stateinfo` optional. The supplied stateinfo
role is preserved rather than dropped. This is the historical Source contract,
not a fresh inspection or authentication of retail bytes. The examples intentionally do not contain retail JSON
or sidecar payloads. The author supplies already owned, qualified templates;
state/technique/other image bindings remain recipient dependencies, not original
authored shaders. Plan does not read those opaque/template inputs or treat
their path declarations as complete closure.

From an exact prepared SDK source workspace, inspect the project with the same
Creator command:

```powershell
./sdk/modding/Creator.ps1 -Action Plan -Adapter ModelLabV2 `
  -Project ./sdk/modding/examples/original-authoring/turn-prism `
  -ClientSource $reviewedClientSource -ServerSource $reviewedServerSource `
  -Protocol 2 -Json
```

Use the actual environment's reviewed sources, never a guessed old pin. The
source selector binds stable manifest/descriptor/geometry/texture/GSC snapshots.
It reports `source_contract_valid`, not geometry, DDS, build or runtime success.
The new `original-rigid-authoring/1` capability remains blocked; static package
validation and compatibility still refuse unsupported inputs. Neither a changed
JSON capability nor a matching protocol qualifies the actual runtime.

Existing BeaconV1, retained ModelLabV2 materialization, BO3 witnesses, PAP and
their source pins remain separate. The selector does not invoke a writer, build
or packager. The small preparation consumers below now use the pinned original
geometry and DDS/material producers, including their existing authored FF stage.
Actual preparation and new build/readback remain separate operations. The
original templates cannot be relabeled as proof for these projects.

The same module exposes small consumer routines for separately authorized
operations; they delegate to the existing reviewed producer APIs:

- `prepare_writer_inputs(project, output, tools_root, native_source_root, manifest=...)`
  prepares source/header/writer inputs and checks the written source recipe.
  The supplied native root is the pinned serializer **source**, not an executable
  or retail stock. It does not compile the writer.
- `material_inputs(project, tools_root, manifest=...)` reads the explicit template
  roles and DDS if selected, or encodes the first validated RGBA8 snapshot through
  the producer. It returns that producer's in-memory payloads unchanged.
- `stage_ff_inputs(project, writer_run, output, tools_root, manifest=...)` requires
  a measured writer run belonging to the current geometry, then delegates the
  model/material/recipe join to `prepare_ff.stage_authored`.

These are not called by Plan. Actual retail templates, serialized model artifacts
and future native/FF operations retain their separate admission. Staging FF
inputs does not create a FF. The existing Build-Writer/Build-ModelFF wrappers own
compilation, strict candidate checks, process/resource lifetimes and readback.
The existing ModelLabV2 `Bind`/`Materialize` entrypoints also dispatch to the
authored plan/3 profile `iw7-authored-rigid-v1`. The resident profile remains its
separate existing branch. No new builder, ZIP writer, engine hook or per-project
allowlist is involved. The consumer calls the existing `prepare_ff` independent
stage/material/image readers and binds their actual receipts.

After a separately admitted writer/FF run has closed and restored successfully:

```powershell
./sdk/modding/Creator.ps1 -Action Bind -Adapter ModelLabV2 `
  -Project $authorProject -ModelSourceRoot $authoredStage -BuildRoot $completedFFRun `
  -ReviewReference $actualGscAndClosureReview `
  -ClientSource $reviewedClientSource -ServerSource $reviewedServerSource -Protocol 2 -Json

./sdk/modding/Creator.ps1 -Action Materialize -Adapter ModelLabV2 `
  -Project $authorProject -BuildRoot $completedFFRun -FinalizeRoot $freshCandidate `
  -ClientSource $reviewedClientSource -ServerSource $reviewedServerSource -Protocol 2 -Json
```

`Bind` preserves existing `composition.json` and requires a fresh declaration.
Its existing composition schema gains `surface_roundtrip_sha256` for this
profile. The immutable binding covers current GSC/closure, source plan,
material derivation, closed build state, native geometry output, surface
readback and exact FF bytes. The current author geometry must match the writer
recipe. Current texture/template/slot inputs are reprocessed by their owner
and must match the staged material metadata and payload hashes; an old valid FF
cannot silently approve edited author inputs. Unlike Plan, these operations
read supplied template/DDS/serialized files and retain their separate admission.

`Materialize` rechecks those bindings and the delegated readback, then writes a
fresh local candidate using the actual names and payload bytes. It records dump,
GSC and NCS representations, adds only producer-declared recipient technique and
image dependencies, and keeps closure incomplete. A missing source proof for
exactly the primary project's blocked `original-rigid-authoring/1` capability
is reported as pending for offline Bind/Materialize only. Other source/capability
errors, active-project errors, Plan, Build and Package keep their refusals.
No runtime/source compatibility proof is created by this inspection allowance.

`Creator Package` uses its unchanged generic checks and sole ZIP writer. These
candidates cannot package while the original capability, recipient closure,
native CBT semantics, zone rawfile, GSC linking, rendered pixels, real input,
multiplayer and owner evidence remain unqualified. Materialize writes both plan
and failing package validation reports; package/runtime/owner flags stay false.
Actual native operation and unchanged-runtime independent creator trials have
not been measured. Source orchestration tests use explicit synthetic text
stand-ins, not genuine DDS/model/FF or native process evidence.

The smallest next measurable lot is producer validation/preparation for these
same inputs, then a separately authorized build/readback and creator trial of
both projects with the same compatible runtime. The criterion is an independent
author changing names, geometry, texture and GSC without a new engine patch,
asset allowlist or SDK edit. It has not been measured here. No PE, native model,
DDS file, FF, stock access, admission, deployment or game trial was performed
for this Source integration.
