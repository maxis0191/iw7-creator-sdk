// Station Zero, package T1: the Capsule Post, version 1 (iw7-creator-sdk docs/station-zero/03-TRANSPORT.md).
// Four hatches (PLAZA, EXCHANGE, BARN, PARLOUR) on a ring driven by the Bellows. Needs power. Unsealing a hatch: 750, once
// per match, hold Use 1.5 s. At an unsealed hatch a tap of Use turns the dial to the next unsealed address, holding Use
// 0.8 s sends: 1, 2 or 3 ring segments = 250, 400, 550 points and (version 1, black-out ride) 2.5, 4.5, 6.5 s. Two
// capsules per hatch, each back 30 s after it leaves; a rider rests 45 s after arriving. The lever in the Bellows Vault
// swaps BLOW and DRAW (near and far): 12 s changeover with no launch, then 45 s before it can be thrown again.
// Blowback: up to 3 zombies within 48 units of the hatch at launch come out of the destination hatch 2 s after the rider.
// Refusals (no points, sealed, no capsule, changeover, inspection, rest, downed, busy) take nothing and say why.
// The rider is placed at the destination at launch, hidden, frozen and protected, so the spawn system counts him in the
// destination zone for the whole ride (03-TRANSPORT.md section 6).
// Self-contained (no call by path): runs from the map zone or as a server custom script. State in level.iwz_t1, every
// event printed "[IWZ level] T1 ...". Test entry: [[ level.iwz_post_ride ]]( player, from, to ) rides without Use (refusals
// apply, points are taken); lab sessions (dvar "gamelab") also read dvar iwz_test_hold (1 = held, 0 = a tap).
// Hooks for later packages: player.iwz_bon_voyages (P1: half postage, weapon up on arrival), level.iwz_inspector (E4: an
// entity or an array of entities; hatches within 300 units say INSPECTION until 15 s after he moved away),
// player.iwz_busy (shared with the Q1 teleport and the emotes of M1).

init()
{
    if ( getdvar( "mapname" ) != "cp_iwz" || isdefined( level.iwz_t1 ) )
        return;
    s = spawnstruct();
    level.iwz_t1 = s;
    s.ring = [ "PLAZA", "EXCHANGE", "BARN", "PARLOUR" ];
    s.price = [ 0, 250, 400, 550 ];
    s.ride_s = [ 0, 2.5, 4.5, 6.5 ];
    s.dir = "BLOW";
    s.changeover_until = 0;
    s.lever_ready_at = 0;
    s.hatches = [];
    s.rides = 0;
    s.arrivals = 0;
    s.unsealed = 0;
    s.refusals = 0;
    s.refused = [];
    s.blowback = 0;
    s.blowback_out = 0;
    s.lever_throws = 0;
    s.riding = 0;
    s.events = 0;
    s.markers = t1_markers();
    level.iwz_post_ride = ::t1_test_ride;
    level thread t1_main();
}

// filled by the emit (sz_modules.py): [ kind, id, zone, origin, yaw ( , lo, hi ) ]
t1_markers()
{
    m = [];
    //@MARKERS@
    return m;
}

t1_volumes()
{
    if ( isdefined( level.iwz_t1.vols ) )
        return level.iwz_t1.vols;
    v = [];
    //@VOLUMES@
    level.iwz_t1.vols = v;
    return v;
}

t1_zone_of( p )
{
    foreach ( v in t1_volumes() )
    {
        if ( p[0] >= v[2][0] && p[0] <= v[3][0] && p[1] >= v[2][1] && p[1] <= v[3][1] && p[2] >= v[2][2] && p[2] <= v[3][2] )
            return v[1];
    }
    return "none";
}

// the spawn volume the engine says the player touches (what the stock spawning uses)
t1_touching( p )
{
    if ( !isdefined( level.spawn_volume_array ) )
        return "none";
    foreach ( name, v in level.spawn_volume_array )
    {
        if ( isdefined( v ) && p istouching( v ) )
            return name;
    }
    return "none";
}

t1_log( text )
{
    level.iwz_t1.events++;
    print( "[IWZ level] T1 " + text + " t=" + gettime() );
}

