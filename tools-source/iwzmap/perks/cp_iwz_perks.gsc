// Station Zero perks (package P1, bible 06-PERKS.md): ten machines, a limit of six, the four new perks and the
// Validated Ticket, on top of the stock perk table.
//
// How it rests on the stock code (decompiled reference: scripts/cp/zombies/zombies_perk_machines.gsc,
// scripts/cp/cp_interaction.gsc, scripts/cp/maps/cp_zmb/cp_zmb_interactions.gsc):
//   - every perk is a stock interaction ("perk_machine_<name>", spend type "perk") and a stock perk callback
//     (level.coop_perk_callbacks[name].set / .unset), so give_zombies_perk, take_zombies_perk, the loss on going down
//     (remove_perks_from_player) and the HUD bit (zm_active_perks, cp/zombies/zombie_perks_bit_mask_table.csv, extended
//     with the four new rows in the map zone) are the stock ones;
//   - the stock limit of five is two hard-coded tests (can_use_perk, activate_perk_machine). This module does not
//     replace any stock function: it sets each perk interaction's own fields (cost, can_use_override_func,
//     activation_func, hint_func), which the map's purchase loop reads; the override runs before the payment and
//     refuses a seventh perk, the activation gives the perk without the stock test of five.
// Hooks into the level script (cp_iwz3.gsc): init() from main(), register() at the end of iwz_register_interactions().
// Other packages call through level function pointers, so they never depend on this file being in the zone:
//   level.iwz_price_func( player, base, kind )      kind "postage" or "trap": the price this player pays
//   level.iwz_arrival_func( player, how )           after a Capsule Post or train arrival (Bon Voyages)
//   level.iwz_grant_ticket_func( player )           the Night Inspector's first Validated Ticket (one free perk)
//   level.iwz_trap_hurts_func( player, owner )      0 when a trap must spare this player (Bon Voyages, own trap)
//   level.szp_ww_weapons                            base names of the wonder weapons (ignored by the new perks)
//   level.szp_unmarkable                            agent types the new perks ignore (Night Inspector, Rollers)
// Lines: "[IWZ perks] ..." in the server log (tests read them).

init()
{
    if ( isdefined( level.szp ) )
        return;
    level.szp = spawnstruct();
    level.szp.limit = 6;
    level.szp.names = [ "perk_machine_revive", "perk_machine_tough", "perk_machine_run", "perk_machine_rat_a_tat", "perk_machine_flash",
        "perk_machine_deadeye", "perk_machine_bakers", "perk_machine_voyage", "perk_machine_grudge", "perk_machine_double" ];
    level.szp.price = [];
    level.szp.price["perk_machine_revive"] = 1500;
    level.szp.price["perk_machine_tough"] = 2500;
    level.szp.price["perk_machine_run"] = 2000;
    level.szp.price["perk_machine_rat_a_tat"] = 2000;
    level.szp.price["perk_machine_flash"] = 3000;
    level.szp.price["perk_machine_deadeye"] = 1500;
    level.szp.price["perk_machine_bakers"] = 3000;
    level.szp.price["perk_machine_voyage"] = 2000;
    level.szp.price["perk_machine_grudge"] = 2500;
    level.szp.price["perk_machine_double"] = 3000;
    // the four new perks and Deadeye Dewdrops have no stock machine on this map: placeholder bodies (script models
    // placed by the map generator, targetname iwz_perk_body) and the perk's icon over them
    level.szp.newperks = [ "perk_machine_deadeye", "perk_machine_bakers", "perk_machine_voyage", "perk_machine_grudge", "perk_machine_double" ];
    level.szp.icon = [];
    level.szp.icon["perk_machine_deadeye"] = "cp_zmb_perk_icon_deadeye";
    level.szp.icon["perk_machine_bakers"] = "iwz_perk_icon_bakers";
    level.szp.icon["perk_machine_voyage"] = "iwz_perk_icon_voyage";
    level.szp.icon["perk_machine_grudge"] = "iwz_perk_icon_grudge";
    level.szp.icon["perk_machine_double"] = "iwz_perk_icon_double";
    level.szp.icon["perk_machine_double_cd"] = "iwz_perk_icon_double_cd";
    foreach ( name, mat in level.szp.icon )
        precacheshader( mat );
    precacheshader( "white" );
    if ( !isdefined( level.szp_ww_weapons ) )
        level.szp_ww_weapons = [];
    if ( !isdefined( level.szp_unmarkable ) )
        level.szp_unmarkable = [ "zombie_inspector", "zombie_roller" ];
    level.szp.free_tickets = 0;
    level.szp.machines_on = [];
    level.iwz_price_func = ::price;
    level.iwz_arrival_func = ::arrival;
    level.iwz_grant_ticket_func = ::grant_ticket;
    level.iwz_trap_hurts_func = ::trap_hurts;
    level.perk_registration_func = ::register_callbacks;
    scripts\cp\maps\cp_iwz\cp_iwz_perk_bakers::init();
    scripts\cp\maps\cp_iwz\cp_iwz_perk_voyages::init();
    scripts\cp\maps\cp_iwz\cp_iwz_perk_grudges::init();
    scripts\cp\maps\cp_iwz\cp_iwz_perk_doubletakes::init();
    level thread revive_price_watch();
    level thread damage_hooks();
    level thread player_watch();
    print( "[IWZ perks] INIT limit=" + level.szp.limit + " perks=" + level.szp.names.size );
}

