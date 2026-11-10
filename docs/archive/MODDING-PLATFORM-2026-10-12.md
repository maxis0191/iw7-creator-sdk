# Community mod SDK: status and validation records of 2026-10-12

History, not instructions. These paragraphs stood in `docs/MODDING-PLATFORM.md` until 2026-11-10: the opening
status and the three dated sections at its end. The words are unchanged; only the link targets were adjusted to
this folder, and links to documents of other repositories were replaced by their name and repository. Pull
request and issue numbers are those of the server repository (iw7-paris-server), where this work was done
before the extraction. The contract itself is in [MODDING-PLATFORM.md](../MODDING-PLATFORM.md).

SelfContained runtime preparation now selects the exact composed `.gsc` source
through Agent-Lab, with separate dedicated-only and protected Use/rejoin phases.
This is source/pure-test preparation; the complete preflight and game trial are
pending. See the pinned plan and limits (server repository: `docs/SELF-CONTAINED-BEACON-RUNTIME.md`).

Current checkpoint, 2026-10-12: PR148 is merged as `178708b` under the recorded
owner CI-admission exception; CI did not pass. The SDK now has real Beacon FF
build/readback and Creator finalization evidence, plus protected run 5 Use/HUD and
controlled base-client restart/rejoin with verified Aurora cdata and restoration.
Run 5 retains two unresolved retail errors in issue 150; it is a targeted witness,
not global engine integrity, human acceptance or actual second-player/WAN proof.
Material C adds offline geometry/pixel-byte verification, not rendered material.

The PR151 tranche adds original two-bone authoring, independent readers, original
PCM/FLAC sound preparation, a bounded H1 trigger adapter, recipient evidence
analysis, a local-flag Beacon variant, a strict-consumption binder and passive
ticket telemetry. Source Test-Platform at `f99041f` passes 540 cases (537 pass,
three skips), PowerShell checks and four actual GSC syntax parses. Later focused
checks cover the diagnostic rig and four-PAK stock binding.

Measured capabilities and remaining gaps are separate:

| Area | Verified progress | Still open |
| --- | --- | --- |
| Original models/animation | Rig E FF builds/verifies/dumps; seven assets and CPU authoring evidence | Strict redump rejects two loader-modified pointer fields; rendered skinning and animation |
| Original sound | Real FFmpeg decode reproduces the complete original WAV | SAB/FF construction, delivery and IW7 playback |
| Compiled GSC | Two real complete-consumption witnesses, one CTest and 13 native methods pass | Build supervisor fails on a residual descendant; import-absence consumer and package closure |
| Recipient dependencies | C identifies pak17; D's four-PAK overlay advances to global_cp and restores | Another fatal body remains unknown; no successful reference CSV |
| Material C | Offline original pixels and reviewed runtime candidate | Full16/16 admission refused before any game invocation; no rendered witness |
| World/map authoring | Strict trigger-record conversion and source-backed H1 route audit | Havok world collision, playable map, actual H1 donor import |

The nine reviewed GSC tool patches and licenses are retained in the private
source archive with a verified source tree; reconstruction does not reproduce the
original commit ID or promise binary identity. No Main deployment, human/WAN
acceptance, weapon/AI qualification or BO3 equivalence follows from this checkpoint.
Current evidence (server repository: `docs/STATE.md`), runtime limits (iw7-mod-components: `docs/MODDING-ENGINE-RE.md`).

The original source-only SDK checkpoint was based on `21b91e3`; its contract and
preparation behavior below remain applicable to fresh inputs. It must not be read
as the current validation status of the whole platform.

## Validation and integration record

2026-10-12:18 standard-library tests (including300 bounded malformed mutations)
pass, including malformed/duplicate keys,
wrong capability side, undeclared asset requirements, lifecycle/path conflicts,
unknown protocol, unsafe transport, complete-package hash tamper, blocked import
packaging and bounded original-writer staging/refusal. The GSC Tool1.5.1 parser
passes the beacon. Existing transport regression suite:25 pass, one host symlink
case skipped. Synthetic fixture bytes are labelled and do not prove FF or
XMB validity. No native compilation, runtime link or gameplay was executed.

Only local source is prepared in this tranche. Parent integration must include
the SDK tests in appropriate source checks, review the final combined diff and
complete the authorized private PR/exact-head CI/merge workflow. Shared STATE,
BUGS, CHANGELOG, VALIDATION and PLAN updates belong to that integration owner to
avoid cross-chat edits. Main27016, owner client, banks/configs are unchanged.