t1_main()
{
    level endon( "game_ended" );
    s = level.iwz_t1;
    level thread t1_players();
    level thread t1_end_cleanup();
    wait 1;
    t1_sounds_check();
    foreach ( m in s.markers )
    {
        if ( m[0] != "hatch" )
            continue;
        h = spawn( "script_model", m[3] + ( 0, 0, 52 ) );
        h setmodel( "pipe_metal_painted_bend_90_lrg_blue" );
        h.angles = ( 0, m[4], 0 );
        h.targetname = "iwz_t1_hatch_" + tolower( m[1] );
        h.iwz_id = m[1];
        h.iwz_zone = m[2];
        h.iwz_sealed = 1;
        h.iwz_dial = -1;
        h.iwz_caps = [ 0, 0 ];
        h.iwz_insp_until = 0;
        f = anglestoforward( ( 0, m[4], 0 ) );
        g = getclosestpointonnavmesh( m[3] + f * 40 );
        if ( !isdefined( g ) )
            g = m[3] + f * 40;
        h.iwz_out = g;
        h makeusable();
        h sethintstring( "CAPSULE POST " + m[1] + ": THE BELLOWS IS COLD (NO POWER)" );
        s.hatches[m[1]] = h;
        h thread t1_hatch_use();
    }
    lm = undefined;
    foreach ( m in s.markers )
    {
        if ( m[0] == "post_lever" )
            lm = m;
    }
    if ( isdefined( lm ) )
    {
        s.lever = spawn( "script_model", lm[3] + ( 0, 0, 44 ) );
        s.lever setmodel( "icbm_electricpanel_switch_02" );
        s.lever.angles = ( 0, lm[4], 0 );
        s.lever.iwz_base = s.lever.angles;
        s.lever.targetname = "iwz_t1_lever";
        s.lever makeusable();
        s.lever sethintstring( "BELLOWS LEVER: COLD (NO POWER)" );
        s.lever thread t1_lever_use();
    }
    t1_log( "INIT hatches=" + s.hatches.size + " lever=" + isdefined( s.lever ) + " dir=" + s.dir );
    while ( !scripts\engine\utility::flag_exist( "power_on" ) )
        wait 0.5;
    scripts\engine\utility::flag_wait( "power_on" );
    t1_log( "POWER on" );
    t1_hints();
    level thread t1_inspection_watch();
}

t1_sounds_check()
{
    s = level.iwz_t1;
    s.sounds = [];
    have = 0;
    names = [ "purchase_deny", "purchase_generic", "zmb_wheel_spin_tick", "ftl_phase_out", "ftl_phase_in", "zmb_portal_travel_lr", "trap_rocket_start", "trap_waterfall_valve", "zmb_challenge_complete" ];
    foreach ( n in names )
    {
        s.sounds[n] = soundexists( n );
        if ( s.sounds[n] )
            have++;
    }
    t1_log( "SOUNDS have=" + have + " of=" + names.size );
}

t1_sound( ent, alias )
{
    if ( isdefined( level.iwz_t1.sounds[alias] ) && level.iwz_t1.sounds[alias] )
        ent playsound( alias );
}

t1_local_sound( p, alias )
{
    if ( isdefined( level.iwz_t1.sounds[alias] ) && level.iwz_t1.sounds[alias] )
        p playlocalsound( alias );
}

t1_fx( name, origin )
{
    if ( isdefined( level._effect ) && isdefined( level._effect[name] ) )
        playfx( level._effect[name], origin );
}

// ---------------------------------------------------------------------------------------------- the ring

t1_index( id )
{
    s = level.iwz_t1;
    for ( i = 0; i < s.ring.size; i++ )
    {
        if ( s.ring[i] == id )
            return i;
    }
    return -1;
}

// ring segments from a to b in the current direction: BLOW runs PLAZA, EXCHANGE, BARN, PARLOUR; DRAW the other way
t1_segments( a, b, dir )
{
    ia = t1_index( a );
    ib = t1_index( b );
    if ( dir == "BLOW" )
        return ( ib - ia + 4 ) % 4;
    return ( ia - ib + 4 ) % 4;
}

t1_price( p, segs )
{
    c = level.iwz_t1.price[segs];
    if ( isdefined( p ) && scripts\engine\utility::is_true( p.iwz_bon_voyages ) )
        c = int( c / 2 );
    return c;
}

