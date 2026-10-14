# Stock Option source prototype

A separate [persistent HUD variant](HUD.md) uses
`sdk_stock_option_hud_v1.gsc` and its own source/validation pin. This original
SDK50 file and the E2E plan below remain frozen. Load only one provider.

An original, opt-in server script inspired by classic
[BO3 Stock Option](https://www.callofduty.com/ca/en/blog/archives/call-of-duty-black-ops-3-zombies--gobblegum-101):
reserve ammo pays for shots while the magazine remains at its captured level.
The original lasts three minutes. This private prototype lasts 1–30 seconds
(default 10), at most 64 accepted shots, for one player and one equipped weapon.
No BO3 texture, model, UI, client file or new native method is included.

Load `sdk_stock_option_v1.gsc` as a standalone CP custom script. It is disabled
by default. Before map load, the private test dedicated must explicitly set
`sdk_stock_option_demo_enable 1`, use `cp_zmb`, password/LAN privacy, an empty
`fs_game`, a non-Main port and `sv_cheats 0`. Heartbeat suppression, actual engine
godmode, inactivity 0, ownership/backup/restoration and real input belong to
the separately reviewed Agent-Lab harness. No game launch is authorized by
this source checkpoint.

The fixture can request activation on its actual protected player:

```gsc
setdvar("sdk_stock_option_seconds", 10);
player notify("sdk_stock_option_activate");
```

Activation requires a living, playing player, a full primary magazine with
capacity at least two and positive reserve. Dual wield, reloading, switching,
last stand or frozen controls refuse activation. Only one player owns the
effect; duplicate requests do not refresh it. Death, disconnect, weapon change,
reload start, respawn, privacy changes, expiry and exhausted reserve end it.
Stopping releases the observer/state without restoring old ammo.

Each `weapon_fired` notification must identify the captured weapon, show exactly
one magazine round spent since the last accepted snapshot and an unchanged
reserve. Every other delta stops the effect. The handler rechecks its context
and values, debits reserve first, verifies it, restores one magazine round and
checks both outputs. There is no wait between the paired writes. Total ammo
drops by exactly one for a confirmed transfer; this is not unlimited ammo.
An uncertain partial write stops conservatively and may cost an extra round.
It never refunds a guessed engine change or grants an unpaid magazine round.

Primary IW7 evidence is recorded in `api-evidence.json`: builtin names/IDs and
the existing decompiled CP notify/ammo patterns, with hashes and pinned sources.
Those references do not establish the engine's clip-debit/notify order or
compound atomicity. If the event arrives before debit, the prototype refuses
the ambiguous delta instead of claiming success. Reload/switch cancellation and
source arithmetic checks are not gameplay proof. No generic import/asset port
capability is introduced.

The tests execute the arithmetic from the production GSC helper, check rejection
and conservation, and inspect the existing SDK Plan/package gates. Offline
parse/compile evidence is separate. The manifest keeps closure incomplete and
runtime/owner evidence pending, so no community/player archive is ready.

Next private test: real separated firing with measured clip/reserve before,
during and after expiry; reserve depletion; refusal at zero reserve; actual
reload/switch cancellation. Prove normal magazine consumption after stopping.
No fabricated `weapon_fired`, scripted damage, ammo reset at expiry or claimed
client/WAN/owner acceptance is part of that evidence.

The machine-readable private test protocol is [e2e-plan.json](e2e-plan.json).
It retains the original source/compiler checkpoint and pins this separate
instrumented source. `SHOT` now adds the actual entry, reserve-readback and
clip-readback samples, while failed paths use `TRACE`. Values not reached by the
original short-circuit reads remain `unobserved`. One line emits after the path's
last write; no logging occurs between successful paired writes. `trace_ms` is
emission time, not a timestamp for every phase. The fields explicitly say
`observed_handler_order_only=1` and `engine_atomicity=unknown`.

The pure accounting helper is byte unchanged; its earlier 8,064-pair evidence
remains historical and was not rerun for telemetry. Targeted source/actual
disassembly checks cover the capture/read/write/emit order. This plan has not
run and modifies no harness. The phase trace still needs an actual private run;
offline compiled ordering is not engine timing, atomicity or rendered-client
proof. The plan identifies full-clip Reload no-ops, genuine-death protection
constraints and the need for a real second player without automatic cloning.
