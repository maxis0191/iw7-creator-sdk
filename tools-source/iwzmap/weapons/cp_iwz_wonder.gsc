// Station Zero wonder weapons, module of the map zone (add_weapons.py puts it at
// scripts/cp/maps/<map>/<map>_wonder.gsc and calls init() from the level script's main()).
// WW1 EXACT CHANGE (docs/station-zero/05-WONDER-WEAPONS.md section 1): every shot is bought with points.
//   fare 30 a shot, surge +10 for each shot within 0.6 s of the last (cap 100), back to 30 after 1.5 s;
//   under the fare the hopper is held empty (the trigger clicks); doubled while level.iwz_penalty_fare is set;
//   flat rated damage: body R24 3,970 / head 9,920; upgraded (Pack-a-Punch: +spasslugpap1) R32 8,510 / 21,270;
//   specials (anything but an ordinary zombie) take at most 2,000 a hit;
//   pierces: 3 zombies a shot (upgraded 5); its hits pay no hit points; kills behind the first pay half;
//   a one-token head kill of the first zombie refunds the base fare 30, at most once every 1.5 s;
//   no reserve: the stock is kept equal to the hopper (reload is free, Max Ammo does nothing);
//   upgraded: a kill drops a brass token worth 25 to whoever picks it up (12 s, one a second a shooter, 12 lying).
// Hooks are chained (the previous function, if any, runs first), so other modules may hook the same events.
// Lines "[IWZ wonder] ..." are the measurable trace of each rule (read by the headless plans).

init()
{
    level.coop_weapontable = "cp/cp_iwz_weapontable.csv";       // the map's table: stock rows + EXACT CHANGE (magic upgrade)
    precacheitem( "iw7_exactchange_zm" );
    precachemodel( "zmb_coin_space" );                            // token stand-in model (stock Spaceland coin): placeholder
    level.iwz_ec_fare = 30;
    level.iwz_ec_tokens = [];
    level.iwz_ec_prev_damage = level.onzombiedamage_func;
    level.onzombiedamage_func = ::iwz_ec_damage;
    level.iwz_ec_prev_reward = level.eligable_for_reward_func;
    level.eligable_for_reward_func = ::iwz_ec_reward;
    level thread iwz_ec_pap_register();
    level thread iwz_ec_players();
    print( "[IWZ wonder] INIT exactchange table=" + level.coop_weapontable );
}

iwz_ec_is( weapon )
{
    return isdefined( weapon ) && isstring( weapon ) && issubstr( weapon, "exactchange" );
}

iwz_ec_upgraded( weapon )
{
    return iwz_ec_is( weapon ) && issubstr( weapon, "pap" );
}

// Pack-a-Punch: the generic "pap1"/"pap2" of every machine becomes the stock attachment spasslugpap1 (hopper 18,
// one shot), which the weapon definition lists; level.pap comes from the map's table ("upgrade" tag).
iwz_ec_pap_register()
{
    level endon( "game_ended" );
    for ( i = 0; i < 600 && !isdefined( level.attachmentmap_basetounique ); i++ )
        wait 0.1;
    if ( !isdefined( level.attachmentmap_basetounique ) )
        level.attachmentmap_basetounique = [];
    foreach ( key in [ "iw7_exactchange_zm", "iw7_exactchange" ] )
    {
        if ( !isdefined( level.attachmentmap_basetounique[key] ) )
            level.attachmentmap_basetounique[key] = [];
        level.attachmentmap_basetounique[key]["pap1"] = "spasslugpap1";
        level.attachmentmap_basetounique[key]["pap2"] = "spasslugpap1";
    }
    if ( !isdefined( level.attachmentmap_uniquetobase ) )
        level.attachmentmap_uniquetobase = [];
    if ( !isdefined( level.attachmentmap_uniquetobase["spasslugpap1"] ) )
        level.attachmentmap_uniquetobase["spasslugpap1"] = "pap1";
    for ( i = 0; i < 600 && !( isdefined( level.pap ) && isdefined( level.magic_weapons ) ); i++ )
        wait 0.1;
    pap = isdefined( level.pap ) && isdefined( level.pap["exactchange"] );
    wheel = isdefined( level.magic_weapons ) && isdefined( level.magic_weapons["exactchange"] );
    print( "[IWZ wonder] PAP exactchange pap=" + pap + " wheel=" + wheel );
}