t1_lamps( segs )
{
    if ( segs == 1 )
        return "*";
    if ( segs == 2 )
        return "**";
    return "***";
}

// the next unsealed address after the dial's current one (never the hatch itself); -1 when none
t1_next_address( h )
{
    s = level.iwz_t1;
    me = t1_index( h.iwz_id );
    start = h.iwz_dial;
    if ( start < 0 )
        start = me;
    for ( k = 1; k <= 4; k++ )
    {
        i = ( start + k ) % 4;
        if ( i == me )
            continue;
        o = s.hatches[s.ring[i]];
        if ( isdefined( o ) && !o.iwz_sealed )
            return i;
    }
    return -1;
}

t1_hints()
{
    s = level.iwz_t1;
    foreach ( h in s.hatches )
        t1_hint( h );
    if ( isdefined( s.lever ) )
    {
        if ( gettime() < s.changeover_until )
            s.lever sethintstring( "BELLOWS: CHANGEOVER (all lamps amber)" );
        else if ( gettime() < s.lever_ready_at )
            s.lever sethintstring( "BELLOWS LEVER: " + s.dir + " (resetting)" );
        else
            s.lever sethintstring( "BELLOWS LEVER: " + s.dir + " - Use to throw" );
    }
}

t1_hint( h )
{
    s = level.iwz_t1;
    if ( !scripts\engine\utility::flag( "power_on" ) )
        return;
    if ( h.iwz_sealed )
    {
        h sethintstring( "Hold Use: unseal the " + h.iwz_id + " hatch (750)" );
        return;
    }
    if ( gettime() < h.iwz_insp_until )
    {
        h sethintstring( h.iwz_id + ": INSPECTION" );
        return;
    }
    if ( gettime() < s.changeover_until )
    {
        h sethintstring( h.iwz_id + ": CHANGEOVER (all lamps amber)" );
        return;
    }
    if ( h.iwz_dial < 0 || s.hatches[s.ring[h.iwz_dial]].iwz_sealed )
        h.iwz_dial = t1_next_address( h );
    if ( h.iwz_dial < 0 )
    {
        h sethintstring( h.iwz_id + ": NO OTHER HATCH UNSEALED (TUBE SEALED)" );
        return;
    }
    to = s.ring[h.iwz_dial];
    segs = t1_segments( h.iwz_id, to, s.dir );
    h sethintstring( "To " + to + " " + t1_lamps( segs ) + " " + s.price[segs] + " - tap Use: next address, hold Use: send" );
}

// ---------------------------------------------------------------------------------------------- use

t1_hold( p, ent, seconds )
{
    if ( ( getdvar( "gamelab" ) != "" || getdvar( "soak_driver" ) == "1" ) && getdvar( "iwz_test_hold" ) != "" )
        return getdvarint( "iwz_test_hold" ) == 1;
    t = 0;
    while ( t < seconds )
    {
        if ( !isdefined( p ) || !isalive( p ) || !p usebuttonpressed() || distance( p.origin, ent.origin ) > 140 )
            return 0;
        wait 0.05;
        t += 0.05;
    }
    return 1;
}

t1_downed( p )
{
    return scripts\engine\utility::is_true( p.inlaststand );
}

t1_hatch_use()
{
    level endon( "game_ended" );
    for ( ;; )
    {
        self waittill( "trigger", p );
        if ( !isplayer( p ) || isdefined( p.iwz_t1_pressing ) )
            continue;
        level thread t1_press( self, p );
    }
}

t1_press( h, p )
{
    level endon( "game_ended" );
    s = level.iwz_t1;
    p.iwz_t1_pressing = 1;
    if ( !scripts\engine\utility::flag( "power_on" ) )
    {
        t1_refuse( p, h, "power", "THE BELLOWS IS COLD: NO POWER" );
    }
    else if ( h.iwz_sealed )
    {
        if ( t1_hold( p, h, 1.5 ) )
            t1_unseal( h, p );
        else if ( isdefined( p ) )
            t1_msg( p, "HOLD USE ON THE PRESSURE WHEEL TO UNSEAL", 1.5 );
    }
    else
    {
        held = t1_hold( p, h, 0.8 );
        if ( isdefined( p ) )
        {
            if ( held )
                t1_send( h, p, -1 );
            else
                t1_dial( h, p );
        }
    }
    if ( isdefined( p ) )
        p.iwz_t1_pressing = undefined;
}

