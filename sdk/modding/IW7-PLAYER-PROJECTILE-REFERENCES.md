# IW7 player projectile template: exact Source references

2026-10-14, Source inventory only. The initial name selected with the native
owner is `iw7_shredder_zm`, with attachment `shredderpap1` and normalized PAP
weapon name `iw7_shredder_zm_pap1`. These are retained retail-script identities,
not a qualified full weapon/attachment JSON template or an authenticated BO3
Ray Gun. No game, asset extraction, compiler, native/FF build or opaque hash was
performed for this inventory.

The existing retained [retail GSC source](https://github.com/mjkzy/iw7-gsc-dump/tree/1dd48a78e55ef9c99519fc5221a206168ce2e98a)
is pinned at `1dd48a78e55ef9c99519fc5221a206168ce2e98a`. Its current tracked
source matches that revision. Paths below are relative to `decompiled/`.
No decompiled script body or game-derived template is copied into this SDK.

| Reference | What it establishes |
| --- | --- |
| `scripts/cp/utility.gsc:4193-4195` | Exact Shredder base, PAP attachment and normalized PAP weapon names |
| `scripts/cp/maps/cp_zmb/cp_zmb.gsc:109` | Base/PAP Shredder belong to the map's player last-stand weapon list |
| `scripts/cp/zombies/direct_boss_fight.gsc:975-976` | Family `shredder` maps to player weapon `iw7_shredder_zm` |
| `scripts/cp/zombies/zombies_weapons.gsc:108-115` | Base/PAP Shredder enter the existing special-damage path and `shredder_death_logic` |
| `scripts/cp/utility.gsc:4198-4200` | Separate fallback only: `iw7_dischord_zm`, `dischordpap1`, `iw7_dischord_zm_pap1` |

Dummy damage names such as `iw7_shredderdummy_zm` and NPC
`iw7_zapper_grey` do not qualify a player weapon template. The Dischord pair is
a Source fallback if the observed Shredder JSON is refused, not another asset
to dump automatically. No Howitzer/Spartan asset alias is guessed.

## PAP path and renamed-family boundary

`scripts/cp/utility.gsc:781-790` strips only `iw5`, `iw6`, `iw7` and `alt`
prefixes. Thus `sdk_raygun_zm` remains that entire family key; it does not inherit
`shredder` or `dischord` by renaming its native definition.

`scripts/cp/cp_weapon.gsc:4862-4886` checks `level.pap`, its optional
`level.max_pap_func` callback and the family entry. The special wonder-weapon
gate at `4895-4913` preserves native fuse/Director's Cut limits.
`return_weapon_name_with_like_attachments` starts at `3887`, checks attachment
availability at `3920`, and uses the PAP branch at `3961`.
`get_possible_attachments_by_weaponclass:3816-3834` consults the existing
`attachmentmap_basetounique` table. This Source machinery must be bound for a
custom family; a renamed native PAP attachment alone does not establish it.
No callback or table mutation is implemented by this inventory.

The real machine's `scripts/cp/zombies/interaction_weapon_upgrade.gsc` selects
the family at `69-71`, preserves its special gate at `78-81`, selects a PAP
attachment at `195` and rebuilds the weapon at `220-221`. Its `pap_used` event
at `232` occurs before pickup. Actual pickup calls `_giveweapon` at `471`,
`givemaxammo` at `472`, `switchtoweapon` at `492`, increments the player's family
level at `494`, then emits `weapon_level_changed` at `496`. The earlier event
alone is not a successfully acquired PAP weapon.

`cp_weapon.gsc:3805-3813` identifies PAP by a name substring. It does **not**
prove the native attachment's `papAttachment` boolean, projectile weapon type
or membership in the full definition's attachment lists.

## Qualification still required

The Source names and player/PAP references above are sufficient to select a
bounded future one-weapon/one-attachment request. The existing native owner's
`ops/raygun/prepare_weapon.py` requires full, hash-pinned JSON templates. Its
projectile type, primary inventory, clip/reserve/per-shot ammunition, damage,
projectile speed/lifetime, FP/TP models, weapon animation package, native PAP
flag and exactly one matching attachment-list entry remain unobserved here.
Player reload/fire/projectile travel/impact and actual machine pickup remain
runtime checks. The generic `reload_watcher` at
`zombies_weapons.gsc:1212-1228` handles an Escape-gametype reserve adjustment;
it does not qualify Shredder's reload mechanics in Spaceland.

The next authorized operator must use exact loaded/nondefault asset identities,
the existing full weapon exporter and an independently reviewed bounded
attachment export route. Generic console `dumpasset` availability is not proof
that its channel is accessible or its output is nondefault. This document adds
no exporter, live fixture, sparse template, renamed family hook or new framework.
