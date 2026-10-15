# Original author inputs through Creator

The creation objective extends beyond BO3 imports. These are editable original
source projects, using the existing community manifest, ModelLabV2 selector and
producer ownership. No engine hook, per-asset allowlist or new runtime framework
is introduced by this source selection.

| Project | Geometry source | Original RGBA8 source | Authored behavior |
| --- | --- | --- | --- |
| `examples/original-authoring/turn-prism` | Triangular prism, 18 vertices / 8 triangles | 4 x 4 navy/cyan bands | Use rotates through four orientations |
| `examples/original-authoring/step-lantern` | Two stacked boxes, 48 vertices / 24 triangles | 8 x 4 orange/cream/brown pattern | Use arms or cancels a four-second pulse |

Their names, geometry, pixels and GSC are separate editable files. The second
project is not a renamed singleton plan. Both retain one rigid root, one surface
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

`material_template` maps explicit roles to relative author project paths:
material, statebits, statebitsmap, optionally stateinfo/cbi/cbt as required by
the actual IW7 template. The examples intentionally do not contain retail JSON
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
their source pins remain separate. The current new selector does not invoke a
writer, build or packager. Producer integration is required before this becomes
a complete authored build route. The original templates cannot be relabeled as
proof for these projects.

The smallest next measurable lot is producer validation/preparation for these
same inputs, then a separately authorized build/readback and creator trial of
both projects with the same compatible runtime. The criterion is an independent
author changing names, geometry, texture and GSC without a new engine patch,
asset allowlist or SDK edit. It has not been measured here. No PE, native model,
DDS file, FF, stock access, admission, deployment or game trial was performed.