// Called by the level script's iwz_register_interactions(), right after the stock registry: the new perks enter the
// stock interaction table, and every perk interaction gets this map's cost, limit and activation.
register()
{
    if ( !isdefined( level.szp ) )
        init();
    hint = [];
    hint[1500] = &"COOP_PERK_MACHINES_1500";
    hint[2000] = &"COOP_PERK_MACHINES_2000";
    hint[2500] = &"COOP_PERK_MACHINES_2500";
    hint[3000] = &"COOP_PERK_MACHINES_3000";
    foreach ( name in level.szp.newperks )
    {
        if ( name == "perk_machine_deadeye" )
            continue;      // registered by the stock registry already
        scripts\cp\cp_interaction::register_interaction( name, "perk", 1, ::hint_func, ::activate, level.szp.price[name], 1, ::machines_init );
    }
    foreach ( name in level.szp.names )
    {
        if ( !isdefined( level.interactions[name] ) )
        {
            print( "[IWZ perks] REGISTER_MISSING " + name );
            continue;
        }
        i = level.interactions[name];
        i.cost = level.szp.price[name];
        i.can_use_override_func = ::can_use;
        i.activation_func = ::activate;
        i.hint_func = ::hint_func;
        i.spend_type = "perk";
        if ( scripts\engine\utility::array_contains( level.szp.newperks, name ) )
            i.init_func = ::machines_init;     // Deadeye's stock init needs its scriptable machine, which this map has not
        if ( isdefined( hint[i.cost] ) )
            level.interaction_hintstrings[name] = hint[i.cost];
    }
    register_callbacks();
    print( "[IWZ perks] REGISTERED " + level.szp.names.size );
}

register_callbacks()
{
    if ( !isdefined( level.coop_perk_callbacks ) )
        level.coop_perk_callbacks = [];
    scripts\cp\perks\perkmachines::register_perk_callback( "perk_machine_bakers", scripts\cp\maps\cp_iwz\cp_iwz_perk_bakers::give, scripts\cp\maps\cp_iwz\cp_iwz_perk_bakers::take );
    scripts\cp\perks\perkmachines::register_perk_callback( "perk_machine_voyage", scripts\cp\maps\cp_iwz\cp_iwz_perk_voyages::give, scripts\cp\maps\cp_iwz\cp_iwz_perk_voyages::take );
    scripts\cp\perks\perkmachines::register_perk_callback( "perk_machine_grudge", scripts\cp\maps\cp_iwz\cp_iwz_perk_grudges::give, scripts\cp\maps\cp_iwz\cp_iwz_perk_grudges::take );
    scripts\cp\perks\perkmachines::register_perk_callback( "perk_machine_double", scripts\cp\maps\cp_iwz\cp_iwz_perk_doubletakes::give, scripts\cp\maps\cp_iwz\cp_iwz_perk_doubletakes::take );
}

// ---- the limit, the payment and the purchase -----------------------------------------------------------------------

count( p )
{
    if ( !isdefined( p.zombies_perks ) )
        return 0;
    return p.zombies_perks.size;
}

has( p, name )
{
    return isdefined( p.zombies_perks ) && isdefined( p.zombies_perks[name] );
}

