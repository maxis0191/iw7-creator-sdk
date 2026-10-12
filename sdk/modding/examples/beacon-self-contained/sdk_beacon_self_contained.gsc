// Separate original SDK variant; script dependencies only, not a self-contained asset pack.
// Opt-in source candidate; no automatic deployment or current Creator adapter support.
// The external agent harness owns fresh engine protection and restoration.
init()
{
    if (!getdvarint("dedicated") || !getdvarint("sdk_beacon_self_contained_enable") ||
        getdvar("mapname") != "cp_zmb" || getdvar("fs_game") != "mods/sdk_beacon_self_contained") return;
    if (isdefined(level.sdk_beacon_self_contained)) return;
    precachemodel("paris_model_probe");
    state = spawnstruct();
    state.model = undefined;
    state.total = 0;
    state.stopped = false;
    level.sdk_beacon_self_contained = state;
    level thread connections(state);
    level thread shutdown(state);
    print("[SDK beacon self-contained] initialized; version=0.1.0; gameplay_pending=1.");
}

connections(state)
{
    level endon("game_ended");
    for (;;)
    {
        level waittill("connected", player);
        player thread joined(state);
    }
}

joined(state)
{
    self endon("disconnect");
    level endon("game_ended");
    self waittill("spawned_player");
    // Avoid placing the shared object during the stock intro/cinematic.
    while (!intro_flag_ready() ||
           (isdefined(self.controlsfrozen) && self.controlsfrozen)) wait 0.1;
    if (state.stopped) return;
    personal = spawnstruct();
    personal.uses = 0;
    personal.last_use = -1000;
    personal.hud = newclienthudelem(self);
    personal.hud.horzalign = "left";
    personal.hud.vertalign = "top";
    personal.hud.alignx = "left";
    personal.hud.aligny = "top";
    personal.hud.x = 42;
    personal.hud.y = 140;
    personal.hud.fontscale = 1;
    personal.hud.foreground = true;
    self.sdk_beacon_self_contained = personal;
    self thread departed(personal);
    if (!isdefined(state.model))
    {
        angles = self getplayerangles();
        origin = self.origin + anglestoforward((0, angles[1], 0)) * 96 + (0, 0, 32);
        state.model = spawn("script_model", origin);
        if (!isdefined(state.model))
        {
            state.stopped = true;
            personal.hud destroy();
            personal.hud = undefined;
            print("[SDK beacon self-contained] model creation failed.");
            return;
        }
        state.model.angles = (0, 0, 0);
        state.model.sdk_beacon_self_contained_total = 0;
        state.model.sdk_beacon_self_contained_instance = gettime();
        state.model setmodel("paris_model_probe");
        state.model makeusable();
        state.model sethintstring("Activate beacon");
        state.model thread interact(state);
        print("[SDK beacon self-contained] ready; entity=" + state.model getentitynumber() + "; total=0.");
    }
    self render(state);
}

// Preserve the retail definedness guards before reading the flag value.
// This function only reads state and never initializes or changes retail flags.
intro_flag_ready()
{
    if (!isdefined(level.flag)) return 0;
    if (!isdefined(level.flag["intro_gesture_done"])) return 0;
    return level.flag["intro_gesture_done"];
}

interact(state)
{
    level endon("game_ended");
    self endon("death");
    for (;;)
    {
        self waittill("trigger", player);
        if (state.stopped || !isdefined(player) || !isplayer(player) || !isalive(player) ||
            !isdefined(player.sdk_beacon_self_contained) || distancesquared(player.origin, self.origin) > 14400) continue;
        personal = player.sdk_beacon_self_contained;
        if (gettime() - personal.last_use < 750 || personal.uses >= 9999 || state.total >= 9999) continue;
        personal.last_use = gettime();
        personal.uses++;
        state.total++;
        self.sdk_beacon_self_contained_total = state.total;
        self.angles = (0, (state.total % 12) * 30, 0);
        // Event-driven updates only; no per-frame reliable text traffic.
        foreach (observer in level.players)
        {
            if (isdefined(observer) && isdefined(observer.sdk_beacon_self_contained)) observer render(state);
        }
        player notify("sdk_beacon_self_contained_used", self, state.total, personal.uses);
        print("[SDK beacon self-contained] activation; entity=" + self getentitynumber() + "; total=" + state.total + "; personal=" + personal.uses + "; rendering_pending=1.");
    }
}

render(state)
{
    if (isdefined(self.sdk_beacon_self_contained.hud))
    {
        self.sdk_beacon_self_contained.hud settext("Beacon | You: " + self.sdk_beacon_self_contained.uses + " | Team: " + state.total);
        // Delivery intent for an external fixture; these are not pixel witnesses.
        self.sdk_beacon_self_contained.rendered_total = state.total;
        self.sdk_beacon_self_contained.rendered_uses = self.sdk_beacon_self_contained.uses;
    }
}

departed(personal)
{
    level endon("game_ended");
    self waittill("disconnect");
    if (isdefined(personal.hud)) personal.hud destroy();
    personal.hud = undefined;
}

shutdown(state)
{
    level waittill("game_ended");
    state.stopped = true;
    if (isdefined(state.model)) state.model delete();
    state.model = undefined;
    foreach (player in level.players)
    {
        if (!isdefined(player) || !isdefined(player.sdk_beacon_self_contained)) continue;
        if (isdefined(player.sdk_beacon_self_contained.hud)) player.sdk_beacon_self_contained.hud destroy();
        player.sdk_beacon_self_contained = undefined;
    }
    print("[SDK beacon self-contained] map cleanup complete.");
}