t1_unseal( h, p )
{
    s = level.iwz_t1;
    if ( !h.iwz_sealed )
        return;
    if ( !p scripts\cp\cp_persistence::player_has_enough_currency( 750 ) )
    {
        t1_refuse( p, h, "points", "NOT ENOUGH POINTS (750)" );
        return;
    }
    p scripts\cp\cp_persistence::take_player_currency( 750, 1, "door" );
    h.iwz_sealed = 0;
    s.unsealed++;
    t1_sound( h, "purchase_generic" );
    t1_fx( "iwz_rail_spark", h.origin );
    t1_log( "UNSEAL hatch=" + h.iwz_id + " by=" + p.name + " unsealed=" + s.unsealed );
    t1_msg( p, h.iwz_id + " HATCH UNSEALED", 2 );
    t1_hints();
}

t1_dial( h, p )
{
    s = level.iwz_t1;
    n = t1_next_address( h );
    if ( n < 0 )
    {
        t1_refuse( p, h, "sealed", "TUBE SEALED: NO OTHER HATCH IS OPEN" );
        return;
    }
    if ( n == h.iwz_dial )
        return;          // a dial with one address does nothing
    h.iwz_dial = n;
    t1_local_sound( p, "zmb_wheel_spin_tick" );
    t1_hint( h );
    t1_log( "DIAL hatch=" + h.iwz_id + " to=" + s.ring[n] + " by=" + p.name );
}

t1_refuse( p, h, why, text )
{
    s = level.iwz_t1;
    s.refusals++;
    if ( !isdefined( s.refused[why] ) )
        s.refused[why] = 0;
    s.refused[why]++;
    if ( isdefined( p ) )
    {
        t1_local_sound( p, "purchase_deny" );
        t1_msg( p, text, 2 );
    }
    name = "none";
    if ( isdefined( p ) )
        name = p.name;
    t1_log( "REFUSE why=" + why + " hatch=" + h.iwz_id + " by=" + name + " n=" + s.refused[why] );
    return 0;
}

t1_inspected( h )
{
    return gettime() < h.iwz_insp_until;
}

// send the player from hatch h to ring address 'to' (-1: the dial's address); every refusal is checked before anything
// is taken. Returns 1 when the ride started.
t1_send( h, p, to )
{
    s = level.iwz_t1;
    if ( to < 0 )
        to = h.iwz_dial;
    if ( t1_downed( p ) )
        return t1_refuse( p, h, "downed", "DOWNED RIDERS CANNOT BOARD" );
    if ( isdefined( p.iwz_busy ) )
        return t1_refuse( p, h, "busy", "NOT NOW" );
    if ( gettime() < s.changeover_until )
        return t1_refuse( p, h, "changeover", "CHANGEOVER: ALL LAMPS AMBER" );
    if ( t1_inspected( h ) )
        return t1_refuse( p, h, "inspection", "INSPECTION: THIS HATCH IS CLOSED" );
    if ( h.iwz_sealed || to < 0 || !isdefined( s.hatches[s.ring[to]] ) || s.hatches[s.ring[to]].iwz_sealed || s.ring[to] == h.iwz_id )
        return t1_refuse( p, h, "sealed", "TUBE SEALED" );
    if ( isdefined( p.iwz_t1_rest_until ) && gettime() < p.iwz_t1_rest_until )
        return t1_refuse( p, h, "rest", "REST: YOU HAVE JUST ARRIVED" );
    cap = -1;
    for ( k = 0; k < h.iwz_caps.size; k++ )
    {
        if ( gettime() >= h.iwz_caps[k] )
        {
            cap = k;
            break;
        }
    }
    if ( cap < 0 )
        return t1_refuse( p, h, "capsule", "NO CAPSULE: WAIT FOR ONE TO RETURN" );
    segs = t1_segments( h.iwz_id, s.ring[to], s.dir );
    price = t1_price( p, segs );
    if ( !p scripts\cp\cp_persistence::player_has_enough_currency( price ) )
        return t1_refuse( p, h, "points", "NOT ENOUGH POINTS (" + price + ")" );
    // from here nothing waits: the first of two players on the last capsule wins it, the second is refused above
    h.iwz_caps[cap] = gettime() + 30000;
    p scripts\cp\cp_persistence::take_player_currency( price, 1, "trap" );
    p.iwz_busy = "post";
    level thread t1_ride( h, s.hatches[s.ring[to]], p, segs, price, cap );
    return 1;
}