// Runs in the purchase loop before the payment (cp_zmb_interactions: can_use_override_func). 0 = no payment, no
// activation.
can_use( s, p )
{
    if ( !isdefined( s.perk_type ) )
        s.perk_type = s.script_noteworthy;
    name = s.perk_type;
    if ( isdefined( s.last_time_used ) && isdefined( s.last_time_used[p.name] ) )
        return 0;
    if ( has( p, name ) )
    {
        // the stock machine sells a perk back for nothing when its owner uses it again
        if ( soundexists( "perk_machine_remove_perk" ) )
            p playlocalsound( "perk_machine_remove_perk" );
        if ( name == "perk_machine_revive" )
            p.self_revives_purchased--;
        p scripts\cp\zombies\zombies_perk_machines::take_zombies_perk( name );
        p scripts\cp\cp_interaction::refresh_interaction();
        print( "[IWZ perks] RETURN player=" + p getentitynumber() + " perk=" + name + " count=" + count( p ) );
        return 0;
    }
    if ( name == "perk_machine_revive" && solo() && p.self_revives_purchased >= p.max_self_revive_machine_use )
    {
        p scripts\cp\cp_interaction::interaction_show_fail_reason( s, &"COOP_INTERACTIONS_CANNOT_BUY_SELF_REVIVE" );
        return 0;
    }
    if ( count( p ) >= level.szp.limit )
    {
        p scripts\cp\cp_interaction::interaction_show_fail_reason( s, &"COOP_PERK_MACHINES_PERK_SLOTS_FULL" );
        if ( soundexists( "perk_machine_deny" ) )
            p playlocalsound( "perk_machine_deny" );
        print( "[IWZ perks] LIMIT player=" + p getentitynumber() + " perk=" + name + " count=" + count( p ) );
        return 0;
    }
    if ( isdefined( p.szp_ticket ) && p.szp_ticket > 0 )
    {
        // the Validated Ticket: this purchase is free (no payment), the limit still holds
        p.szp_ticket--;
        level.szp.free_tickets++;
        p ticket_hud();
        print( "[IWZ perks] TICKET_USED player=" + p getentitynumber() + " perk=" + name );
        level thread activate( s, p, 1 );
        return 0;
    }
    return 1;
}

activate( s, p, free )
{
    p endon( "disconnect" );
    if ( !isdefined( s.perk_type ) )
        s.perk_type = s.script_noteworthy;
    name = s.perk_type;
    if ( has( p, name ) )
        return;
    paid = level.interactions[name].cost;
    if ( isdefined( free ) && free )
        paid = 0;
    if ( count( p ) >= level.szp.limit )
    {
        // a second purchase in the same frame passed the test before the first one landed: give the money back
        if ( paid > 0 )
            p scripts\cp\cp_persistence::give_player_currency( paid, undefined, undefined, 1, "bonus" );
        print( "[IWZ perks] LIMIT_REFUND player=" + p getentitynumber() + " perk=" + name + " refund=" + paid );
        return;
    }
    level thread scripts\cp\zombies\zombies_perk_machines::turn_off_interaction_for_time( s, p, 2000 );
    stock = !scripts\engine\utility::array_contains( level.szp.newperks, name ) || name == "perk_machine_deadeye";
    if ( stock )
        level thread scripts\cp\zombies\zombies_perk_machines::play_perk_machine_purchase_sound( s, p );
    else
        level thread new_perk_purchase_sound( s, p );
    scripts\cp\cp_vo::remove_from_nag_vo( "dj_perkstation_use_nag" );
    if ( p scripts\cp\utility::is_consumable_active( "perk_refund" ) && paid > 0 )
    {
        p scripts\cp\cp_persistence::give_player_currency( 1000, undefined, undefined, 1, "bonus" );
        p scripts\cp\utility::notify_used_consumable( "perk_refund" );
    }
    // the perk first, then the candy gesture (the stock order of Bang Bangs; an engine bot never ends a gesture, and a
    // perk that waits for it was never given to the headless player, 11 Nov 2026)
    p scripts\cp\zombies\zombies_perk_machines::give_zombies_perk( name, 1 );
    print( "[IWZ perks] BUY player=" + p getentitynumber() + " perk=" + name + " paid=" + paid + " count=" + count( p ) + " money=" + p scripts\cp\cp_persistence::get_player_currency() );
    if ( !scripts\engine\utility::array_contains( level.szp.newperks, name ) && !( isdefined( p.pers ) && isdefined( p.pers["isBot"] ) ) )
        p thread scripts\cp\zombies\zombies_perk_machines::play_perk_gesture( name );
}

