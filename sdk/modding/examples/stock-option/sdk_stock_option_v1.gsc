// Original, disabled-by-default Stock Option-inspired private source prototype.
// The agent harness owns real engine godmode/inactivity protection, not this payload.
init()
{
    if (!private_context() || isdefined(level.sdk_stock_option_v1)) return;
    shared = spawnstruct();
    shared.owner = undefined;
    shared.stopped = false;
    level.sdk_stock_option_v1 = shared;
    foreach (player in getentarray("player", "classname")) player listen(shared);
    level thread connections(shared);
    level thread shutdown(shared);
    print("[SDK Stock Option] READY; activation=explicit; seconds=1..30; max_shots=64; runtime_qualified=0.");
}

private_context()
{
    return getdvarint("dedicated") && getdvarint("sdk_stock_option_demo_enable") == 1 &&
        getdvar("mapname") == "cp_zmb" && getdvarint("sv_lanOnly") == 1 &&
        getdvar("g_password") != "" && getdvarint("net_port") != 27016 &&
        getdvarint("sv_cheats") == 0 && getdvar("fs_game") == "";
}

connections(shared)
{
    level endon("game_ended");
    for (;;)
    {
        level waittill("connected", player);
        if (isdefined(player)) player listen(shared);
    }
}

listen(shared)
{
    if (!isplayer(self) || isdefined(self.sdk_stock_option_listener)) return;
    self.sdk_stock_option_listener = true;
    self thread requests(shared);
}

requests(shared)
{
    self endon("disconnect");
    level endon("game_ended");
    for (;;)
    {
        self waittill("sdk_stock_option_activate");
        self activate(shared);
    }
}

eligible(weapon)
{
    return private_context() && isplayer(self) && self.health > 0 && self.sessionstate == "playing" &&
        (!isdefined(self.inlaststand) || !self.inlaststand) &&
        (!isdefined(self.controlsfrozen) || !self.controlsfrozen) &&
        self hasweapon(weapon) && self getcurrentweapon() == weapon &&
        !self isreloading() && !self isswitchingweapon() && !self isdualwielding();
}

activate(shared)
{
    if (shared.stopped || isdefined(shared.owner) || !private_context()) return;
    seconds = 10;
    if (getdvar("sdk_stock_option_seconds") != "") seconds = getdvarint("sdk_stock_option_seconds");
    if (seconds < 1 || seconds > 30) return;
    weapon = self getcurrentweapon();
    if (!isdefined(weapon) || weapon == "" || weapon == "none" || !self eligible(weapon)) return;
    primary = false;
    foreach (candidate in self getweaponslistprimaries()) if (candidate == weapon) primary = true;
    if (!primary) return;
    clip = self getweaponammoclip(weapon);
    stock = self getweaponammostock(weapon);
    capacity = weaponclipsize(weapon);
    if (capacity < 2 || capacity > 512 || clip != capacity || stock < 1 || stock > 65535) return;
    state = spawnstruct();
    state.weapon = weapon;
    state.clip = clip;
    state.stock = stock;
    state.shots = 0;
    state.deadline = gettime() + seconds * 1000;
    state.stopped = false;
    self.sdk_stock_option_active = state;
    shared.owner = self;
    self thread shots(shared, state);
    self thread expires(shared, state, seconds);
    self thread context_guard(shared, state);
    self thread life_end(shared, state, "death");
    self thread life_end(shared, state, "disconnect");
    self thread life_end(shared, state, "weapon_change");
    self thread life_end(shared, state, "reload_start");
    self thread life_end(shared, state, "faux_spawn");
    self iprintln("Stock Option active: shots use reserve ammo.");
    print("[SDK Stock Option] ARMED; weapon=" + weapon + "; clip=" + clip + "; stock=" + stock + "; seconds=" + seconds + ".");
}

// Pure production decision, exercised directly by the source accounting tests.
one_round_transfer(before_clip, before_stock, after_clip, after_stock)
{
    if (before_clip < 2 || before_clip > 512 || before_stock < 1 || before_stock > 65535 ||
        after_clip != before_clip - 1 || after_stock != before_stock) return undefined;
    transaction = [];
    transaction[0] = before_clip;
    transaction[1] = before_stock - 1;
    return transaction;
}

