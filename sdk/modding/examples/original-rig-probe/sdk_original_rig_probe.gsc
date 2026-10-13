// Original two-bone experiment. Source calls are not rendering/motion evidence.
// The external native fixture owns fresh engine protection and restoration.
init()
{
    if (!getdvarint("dedicated") || !getdvarint("sdk_original_rig_probe_enable") ||
        getdvar("mapname") != "cp_zmb" || getdvar("fs_game") != "mods/sdk_original_rig_probe" ||
        getdvarint("sv_lanOnly") != 1 || getdvar("g_password") == "" ||
        getdvarint("net_port") == 27016 || getdvarint("sv_cheats") != 0 ||
        isdefined(level.sdk_original_rig_probe)) return;
    mode = getdvar("sdk_original_rig_probe_mode");
    if (mode != "DISPLAY" && mode != "ANIMATE") return;
    print("[SDK original rig] PRECACHE_BEGIN; mode=" + mode + "; runtime_pending=1.");
    // Retail animatedmodels precaches before its first wait. Keep this phase.
    precachemodel("paris_doom_skin_two_bone_first_a");
    precachemodel("paris_doom_skin_two_bone_second_a");
    if (mode == "ANIMATE") precachempanim("paris_original_probe_bend");
    state = spawnstruct();
    state.mode = mode;
    state.actors = [];
    state.placed = false;
    state.stopped = false;
    level.sdk_original_rig_probe = state;
    level thread connections(state);
    level thread shutdown(state);
    level thread stop_requested(state);
    print("[SDK original rig] PRECACHE_RETURNED; mode=" + mode + "; registry_pending=1.");
}

connections(state)
{
    level endon("game_ended");
    level endon("sdk_original_rig_probe_stopped");
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
    self waittill("spawned_player");
    while (!intro_ready() || (isdefined(self.controlsfrozen) && self.controlsfrozen)) wait 0.1;
    if (state.stopped || state.placed) return;
    // No yield while reserving/placing the shared scene.
    state.placed = true;
    angles = self getplayerangles();
    facing = (0, angles[1], 0);
    center = self.origin + anglestoforward(facing) * 160 + (0, 0, 48);
    right = anglestoright(facing);
    for (i = 0; i < 3; i++)
    {
        origin = center + right * ((i - 1) * 64);
        actor = spawn("script_model", origin);
        if (!isdefined(actor))
        {
            print("[SDK original rig] FAIL; reason=spawn; actor=" + i + ".");
            stop(state);
            return;
        }
        state.actors[state.actors.size] = actor;
        actor.angles = facing;
        actor.scale = 3;
        model = "paris_doom_skin_two_bone_first_a";
        if (i == 2) model = "paris_doom_skin_two_bone_second_a";
        actor setmodel(model);
        print("[SDK original rig] MODEL_CALL_RETURNED; actor=" + i + "; entity=" + actor getentitynumber() + "; model=" + model + "; origin=" + origin + "; angles=" + facing + "; scale=3; pixels_pending=1.");
    }
    print("[SDK original rig] DISPLAY_READY; mode=" + state.mode + "; time_ms=" + gettime() + "; camera_origin=" + self.origin + "; camera_angles=" + angles + "; pixels_pending=1.");
    level thread playback(state);
}

intro_ready()
{
    return isdefined(level.flag) && isdefined(level.flag["intro_gesture_done"]) &&
        level.flag["intro_gesture_done"];
}

playback(state)
{
    level endon("game_ended");
    level endon("sdk_original_rig_probe_stopped");
    for (;;)
    {
        if (state.mode == "ANIMATE" && getdvarint("sdk_original_rig_probe_play"))
        {
            // One engine playback request each; no pose/rotation timer or note synthesis.
            for (i = 1; i < 3; i++)
            {
                print("[SDK original rig] PLAY_BEGIN; actor=" + i + "; entity=" + state.actors[i] getentitynumber() + "; clip=paris_original_probe_bend; time_ms=" + gettime() + ".");
                state.actors[i] scriptmodelplayanim("paris_original_probe_bend");
                print("[SDK original rig] PLAY_CALL_RETURNED; actor=" + i + "; time_ms=" + gettime() + "; motion_pending=1.");
            }
            state.mode = "PLAY_REQUESTED";
        }
        wait 0.1;
    }
}

stop_requested(state)
{
    level endon("game_ended");
    level endon("sdk_original_rig_probe_stopped");
    while (!getdvarint("sdk_original_rig_probe_stop")) wait 0.1;
    stop(state);
}

stop(state)
{
    if (state.stopped) return;
    state.stopped = true;
    foreach (actor in state.actors)
    {
        if (isdefined(actor)) actor delete();
    }
    state.actors = [];
    print("[SDK original rig] STOPPED; entities_deleted=1; player_state_changed=0.");
    // This notification can end the calling playback thread too.
    level notify("sdk_original_rig_probe_stopped");
}

shutdown(state)
{
    level endon("sdk_original_rig_probe_stopped");
    level waittill("game_ended");
    stop(state);
}