new_perk_purchase_sound( s, p )
{
    p playlocalsound( "perk_purchase_foley_candy_box" );
    // the jingles are not in the map's sound bank yet (P2, AU1): only the candy-box sound plays until they are
    jingle = "iwz_perk_jingle_" + getsubstr( s.perk_type, 13 );
    if ( soundexists( jingle ) )
        playsoundatpos( s.origin, jingle );
}

hint_func( s, p )
{
    if ( !scripts\engine\utility::is_true( s.powered_on ) )
    {
        if ( isdefined( level.needspowerstring ) )
            return level.needspowerstring;
        return &"COOP_INTERACTIONS_REQUIRES_POWER";
    }
    if ( isdefined( s.last_time_used ) && isdefined( s.last_time_used[p.name] ) )
        return "";
    if ( has( p, s.script_noteworthy ) )
        return &"COOP_PERK_MACHINES_REMOVE_PERK";
    if ( count( p ) >= level.szp.limit )
        return &"COOP_PERK_MACHINES_PERK_SLOTS_FULL";
    if ( s.script_noteworthy == "perk_machine_revive" && solo() )
        return &"COOP_PERK_MACHINES_SELF_REVIVE";
    return level.interaction_hintstrings[s.script_noteworthy];
}

solo()
{
    return scripts\cp\utility::isplayingsolo() || scripts\engine\utility::is_true( level.only_one_player );
}

// Up 'N Atoms costs 500 for a player alone (stock rule, read per purchase by the stock loop from the interaction's cost)
revive_price_watch()
{
    level endon( "game_ended" );
    for ( ;; )
    {
        if ( isdefined( level.interactions ) && isdefined( level.interactions["perk_machine_revive"] ) )
        {
            want = 1500;
            if ( isdefined( level.players ) && level.players.size > 0 && solo() )
                want = 500;
            level.interactions["perk_machine_revive"].cost = want;
        }
        wait 0.5;
    }
}

// ---- machines of the perks that have no stock machine on this map --------------------------------------------------

machines_init()
{
    s = self;
    if ( isdefined( s.script_noteworthy ) )
        name = s.script_noteworthy;
    else
        return;
    foreach ( st in scripts\engine\utility::getstructarray( name, "script_noteworthy" ) )
        st thread machine_power();
}

machine_power()
{
    self.perk_type = self.script_noteworthy;
    self.last_time_used = [];
    self.powered_on = 0;
    self.szp_body = undefined;
    foreach ( m in getentarray( "iwz_perk_body", "targetname" ) )
    {
        if ( isdefined( m.script_noteworthy ) && m.script_noteworthy == self.perk_type && distance( m.origin, self.origin ) < 128 )
            self.szp_body = m;
    }
    scripts\engine\utility::flag_wait( "player_count_determined" );
    if ( scripts\engine\utility::is_true( self.requires_power ) )
    {
        for ( ;; )
        {
            area = "";
            if ( isdefined( self.power_area ) )
                area = self.power_area + " power_on";
            msg = level scripts\engine\utility::waittill_any_return_no_endon_death( "power_on", area, "power_off" );
            if ( msg == "power_off" )
            {
                self.powered_on = 0;
                continue;
            }
            break;
        }
    }
    self.powered_on = 1;
    print( "[IWZ perks] MACHINE_ON perk=" + self.perk_type + " body=" + isdefined( self.szp_body ) + " origin=" + self.origin );
    if ( isdefined( self.szp_body ) )
        playsoundatpos( self.szp_body.origin, "power_buy_neon_vending_turn_on" );
    level.szp.machines_on[self.perk_type] = self;
}

