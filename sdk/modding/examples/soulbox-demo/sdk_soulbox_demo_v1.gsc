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
    level thread install_kill_observer(state);
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
    // Retail CP interaction models declare these explicitly. The placement is
    // about 102.5 units from the player; unspecified native defaults are not a
    // guarantee that a visible hint can actually be used at this distance.
    model setuserange(120);
    model setusefov(360);
    model sethintstring("Fill the Soul Box with nearby zombie kills");
    model thread interact(state);
    print("[SDK Soul Box] READY; entity=" + model getentitynumber() + "; origin=" + origin + "; souls=0; rewards=0; pixels_pending=1.");
}

install_kill_observer(state)
{
    level endon("game_ended");
    while (!isdefined(level.agent_funcs) || !isdefined(level.agent_funcs["generic_zombie"]) ||
        !isdefined(level.agent_funcs["generic_zombie"]["on_killed"])) wait 0.05;
    state.original_killed = level.agent_funcs["generic_zombie"]["on_killed"];
    level.agent_funcs["generic_zombie"]["on_killed"] = ::ordinary_killed;
    print("[SDK Soul Box] KILL_OBSERVER; generic_zombie=1; original_callback_preserved=1.");
}

ordinary_killed(a0, attacker, damage, means, weapon, direction, hitloc, a7, a8)
{
    state = level.sdk_soulbox_demo;
    // The player notify resumes after the actor's script fields disappear.
    // Capture only immutable classification/origin here, in the real engine
    // killed callback, before forwarding every retail argument exactly once.
    death_origin = self.origin;
    eligible = !state.stopped && state.phase == "collecting" && isdefined(state.model) &&
        isdefined(attacker) && isplayer(attacker) && isdefined(attacker.sdk_soulbox_demo) &&
        isdefined(self.agent_type) && self.agent_type == "generic_zombie" &&
        isdefined(self.team) && self.team == "axis" &&
        (!isdefined(self.is_reserved) || !self.is_reserved) &&
        (!isdefined(self.died_poorly) || !self.died_poorly) && means != "MOD_SUICIDE" &&
        distancesquared(death_origin, state.model.origin) <= state.radius * state.radius;
    self [[ state.original_killed ]](a0, attacker, damage, means, weapon, direction, hitloc, a7, a8);
    if (eligible && !state.stopped && state.phase == "collecting" && isdefined(state.model) &&
        isdefined(attacker) && isdefined(attacker.sdk_soulbox_demo))
    {
        // No waits and no permanent field on recycled agents. Retail owns the
        // death, quota, loot and respawn ledger; this listener only counts.
        state.souls++;
        attacker.sdk_soulbox_demo.contributed++;
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
    print("[SDK Soul Box] USE_WATCH; armed=1; range=120; fov=360.");
    for (;;)
    {
        self waittill("trigger", player);
        if (state.phase == "ready") print("[SDK Soul Box] USE_EVENT; player_defined=" + isdefined(player) + ".");
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
        print("[SDK Soul Box] CLAIM_BEGIN; count=" + state.rewards + "; weapon=" + weapon + ".");
        before_clip = player getweaponammoclip(weapon);
        before_stock = player getweaponammostock(weapon);
        state.reward_before_clip = before_clip;
        state.reward_before_stock = before_stock;
        player givemaxammo(weapon);
        print("[SDK Soul Box] AMMO_STAGE; reserve_refilled=1.");
        player setweaponammoclip(weapon, weaponclipsize(weapon));
        print("[SDK Soul Box] AMMO_STAGE; clip_refilled=1.");
        if (issubstr(weapon, "akimbo")) player setweaponammoclip(weapon, weaponclipsize(weapon), "left");
        state.reward_weapon = weapon;
        state.reward_clip = player getweaponammoclip(weapon);
        print("[SDK Soul Box] CLAIM_STAGE; clip_read=1.");
        state.reward_stock = player getweaponammostock(weapon);
        print("[SDK Soul Box] CLAIM_STAGE; stock_read=1.");
        state.reward_clip_capacity = weaponclipsize(weapon);
        print("[SDK Soul Box] CLAIM_STAGE; capacity_read=1.");
        state.reward_max_ammo = weaponmaxammo(weapon);
        print("[SDK Soul Box] CLAIM_STAGE; maximum_read=1.");
        print("[SDK Soul Box] AMMO_STAGE; readback_complete=1; clip=" + state.reward_clip + "; stock=" + state.reward_stock + "; capacity=" + state.reward_clip_capacity + "; maximum=" + state.reward_max_ammo + ".");
        // Retain the ready token's observed green state. Retail uses fx/blue
        // for coin_space; that state is not qualified on this coin_alien.
        // Keep the existing usable-token hint. I ended before this late hint
        // change returned; the completion HUD/message carry the claimed state.
        print("[SDK Soul Box] CLAIM_STAGE; hint_retained=1.");
        player iprintln("Soul Box complete! Equipped firearm ammunition refilled.");
        print("[SDK Soul Box] CLAIM_STAGE; completion_printed=1.");
        render_all(state);
        print("[SDK Soul Box] CLAIM_STAGE; hud_rendered=1.");
        level notify("sdk_soulbox_demo_claimed", player, weapon);
        print("[SDK Soul Box] CLAIM_STAGE; notify_sent=1.");
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
    if (state.phase == "claimed") print("[SDK Soul Box] CLAIM_STAGE; hud_souls_set=1.");
    text = "Kill ordinary zombies near the glowing token";
    if (state.phase == "ready") text = "Box filled. Use the token to claim ammunition";
    if (state.phase == "claimed") text = "Completed  |  Ammunition reward claimed";
    personal.hud[1] settext(text);
    if (state.phase == "claimed") print("[SDK Soul Box] CLAIM_STAGE; hud_status_set=1.");
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
    if (isdefined(state.original_killed) && isdefined(level.agent_funcs["generic_zombie"]) &&
        level.agent_funcs["generic_zombie"]["on_killed"] == ::ordinary_killed)
        level.agent_funcs["generic_zombie"]["on_killed"] = state.original_killed;
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
