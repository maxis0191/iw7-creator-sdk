// Neutral private SDK fixture. The external harness owns protection and input.
// No client asset is requested, precached or played by this script.
init()
{
    port = getdvarint("net_port");
    if (!getdvarint("dedicated") || !getdvarint("paris_isolated_lab") ||
        getdvar("fs_game") != "mods/sdk_original_sound_v1" || getdvar("mapname") != "cp_zmb" ||
        port < 27100 || port > 27999 || getdvar("g_password") == "" ||
        !getdvarint("sv_lanOnly") || getdvarint("sv_cheats") != 0) return;
    if (isdefined(level.sdk_original_sound_v1)) return;
    state = spawnstruct();
    state.stopped = false;
    level.sdk_original_sound_v1 = state;
    level thread shutdown(state);
    print("[SDK original sound] initialized; version=0.1.0; playback_requested=0; runtime_ready=0.");
}

shutdown(state)
{
    // Do not endon this event: this thread performs its own one-shot cleanup.
    // Map unload also discards the level VM. No per-player state is allocated.
    level waittill("game_ended");
    state.stopped = true;
    if (isdefined(level.sdk_original_sound_v1) && level.sdk_original_sound_v1 == state)
        level.sdk_original_sound_v1 = undefined;
    print("[SDK original sound] stopped; player_state_allocated=0; playback_requested=0.");
}
