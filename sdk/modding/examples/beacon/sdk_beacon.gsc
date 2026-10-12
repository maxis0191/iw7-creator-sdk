// Original SDK example; opt-in candidate only, never automatically deployed.
// The external agent harness owns fresh engine protection and restoration.
init()
{
    if (!getdvarint("dedicated") || !getdvarint("sdk_beacon_enable") ||
        getdvar("mapname") != "cp_zmb" || getdvar("fs_game") != "mods/sdk_beacon") return;
    if (isdefined(level.sdk_beacon)) return;
    precachemodel("paris_model_probe");
    state = spawnstruct();
    state.model = undefined;
    state.total = 0;
    state.stopped = false;
    level.sdk_beacon = state;
    level thread connections(state);
    level thread shutdown(state);
    print("[SDK beacon] initialized; version=0.1.0; gameplay_pending=1.");
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
    while (!scripts\engine\utility::flag_exist("intro_gesture_done") ||
           !scripts\engine\utility::flag("intro_gesture_done") ||
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
    self.sdk_beacon = personal;
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
            print("[SDK beacon] model creation failed.");
            return;
        }
        state.model.angles = (0, 0, 0);
        state.model.sdk_beacon_total = 0;
        state.model.sdk_beacon_instance = gettime();
        state.model setmodel("paris_model_probe");
        state.model makeusable();
        state.model sethintstring("Activate beacon");
        state.model thread interact(state);
        print("[SDK beacon] ready; entity=" + state.model getentitynumber() + "; total=0.");
    }
    self render(state);
}

interact(state)
{
    level endon("game_ended");
    self endon("death");
    for (;;)
    {
        self waittill("trigger", player);
        if (state.stopped || !isdefined(player) || !isplayer(player) || !isalive(player) ||
            !isdefined(player.sdk_beacon) || distancesquared(player.origin, self.origin) > 14400) continue;
        personal = player.sdk_beacon;
        if (gettime() - personal.last_use < 750 || personal.uses >= 9999 || state.total >= 9999) continue;
        personal.last_use = gettime();
        personal.uses++;
        state.total++;
        self.sdk_beacon_total = state.total;
        self.angles = (0, (state.total % 12) * 30, 0);
        // Event-driven updates only; no per-frame reliable text traffic.
        foreach (observer in level.players)
        {
            if (isdefined(observer) && isdefined(observer.sdk_beacon)) observer render(state);
        }
        player notify("sdk_beacon_used", self, state.total, personal.uses);
        print("[SDK beacon] activation; entity=" + self getentitynumber() + "; total=" + state.total + "; personal=" + personal.uses + "; rendering_pending=1.");
    }
}

render(state)
{
    if (isdefined(self.sdk_beacon.hud))
    {
        self.sdk_beacon.hud settext("Beacon | You: " + self.sdk_beacon.uses + " | Team: " + state.total);
        // Delivery intent for an external fixture; these are not pixel witnesses.
        self.sdk_beacon.rendered_total = state.total;
        self.sdk_beacon.rendered_uses = self.sdk_beacon.uses;
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
        if (!isdefined(player) || !isdefined(player.sdk_beacon)) continue;
        if (isdefined(player.sdk_beacon.hud)) player.sdk_beacon.hud destroy();
        player.sdk_beacon = undefined;
    }
    print("[SDK beacon] map cleanup complete.");
}
