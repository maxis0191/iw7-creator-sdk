# IW7 engine modding: primary objective and working method

Owner decision, 16 October 2026: the primary objective is practical freedom to
modify IW7, including its deepest native rules and engine systems. BO3 import
is an optional interoperability use case, not the objective, ceiling, or an
obligatory dependency of original IW7 development. This decision supersedes
earlier priority language that made BO3 portability the programme's destination.

Kino's zombie and the Ray Gun remain specifically requested demonstrations.
They do not block useful engine work until completed. Rhino remains retired
and the HUD showcase remains cancelled. This strategy does not restore stopped
experiments, removed infrastructure, or rejected operations through another tool.

## What success means

An author can change a meaningful engine behaviour or create content using a
documented, reusable interface, build and load it, observe the intended effect,
and remove or change it without breaking unrelated systems. GSC and LUI are
valuable surfaces; their existing capabilities are not the programme's limit.
Native hooks, data representations and lifecycle integration are legitimate
work where those surfaces cannot express the requested behaviour.

Do not promise unrestricted control of every subsystem. Record the exact
capability, supported engine revision, known limits and proof. A BO3-looking
object, a decompiled function, a source check, or an accepted manifest alone
does not establish control of an engine rule.

## Work from the behaviour to the smallest missing primitive

1. State the desired observable change in IW7 and the stock behaviour it alters.
   Identify the subsystem, its current owner and the smallest unresolved fact.
2. Reuse pinned source, symbols, references and retained observations. Form a
   falsifiable hypothesis about the relevant function, data layout, ownership,
   thread, or lifecycle. Decompile selected functions and their actual callers;
   do not begin with whole-game reconstruction or an unbounded binary scan.
3. Establish the native contract: arguments and layout, allocation/lifetime,
   scheduler/thread, dependencies, client/server authority and failure path.
   Decompiler types and similarity matches are hypotheses until corroborated.
4. Implement the smallest controllable seam. Keep it reusable where the second
   consumer is known; avoid a universal plugin framework before a real consumer.
   Separate finding an internal address from exposing a stable author API.
5. Exercise a discriminating engine test: baseline, controlled change, expected
   effect, negative/control case and restoration. Use synthetic input for format
   and ABI checks, but test engine semantics in the engine when necessary.
6. Prove reuse with a second input or parameterisation through the same API and
   toolchain, without an example-specific engine patch or hidden allowlist.
   Add composition, map transitions and independent peers when that capability
   actually depends on them. Keep owner acceptance separate.

Necessary validation is not a new showcase programme. Retain relevant crash,
rollback and compatibility controls; remove duplicated paperwork that produces
no new evidence or protection. A failed test should narrow the hypothesis.

## Capability tracks and ownership

| Track | Primary owner | Decisive outcome |
| --- | --- | --- |
| Native rules and observability | iw7-mod-components | A real engine rule can be inspected, changed through a scoped native seam, and restored; effects and thread/lifetime assumptions are measured. |
| Assets and representations | x64-zt-extensions | Original input can be written, loaded and used by IW7 with correct dependencies; imports from another game are optional adapters. |
| Animation and AI | Native plus asset owners | A controlled original rig/clip and a behaviour transition work in-engine; skeleton, events, movement, damage and lifecycle are tested as separate dependencies. |
| Physics and worlds | Native plus asset owners | Authored collision affects real traces and player/actor contact; rendering geometry or an AABB alone is insufficient. |
| Author-facing interfaces | iw7-creator-sdk | A second project can use the qualified primitive through a documented build/load/configure path without editing engine internals. |
| Gameplay and delivery | iw7-paris-server | The capability operates with the required server/client authority and survives its relevant session transitions and rollback. |

These are capability tracks, not orders to start six simultaneous heavy jobs.
The orchestrator selects the current critical path from concrete evidence.
Prioritise a primitive that unlocks several real consumers, has a short decisive
test, and removes an observed blocker. Source preparation can remain parallel;
heavy work retains the common scheduler and exact process ownership.

The immediate review found reusable gaps in native rule access, complete
original asset/rig consumption and composition. BO3 identity or extraction
gaps must remain local to BO3 consumers. Missing Ray Gun metadata cannot justify
holding an independent IW7-native rule experiment or original rig test idle.
This is a prioritisation rule, not a claim those experiments already pass.

## Evidence and progress

For each active capability, keep a short record of: desired behaviour, owner,
current evidence, one blocking fact, next decisive test and resulting decision.
Use these distinctions without building another receipt framework:

- **Observed:** an existing behaviour or data relationship was measured.
- **Implemented:** a source interface exists and its relevant checks pass.
- **Engine-verified:** the controlled change produced the intended engine effect.
- **Reusable:** another input/consumer works through the same interface.
- **Owner-accepted:** the owner explicitly accepted the stated playable result.

Count capabilities and retired uncertainties, not PRs, lines, tokens, manifest
fields or synthetic tests. Keep failed candidates and precise limits. No global
percentage of engine ownership, BO3 compatibility, or unlimited modding is inferred.

## Strategic review and execution are separate roles

The execution orchestrator remains chat
`01a1364c-8574-72c2-bf64-079c5f1459d8`. It owns assignments, sequencing, resource
coordination and daily worker reports. The strategic reviewer is chat
`01a142b6-dd2b-7091-a408-9655304bf18b`, authorised by the owner to correct goals,
architecture and priorities and to review hourly.

Workers report to the orchestrator, not to both chats. The reviewer reads their
work and sends consolidated, actionable corrections when needed. It is not an
extra routine approval gate. An unchanged hour requires no status broadcast.
Escalate only a strategic conflict, a materially unsupported claim, a repeated
technical impasse, or a decision actually requiring the owner.

Preserve the canonical product boundaries, private Git/PR workflow, Main27016,
banks and occupied client. Existing specific human prohibitions and execution
refusals remain in effect; a tool installation or strategic correction does
not erase them. Do not recreate retired labs, access bridges or deleted stock.

## Tooling direction

Reuse the existing Ghidra installation and bounded native diagnostics. A
persistent PyGhidra/MCP project can avoid repeated imports and preserve shared
annotations; qualify it on our own fixture before admitting an IW7 corpus.
BSim is a separate aid for finding similar functions, not a proof of matching
types, ABI or gameplay semantics. Neither tool substitutes for the engine test.
Keep one owner of analysis mutations and reuse results rather than starting a
separate JVM and database for every chat. Installation and runtime qualification
are tracked by the native tooling owner, not duplicated inside this SDK.
