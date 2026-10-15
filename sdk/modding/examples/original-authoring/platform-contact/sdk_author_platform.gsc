// Project-specific GSC content seam, not a native ABI or universal SDK bus.
// The separate fixture owns protection, frozen P, physics and the one Use driver.
init()
{
    if (context()) precachemodel("sdk_author_platform_model");
}

context()
{
    return getdvarint("dedicated") && getdvarint("sdk_author_platform_enable") == 1 &&
        getdvar("mapname") == "cp_zmb" && getdvar("fs_game") == "mods/sdk_author_platform" &&
        getdvarint("net_port") != 27016 && getdvarint("sv_maxclients") == 1 &&
        getdvarint("sv_lanOnly") == 1 && getdvar("g_password") != "" &&
        getdvarint("sv_cheats") == 0 && getdvarint("g_inactivity") == 0;
}

// GSC caller passes the real frozen player origin after protection/intro/ground.
// No visual is created by init, first spawn or an external/native guessed call.
create_visual(player, anchor, token)
{
    if (!context() || !isdefined(token) || !isdefined(anchor) ||
        !isdefined(player) || !isplayer(player) || !isalive(player) ||
        !isdefined(level.players) || level.players.size != 1 || level.players[0] != player ||
        isdefined(level.sdk_author_platform)) return undefined;
    actor = spawn("script_model", anchor + (0, 0, 96));
    if (!isdefined(actor)) return undefined;
    actor.angles = (0, 0, 0);
    actor.scale = 1;
    actor setmodel("sdk_author_platform_model");
    actor notsolid();
    actor makeusable();
    actor setuserange(160);
    actor setusefov(360);
    actor sethintstring("Confirm platform interaction");
    state = spawnstruct();
    state.token = token;
    state.owner = player;
    state.anchor = anchor;
    state.model = actor;
    state.entity = actor getentitynumber();
    state.instance_id = gettime();
    state.origin = actor.origin;
    state.uses = 0;
    state.armed = false;
    state.armed_ms = -1;
    state.last_player = undefined;
    state.last_token = undefined;
    state.last_entity = undefined;
    state.last_use_ms = -1;
    state.stopped = false;
    actor.sdk_author_platform_token = token;
    actor.sdk_author_platform_instance = state.instance_id;
    level.sdk_author_platform = state;
    actor thread interact(state);
    level thread shutdown(state);
    level thread watch_context(state);
    player thread departed(state);
    print("[SDK author platform] SCENE_READY; token=" + token + "; entity=" + state.entity + "; instance=" + state.instance_id + "; uses=0; physics_unverified=1; runtime_ready=0.");
    return state;
}

owned(state)
{
    return isdefined(state) && isdefined(level.sdk_author_platform) && level.sdk_author_platform == state &&
        !state.stopped && isdefined(state.model) && state.model.sdk_author_platform_token == state.token &&
        state.model.sdk_author_platform_instance == state.instance_id && state.model getentitynumber() == state.entity;
}

// Call once only after the fixture's F1 movement and released-stable interval.
// This arms a future real trigger; it neither reads nor simulates an input edge.
arm_use(state, player)
{
    if (!context() || !owned(state) || player != state.owner || !isdefined(player) ||
        !isplayer(player) || !isalive(player) || state.armed || state.uses != 0) return false;
    state.armed_ms = gettime();
    state.armed = true;
    return true;
}

read_state(token)
{
    if (!isdefined(level.sdk_author_platform)) return undefined;
    state = level.sdk_author_platform;
    if (!owned(state) || state.token != token) return undefined;
    return state;
}

interact(state)
{
    level endon("game_ended");
    self endon("death");
    for (;;)
    {
        self waittill("trigger", player);
        if (!context() || !owned(state) || state.model != self || !state.armed || state.uses != 0 ||
            !isdefined(player) || player != state.owner || !isplayer(player) || !isalive(player) ||
            distancesquared(player.origin, self.origin) > 25600 || gettime() <= state.armed_ms) continue;
        state.armed = false;
        state.last_player = player;
        state.last_token = state.token;
        state.last_entity = self getentitynumber();
        state.last_use_ms = gettime();
        state.uses++;
        player iprintln("Platform interaction: 1 / 1");
        print("[SDK author platform] USED; token=" + state.token + "; entity=" + state.entity + "; instance=" + state.instance_id + "; uses=1; retail_trigger=1; runtime_ready=0.");
    }
}

// The fixture keeps the visual alive through F0/F1/F2 and calls this afterwards.
// This owns only the visual. It never constructs or clears a physics body.
teardown(state)
{
    if (!isdefined(state) || state.stopped) return false;
    if (!owned(state))
    {
        state.stopped = true;
        print("[SDK author platform] RESTORE_PENDING; reason=ownership_changed; runtime_ready=0.");
        return false;
    }
    state.stopped = true;
    state.model delete();
    state.model = undefined;
    level.sdk_author_platform = undefined;
    print("[SDK author platform] VISUAL_REMOVED; token=" + state.token + "; uses=" + state.uses + "; runtime_ready=0.");
    return true;
}

shutdown(state)
{
    level waittill("game_ended");
    teardown(state);
}

departed(state)
{
    self waittill("disconnect");
    teardown(state);
}

watch_context(state)
{
    level endon("game_ended");
    while (!state.stopped)
    {
        if (!context() || !owned(state)) { teardown(state); return; }
        wait 0.1;
    }
}
