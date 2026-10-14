# Scale after setmodel: one-variable stock experiment

This separate source variant moves only the existing `actor.scale = 3` assignment
after `actor setmodel("zmb_coin_alien")`. It is an experiment, not an accepted
scale fix. The original addon, three custom actors, FF and native evidence stay
immutable. Native placement scale 1 versus server field 3 does not itself prove
effective vertex scale, a setter defect or the cause of missing ribbons.

## Exact source relation

| Source | Bytes | SHA-256 |
| --- | ---: | --- |
| `sdk_original_rig_stock_witness.gsc` | 5375 | `649b7497af5e2f11c7ca5a959f5e0cabfa0e42fc4939675578ffc8bfe3275a7e` |
| `sdk_original_rig_stock_witness_scale_after.gsc` | 5375 | `40e8990cb27f49244499c57ae9f19b635f0515c5c35442919af0b90c8a377ed0` |

The variant is byte-for-byte the baseline except this unique adjacent pair:

```diff
-    actor.scale = 3;
     actor setmodel("zmb_coin_alien");
+    actor.scale = 3;
```

Origin/angles snapshot from actor 1, scale value 3, stock name, Use release/rising
edge, one reserved attempt, markers, ten-second TTL and all cleanup paths are
unchanged. The source identity test rejects baseline drift, the old order or any
extra change, including TTL. It does not simulate GSC lifetime or runtime input.

Primary retained retail pin `1dd48a78e55ef9c99519fc5221a206168ce2e98a`:

- `decompiled/scripts/cp/crafted_trap_fireworks.gsc:154-158`, SHA-256
  `1caeccf0bfa6ddbe629fab5ca293ec79212f1c25482a67b4067b64be670ffba0`.
- `decompiled/scripts/mp/killstreaks/ims.gsc:201-204`, SHA-256
  `d2867bed6ac5bc4ce7b499770683d521d6025a3b95f95c3d316f77f4db43ae2b`.

Both create a real script model, call setmodel, then assign scale 3. This supplies
an observed call order, not an engine setter/renderer guarantee. The variant
changes no alias, API, native code, shared helper or packed geometry.

## Exclusive staging contract

Logical namespace remains `sdk_original_rig_stock_witness`. State remains
`level.sdk_original_rig_stock_witness`; dvars and `[SDK rig stock witness]`
markers are identical. Select the new SDK source but stage its bytes only to the
existing dedicated destination:

```text
iw7-mod/custom_scripts/cp/sdk_original_rig_stock_witness.gsc
```

Do not stage both filenames in auto-loaded custom_scripts. Source selection must
be explicit in a new plan (`ScaleAfterModel`); old plans retain the original 649b
tuple. Demo owns destination exclusivity, backup/hash verification, fixture
binding and restoration. The stock-witness source contract in `SCENARIO.md`
still applies, including neutral-before-Use, real native protection, private
loopback, non-Main port and `sv_cheats 0`. The old original-rig GSC remains 49f,
FF remains ea7 and d25 remains its source-provenance pin. Existing B78 can observe
this experiment; no C++ or FF rebuild is needed for the changed source order.

After a separate parent runtime GO, one private fresh run may compare its stock
placement scale, pose, records and authentic image with the retained before-order
run. Keep FOV, effective DObj scale, GPU interpretation and positive geometry
identification unqualified unless measured. An unchanged or changed scene-field
value is an experiment result, not automatic proof of rendering or a ScaleBug.
No ANIMATE, Main promotion or owner acceptance follows from source validation.

Source validation on 2026-10-14: IW7/PC parse and dry compilation pass with the
existing GSC Tool 1.5.1.359. Four source-relation tests pass, including negative
controls for baseline drift, unchanged order and an extra TTL/pose change. The
test is discovered by the existing SDK test group. No native build, FF read,
asset regeneration, runtime launch or owner gameplay occurred in this change.