t1_ride( from, to, p, segs, price, cap )
{
    level endon( "game_ended" );
    s = level.iwz_t1;
    s.rides++;
    s.riding++;
    secs = s.ride_s[segs];
    name = p.name;
    t0 = gettime();
    // blowback: up to three zombies touching the hatch go into the tube behind the rider
    bb = [];
    if ( isdefined( level.spawned_enemies ) )
    {
        foreach ( z in level.spawned_enemies )
        {
            if ( bb.size < 3 && isdefined( z ) && isalive( z ) && distance2d( z.origin, from.iwz_out ) < 48 + 40 && abs( z.origin[2] - from.iwz_out[2] ) < 72 )
                bb[bb.size] = z;
        }
    }
    s.blowback += bb.size;
    t1_log( "LAUNCH from=" + from.iwz_id + " to=" + to.iwz_id + " segs=" + segs + " price=" + price + " s=" + secs + " dir=" + s.dir + " capsule=" + cap + " by=" + name + " blowback=" + bb.size + " ride=" + s.rides );
    t1_sound( from, "ftl_phase_out" );
    t1_fx( "iwz_rail_arc", from.origin );
    // drawn in: hidden and held where they stood (scripted, ignoring everyone) until they come out at the destination
    foreach ( z in bb )
    {
        z hide();
        z.ignoreall = 1;
        z.scripted_mode = 1;
        z.iwz_t1_tube = 1;
        z scragentsetgoalpos( z.origin );
    }
    // the rider: protected, frozen, hidden, behind a black screen, already standing in the destination zone
    p scripts\cp\utility::adddamagemodifier( "iwz_t1_ride", 0.0, 0 );
    p.is_off_grid = 1;
    p.iwz_t1_ignore = p.ignoreme;
    p.ignoreme = 1;
    p freezecontrols( 1 );
    bon = scripts\engine\utility::is_true( p.iwz_bon_voyages );
    if ( !bon )
        p disableweapons();
    p t1_black( 1 );
    p playlocalsound( "zmb_portal_travel_lr" );
    p earthquakeforplayer( 0.25, secs, p.origin, 200 );
    hold = to.iwz_out + anglestoforward( to.angles ) * -8;
    p playerhide();
    p dontinterpolate();
    p setvelocity( ( 0, 0, 0 ) );
    p setorigin( hold );
    lab = getdvar( "gamelab" ) != "";
    for ( e = 0; e < secs * 1000; e += 250 )
    {
        if ( !isdefined( p ) )
            break;
        if ( lab )
            print( "[IWZ level] T1 RIDE_S ride=" + s.rides + " ms=" + e + " origin=" + p.origin + " zone=" + t1_zone_of( p.origin ) + " volume=" + t1_touching( p ) );
        wait 0.25;
    }
    s.riding--;
    if ( !isdefined( p ) )
    {
        // the rider left mid-ride: the capsule completes empty and returns on its own time; nothing stays linked or frozen
        t1_log( "RIDER_LEFT ride=" + s.rides + " from=" + from.iwz_id + " to=" + to.iwz_id );
        level thread t1_blowback_out( bb, to );
        return;
    }
    // arrival: a player standing on the hatch is moved aside
    foreach ( o in level.players )
    {
        if ( isdefined( o ) && o != p && isalive( o ) && distance2d( o.origin, to.iwz_out ) < 32 )
        {
            side = to.iwz_out + anglestoright( to.angles ) * 64;
            g = getclosestpointonnavmesh( side );
            if ( isdefined( g ) )
                o setorigin( g );
            t1_log( "PUSHED player=" + o.name + " hatch=" + to.iwz_id );
        }
    }
    g = playerphysicstrace( to.iwz_out + ( 0, 0, 32 ), to.iwz_out - ( 0, 0, 64 ) );
    p setorigin( g );
    p setplayerangles( to.angles );
    p playershow();
    p freezecontrols( 0 );
    if ( !bon )
        p enableweapons();      // the weapon comes up as it is drawn: no slow-down
    p t1_black( 0 );
    p scripts\cp\utility::removedamagemodifier( "iwz_t1_ride", 0 );
    p.is_off_grid = undefined;
    p.ignoreme = p.iwz_t1_ignore;
    p.iwz_busy = undefined;
    p.iwz_t1_rest_until = gettime() + 45000;
    t1_sound( to, "ftl_phase_in" );
    t1_fx( "iwz_rail_spark", to.origin );
    s.arrivals++;
    s.last = spawnstruct();
    s.last.from = from.iwz_id;
    s.last.to = to.iwz_id;
    s.last.ms = gettime() - t0;
    s.last.origin = p.origin;
    s.last.zone = t1_zone_of( p.origin );
    s.last.volume = t1_touching( p );
    s.last.price = price;
    s.last.segs = segs;
    s.last.blowback = bb.size;
    t1_log( "ARRIVE to=" + to.iwz_id + " by=" + p.name + " ms=" + s.last.ms + " origin=" + p.origin + " zone=" + s.last.zone + " volume=" + s.last.volume + " arrivals=" + s.arrivals );
    level thread t1_blowback_out( bb, to );
}