shots(shared, state)
{
    self endon("sdk_stock_option_stopped");
    level endon("game_ended");
    for (;;)
    {
        self waittill("weapon_fired", fired_weapon);
        self transfer(shared, state, fired_weapon);
    }
}

// No wait/thread/notify between sampling and paired writes. Unknown timing,
// other ammo mutations and reload/switch cases stop instead of guessing/refilling.
transfer(shared, state, fired_weapon)
{
    if (state.stopped) return;
    if (!isdefined(fired_weapon) || fired_weapon != state.weapon || gettime() >= state.deadline ||
        !self eligible(state.weapon))
    {
        self stop(shared, state, "context_or_expiry");
        return;
    }
    clip = self getweaponammoclip(state.weapon);
    stock = self getweaponammostock(state.weapon);
    transaction = one_round_transfer(state.clip, state.stock, clip, stock);
    if (!isdefined(transaction))
    {
        self stop(shared, state, "ambiguous_ammo_delta");
        return;
    }
    if (!self eligible(state.weapon) || gettime() >= state.deadline ||
        self getweaponammoclip(state.weapon) != clip || self getweaponammostock(state.weapon) != stock)
    {
        self stop(shared, state, "prewrite_changed");
        return;
    }
    // Pay first. A failed readback never grants a free clip round or rolls back
    // an unknown engine change. A partial write may cost a round and ends the effect.
    self setweaponammostock(state.weapon, transaction[1]);
    if (!self eligible(state.weapon) || self getweaponammostock(state.weapon) != transaction[1] ||
        self getweaponammoclip(state.weapon) != clip)
    {
        self stop(shared, state, "reserve_write_unconfirmed");
        return;
    }
    self setweaponammoclip(state.weapon, transaction[0]);
    if (!self eligible(state.weapon) || self getweaponammostock(state.weapon) != transaction[1] ||
        self getweaponammoclip(state.weapon) != transaction[0])
    {
        self stop(shared, state, "clip_write_unconfirmed");
        return;
    }
    state.clip = transaction[0];
    state.stock = transaction[1];
    state.shots++;
    print("[SDK Stock Option] SHOT; weapon=" + state.weapon + "; n=" + state.shots +
        "; clip=" + state.clip + "; stock=" + state.stock + "; total=" + (state.clip + state.stock) + ".");
    if (state.stock == 0) self stop(shared, state, "reserve_empty");
    else if (state.shots >= 64) self stop(shared, state, "shot_budget");
}

expires(shared, state, seconds)
{
    self endon("sdk_stock_option_stopped");
    level endon("game_ended");
    wait seconds;
    self stop(shared, state, "expired");
}

context_guard(shared, state)
{
    self endon("sdk_stock_option_stopped");
    level endon("game_ended");
    for (;;)
    {
        wait 0.05;
        if (!self eligible(state.weapon))
        {
            self stop(shared, state, "reload_switch_or_context");
            return;
        }
    }
}

life_end(shared, state, event)
{
    self endon("sdk_stock_option_stopped");
    level endon("game_ended");
    self waittill(event);
    self stop(shared, state, event);
}

stop(shared, state, reason)
{
    if (state.stopped) return;
    state.stopped = true;
    if (isdefined(shared.owner) && shared.owner == self) shared.owner = undefined;
    self.sdk_stock_option_active = undefined;
    print("[SDK Stock Option] STOP; reason=" + reason + "; shots=" + state.shots + "; ammo_restored=0.");
    if (reason != "disconnect" && reason != "game_ended" && isplayer(self) && self.health > 0)
        self iprintln("Stock Option ended: normal ammo use restored.");
    // Release state/log before notify: callers also end on this event.
    self notify("sdk_stock_option_stopped");
}

shutdown(shared)
{
    level waittill("game_ended");
    shared.stopped = true;
    if (isdefined(shared.owner) && isdefined(shared.owner.sdk_stock_option_active))
        shared.owner stop(shared, shared.owner.sdk_stock_option_active, "game_ended");
    foreach (player in getentarray("player", "classname"))
    {
        player.sdk_stock_option_listener = undefined;
        player.sdk_stock_option_active = undefined;
    }
}
