// Original, opt-in BO3-inspired mechanic using an IW7 retail token.
// No BO3 asset is included. The separate agent fixture owns engine protection.
init()
{
    if (!getdvarint("dedicated") || !getdvarint("sdk_soulbox_demo_enable") ||
        getdvar("mapname") != "cp_zmb" || getdvarint("sv_lanOnly") != 1 ||
        getdvar("g_password") == "" || getdvarint("net_port") == 27016 ||
        getdvarint("sv_cheats") != 0 || isdefined(level.sdk_soulbox_demo)) return;
    precachemodel("zmb_coin_alien");
    state = spawnstruct();
    state.model = undefined;
    state.phase = "collecting";
    state.souls = 0;
    state.goal = 6;
    state.radius = 384;
    state.rewards = 0;
    state.repeat_uses = 0;
    state.stopped = false;
    level.sdk_soulbox_demo = state;
    level thread connections(state);
    level thread shutdown(state);
    print("[SDK Soul Box] ARMED; map=cp_zmb; goal=6; radius=384; model=zmb_coin_alien; asset_origin=IW7; mechanic=BO3-inspired.");
}

connections(state)
{
    level endon("game_ended");
    for (;;)
    {
        level waittill("connected", player);
        if (!isdefined(player) || isdefined(player.sdk_soulbox_demo)) continue;
        personal = spawnstruct();
        personal.hud = [];
        personal.last_use = -1000;
        personal.contributed = 0;
        player.sdk_soulbox_demo = personal;
        player thread kills(state);
        player thread spawns(state, personal);
        player thread departed(personal);
    }
}

spawns(state, personal)
{
    self endon("disconnect");
    level endon("game_ended");
    for (;;)
    {
        self waittill("spawned_player");
        while (!intro_ready() || (isdefined(self.controlsfrozen) && self.controlsfrozen)) wait 0.1;
        if (state.stopped) return;
        // A respawn rebuilds the two HUDs instead of keeping stale handles or
        // adding another kill watcher. The team object/progress survives.
        clear_hud(personal);
        for (i = 0; i < 2; i++)
        {
            hud = newclienthudelem(self);
            hud.horzalign = "left";
            hud.vertalign = "top";
            hud.alignx = "left";
            hud.aligny = "top";
            hud.x = 42;
            hud.y = 216 + i * 20;
            hud.fontscale = 1.05 - i * 0.15;
            hud.foreground = true;
            hud.color = (0.35, 0.9, 1);
            hud.alpha = 1;
            personal.hud[i] = hud;
        }
        if (!isdefined(state.model)) self place(state);
        self render(state);
    }
}

intro_ready()
{
    return isdefined(level.flag) && isdefined(level.flag["intro_gesture_done"]) &&
        level.flag["intro_gesture_done"];
}

place(state)
{
    angles = self getplayerangles();
    origin = self.origin + anglestoforward((0, angles[1], 0)) * 96 + (0, 0, 36);
    model = spawn("script_model", origin);
    if (!isdefined(model))
    {
        state.stopped = true;
        print("[SDK Soul Box] FAIL; reason=model_creation;");
        return;
    }
    // Commit before another player's spawn thread can place a second object.
    state.model = model;
    model.angles = (0, angles[1], 0);
    model.scale = 2;
    model setmodel("zmb_coin_alien");
    model setscriptablepartstate("fx", "red");
    model makeusable();
    model sethintstring("Fill the Soul Box with nearby zombie kills");
    model thread interact(state);
    print("[SDK Soul Box] READY; entity=" + model getentitynumber() + "; origin=" + origin + "; souls=0; rewards=0; pixels_pending=1.");
}

kills(state)
{
    self endon("disconnect");
    level endon("game_ended");
    for (;;)
    {
        // Retail gametype_zombie notifies the actual player credited with this
        // kill. Its level event lacks the actor and killer and is not used here.
        self waittill("zombie_killed", zombie, death_origin, weapon, means);
        if (state.stopped || state.phase != "collecting" || !isdefined(state.model) ||
            !isdefined(zombie) || !isdefined(zombie.agent_type) || zombie.agent_type != "generic_zombie" ||
            !isdefined(zombie.team) || zombie.team != "axis" ||
            (isdefined(zombie.is_reserved) && zombie.is_reserved) ||
            (isdefined(zombie.died_poorly) && zombie.died_poorly) || means == "MOD_SUICIDE" ||
            !isdefined(death_origin) || distancesquared(death_origin, state.model.origin) > state.radius * state.radius) continue;
        // No waits and no permanent field on recycled agents. Retail owns the
        // death, quota, loot and respawn ledger; this listener only counts.
        state.souls++;
        self.sdk_soulbox_demo.contributed++;
        state.last_death_origin = death_origin;
        state.model.angles = (0, (state.souls * 60) % 360, 0);
        if (state.souls >= state.goal)
        {
            state.phase = "ready";
            state.model setscriptablepartstate("fx", "green");
            state.model sethintstring("Collect ammunition reward");
        }
        render_all(state);
        level notify("sdk_soulbox_demo_progress", state.souls, state.phase);
        print("[SDK Soul Box] SOUL; total=" + state.souls + "/" + state.goal + "; distance=" + distance(death_origin, state.model.origin) + "; phase=" + state.phase + "; means=" + means + ".");
    }
}