iwz_ec_players()
{
    level endon( "game_ended" );
    foreach ( p in level.players )
        p thread iwz_ec_player();
    for ( ;; )
    {
        level waittill( "connected", p );
        p thread iwz_ec_player();
    }
}

iwz_ec_player()
{
    self endon( "disconnect" );
    if ( isdefined( self.iwz_ec_on ) )
        return;
    self.iwz_ec_on = 1;
    self.iwz_ec_last_fire = -100000;
    self.iwz_ec_surge = level.iwz_ec_fare;
    self.iwz_ec_last_refund = -100000;
    self.iwz_ec_last_token = -100000;
    self.iwz_ec_hit_time = -1;
    self.iwz_ec_hits = 0;
    self thread iwz_ec_fire_watch();
    self thread iwz_ec_hopper();
}

// The fare of the next shot fired at time t.
iwz_ec_next_fare( t )
{
    gap = t - self.iwz_ec_last_fire;
    fare = level.iwz_ec_fare;
    if ( gap <= 600 )
        fare = int( min( self.iwz_ec_surge + 10, 100 ) );
    else if ( gap < 1500 )
        fare = self.iwz_ec_surge;
    if ( isdefined( level.iwz_penalty_fare ) && level.iwz_penalty_fare )
        fare = fare * 2;
    return fare;
}

iwz_ec_fire_watch()
{
    self endon( "disconnect" );
    for ( ;; )
    {
        self waittill( "weapon_fired", weapon );
        if ( !iwz_ec_is( weapon ) )
            continue;
        t = gettime();
        fare = self iwz_ec_next_fare( t );
        base = fare;
        if ( isdefined( level.iwz_penalty_fare ) && level.iwz_penalty_fare )
            base = int( fare / 2 );
        self.iwz_ec_surge = base;
        self.iwz_ec_last_fire = t;
        before = self scripts\cp\cp_persistence::get_player_currency();
        self iwz_ec_pay( fare );
        print( "[IWZ wonder] FARE player=" + self getentitynumber() + " fare=" + fare + " money=" + before + "->" + self scripts\cp\cp_persistence::get_player_currency() + " t=" + t );
    }
}

// No reserve: the stock follows the hopper size, so a reload is free and Max Ammo does nothing. Under the fare the
// hopper is held empty, so the trigger only clicks; it comes back as soon as the player can pay.
iwz_ec_hopper()
{
    self endon( "disconnect" );
    held = undefined;
    for ( ;; )
    {
        wait 0.05;
        w = self getcurrentweapon();
        if ( !iwz_ec_is( w ) )
            continue;
        size = weaponclipsize( w );
        money = self scripts\cp\cp_persistence::get_player_currency();
        if ( money < self iwz_ec_next_fare( gettime() ) )
        {
            if ( !isdefined( held ) )
            {
                held = self getweaponammoclip( w );
                self setweaponammoclip( w, 0 );
                print( "[IWZ wonder] EXACT_FARE_ONLY player=" + self getentitynumber() + " money=" + money );
            }
            self setweaponammostock( w, 0 );
            continue;
        }
        if ( isdefined( held ) )
        {
            self setweaponammoclip( w, held );
            held = undefined;
        }
        if ( self getweaponammostock( w ) != size )
            self setweaponammostock( w, size );
    }
}

iwz_ec_head( hitloc )
{
    return isdefined( hitloc ) && ( hitloc == "head" || hitloc == "helmet" || hitloc == "neck" );
}