The agent observer can bind actual Use to `level.sdk_beacon.model` (entity number)
and its `sdk_beacon_total`, updated in the accepted trigger handler together with
`level.sdk_beacon.total` and `player.sdk_beacon.uses`. Ready/activation markers
include the entity number. This is source preparation for the observer; logs alone
do not prove remote rendering. The enclosing harness must supply session nonce,
map generation, exact process identity and fresh safety checks. The model's
`sdk_beacon_instance` is its creation game time within that map generation.
`player notify("sdk_beacon_used", model, total, personalUses)` occurs only after
an accepted trigger updates rotation and HUD. The external fixture can listen
without coupling production source to `paris_test_*` native methods.
`player.sdk_beacon.rendered_total/rendered_uses` records settext intent only;
there is no Lua HUD or client pixel acknowledgment in this GSC example.

## Actual original-beacon preparation, 2026-10-12

After explicit parent authorization for tiny asset preparation, `prepare_beacon.py`
ran against the retained `modular-agent-platform` writer run
`runtime/model-lod1m-source-20261007`. No new writer was needed. Rehashed writer,
source/header/geometry, original XMB/XSB and historical visible FF match their
retained provenance. The retained FF reader's inputs and stdout JSON also match
its evidence. This is fresh integrity checking of historical proof, not a new
native reader execution or game acceptance.

The ignored SDK worktree output is `runtime/beacon-v1-source-20261012`:
10 prepared files totaling14,427B, plus4,752B local receipt = **19,179B** new data.
No executable, stock or retail material bytes were copied. The two original
geometry inputs are978B XMB (`F4160133AB4D19DFD1868C4DF8A935505466BDEBCFBEEE5898DFC535E92CFB29`)
and1231B XSB (`3D55171CB581DFA2EA249BEA1DE1A1F939F6AAEBBC8995E291C005540E388F27`).
The4802B GSC is unchanged at
`8BA85B3F5B3014D0C4D02B0E71F49BF617959B486502E4C63243B065ABC2A0B6`
and passes the real parser. Prepared manifest validates as a plan only.

`source-receipt.local.json` hashes every prepared file and records writer
provenance, checked reader inputs, expected inventory and policy baseline. Its
SHA256 is `B8229D50751FA990A925B4CB3C3E2C8110A373D645764D0580959D55D78277AA`.
Use `-buildzone sdk_beacon` and expect `rawfile,sdk_beacon`; the retained
`model-ff-plan.json` is original-model staging provenance, not the new build name.
Do not relabel the old1040B model FF as the unbuilt beacon FF. All binary inputs
and raw local evidence remain ignored and outside commits.

Future runtime follows privacy baseline `24d5c4f`: random nonempty password,
`sv_lanOnly=1` in final configuration and launch, loopback by default, reviewed
native master-heartbeat suppression and fresh privacy telemetry before client
join. The parent alone coordinates the next admitted build/test. This preparation
acquired no lease and ran no native executable, ZoneTool, game or network service.
Material variant2 remains a separate measured-model/closure preparation.

The subsequent [bounded FF runbook](../../sdk/modding/BEACON-FF.md) supplies a
default-plan-only SDK adapter for the actual `sdk_beacon` name. It reuses shared
transaction/admission/NTFS helpers and the H1 owner's final job implementation.
The real metadata plan passes without native loading; Run remains dependent on
the new macro-qualified ZoneTool receipt, final job source hash and parent GO.

## Native beacon FF checkpoint, 2026-10-12

Those prerequisites were subsequently met. The first admitted native execution
completed build, exact five-asset verification, dump and geometry readback with
exit 0 and zero job members in all four phases. The new FF is 1,048 bytes, SHA256
`76ed0701dc1480c501604db04999f300394c65877aa24a70dfe7afc2cd662d4a`.
The [execution record](../../sdk/modding/beacon-ff-validation-2026-10-12.json)
binds the tool/source/state hashes and validation limits. All temporary input
entries were removed, stock preservation checks passed and the complete 8/11 GiB
reservation was released. No game was launched. This establishes FF serialization
and original-model readback, not rendering, interaction, recipient material
binding, H1 donor import or map support. Ready and owner acceptance remain false.

The [recipient closure audit](../../sdk/modding/RECIPIENT-CLOSURE.md) recovers and
freshly hashes the existing retail material snapshot and diffuse-image export,
without copying their bytes or changing the schema. It supplies exact existing
ZoneTool requests for the missing recipient checks and compiled utility export.
Historical dump integrity, current DB resolution and transitive dependency proof
remain separate; the package closure is still incomplete.