interact(state)
{
    level endon("game_ended");
    self endon("death");
    for (;;)
    {
        self waittill("trigger", player);
        if (state.stopped || !isdefined(player) || !isplayer(player) || !isalive(player) ||
            (isdefined(player.inlaststand) && player.inlaststand) ||
            !isdefined(player.sdk_soulbox_demo) || distancesquared(player.origin, self.origin) > 14400) continue;
        personal = player.sdk_soulbox_demo;
        if (gettime() - personal.last_use < 750) continue;
        personal.last_use = gettime();
        if (state.phase == "collecting")
        {
            player iprintln("Soul Box: " + state.souls + "/" + state.goal + " nearby zombie souls.");
            continue;
        }
        if (state.phase == "claimed")
        {
            state.repeat_uses++;
            print("[SDK Soul Box] REPEAT_USE; accepted=" + state.repeat_uses + "; rewards=" + state.rewards + ".");
            continue;
        }
        if (state.phase != "ready") continue;
        weapon = player getcurrentweapon();
        if (weapon == "" || weapon == "none" || weaponclipsize(weapon) <= 0 || weaponmaxammo(weapon) <= 0 ||
            issubstr(weapon, "alt_"))
        {
            player iprintln("Equip a firearm to claim the ammunition reward.");
            continue;
        }
        // Lock the shared one-time claim before any possible yield/notification.
        state.phase = "claimed";
        state.rewards++;
        before_clip = player getweaponammoclip(weapon);
        before_stock = player getweaponammostock(weapon);
        state.reward_before_clip = before_clip;
        state.reward_before_stock = before_stock;
        player givemaxammo(weapon);
        player setweaponammoclip(weapon, weaponclipsize(weapon));
        if (issubstr(weapon, "akimbo")) player setweaponammoclip(weapon, weaponclipsize(weapon), "left");
        state.reward_weapon = weapon;
        state.reward_clip = player getweaponammoclip(weapon);
        state.reward_stock = player getweaponammostock(weapon);
        state.reward_clip_capacity = weaponclipsize(weapon);
        state.reward_max_ammo = weaponmaxammo(weapon);
        state.model setscriptablepartstate("fx", "blue");
        state.model sethintstring("Soul Box complete");
        player iprintln("Soul Box complete! Equipped firearm ammunition refilled.");
        render_all(state);
        level notify("sdk_soulbox_demo_claimed", player, weapon);
        print("[SDK Soul Box] REWARD; count=" + state.rewards + "; weapon=" + weapon + "; clip_before=" + before_clip + "; clip_after=" + state.reward_clip + "; stock_before=" + before_stock + "; stock_after=" + state.reward_stock + ".");
    }
}

render_all(state)
{
    if (!isdefined(level.players)) return;
    foreach (player in level.players)
        if (isdefined(player) && isdefined(player.sdk_soulbox_demo)) player render(state);
}

render(state)
{
    personal = self.sdk_soulbox_demo;
    if (personal.hud.size != 2 || !isdefined(personal.hud[0]) || !isdefined(personal.hud[1])) return;
    personal.hud[0] settext("SOUL BOX  |  " + state.souls + " / " + state.goal);
    text = "Kill ordinary zombies near the glowing token";
    if (state.phase == "ready") text = "Box filled. Use the token to claim ammunition";
    if (state.phase == "claimed") text = "Completed  |  Ammunition reward claimed";
    personal.hud[1] settext(text);
    personal.rendered_souls = state.souls;
    personal.rendered_phase = state.phase;
}

departed(personal)
{
    level endon("game_ended");
    self waittill("disconnect");
    clear_hud(personal);
}

clear_hud(personal)
{
    foreach (hud in personal.hud) if (isdefined(hud)) hud destroy();
    personal.hud = [];
}

shutdown(state)
{
    level waittill("game_ended");
    state.stopped = true;
    if (isdefined(state.model)) state.model delete();
    state.model = undefined;
    if (isdefined(level.players)) foreach (player in level.players)
    {
        if (!isdefined(player) || !isdefined(player.sdk_soulbox_demo)) continue;
        clear_hud(player.sdk_soulbox_demo);
        player.sdk_soulbox_demo = undefined;
    }
    print("[SDK Soul Box] CLEANUP; souls=" + state.souls + "; rewards=" + state.rewards + ".");
}
