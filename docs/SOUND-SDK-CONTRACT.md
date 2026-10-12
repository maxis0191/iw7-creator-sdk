# Private sound research package: SDK contract

Implementation decision under the owner's modding authorization, 2026-10-12:
this private research package declares static content
integrity and the existing CP, mod transport and GSC capabilities it actually
requires. There is no registered `custom-sound/1` capability; do not invent or
declare it as qualified. No currently required capability is removed to obtain
readiness or avoid a validator refusal. A generic sound capability will be defined
from concrete engine evidence later.

`package.ready` is limited to static package integrity/contract. Sound readiness
remains explicitly unestablished in the specialized producer/native gates and
runtime reports. Static readiness does not permit a public release or establish
engine loading, alias lookup, playback, audibility, WAN or owner acceptance.
Existing validators and capability refusal rules remain authoritative.

## Files, closure and neutral fixture

The common contract represents the standard client destinations:

| Destination | Generic closure binding |
| --- | --- |
| `mods/sdk_original_sound_v1/mod.ff` | Bank `sound` root and branding rawfile `other` root |
| `mods/sdk_original_sound_v1/mod.sabl` | Bank `sound` root |
| `mods/sdk_original_sound_v1/mod.sabs` | Bank `sound` root, including when the streamed bank is empty |

The native inventory labels `soundbank` and `rawfile` are not generic SDK kinds.
Use `kind=sound` with ID `soundbank:community_original_sound_v1.all`, and
`kind=other` with ID `rawfile:mod`. Preserve the native inventory types in their
own evidence; this mapping does not alter or certify those assets. A SAB root
cannot use `kind=other`, and every file needs a nonempty closure root binding.
Both sidecars may bind the same bank root without inventing a streamed alias.

For the neutral server fixture, the canonical lifecycle entrypoint is
`custom_scripts/cp/sdk_original_sound_v1.gsc::init`. Bind its server ScriptFile
node to `iw7-mod/custom_scripts/cp/sdk_original_sound_v1.gsc` and declare cleanup
for `threads` and `player-state`. A suffixed `_neutral.gsc` can be an auxiliary
source but cannot replace the canonical entrypoint. The minimum fixture package
has three client files and this server file. No Beacon, XModel, NCS, HUD or Lua
asset is required by this contract.

The common transport makes SAB files optional and requires `mod.ff`; the Sound
adapter separately requires exactly three client files. Preserve both boundaries.
Unknown file sizes/hashes and an incomplete closure are valid only as a plan with
pending evidence. Complete closure requires established node hashes and evidence;
the plan cannot declare itself ready.

The SDK has no typed `bank_zone` or `alias` field. An opaque named alias dependency
can be represented, but is not another proven native asset callback. The producer
gate must establish internal zone `mod`, bank `community_original_sound_v1.all`,
alias `community_original_chime_v1` and their actual FF/SABL/SABS relationship from
its qualified receipt. Source commit declarations likewise do not identify the
measured native binary or all R2 overlays; native qualification remains separate.

## Real-validator source tests

Run from the repository root:

```text
python -B tests/ops/agent_sound_contract_test.py -v
```

The 17 cases call the real SDK validator with `stage=plan`, no payload root and
no validator mocks. They also exercise the real Distribution-Compat declarations.
Every file size/hash, node hash and network protocol stays null; all evidence stays
pending and every SDK result has `ready=false`, `runtime_ready=false`,
`owner_accepted=false` and no checked payload. Source commit strings are explicitly
hypothetical environment declarations, not executable proof.

The in-memory fixture is not written or distributed as a deliverable manifest.
Positive cases cover the generic sound/rawfile mapping, canonical neutral fixture,
generic alias dependency, optional common SAB transport and declared source pins.
Negative cases cover native type names, invalid SAB roots, missing/noncanonical
entrypoints, an unregistered capability, unsupported typed metadata, missing FF,
historical SAB destinations, absent roots and falsely complete closure. Unknown
protocol/source inputs remain refused by distribution compatibility.

These tests complement the six mock-based PackageGate API tests: they verify real
schema/closure/lifecycle/capability behavior without running package validation,
reading game/audio payloads, hashing binaries, obtaining a lease, listening,
building or launching a game. Runtime sound readiness remains unestablished.

Local validation on 2026-10-12 at 20:25 UTC: all 17 cases passed against base
`1b2764958c86a24eea0942d08e2393882180f41c`. This is source-contract evidence;
coordinator integration and exact-head CI remain separate.