// one icon over each new machine, for each player, shown within 700 units (the machine's sign until P2's models)
machine_icons()
{
    self endon( "disconnect" );
    self.szp_machine_icons = [];
    for ( ;; )
    {
        if ( isdefined( level.szp.machines_on ) )
        {
            foreach ( name, s in level.szp.machines_on )
            {
                if ( !isdefined( self.szp_machine_icons[name] ) )
                {
                    e = newclienthudelem( self );
                    e.archived = 1;
                    e.x = s.origin[0];
                    e.y = s.origin[1];
                    e.z = s.origin[2] + 92;
                    e.alpha = 0;
                    e setshader( level.szp.icon[name], 12, 12 );
                    e setwaypoint( 0, 0, 0, 1 );
                    self.szp_machine_icons[name] = e;
                }
                e = self.szp_machine_icons[name];
                want = 0;
                if ( distancesquared( self.origin, s.origin ) < 490000 )
                    want = 0.9;
                if ( e.alpha != want )
                    e.alpha = want;
            }
        }
        wait 0.5;
    }
}

// ---- players --------------------------------------------------------------------------------------------------------

player_watch()
{
    level endon( "game_ended" );
    for ( ;; )
    {
        level waittill( "connected", p );
        p thread player_setup();
    }
}

player_setup()
{
    self endon( "disconnect" );
    self waittill( "spawned_player" );
    if ( !isdefined( self.szp_ticket ) )
        self.szp_ticket = 0;
    self thread machine_icons();
}

// a player added before this module ran (the headless bot) gets the same set-up from a test library
setup_player_now()
{
    if ( !isdefined( self.szp_ticket ) )
        self.szp_ticket = 0;
    if ( !isdefined( self.szp_machine_icons ) )
        self thread machine_icons();
}

// ---- damage hooks shared by the new perks -------------------------------------------------------------------------

// The zombie damage hook (level.onzombiedamage_func, read by the stock agent damage callback before the damage is
// applied: its return value is the damage) and the player damage callback (level.callbackplayerdamage) are each
// chained once; the previous value is called first.
damage_hooks()
{
    level endon( "game_ended" );
    while ( !isdefined( level.callbackplayerdamage ) )
        wait 0.1;
    wait 1;
    level.szp.prev_zombie_damage = level.onzombiedamage_func;
    level.onzombiedamage_func = ::on_zombie_damage;
    level.szp.prev_player_damage = level.callbackplayerdamage;
    level.callbackplayerdamage = ::on_player_damage;
    print( "[IWZ perks] DAMAGE_HOOKS zombie=1 player=1" );
}

on_zombie_damage( inflictor, attacker, damage, flags, mod, weapon, point, dir, hitloc, timeoffset, modelindex, partname )
{
    if ( isdefined( level.szp.prev_zombie_damage ) )
        damage = [[ level.szp.prev_zombie_damage ]]( inflictor, attacker, damage, flags, mod, weapon, point, dir, hitloc, timeoffset, modelindex, partname );
    if ( isdefined( attacker ) && isplayer( attacker ) )
    {
        self.szp_last_attacker = attacker;
        self.szp_last_weapon = weapon;
        attacker.szp_last_hit_ent = self;          // the agent's own fields do not survive its death (pooled agents)
        attacker.szp_last_hit_weapon = weapon;
        if ( has( attacker, "perk_machine_bakers" ) )
            damage = self scripts\cp\maps\cp_iwz\cp_iwz_perk_bakers::on_hit( attacker, damage, mod, weapon, point, dir, hitloc );
    }
    return damage;
}

on_player_damage( inflictor, attacker, damage, flags, mod, weapon, point, dir, hitloc, timeoffset, modelindex, partname )
{
    if ( isdefined( attacker ) && is_zombie( attacker ) && damage > 0 )
    {
        if ( has( self, "perk_machine_grudge" ) )
            damage = self scripts\cp\maps\cp_iwz\cp_iwz_perk_grudges::on_hurt( attacker, damage );
    }
    h0 = self.health;
    [[ level.szp.prev_player_damage ]]( inflictor, attacker, damage, flags, mod, weapon, point, dir, hitloc, timeoffset, modelindex, partname );
    if ( isdefined( attacker ) && is_zombie( attacker ) && damage > 0 )
    {
        self.szp_last_zombie_damage = damage;
        if ( isdefined( self.szp_hurt_n ) )
        {
            // a test reads what each zombie hit took (gamelab library szperks: szp_hurt)
            took = h0 - self.health;
            self.szp_hurt_n++;
            self.szp_hurt_asked = damage;
            if ( took > self.szp_hurt_max )
                self.szp_hurt_max = took;
            if ( self.szp_hurt_min < 0 || took < self.szp_hurt_min )
                self.szp_hurt_min = took;
        }
        if ( getdvarint( "szp_log_damage" ) )
            print( "[IWZ perks] HURT player=" + self getentitynumber() + " by=" + attacker.agent_type + " damage=" + damage + " health0=" + h0 + " health1=" + self.health + " max=" + self.maxhealth + " wave=" + level.wave_num );
        if ( has( self, "perk_machine_double" ) )
            self scripts\cp\maps\cp_iwz\cp_iwz_perk_doubletakes::after_hurt( attacker, damage, h0 );
    }
}

