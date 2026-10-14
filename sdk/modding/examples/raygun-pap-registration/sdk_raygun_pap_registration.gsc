// Private Source-only registration seam. Default init never installs bindings.
// The reviewed operator must supply actual asset/scenario attestations later.
// No weapon grant, ammunition, currency, quest or retail callback is changed.
init()
{
    if (getdvarint("dedicated") && getdvarint("sdk_raygun_pap_enable"))
        print("[SDK raygun PAP] BLOCKED; reason=explicit_caller_attestations_required; runtime_ready=0.");
}

// Call on the selected, protected player already holding the bare private base.
// Undefined/false arguments refuse before any private dictionary mutation.
activate(assets_observed, scenario_reviewed, approved_fs_game)
{
    if (!isdefined(assets_observed) || assets_observed != true ||
        !isdefined(scenario_reviewed) || scenario_reviewed != true ||
        !private_context(approved_fs_game) || !isplayer(self) || !isalive(self) ||
        !isdefined(level.players) || level.players.size != 1 || level.players[0] != self ||
        isdefined(level.sdk_raygun_pap_registration)) return false;
    base = "sdk_raygun_zm";
    pap = "sdk_raygun_pap_zm";
    upgraded = "sdk_raygun_zm+sdk_raygun_pap_zm";
    upgraded_fallback = getsubstr(upgraded, 0, upgraded.size - 1);
    if (self getcurrentweapon() != base || !(self hasweapon(base)) || self hasweapon(upgraded) ||
        !isdefined(self.pap) || !isdefined(level.pap) ||
        !isdefined(level.attachmentmap_basetounique) || !isdefined(level.attachmentmap_uniquetobase) ||
        isdefined(level.max_pap_func) || !isdefined(level.pap_max) || level.pap_max != 2 ||
        isdefined(level.pap[base]) || isdefined(level.pap[upgraded]) ||
        isdefined(level.pap[upgraded_fallback]) ||
        isdefined(level.attachmentmap_basetounique[base]) ||
        isdefined(level.attachmentmap_uniquetobase[pap]) || isdefined(self.pap[upgraded])) return false;
    // Retain the donor family's real prerequisite; never unlock fuses or DC.
    if (!scripts\engine\utility::flag("fuses_inserted") &&
        !scripts\cp\zombies\directors_cut::directors_cut_is_activated()) return false;
    before_base = self.pap[base];
    if (isdefined(before_base) && (!isdefined(before_base.lvl) || before_base.lvl != 1)) return false;
    state = spawnstruct();
    state.owner = self;
    state.base = base;
    state.pap = pap;
    state.upgraded = upgraded;
    state.upgraded_fallback = upgraded_fallback;
    state.fs_game = approved_fs_game;
    state.before_base = before_base;
    state.record = before_base;
    if (!isdefined(state.record))
    {
        state.record = spawnstruct();
        state.record.lvl = 1;
    }
    state.map = [];
    state.map["pap1"] = pap;
    state.stopped = false;
    state.defer_logged = false;
    state.restoration_confirmed = false;
    state.level_pap_written = false;
    state.base_map_written = false;
    state.unique_map_written = false;
    state.player_base_written = false;
    state.player_upgraded_written = false;
    // Publish the state before the first owned write; no yield during binding.
    level.sdk_raygun_pap_registration = state;
    level.pap[base] = base;
    state.level_pap_written = true;
    level.attachmentmap_basetounique[base] = state.map;
    state.base_map_written = true;
    level.attachmentmap_uniquetobase[pap] = "pap1";
    state.unique_map_written = true;
    self.pap[base] = state.record;
    state.player_base_written = true;
    self.pap[upgraded] = state.record;
    state.player_upgraded_written = true;
    // Deliberately no level.pap[upgraded] entry: the stock eligibility path
    // rejects a second private PAP. Retail pickup alone increments lvl 1 -> 2.
    level thread watch_context(state);
    level thread game_end(state);
    self thread departed(state);
    print("[SDK raygun PAP] BINDINGS_REGISTERED; base=sdk_raygun_zm; pap=sdk_raygun_pap_zm; semantic_max_tier=1; native_base_level=1; native_pap_level=2; callbacks_changed=0; transaction_pending=1; runtime_ready=0.");
    return true;
}

