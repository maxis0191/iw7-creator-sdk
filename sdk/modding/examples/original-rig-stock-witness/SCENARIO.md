# Original-rig stock witness: independent addon

This opt-in addon creates at most one stock `zmb_coin_alien` script model at
the central original actor's observed pose. The original source, its three
actors and their public state remain unchanged and active. This is an
experimental source contract, not a package or runtime pass. Demo owns the
separate ops route/plan, fresh native protection, real input, captures and
restoration. SDK author bindings and native stock-observer filters have separate
owners.

## Primary pipeline

Original `sdk_original_rig_probe.gsc`: 4,866 bytes, SHA-256
`49f7e1aa336bb2fdb73e5c36be03c213311ead4555fc9bca0d7b4e69ccdc219b`.
Its lines 57/65/66/69 call `spawn("script_model", origin)`, assign angles,
assign scale 3, then call `setmodel`. No `scene_spawn_actor` helper exists there.
The addon uses that same sequence in `create_witness`; it claims no shared
function identity. It reads actor 1's current origin/angles and assigns the same
authored scale 3. It introduces no offset, new animation, Use trigger, hint,
FX-part state or change to player health, inventory, position or camera.

Retained primary `scripts/cp/cp_weapon.gsc:2926-2941` polls the player method
`usebuttonpressed()`, including held/released states. This addon reads actual
Use, never synthesizes a script notification or console command to create a
witness. `time_ms` is the engine game clock; the fixture separately correlates
native wall ticks and capture timestamps.

The combined FF stays 1,064 bytes, SHA-256
`ea7ba4be1d5e6f0878431b51e7b9b1ba9d2b10bf74b1ad21da14d55c414e145d`,
and pin d25 stays unchanged. No FF rebuild or old SourceRig guard relaxation is
part of this addon. The new ops route must bind the added source separately.
A native capsule that observes only the two custom model names does not qualify
the third stock lookup; the stock name needs its own explicit native capability.

## Private activation and observation

Install the new source on the test dedicated only as
`iw7-mod/custom_scripts/cp/sdk_original_rig_stock_witness.gsc`, alongside the
unchanged original. Before a fresh `cp_zmb` load:

```text
fs_game mods/sdk_original_rig_probe
sdk_original_rig_probe_enable 1
sdk_original_rig_probe_mode DISPLAY
sdk_original_rig_probe_play 0
sdk_original_rig_probe_stop 0
sdk_original_rig_stock_witness_enable 1
sdk_original_rig_stock_witness_stop 0
```

The addon is disabled by default. It requires dedicated, exact map/mod, non-Main
port, `sv_lanOnly 1`, a nonempty password, `sv_cheats 0` and configured
`g_inactivity 0`. The fixture additionally suppresses master heartbeat, uses
loopback/private credentials and verifies fresh actual engine godmode and
inactivity protection before exposure and Use. A source dvar check is not
godmode evidence. Preserve Main, banks/config and occupied owner clients.

1. Wait for original `DISPLAY_READY` and addon `READY`. The addon checks the
   original state defined, stopped false, placed true, DISPLAY mode, exactly
   three defined actors; `placed` alone is insufficient. Only its selected
   playable player can trigger its one attempt.
2. Capture authentic `00-neutral` before any witness creation. GSC cannot see
   that capture. The ops route must reject a pre-neutral `WITNESS_CREATED`.
3. After fresh native protection, use the existing AgentScenario real Use action
   for 175 ms, then release. The addon requires an observed release after READY
   and a new rising edge while the player is alive and unfrozen. A held Use at
   READY is ignored. There is no show dvar or ninth console command.
4. On `WITNESS_CREATED`, capture authentic `01-stock-witness` before expiry.
   Record entity, anchor entity, stock name, observed origin/angles, scale and
   clocks. At the reported RIG7 pose, both origin tuples should be
   `(467.546,3517.47,48.0679)`, angles `(0,-90,0)`, authored scale 3. These are
   comparison references, not hardcoded coordinates or proof of rendered scale.
5. Inspect actual stock pixels and the independently qualified stock native
   record. A call return, entity marker, non-default header or resource presence
   is not visibility. Co-location is deliberate: custom-only pixels are assessed
   from the neutral frame and lateral actors, not from stock overlap at center.

Exact prefix: `[SDK rig stock witness]`. Markers are `ARMED`, `READY`, `USE_EDGE`,
`WITNESS_CREATED`, `FAIL` and `STOPPED`. Public addon state is
`level.sdk_original_rig_stock_witness`, with `actor`, `owner`, `requested` and
`stopped`. It never writes the original rig's state or actor array.

TTL starts after stock `setmodel` returns and is ten seconds. Game end, original
`sdk_original_rig_probe_stopped`, selected-player disconnect or the addon's stop
dvar also delete only the stock entity and end addon threads. The existing
console stop still stops the original, whose notification cleans up the addon;
no extra console operation is needed. A second witness is refused in that map.
The fixture owns source/config restoration and guarded process teardown. No
gameplay, FF, rendered-output or owner acceptance follows from source checks.

Source validation on 2026-10-14: GSC Tool 1.5.1.359 parsed and dry-compiled the
addon for IW7/PC with no script imports. Its tool SHA-256 is
`1adfd67414a9b886cbad57ee0378f622eed485bcef7711322aee478e298fadcb`.
These checks do not establish runtime linking, input, TTL execution or pixels.