is_zombie( e )
{
    return isdefined( e ) && !isplayer( e ) && isdefined( e.agent_type ) && isdefined( e.team ) && e.team == "axis";
}

// Nothing of the new perks touches the wonder weapons, launchers or explosives.
ordinary_weapon( weapon, mod )
{
    if ( !isdefined( weapon ) || weapon == "none" )
        return 0;
    base = getweaponbasename( weapon );
    foreach ( w in level.szp_ww_weapons )
    {
        if ( issubstr( base, w ) )
            return 0;
    }
    if ( isdefined( mod ) && ( mod == "MOD_EXPLOSIVE" || mod == "MOD_GRENADE" || mod == "MOD_GRENADE_SPLASH" || mod == "MOD_PROJECTILE" || mod == "MOD_PROJECTILE_SPLASH" ) )
        return 0;
    c = weaponclass( weapon );
    if ( c == "rocketlauncher" || c == "grenade" )
        return 0;
    return 1;
}

markable( z )
{
    if ( !isdefined( z ) || !isdefined( z.agent_type ) )
        return 0;
    return !scripts\engine\utility::array_contains( level.szp_unmarkable, z.agent_type );
}

// ---- other packages' hooks ---------------------------------------------------------------------------------------

price( p, base, kind )
{
    if ( isdefined( p ) && has( p, "perk_machine_voyage" ) && ( kind == "postage" || kind == "trap" ) )
        return int( base / 2 );
    return base;
}

arrival( p, how )
{
    if ( isdefined( p ) && has( p, "perk_machine_voyage" ) )
        p thread scripts\cp\maps\cp_iwz\cp_iwz_perk_voyages::on_arrival( how );
}

trap_hurts( p, owner )
{
    if ( isdefined( owner ) && p == owner && has( p, "perk_machine_voyage" ) )
        return 0;
    return 1;
}

grant_ticket( p )
{
    if ( !isdefined( p.szp_ticket ) )
        p.szp_ticket = 0;
    p.szp_ticket++;
    p ticket_hud();
    print( "[IWZ perks] TICKET_GRANTED player=" + p getentitynumber() + " tickets=" + p.szp_ticket );
}

// one line over the perk row while a Validated Ticket is held
ticket_hud()
{
    if ( !isdefined( self.szp_ticket_hud ) )
    {
        e = newclienthudelem( self );
        e.horzalign = "left";
        e.vertalign = "bottom";
        e.alignx = "left";
        e.aligny = "bottom";
        e.x = 18;
        e.y = -118;
        e.fontscale = 1.0;
        e.color = ( 1, 0.78, 0.35 );
        e.archived = 1;
        e.hidewheninmenu = 1;
        e.sort = 20;
        self.szp_ticket_hud = e;
    }
    if ( self.szp_ticket > 0 )
    {
        self.szp_ticket_hud settext( "VALIDATED TICKET  next perk free" );
        self.szp_ticket_hud.alpha = 1;
    }
    else
        self.szp_ticket_hud.alpha = 0;
}

// The state this module holds for a player, one line (tests read it).
state_line( p )
{
    s = "player=" + p getentitynumber() + " count=" + count( p ) + " limit=" + level.szp.limit + " ticket=" + p.szp_ticket;
    s += " " + p scripts\cp\maps\cp_iwz\cp_iwz_perk_bakers::state();
    s += " " + p scripts\cp\maps\cp_iwz\cp_iwz_perk_grudges::state();
    s += " " + p scripts\cp\maps\cp_iwz\cp_iwz_perk_doubletakes::state();
    s += " " + p scripts\cp\maps\cp_iwz\cp_iwz_perk_voyages::state();
    return s;
}
