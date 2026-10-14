# SeparatePose: independent stock placement

This opt-in source variant addresses the stock/central-rig overlap observed in
the Native25 V2 scene. It derives from Original649b and changes only the stock
placement, its explicit enable guard and its placement journal. Scale 3 remains
assigned **before** setmodel, exactly as in Original. This is not the ScaleAfter
experiment. The original scenario, core49f, Original649b and ScaleAfter40e remain
byte-for-byte unchanged and independently replayable.

## Source and ownership contract

| Source | Bytes | SHA-256 |
| --- | ---: | --- |
| Original | 5 375 | `649b7497af5e2f11c7ca5a959f5e0cabfa0e42fc4939675578ffc8bfe3275a7e` |
| SeparatePose | 5 935 | `30115aa45405594f66dc33871db58d840fd04c5ffb009e2f29b7b3cdfdb1bff1` |
| ScaleAfter | 5 375 | `40e8990cb27f49244499c57ae9f19b635f0515c5c35442919af0b90c8a377ed0` |

The new canonical source is `sdk_original_rig_stock_witness_separated_pose.gsc`.
Demo owns the typed `AddonVariant: SeparatePose` selection, exact source/plan
pins, parser and fixture. Stage only the selected source to the existing runtime
basename `iw7-mod/custom_scripts/cp/sdk_original_rig_stock_witness.gsc`, alongside
core49f. Never auto-load both stock sources. State, event names, old markers and
the old enable/stop interface stay the same. The extra private enable is
`sdk_original_rig_stock_witness_separated_pose_enable`; it defaults to zero and
is required to activate this variant. No player command is added.

In addition to the existing private DISPLAY configuration, a future reviewed
SeparatePose plan sets that enable to 1. Original and ScaleAfter plans leave it
zero. Real Use still requires a release after READY and a new rising edge after
the external neutral capture and fresh actual engine godmode/inactivity checks.
The one reserved attempt, ten-second TTL, selected-player disconnect, original
stop and game-ended cleanup remain unchanged.

## Relative pose and strict journal

The source snapshots the real central actor 1's origin and angles, computes
`right_basis = anglestoright(angles)` and chooses:

```text
stock_origin = anchor_origin + right_basis * 32 + (0, 0, 48)
stock_angles = anchor_angles
```

There is no forward offset and no absolute world coordinate in the GSC. World
up is the existing Z axis. The frozen core already uses the same right primitive
to place its three actors. For the retained V2 reference only, anchor
`(467.546,3517.47,48.0679)` and yaw -90 imply right `(-1,0,0)` and a proposed stock
origin `(435.546,3517.47,96.0679)`. This is a nominal calculation, never a pose
already exercised by SeparatePose or a measured client camera/frustum.

After snapshots and before spawn, exactly one extra marker is emitted:

```text
[SDK rig stock witness] PLACEMENT_SELECTED; variant=SeparatePose; anchor_entity=...; anchor_origin=...; anchor_angles=...; right_basis=...; offset_right=32; offset_up=48; offset_forward=0; origin=...; angles=...; server_scale=3; time_ms=...; pixels_pending=1.
```

`origin` in that marker is the selected stock pose. The complete old
`WITNESS_CREATED` print expression remains literal-identical; the fixture joins
the new marker with creation and actual native pose records by anchor, pose,
angles and clocks. The marker is not evidence that spawn/setmodel succeeded,
that the actor rendered or that scene/native scale is 3. The original and
ScaleAfter parsers retain their own old co-location contracts.

## Retained assets and validation limits

Reuse the reviewed Native25 binary from compiled source
`785ddd43d18c4eebd599bab10880e83d73a950e9`, expected EXE SHA-256
`012e6cddcd6a91adc2f041035c86417064998127044a11341895c55f8bd4fc53`, and
the retained rigid-control FF: 888 bytes, reported SHA-256
`b7b7c4a1147e7e6c5d19cd33ad3a9e9701cda1bc31123ff22caa239d0aa4014a`.
These prerequisite identities come from closed text receipts; this source change
does not read, hash, rebuild, deploy or launch either artifact. The old ea7 FF
and its old scenario remain historical; they are not silently requalified.

V2 published four scene rows and nine protected poses with closure/restoration.
Its stock and central custom row shared origin/angles, while their observed
native scale was 1 despite server field 3. The separate source removes that
nominal overlap without changing scale order. Keep actual scale, renderer/GPU,
pixel identification, client camera/FOV and culling unqualified until measured.
The YZ-plane ribbon's nominal qZ -90 orientation is unchanged; no inversion or
camera manipulation is introduced.

Eight targeted Python source-relation and nominal-math tests pass. Negative
controls reject the old co-location, ScaleAfter timing, wrong offset/basis,
anchor, angle, scale, TTL and absolute-coordinate substitutions. No GSC parse,
compilation, FF/native build, runtime launch or new pose validation was performed
while the owner's client/Main were occupied. The next step is an independently
reviewed caller/capsule and a separate private runtime GO after ownership permits
the test. Main, banks/configs and occupied clients stay preserved.
