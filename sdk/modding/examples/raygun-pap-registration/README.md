# Private Ray Gun PAP registration seam

2026-10-14: Source only. This module installs no bindings from `init()`. Its
`sdk_raygun_pap_enable` dvar defaults to zero; setting it alone still refuses.
There is no player command, weapon grant, asset loader or standalone launcher.
The native owner owns full weapon/attachment JSON and FF qualification. The
server operator owns the protected player, real scenario and exact mod binding.
None of those runtime inputs is qualified by this example.

The reviewed caller invokes
`player sdk_raygun_pap_registration::activate(assets_observed, scenario_reviewed, approved_fs_game)`
using its staged script path. Undefined or false attestations refuse. The caller
must derive them from actual, reviewed evidence; source names or an earlier Rig,
HUD or BO3 static-prop receipt cannot satisfy them. `approved_fs_game` is the exact
new weapon project's mod, not a guessed namespace. Rig and HUD mods refuse.
No magic readiness dvar, new proof schema or automatic true argument is supplied.

## Binding and retail path

| Identity | Meaning |
| --- | --- |
| `sdk_raygun_zm` | Bare player weapon, semantic tier 0 / retail level 1 |
| `sdk_raygun_pap_zm` | Native PAP attachment, still awaiting actual asset proof |
| `sdk_raygun_zm+sdk_raygun_pap_zm` | Expected rebuilt variant, tier 1 / retail level 2 |

Activation requires the sole live selected player already holding the exact
bare weapon, no upgraded variant, existing retail dictionaries, and an existing
base PAP record at level 1 or no such record. It requires dedicated `cp_zmb`,
Zombies, port 27116, one maximum client, LAN-only, a password, `sv_cheats=0`,
`g_inactivity=0`, exact approved `fs_game`, enable 1 and stop 0. The external
operator must establish fresh actual engine godmode before enemy exposure.
These dvars are context checks, not evidence of protection or loaded assets.

The module refuses a present `level.max_pap_func`, a global `pap_max` other than
2, or any occupied private global/attachment/upgraded-player key. It preserves
the absent Spaceland callback. It neither wraps a callback nor changes the
global maximum. The real donor prerequisite, inserted fuses or activated
Director's Cut, must already hold; the module never unlocks either.

Only five scoped bindings are written: the string `level.pap[base]=base`, a new
base-to-unique map containing `pap1` to the private attachment, its reverse
attachment-to-`pap1` entry, and the player's base/upgraded aliases pointing to
the same level-1 PAP record. An existing base record retains its identity.
There is deliberately no global PAP entry for the full upgraded variant.
Retail raw-family parsing retains SDK names in full; that missing entry rejects
a second private upgrade. Activation also refuses the stock shortened-name
fallback key; the watchdog checks both forbidden upgrade entries for changes.

The retained retail source is pinned at
[`mjkzy/iw7-gsc-dump` 1dd48a78](https://github.com/mjkzy/iw7-gsc-dump/tree/1dd48a78e55ef9c99519fc5221a206168ce2e98a).
Paths below are relative to `decompiled/`; no script body is copied here.

| Retail reference | Contract used |
| --- | --- |
| `scripts/cp/zombies/coop_wall_buys.gsc:35-70` | Global PAP entries contain weapon strings |
| `scripts/cp/utility.gsc:781-790,1000-1005,1046-1107` | Full SDK raw family and generic/unique attachment dictionaries |
| `scripts/cp/cp_weapon.gsc:3816-3834,3887,3961,4862-4933` | Existing attachment builder and eligibility path |
| `scripts/cp/cp_interaction.gsc:345-358` | Existing real price calculation, including retail exceptions |
| `scripts/cp/zombies/interaction_weapon_upgrade.gsc:195,220-221,232,235,279,492-496` | Attachment selection, rebuild, pre-pickup event, transaction lifetime and pickup increment |

The machine, cost, charge, gesture, pickup, ammo grant and all retail events
remain retail-owned. This module does not call them, give ammo, change currency,
adjust companion/self-revive behavior, quests, fuses, DC or any other weapon.
It does not increment the PAP level. A direct grant or `pap_used` event cannot
prove a paid pickup. Real gameplay must confirm the exact resulting name,
shared record's 1-to-2 increment, real charge/pickup and second-upgrade refusal.

## Stop and ownership

The watchdog stops on a changed private context, player set, callback or maximum.
It retries while the retail owner's `paping_weapon` is defined, preserving the
pickup alias until that transaction finishes. Game end and owner disconnect
also request cleanup. The state is published before the first write, with no
yield during registration. Each written key is recorded.

Before reverting any key, cleanup verifies the exact root state identity and
all remaining owned bindings. An absent/replaced root or changed binding produces
`RESTORE_PENDING`, preserves the dictionaries and current root, and requires
operator diagnosis/level teardown; no restoration is claimed. This refusal does
not send the global stop event, so it cannot stop replacement-state listeners.
The old watchdog exits through its own `state.stopped` flag.
Successful cleanup removes added keys and restores the prior base-record
pointer, retaining any real retail increment in that prior record. It never
rolls back a paid transaction or changes inventory. It clears its own level
state before the stop notification, since `endon` can terminate the caller. No
yield occurs from ownership verification through restoration, clear and notify.
Only this confirmed owned cleanup sends the global notification.
Level unload discards the VM. Disconnected entities require runtime validation.

Markers `BINDINGS_REGISTERED`, `RESTORE_DEFERRED`, `RESTORE_PENDING` and
`BINDINGS_RESTORED` always retain `runtime_ready=0`; none is an accepted PAP
transaction. Source fixtures exercise guard/mutation/cleanup regressions with
negative source controls. The retained gsc-tool 1.5.1.359 parsed this module's
grammar. Neither those fixtures nor grammar parsing prove engine linking,
array/struct reference comparison, actual loaded assets, weapon rebuild, cost,
pickup, restoration under disconnect or owner acceptance. No engine compiler,
native/FF build, asset extraction, deployment or game test was run here.

Next: qualify the actual full assets and fresh protected private scenario with
the native/server owners, then obtain the distinct runtime GO. Keep this module
inactive and Main's runtime untouched until those proofs exist.
