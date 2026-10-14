// Private stock witness addon. The original rig source and actors stay unchanged.
// The external native fixture verifies fresh engine protection and captures neutral
// before sending the real Use edge. This script never synthesizes input or pixels.
init()
{
    if (!getdvarint("dedicated") || !getdvarint("sdk_original_rig_stock_witness_enable") ||
        getdvar("mapname") != "cp_zmb" || getdvar("fs_game") != "mods/sdk_original_rig_probe" ||
        getdvarint("sv_lanOnly") != 1 || getdvar("g_password") == "" ||
        getdvarint("net_port") == 27016 || getdvarint("sv_cheats") != 0 ||
        getdvarint("g_inactivity") != 0 ||
        getdvarint("sdk_original_rig_stock_witness_stop") ||
        !getdvarint("sdk_original_rig_probe_enable") ||
        getdvar("sdk_original_rig_probe_mode") != "DISPLAY" ||
        isdefined(level.sdk_original_rig_stock_witness)) return;
    // Stock is precached before the first wait; the original owns custom precache.
    precachemodel("zmb_coin_alien");
    state = spawnstruct();
    state.actor = undefined;
    state.owner = undefined;
    state.requested = false;
    state.stopped = false;
    level.sdk_original_rig_stock_witness = state;
    level thread connections(state);
    level thread stop_requested(state);
    level thread cleanup_on(state, "game_ended");
    level thread cleanup_on(state, "sdk_original_rig_probe_stopped");
    print("[SDK rig stock witness] ARMED; model=zmb_coin_alien; ttl_ms=10000; pixels_pending=1.");
}

connections(state)
{
    level endon("game_ended");
    level endon("sdk_original_rig_probe_stopped");
    level endon("sdk_original_rig_stock_witness_stopped");
    for (;;)
    {
        level waittill("connected", player);
        if (isdefined(player)) player thread joined(state);
    }
}

joined(state)
{
    self endon("disconnect");
    level endon("game_ended");
    level endon("sdk_original_rig_probe_stopped");
    level endon("sdk_original_rig_stock_witness_stopped");
    self waittill("spawned_player");
    while (!scene_ready()) wait 0.05;
    if (state.stopped || isdefined(state.owner)) return;
    state.owner = self;
    self thread departed(state);
    self watch_use(state);
}

scene_ready()
{
    if (!isdefined(level.sdk_original_rig_probe)) return false;
    rig = level.sdk_original_rig_probe;
    if (!isdefined(rig.stopped) || rig.stopped || !isdefined(rig.placed) || !rig.placed ||
        !isdefined(rig.mode) || rig.mode != "DISPLAY" || !isdefined(rig.actors) ||
        rig.actors.size != 3) return false;
    foreach (actor in rig.actors)
    {
        if (!isdefined(actor)) return false;
    }
    return true;
}

watch_use(state)
{
    // Require a release after READY. A held button cannot create the witness.
    released = false;
    previous = true;
    print("[SDK rig stock witness] READY; use_edge_pending=1; neutral_capture_external=1.");
    for (;;)
    {
        pressed = self usebuttonpressed();
        if (!pressed) released = true;
        if (released && pressed && !previous && !state.requested && scene_ready() &&
            isalive(self) && (!isdefined(self.controlsfrozen) || !self.controlsfrozen))
        {
            // Commit the one attempt before any native call or event.
            state.requested = true;
            print("[SDK rig stock witness] USE_EDGE; time_ms=" + gettime() + ".");
            create_witness(state);
            return;
        }
        previous = pressed;
        wait 0.05;
    }
}

create_witness(state)
{
    anchor = level.sdk_original_rig_probe.actors[1];
    origin = anchor.origin;
    angles = anchor.angles;
    anchor_entity = anchor getentitynumber();
    actor = spawn("script_model", origin);
    if (!isdefined(actor))
    {
        print("[SDK rig stock witness] FAIL; reason=spawn.");
        stop(state, "spawn_failed");
        return;
    }
    // Keep the handle for cleanup before calling setmodel.
    state.actor = actor;
    actor.angles = angles;
    actor.scale = 3;
    actor setmodel("zmb_coin_alien");
    print("[SDK rig stock witness] WITNESS_CREATED; entity=" + actor getentitynumber() + "; anchor_entity=" + anchor_entity + "; model=zmb_coin_alien; origin=" + origin + "; angles=" + angles + "; scale=3; time_ms=" + gettime() + "; pixels_pending=1.");
    level thread expiry(state);
}

expiry(state)
{
    level endon("game_ended");
    level endon("sdk_original_rig_probe_stopped");
    level endon("sdk_original_rig_stock_witness_stopped");
    wait 10;
    stop(state, "ttl");
}

stop_requested(state)
{
    level endon("game_ended");
    level endon("sdk_original_rig_stock_witness_stopped");
    while (!getdvarint("sdk_original_rig_stock_witness_stop")) wait 0.05;
    stop(state, "operator_stop");
}

departed(state)
{
    level endon("game_ended");
    level endon("sdk_original_rig_stock_witness_stopped");
    self waittill("disconnect");
    stop(state, "owner_disconnect");
}

cleanup_on(state, event)
{
    level endon("sdk_original_rig_stock_witness_stopped");
    level waittill(event);
    stop(state, event);
}

stop(state, reason)
{
    if (state.stopped) return;
    state.stopped = true;
    if (isdefined(state.actor)) state.actor delete();
    state.actor = undefined;
    print("[SDK rig stock witness] STOPPED; reason=" + reason + "; original_actors_changed=0.");
    level notify("sdk_original_rig_stock_witness_stopped");
}