private_context(approved_fs_game)
{
    if (!isdefined(approved_fs_game) || approved_fs_game == "" ||
        approved_fs_game == "mods/sdk_original_rig_probe" || approved_fs_game == "mods/bo3_zombies_hud") return false;
    return getdvarint("dedicated") && getdvarint("sdk_raygun_pap_enable") == 1 &&
        !getdvarint("sdk_raygun_pap_stop") && getdvar("mapname") == "cp_zmb" &&
        getdvar("g_gametype") == "zombie" && getdvar("fs_game") == approved_fs_game &&
        getdvarint("sv_lanOnly") == 1 && getdvar("g_password") != "" &&
        getdvarint("net_port") == 27116 && getdvarint("sv_maxclients") == 1 &&
        getdvarint("sv_cheats") == 0 && getdvarint("g_inactivity") == 0;
}

watch_context(state)
{
    level endon("sdk_raygun_pap_stopped");
    for (;;)
    {
        if (state.stopped) return;
        if (!isdefined(level.sdk_raygun_pap_registration) || level.sdk_raygun_pap_registration != state ||
            !private_context(state.fs_game) || isdefined(level.max_pap_func) ||
            !isdefined(level.pap_max) || level.pap_max != 2 ||
            isdefined(level.pap[state.upgraded]) || isdefined(level.pap[state.upgraded_fallback]) ||
            !isdefined(level.players) || level.players.size != 1 ||
            !isdefined(state.owner) || level.players[0] != state.owner)
        {
            if (stop(state, "context_changed")) return;
        }
        wait 0.05;
    }
}

game_end(state)
{
    level endon("sdk_raygun_pap_stopped");
    level waittill("game_ended");
    stop(state, "game_ended");
}

departed(state)
{
    level endon("sdk_raygun_pap_stopped");
    self waittill("disconnect");
    stop(state, "owner_disconnect");
}

owned_bindings(state)
{
    if (!isdefined(level.sdk_raygun_pap_registration) || level.sdk_raygun_pap_registration != state) return false;
    if (state.level_pap_written && (!isdefined(level.pap[state.base]) || level.pap[state.base] != state.base)) return false;
    if (state.base_map_written && (!isdefined(level.attachmentmap_basetounique[state.base]) ||
        level.attachmentmap_basetounique[state.base] != state.map)) return false;
    if (state.unique_map_written && (!isdefined(level.attachmentmap_uniquetobase[state.pap]) ||
        level.attachmentmap_uniquetobase[state.pap] != "pap1")) return false;
    if (isdefined(state.owner))
    {
        if (!isdefined(state.owner.pap)) return false;
        if (state.player_base_written && (!isdefined(state.owner.pap[state.base]) || state.owner.pap[state.base] != state.record)) return false;
        if (state.player_upgraded_written && (!isdefined(state.owner.pap[state.upgraded]) || state.owner.pap[state.upgraded] != state.record)) return false;
    }
    return true;
}

stop(state, reason)
{
    if (state.stopped) return true;
    // Never remove the alias used by retail pickup while its machine owns the
    // transaction. No yield or paid-machine replacement occurs in this seam.
    if (reason != "game_ended" && reason != "owner_disconnect" &&
        isdefined(state.owner) && isdefined(state.owner.paping_weapon))
    {
        if (!state.defer_logged)
            print("[SDK raygun PAP] RESTORE_DEFERRED; reason=retail_transaction_in_flight; runtime_ready=0.");
        state.defer_logged = true;
        return false;
    }
    state.stopped = true;
    // Verify every remaining owned reference before reverting any key.
    if (!owned_bindings(state))
    {
        print("[SDK raygun PAP] RESTORE_PENDING; reason=external_binding_change; private_keys_preserved=1; runtime_ready=0.");
        return true;
    }
    if (state.level_pap_written) level.pap[state.base] = undefined;
    if (state.base_map_written) level.attachmentmap_basetounique[state.base] = undefined;
    if (state.unique_map_written) level.attachmentmap_uniquetobase[state.pap] = undefined;
    if (isdefined(state.owner))
    {
        if (state.player_base_written) state.owner.pap[state.base] = state.before_base;
        if (state.player_upgraded_written) state.owner.pap[state.upgraded] = undefined;
    }
    state.restoration_confirmed = true;
    print("[SDK raygun PAP] BINDINGS_RESTORED; reason=" + reason + "; callbacks_changed=0; currency_ammo_weapons_changed=0; transaction_pending=1; runtime_ready=0.");
    // Exact root ownership was checked above; no yield permits a replacement
    // between that check, the dictionary restoration and this root clear.
    level.sdk_raygun_pap_registration = undefined;
    // Endon may terminate this caller. Only this owned cleanup notifies globally;
    // a lost/replaced root preserves all keys and never stops foreign listeners.
    level notify("sdk_raygun_pap_stopped");
    return true;
}