// blown-back zombies come out of the destination hatch 2 s after the rider
t1_blowback_out( bb, to )
{
    level endon( "game_ended" );
    wait 2;
    n = 0;
    foreach ( z in bb )
    {
        if ( !isdefined( z ) || !isalive( z ) )
            continue;
        q = getclosestpointonnavmesh( to.iwz_out + ( randomintrange( -32, 32 ), randomintrange( -32, 32 ), 0 ) );
        if ( isdefined( q ) )
        {
            z setorigin( q, 1 );
            z scragentsetgoalpos( q );
        }
        z show();
        n++;
    }
    level.iwz_t1.blowback_out += n;
    if ( bb.size )
        t1_log( "BLOWBACK_OUT hatch=" + to.iwz_id + " n=" + n + " of=" + bb.size + " total=" + level.iwz_t1.blowback_out );
    // thrown out and down for 1 s, then they behave normally
    wait 1;
    foreach ( z in bb )
    {
        if ( !isdefined( z ) || !isalive( z ) )
            continue;
        z.ignoreall = 0;
        z.scripted_mode = 0;
        z.iwz_t1_tube = undefined;
    }
}

// test entry (03-TRANSPORT.md section 7): ride without Use, from hatch 'from' to hatch 'to' (ids); same rules
t1_test_ride( p, from, to )
{
    s = level.iwz_t1;
    h = s.hatches[from];
    i = t1_index( to );
    if ( !isdefined( h ) || i < 0 || !isdefined( p ) )
        return 0;
    return t1_send( h, p, i );
}

// ---------------------------------------------------------------------------------------------- the Bellows lever

t1_lever_use()
{
    level endon( "game_ended" );
    s = level.iwz_t1;
    for ( ;; )
    {
        self waittill( "trigger", p );
        if ( !isplayer( p ) )
            continue;
        if ( !scripts\engine\utility::flag( "power_on" ) )
        {
            t1_local_sound( p, "purchase_deny" );
            t1_msg( p, "THE BELLOWS IS COLD: NO POWER", 2 );
            continue;
        }
        if ( gettime() < s.changeover_until || gettime() < s.lever_ready_at )
        {
            t1_local_sound( p, "purchase_deny" );
            t1_msg( p, "THE LEVER IS RESETTING", 2 );
            s.refusals++;
            continue;
        }
        s.lever_throws++;
        s.changeover_until = gettime() + 12000;
        t1_log( "LEVER thrown by=" + p.name + " from=" + s.dir + " throws=" + s.lever_throws );
        t1_sound( self, "trap_rocket_start" );
        self rotateto( self.iwz_base + ( 0, 0, 70 ), 0.5 );
        t1_hints();
        level thread t1_changeover();
    }
}