// level.onzombiedamage_func( inflictor, attacker, damage, flags, mod, weapon, point, dir, hitloc, timeoffset, model, part )
iwz_ec_damage( inflictor, attacker, damage, flags, mod, weapon, point, dir, hitloc, timeoffset, modelindex, partname )
{
    if ( isdefined( level.iwz_ec_prev_damage ) )
        damage = self [[ level.iwz_ec_prev_damage ]]( inflictor, attacker, damage, flags, mod, weapon, point, dir, hitloc, timeoffset, modelindex, partname );
    if ( !iwz_ec_is( weapon ) || !isdefined( attacker ) || !isplayer( attacker ) )
        return damage;
    up = iwz_ec_upgraded( weapon );
    // victims of one shot share a server frame: the hopper fires at most once every 545 ms
    t = gettime();
    if ( attacker.iwz_ec_hit_time != t )
    {
        attacker.iwz_ec_hit_time = t;
        attacker.iwz_ec_hits = 0;
    }
    attacker.iwz_ec_hits++;
    index = attacker.iwz_ec_hits;
    limit = 3;
    if ( up )
        limit = 5;
    if ( index > limit )
        return 0;
    head = iwz_ec_head( hitloc );
    if ( up )
        rated = 8510;
    else
        rated = 3970;
    if ( head )
    {
        if ( up )
            rated = 21270;
        else
            rated = 9920;
    }
    special = isdefined( self.agent_type ) && self.agent_type != "generic_zombie";
    if ( special )
        rated = int( min( rated, 2000 ) );
    kills = isdefined( self.health ) && rated >= self.health;
    print( "[IWZ wonder] HIT player=" + attacker getentitynumber() + " victim=" + self getentitynumber() + " index=" + index + " head=" + head + " up=" + up + " special=" + special + " rated=" + rated + " health=" + self.health + " kill=" + kills );
    if ( kills )
    {
        if ( index > 1 )
            attacker thread iwz_ec_half_reward( head );
        else if ( head && !up && t - attacker.iwz_ec_last_refund >= 1500 )
        {
            attacker.iwz_ec_last_refund = t;
            attacker thread iwz_ec_refund();
        }
        if ( up )
            attacker thread iwz_ec_drop_token( self.origin, t );
    }
    return rated;
}

// Its hits pay no hit points (the stock 10 a hit); kill rewards take another path and stay.
iwz_ec_reward( a, b, c, weapon, e, f )
{
    if ( iwz_ec_is( weapon ) )
        return 0;
    if ( isdefined( level.iwz_ec_prev_reward ) )
        return [[ level.iwz_ec_prev_reward ]]( a, b, c, weapon, e, f );
    return 1;
}

iwz_ec_half_reward( head )
{
    self endon( "disconnect" );
    wait 0.05;
    half = 30;
    if ( head )
        half = 50;
    self iwz_ec_pay( half );
    print( "[IWZ wonder] HALF player=" + self getentitynumber() + " back=" + half );
}

iwz_ec_refund()
{
    self endon( "disconnect" );
    wait 0.05;
    self scripts\cp\cp_persistence::give_player_currency( level.iwz_ec_fare, "large", undefined, 1, "bonus" );
    print( "[IWZ wonder] REFUND player=" + self getentitynumber() + " fare=" + level.iwz_ec_fare );
}

iwz_ec_drop_token( origin, t )
{
    if ( t - self.iwz_ec_last_token < 1000 )
        return;
    level.iwz_ec_tokens = scripts\engine\utility::array_removeundefined( level.iwz_ec_tokens );
    if ( level.iwz_ec_tokens.size >= 12 )
        return;
    self.iwz_ec_last_token = t;
    token = spawn( "script_model", origin + ( 0, 0, 12 ) );
    token setmodel( "zmb_coin_space" );
    level.iwz_ec_tokens[level.iwz_ec_tokens.size] = token;
    print( "[IWZ wonder] TOKEN drop at=" + token.origin + " lying=" + level.iwz_ec_tokens.size );
    token thread iwz_ec_token_life();
}

iwz_ec_token_life()
{
    self endon( "death" );
    self rotateyaw( 3600, 12 );
    end = gettime() + 12000;
    while ( gettime() < end )
    {
        foreach ( p in level.players )
        {
            if ( isalive( p ) && distancesquared( p.origin, self.origin ) < 48 * 48 )
            {
                p scripts\cp\cp_persistence::give_player_currency( 25, "large", undefined, 1, "bonus" );
                print( "[IWZ wonder] TOKEN picked player=" + p getentitynumber() + " +25" );
                self delete();
                return;
            }
        }
        wait 0.1;
    }
    self delete();
}

// A fare is not a purchase: set the points directly so purchase consumables (next purchase free, door refund) are
// neither used up nor paid out by fares; the spend still counts in the end-of-game statistics.
iwz_ec_pay( amount )
{
    money = self scripts\cp\cp_persistence::get_player_currency();
    paid = int( min( money, amount ) );
    self scripts\cp\cp_persistence::set_player_currency( money - paid );
    self scripts\cp\cp_persistence::eog_player_update_stat( "currencyspent", paid );
    level notify( "currency_changed" );
}