# Platform contact: project-specific GSC content

Source only. This is a third data project through the same original author
inputs; its 256 x 256 x 16 box is not a restriction on other projects. Its
model-local bounds are [-128,-128,0] to [128,128,16], with 24 vertices/12 triangles.
Original yellow/dark pixel source and the material-template paths remain editable.
The source recipe selects diffuse slot 1 for the known Material C layout, keeping
its normal at slot 0. Actual template/sidecar identity remains pending admission.
No model, DDS file, FF or runtime result is supplied by this source example.

| Binding | Exact project identity |
| --- | --- |
| Namespace / zone | `sdk_author_platform` |
| Model / mesh | `sdk_author_platform_model` / `sdk_author_platform_mesh` |
| Material / image | `sdk_author_platform_material` / `sdk_author_platform_color` |
| Mod | `mods/sdk_author_platform` |
| Server payload | `iw7-mod/custom_scripts/cp/sdk_author_platform.gsc` |
| GSC entry | `custom_scripts\cp\sdk_author_platform::init` |
| Enable | `sdk_author_platform_enable=1`, default zero |

The retained IW7-Mod source `77e6d4d...`,
`src/client/component/gsc/script_loading.cpp:283-297`, removes `.gsc` from the
`custom_scripts/cp/` relative path before `Scr_LoadScript`. This establishes the
source lookup convention; linking this new script and the fixture is still
unqualified. No native-to-GSC bridge is added. The fixture is itself server GSC.

Initialization only precaches under the private context; it never spawns a model.
The separately owned protected fixture invokes these content functions directly:

```gsc
scene = custom_scripts\cp\sdk_author_platform::create_visual(player, frozen_p, token);
// Run F0 and F1. Prove movement and a released-stable interval externally.
armed = custom_scripts\cp\sdk_author_platform::arm_use(scene, player);
// The fixture drives ONE real Use. The SDK waits for the retail entity trigger.
observed = custom_scripts\cp\sdk_author_platform::read_state(token);
// After exact acknowledgement, the fixture alone removes its body for F2.
// The visual stays alive throughout F0/F1/F2, then:
removed = custom_scripts\cp\sdk_author_platform::teardown(scene);
```

This is a small convention of this content project, not a universal author ABI,
event framework or a new input driver. It never notifies a fabricated Use event.
The SDK increments its own counter only inside `waittill("trigger", player)`.
The fixture's `usebuttonpressed()` observation neither increments nor supplies
the count. It must bound its wait and match all of these fields on the same
returned state instance before F2:

- `token`, `owner`, `model`, `entity`, `instance_id`, `anchor`, `origin`;
- `uses == 1`, `last_player == player`, `last_token == token`;
- `last_entity == entity`, `last_use_ms > armed_ms`.

`create_visual` places the visual at frozen P + (0,0,96), angles zero, scale 1.
It requests stock `notsolid()` (retail Source usage: cp_zmb.gsc:849/968 and
cp/utility.gsc:6393), then `makeusable`, range 160 and FOV 360. No collider is
created or cleared by this module. Those calls and the collision LOD sentinel
are not evidence that the actual engine has no hidden body: F0/audit must prove
it. The separate physics owner supplies exactly one body and measures contact,
withdrawal and fall. Geometry bounds alone do not prove contact or prediction.

Context requires dedicated Spaceland, exact mod, one maximum/actual player,
non-Main port, password/LAN, `sv_cheats=0` and inactivity zero. The caller must
establish fresh actual engine protection, intro readiness, ground state and P.
Root/entity/token/instance checks protect ownership; changed ownership is a
pending restoration, not permission to delete another entity. No global stop
notification is emitted. Disconnect, context loss and game end request cleanup.

Source grammar/fixtures do not prove loaded assets, current binary support,
retail trigger delivery, visual pixels, hidden-body absence, physics, same-edge
acknowledgement or gameplay. All require a separate measured run after its GO.