t1_changeover()
{
    level endon( "game_ended" );
    s = level.iwz_t1;
    foreach ( p in level.players )
        t1_msg( p, "THE BELLOWS CHANGES OVER: ALL LAMPS AMBER", 3 );
    wait 12;
    if ( s.dir == "BLOW" )
        s.dir = "DRAW";
    else
        s.dir = "BLOW";
    s.lever_ready_at = gettime() + 45000;
    s.lever rotateto( s.lever.iwz_base, 0.5 );
    t1_sound( s.lever, "trap_waterfall_valve" );
    t1_log( "LEVER changed dir=" + s.dir );
    t1_hints();
    wait 45.5;
    t1_hints();
}

// ---------------------------------------------------------------------------------------------- the Night Inspector

t1_inspection_watch()
{
    level endon( "game_ended" );
    s = level.iwz_t1;
    for ( ;; )
    {
        list = [];
        if ( isdefined( level.iwz_inspector ) )
        {
            if ( isarray( level.iwz_inspector ) )
                list = level.iwz_inspector;
            else
                list[0] = level.iwz_inspector;
        }
        changed = 0;
        foreach ( h in s.hatches )
        {
            near = 0;
            foreach ( e in list )
            {
                if ( isdefined( e ) && distance( e.origin, h.origin ) < 300 )
                    near = 1;
            }
            was = t1_inspected( h );
            if ( near )
                h.iwz_insp_until = gettime() + 15000;
            if ( was != t1_inspected( h ) )
            {
                changed = 1;
                t1_log( "INSPECTION hatch=" + h.iwz_id + " closed=" + t1_inspected( h ) );
            }
        }
        if ( changed )
            t1_hints();
        wait 0.5;
    }
}

// ---------------------------------------------------------------------------------------------- per-player text

t1_players()
{
    level endon( "game_ended" );
    foreach ( p in level.players )
        p thread t1_player_hud();
    for ( ;; )
    {
        level waittill( "connected", p );
        p thread t1_player_hud();
    }
}

t1_player_hud()
{
    self endon( "disconnect" );
    if ( isdefined( self.iwz_t1_msg ) )
        return;
    m = newclienthudelem( self );
    m.x = 0;
    m.y = 122;
    m.alignx = "center";
    m.aligny = "middle";
    m.horzalign = "center";
    m.vertalign = "middle";
    m.fontscale = 1.3;
    m.color = ( 1, 0.86, 0.55 );
    m.alpha = 0;
    m.sort = 3;
    m.hidewheninmenu = 1;
    m settext( "" );
    self.iwz_t1_msg = m;
}

t1_msg( p, text, seconds )
{
    if ( !isdefined( p ) || !isdefined( p.iwz_t1_msg ) )
        return;
    p notify( "iwz_t1_msg" );
    p.iwz_t1_msg settext( text );
    p.iwz_t1_msg.alpha = 1;
    p thread t1_msg_fade( seconds );
}

t1_msg_fade( seconds )
{
    self endon( "disconnect" );
    self endon( "iwz_t1_msg" );
    wait seconds;
    if ( isdefined( self.iwz_t1_msg ) )
    {
        self.iwz_t1_msg fadeovertime( 0.5 );
        self.iwz_t1_msg.alpha = 0;
    }
}

// the black-out of a version 1 ride (the visible ride is T2)
t1_black( on )
{
    if ( on )
    {
        if ( !isdefined( self.iwz_t1_black ) )
        {
            b = newclienthudelem( self );
            b.x = 0;
            b.y = 0;
            b setshader( "black", 640, 480 );
            b.alignx = "left";
            b.aligny = "top";
            b.horzalign = "fullscreen";
            b.vertalign = "fullscreen";
            b.sort = 1;
            b.foreground = 1;
            b.alpha = 0;
            self.iwz_t1_black = b;
        }
        self.iwz_t1_black fadeovertime( 0.3 );
        self.iwz_t1_black.alpha = 1;
    }
    else if ( isdefined( self.iwz_t1_black ) )
    {
        self.iwz_t1_black fadeovertime( 0.4 );
        self.iwz_t1_black.alpha = 0;
    }
}

// a match that ends during a ride: the riders are let go first
t1_end_cleanup()
{
    level waittill( "game_ended" );
    foreach ( p in level.players )
    {
        if ( isdefined( p ) && isdefined( p.iwz_busy ) && p.iwz_busy == "post" )
        {
            p playershow();
            p enableweapons();
            p.is_off_grid = undefined;
            p.iwz_busy = undefined;
            p t1_black( 0 );
        }
    }
}
