// Original editable author source. Runtime/compiler evidence is pending.
init()
{
    if (!context() || isdefined(level.sdk_turn_prism)) return;
    precachemodel("sdk_turn_prism_model");
    state = spawnstruct();
    state.model = undefined;
    state.stopped = false;
    state.uses = 0;
    state.last_use = -1000;
    state.armed = false;
    state.ticket = 0;
    level.sdk_turn_prism = state;
    level thread connections(state);
    level thread shutdown(state);
    level thread watch_context(state);
    print("[Author sdk_turn_prism] initialized; runtime_ready=0.");
}

context()
{
    return getdvarint("dedicated") && getdvarint("sdk_turn_prism_enable") == 1 &&
        getdvar("mapname") == "cp_zmb" && getdvar("fs_game") == "mods/sdk_turn_prism" &&
        getdvarint("net_port") != 27016 && getdvarint("sv_lanOnly") == 1 &&
        getdvar("g_password") != "" && getdvarint("sv_cheats") == 0;
}

connections(state)
{
    level endon("game_ended");
    for (;;)
    {
        level waittill("connected", player);
        if (!state.stopped && isdefined(player)) player thread place(state);
    }
}

place(state)
{
    self endon("disconnect");
    level endon("game_ended");
    self waittill("spawned_player");
    while (!isdefined(level.flag) || !isdefined(level.flag["intro_gesture_done"]) ||
           !level.flag["intro_gesture_done"] || (isdefined(self.controlsfrozen) && self.controlsfrozen)) wait 0.1;
    if (state.stopped || !context() || isdefined(state.model) ||
        !isdefined(level.sdk_turn_prism) || level.sdk_turn_prism != state) return;
    angles = self getplayerangles();
    origin = self.origin + anglestoforward((0, angles[1], 0)) * 96 + (0, 0, 32);
    actor = spawn("script_model", origin);
    if (!isdefined(actor)) return;
    actor.angles = (0, 0, 0);
    actor setmodel("sdk_turn_prism_model");
    actor makeusable();
    actor setuserange(120);
    actor setusefov(360);
    actor sethintstring("Rotate the prism");
    state.model = actor;
    actor thread interact(state);
    print("[Author sdk_turn_prism] placed; entity=" + actor getentitynumber() + "; runtime_ready=0.");
}

interact(state)
{
    level endon("game_ended");
    self endon("death");
    for (;;)
    {
        self waittill("trigger", player);
        if (state.stopped || !context() || !isdefined(level.sdk_turn_prism) || level.sdk_turn_prism != state ||
            !isdefined(player) || !isplayer(player) || !isalive(player) ||
            distancesquared(player.origin, self.origin) > 14400 || gettime() - state.last_use < 750) continue;
        state.last_use = gettime();
        state.uses++;
        phase = state.uses % 4;
        self.angles = (0, phase * 90, 0);
        player iprintln("Prism direction: " + phase + " / 3");
    }
}

watch_context(state)
{
    level endon("game_ended");
    while (!state.stopped)
    {
        if (!context() || !isdefined(level.sdk_turn_prism) || level.sdk_turn_prism != state) { cleanup(state); return; }
        wait 0.1;
    }
}

shutdown(state)
{
    level waittill("game_ended");
    cleanup(state);
}

cleanup(state)
{
    if (state.stopped) return;
    state.stopped = true;
    if (!isdefined(level.sdk_turn_prism) || level.sdk_turn_prism != state) return;
    if (isdefined(state.model)) state.model delete();
    state.model = undefined;
    level.sdk_turn_prism = undefined;
}
