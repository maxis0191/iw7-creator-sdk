# Stock Option HUD source variant

This separate source adds one owner-local persistent English HUD:
`Stock Option active | 10s`. It uses existing IW7 `newclienthudelem`, `settext`
and `destroy` primitives, with no new image, client file, native method or import.
The label is centered near the top at y=70, scale 1.2. Actual visibility,
safe-area placement and coexistence with the retail HUD still need fresh pixels.

Only `sdk_stock_option_hud_v1.gsc` belongs to this variant. Install a single
Stock Option provider on a future private test dedicated: remove/restore the
old provider through the guarded ops plan rather than load both. Activation,
private context, default disabled, default ten seconds, maximum thirty seconds,
one owner/weapon and 64-shot budget stay the same. The source-owned
`hud-manifest.json` declares the original provider as a conflict and keeps
closure incomplete and runtime/gameplay evidence pending.

The HUD is allocated once after activation admission and before shot observers.
Its handle lives only in that activation's `state.hud`. Each refresh calculates
the rounded-up seconds from `state.deadline - gettime()`, on the local engine
clock, without extending the deadline. A separate loop polls at 50 ms and only
changes text when the displayed second changes. It removes the HUD at zero.
The existing effect expiry and ammunition handlers remain unchanged.

Every effect stop first marks the state stopped and destroys its HUD, clears the
handle, releases ownership, then notifies stopped threads. Death, disconnect,
weapon/reload/context changes, expiry, reserve/budget exhaustion and level end
all use that same stop path. Cleanup is idempotent. HUD allocation failure ends
the activation without an ammunition write. No SoulBox HUD state is read or
changed. These are source/compiled-order checks, not executed lifecycle proof.

The original SDK50 source is still 11,035 bytes with SHA-256
`5a28e5a220aedfaed4481bdbd5440aec8c14bf90b5840ae62122d05a86575fba`.
Its source, manifest, contract, E2E plan and historical validation are unchanged.
The previous SDK50/Timer B receipt and five images retain their original input
identities. They do not qualify this HUD variant. The entire transfer, pure
accounting helper, raw telemetry and existing eligibility/lifetime functions are
compared byte-for-byte against that frozen source by the targeted HUD tests.
No HUD update, wait or print is added to the transfer path.

The new exact source/compiler tuple is recorded in `hud-source-validation.json`.
After source review and private Git completion, the ops owner must create a
separate HUD plan for this new pin. That future run needs fresh native protection
and authentic neutral/active/after frames, a readable decreasing HUD, real shots
with the same paid transfer, and actual stop/death/disconnect/level-end cleanup.
No Game, FF or C++ work is part of this source variant. Owner acceptance remains
pending.
