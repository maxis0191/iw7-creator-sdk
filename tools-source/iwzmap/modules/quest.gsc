// Station Zero, package Q1: the road to Pack-a-Punch (iw7-creator-sdk docs/station-zero/04-PAP-QUEST.md).
// Power (stock generator) -> four clocks wound (hold Use 3 s, a burst of zombies each) -> the road set in the Signal Cabin
// (three lit levers of eight, random per match) -> the Conductor of 047 (3x health, walks; drops the Dead-Man's Handle)
// -> the Handle fitted in the cab of car 1 (hold Use 1.5 s) -> the teleport is armed: boarding 4 s, crossing 3 s,
// 40 s at the Terminus (the clock runs 23:59:19 to 23:59:59), back to car 1, 150 s "NOT IN SERVICE".
// Version 1: stand-in stock models, stock sound aliases, stock effects; the hero objects are HO1, the board W5, the Tab H1.
// Self-contained (no call by path): runs from the map zone (scripts/cp/maps/<map>/<map>_quest.gsc, started by the level
// script) or as a server custom script on an already built map. Every state change prints "[IWZ level] Q1 ..." and the
// whole state is in level.iwz_q1 (read as data by the gamelab library szq).
// Test entry (lab sessions only, dvar "gamelab" set): dvar iwz_test_hold 1 = a Use counts as held, 0 = as a tap.

init()
{
    if ( getdvar( "mapname" ) != "cp_iwz" || isdefined( level.iwz_q1 ) )
        return;
    q = spawnstruct();
    level.iwz_q1 = q;
    q.lever_names = [ "BYPASS UP", "BYPASS DOWN", "CROSSOVER", "ZERO", "MAIN UP", "MAIN DOWN", "SIDING", "SHUNT" ];
    q.clocks = [];
    q.clocks_wound = 0;
    q.levers = [];
    q.lit = [];
    q.pulled = 0;
    q.wrong = 0;
    q.road_set = 0;
    q.conductor_state = "none";
    q.conductor_spawns = 0;
    q.handle_state = "none";
    q.armed = 0;
    q.tp_state = "idle";
    q.visits = 0;
    q.travellers = 0;
    q.returned = 0;
    q.pushed_out = 0;
    q.paused = 0;
    q.pause_seconds = 0;
    q.bursts = 0;
    q.burst_made = 0;
    q.events = 0;
    q.board = "047 - POWER: G-2 OFFLINE - CONVERTER HALL";
    q.markers = q1_markers();
    // a new random set of three lit levers per match (the step resets between matches)
    idx = [ 0, 1, 2, 3, 4, 5, 6, 7 ];
    for ( i = 7; i > 0; i-- )
    {
        j = randomint( i + 1 );
        t = idx[i];
        idx[i] = idx[j];
        idx[j] = t;
    }
    q.lit_idx = [ idx[0], idx[1], idx[2] ];
    q1_log( "INIT lit=" + q.lever_names[idx[0]] + "," + q.lever_names[idx[1]] + "," + q.lever_names[idx[2]] + " markers=" + q.markers.size );
    level thread q1_main();
}

// filled by the emit (sz_modules.py): [ kind, id, zone, origin, yaw ( , lo, hi ) ]
q1_markers()
{
    m = [];
    //@MARKERS@
    return m;
}

q1_marker( kind, id )
{
    foreach ( m in level.iwz_q1.markers )
    {
        if ( m[0] == kind && ( id == "" || m[1] == id ) )
            return m;
    }
    return undefined;
}

q1_markers_of( kind )
{
    out = [];
    foreach ( m in level.iwz_q1.markers )
    {
        if ( m[0] == kind )
            out[out.size] = m;
    }
    return out;
}

q1_log( text )
{
    level.iwz_q1.events++;
    print( "[IWZ level] Q1 " + text + " t=" + gettime() );
}

q1_main()
{
    level endon( "game_ended" );
    q = level.iwz_q1;
    level thread q1_players();
    level thread q1_end_cleanup();
    wait 1;
    q1_sounds_check();
    q1_spawn_clocks();
    q1_spawn_levers();
    q1_spawn_cab();
    q1_spawn_terminus_clock();
    while ( !scripts\engine\utility::flag_exist( "power_on" ) )
        wait 0.5;
    scripts\engine\utility::flag_wait( "power_on" );
    q1_log( "POWER on" );
    q1_board( "047 - DUE 00:00 - NOW --:-- - CLOCKS 0/4" );
    foreach ( c in q.clocks )
        c sethintstring( "Hold Use to wind the clock (stopped at 23:47)" );
    level thread q1_round_watch();
}

// ---------------------------------------------------------------------------------------------- shared helpers

// a Use held for 'seconds' by a player who stays near and on his feet; lab sessions can answer for a bot (no buttons)
q1_hold( p, ent, seconds )
{
    if ( ( getdvar( "gamelab" ) != "" || getdvar( "soak_driver" ) == "1" ) && getdvar( "iwz_test_hold" ) != "" )
        return getdvarint( "iwz_test_hold" ) == 1;
    t = 0;
    while ( t < seconds )
    {
        if ( !isdefined( p ) || !isalive( p ) || q1_downed( p ) || !p usebuttonpressed() || distance( p.origin, ent.origin ) > 140 )
            return 0;
        wait 0.05;
        t += 0.05;
    }
    return 1;
}

q1_downed( p )
{
    return scripts\engine\utility::is_true( p.inlaststand );
}

q1_sound( ent, alias )
{
    if ( isdefined( level.iwz_q1.sounds[alias] ) && level.iwz_q1.sounds[alias] )
        ent playsound( alias );
}

q1_local_sound( p, alias )
{
    if ( isdefined( level.iwz_q1.sounds[alias] ) && level.iwz_q1.sounds[alias] )
        p playlocalsound( alias );
}

// which stock aliases this map's zone really has (printed: read as data, not assumed)
q1_sounds_check()
{
    q = level.iwz_q1;
    q.sounds = [];
    have = 0;
    names = [ "zmb_shooting_gal_bell", "zmb_challenge_complete", "zmb_shooting_gal_buzz", "trap_waterfall_valve", "purchase_deny", "zmb_challenge_start", "zmb_item_pickup", "zmb_packapunch_machine_on", "zmb_portal_travel_lr", "zmb_wheel_spin_tick", "purchase_generic" ];
    foreach ( n in names )
    {
        q.sounds[n] = soundexists( n );
        if ( q.sounds[n] )
            have++;
    }
    q1_log( "SOUNDS have=" + have + " of=" + names.size );
}

q1_fx( name, origin )
{
    if ( isdefined( level._effect ) && isdefined( level._effect[name] ) )
        playfx( level._effect[name], origin );
}

q1_usable( model, origin, yaw, name, hint )
{
    e = spawn( "script_model", origin );
    e setmodel( model );
    e.angles = ( 0, yaw, 0 );
    e.targetname = name;
    e makeusable();
    e sethintstring( hint );
    return e;
}

// the zone (spawn volume name) a point is in, from the emitted volume table
q1_zone_of( p )
{
    foreach ( v in q1_volumes() )
    {
        if ( p[0] >= v[2][0] && p[0] <= v[3][0] && p[1] >= v[2][1] && p[1] <= v[3][1] && p[2] >= v[2][2] && p[2] <= v[3][2] )
            return v[1];
    }
    return "none";
}

q1_volumes()
{
    if ( isdefined( level.iwz_q1.vols ) )
        return level.iwz_q1.vols;
    v = [];
    //@VOLUMES@
    level.iwz_q1.vols = v;
    return v;
}

q1_in_box( p, lo, hi )
{
    return p[0] >= lo[0] && p[0] <= hi[0] && p[1] >= lo[1] && p[1] <= hi[1] && p[2] >= lo[2] && p[2] <= hi[2];
}

// ---------------------------------------------------------------------------------------------- per-player text

q1_players()
{
    level endon( "game_ended" );
    foreach ( p in level.players )
        p thread q1_player_hud();
    for ( ;; )
    {
        level waittill( "connected", p );
        p thread q1_player_hud();
    }
}

// one board line (the departure board, until W5's plates) and one message line per player; a late joiner gets the board
q1_player_hud()
{
    self endon( "disconnect" );
    if ( isdefined( self.iwz_q1_board ) )
        return;
    b = newclienthudelem( self );
    b.x = 0;
    b.y = 22;
    b.alignx = "center";
    b.aligny = "top";
    b.horzalign = "center";
    b.vertalign = "top";
    b.fontscale = 1.1;
    b.color = ( 1, 0.78, 0.35 );
    b.alpha = 0.9;
    b.sort = 2;
    b.hidewheninmenu = 1;
    b settext( level.iwz_q1.board );
    self.iwz_q1_board = b;
    m = newclienthudelem( self );
    m.x = 0;
    m.y = 96;
    m.alignx = "center";
    m.aligny = "middle";
    m.horzalign = "center";
    m.vertalign = "middle";
    m.fontscale = 1.3;
    m.color = ( 1, 1, 1 );
    m.alpha = 0;
    m.sort = 3;
    m.hidewheninmenu = 1;
    m settext( "" );
    self.iwz_q1_msg = m;
}

q1_board( text )
{
    level.iwz_q1.board = text;
    q1_log( "BOARD " + text );
    foreach ( p in level.players )
    {
        if ( isdefined( p.iwz_q1_board ) )
            p.iwz_q1_board settext( text );
    }
}

q1_msg( p, text, seconds )
{
    if ( !isdefined( p ) || !isdefined( p.iwz_q1_msg ) )
        return;
    p notify( "iwz_q1_msg" );
    p.iwz_q1_msg settext( text );
    p.iwz_q1_msg.alpha = 1;
    p thread q1_msg_fade( seconds );
}

q1_msg_fade( seconds )
{
    self endon( "disconnect" );
    self endon( "iwz_q1_msg" );
    wait seconds;
    if ( isdefined( self.iwz_q1_msg ) )
    {
        self.iwz_q1_msg fadeovertime( 0.5 );
        self.iwz_q1_msg.alpha = 0;
    }
}

q1_msg_all( text, seconds )
{
    foreach ( p in level.players )
        q1_msg( p, text, seconds );
}

// ---------------------------------------------------------------------------------------------- step 1: the clocks

q1_spawn_clocks()
{
    q = level.iwz_q1;
    foreach ( m in q1_markers_of( "quest_clock" ) )
    {
        c = q1_usable( "com_fire_bell_iw6", m[3] + ( 0, 0, 88 ), m[4], "iwz_q1_" + m[1], "Stopped at 23:47. The winding key is cold (no power)" );
        c.iwz_id = m[1];
        c.iwz_zone = m[2];
        c.iwz_wound = 0;
        q.clocks[q.clocks.size] = c;
        c thread q1_clock_use();
    }
    q1_log( "CLOCKS placed=" + q.clocks.size );
}

q1_clock_use()
{
    level endon( "game_ended" );
    q = level.iwz_q1;
    for ( ;; )
    {
        self waittill( "trigger", p );
        if ( !isplayer( p ) || self.iwz_wound )
            continue;
        if ( !scripts\engine\utility::flag( "power_on" ) )
        {
            q1_msg( p, "THE CLOCK WILL NOT TURN: NO POWER", 2 );
            q1_local_sound( p, "purchase_deny" );
            continue;
        }
        if ( isdefined( self.iwz_busy ) )
            continue;
        self.iwz_busy = 1;
        q1_local_sound( p, "zmb_wheel_spin_tick" );
        ok = q1_hold( p, self, 3 );
        self.iwz_busy = undefined;
        if ( !ok )
        {
            q1_msg( p, "KEEP HOLDING USE TO WIND THE CLOCK", 1.5 );
            continue;
        }
        self.iwz_wound = 1;
        q.clocks_wound++;
        self makeunusable();
        self rotateyaw( 390, 1.5 );
        q1_sound( self, "zmb_shooting_gal_bell" );
        q1_fx( "iwz_rail_spark", self.origin );
        q1_log( "CLOCK wound id=" + self.iwz_id + " zone=" + self.iwz_zone + " by=" + p.name + " clocks=" + q.clocks_wound );
        q1_msg_all( "A CLOCK STRIKES TWELVE (" + q.clocks_wound + "/4)", 3 );
        // the Three-Tone and a burst in that zone: 4 solo, 6 with two or three players, 8 with four or more
        n = 4;
        if ( level.players.size >= 4 )
            n = 8;
        else if ( level.players.size >= 2 )
            n = 6;
        level thread q1_burst( self.origin, n, "clock_" + self.iwz_id );
        if ( q.clocks_wound >= q.clocks.size && q.clocks.size > 0 )
        {
            q1_board( "047 - DUE 00:00 - SET THE ROAD: SIGNAL CABIN" );
            q1_log( "STEP1 done" );
            q1_levers_ready();
        }
        else
            q1_board( "047 - DUE 00:00 - NOW --:-- - CLOCKS " + q.clocks_wound + "/4" );
    }
}

// zombies from the spawners nearest the point, on top of the round (reserved: they neither use nor end the round's count)
q1_burst( origin, n, why )
{
    level endon( "game_ended" );
    q = level.iwz_q1;
    q.bursts++;
    made = 0;
    sp = q1_spawner_near( origin );
    if ( !isdefined( sp ) )
    {
        q1_log( "BURST why=" + why + " made=0 want=" + n + " reason=no_spawner" );
        return;
    }
    tries = 0;
    while ( made < n && tries < n * 4 )
    {
        tries++;
        z = sp scripts\cp\zombies\zombies_spawning::spawn_wave_enemy( "generic_zombie", 1 );
        if ( !isdefined( z ) )
        {
            wait 0.5;
            continue;
        }
        z.is_reserved = 1;
        level.current_num_spawned_enemies--;
        z.iwz_q1_burst = why;
        made++;
        wait 0.4;
    }
    q.burst_made += made;
    q1_log( "BURST why=" + why + " made=" + made + " want=" + n + " spawner=" + sp.origin );
}

q1_spawner_near( pos )
{
    best = undefined;
    bd = 9999999;
    if ( !isdefined( level.spawn_volume_array ) )
        return best;
    foreach ( v in level.spawn_volume_array )
    {
        if ( !isdefined( v.spawners ) )
            continue;
        foreach ( sp in v.spawners )
        {
            d = distance( sp.origin, pos );
            if ( d < bd )
            {
                bd = d;
                best = sp;
            }
        }
    }
    return best;
}

// ---------------------------------------------------------------------------------------------- step 2: the road

q1_spawn_levers()
{
    q = level.iwz_q1;
    k = 0;
    foreach ( m in q1_markers_of( "quest_lever" ) )
    {
        if ( k >= 8 )
            break;
        l = q1_usable( "icbm_electricpanel_switch_02", m[3] + ( 0, 0, 40 ), m[4], "iwz_q1_" + m[1], "Lever " + ( k + 1 ) + ": " + q.lever_names[k] + " (locked: the road waits for the clocks)" );
        l.iwz_k = k;
        l.iwz_pulled = 0;
        l.iwz_base = l.angles;
        q.levers[q.levers.size] = l;
        l thread q1_lever_use();
        k++;
    }
    d = q1_marker( "quest_diagram", "" );
    if ( isdefined( d ) )
    {
        q.diagram = q1_usable( "conduit_metal_outlet_switch", d[3] + ( 0, 0, 56 ), d[4], "iwz_q1_diagram", "Track diagram: dark" );
        q.diagram thread q1_diagram_use();
    }
    q1_log( "LEVERS placed=" + q.levers.size + " diagram=" + isdefined( q.diagram ) );
}

q1_lit_names()
{
    q = level.iwz_q1;
    return q.lever_names[q.lit_idx[0]] + " / " + q.lever_names[q.lit_idx[1]] + " / " + q.lever_names[q.lit_idx[2]];
}

q1_levers_ready()
{
    q = level.iwz_q1;
    if ( isdefined( q.diagram ) )
        q.diagram sethintstring( "Track diagram, lit: " + q1_lit_names() );
    foreach ( l in q.levers )
        q1_lever_hint( l );
}

q1_is_lit( k )
{
    q = level.iwz_q1;
    return k == q.lit_idx[0] || k == q.lit_idx[1] || k == q.lit_idx[2];
}

q1_lever_hint( l )
{
    q = level.iwz_q1;
    if ( q.road_set )
        l sethintstring( "Lever " + ( l.iwz_k + 1 ) + ": " + q.lever_names[l.iwz_k] + " (road set for 047)" );
    else if ( l.iwz_pulled )
        l sethintstring( "Lever " + ( l.iwz_k + 1 ) + ": " + q.lever_names[l.iwz_k] + " (locked over, lamp green)" );
    else
        l sethintstring( "Pull lever " + ( l.iwz_k + 1 ) + ": " + q.lever_names[l.iwz_k] );
}

q1_diagram_use()
{
    level endon( "game_ended" );
    for ( ;; )
    {
        self waittill( "trigger", p );
        if ( isplayer( p ) && level.iwz_q1.clocks_wound >= 4 )
            q1_msg( p, "THE DIAGRAM LIGHTS: " + q1_lit_names(), 4 );
    }
}

q1_lever_use()
{
    level endon( "game_ended" );
    q = level.iwz_q1;
    for ( ;; )
    {
        self waittill( "trigger", p );
        if ( !isplayer( p ) || q.road_set || self.iwz_pulled )
            continue;
        if ( q.clocks_wound < 4 )
        {
            q1_msg( p, "THE LEVER FRAME IS LOCKED: WIND THE FOUR CLOCKS", 2 );
            q1_local_sound( p, "purchase_deny" );
            continue;
        }
        if ( !q1_is_lit( self.iwz_k ) )
        {
            // a wrong lever: every pulled lever springs back, a buzzer, 4 zombies from the cabin
            q.wrong++;
            q.pulled = 0;
            foreach ( l in q.levers )
            {
                if ( l.iwz_pulled )
                {
                    l.iwz_pulled = 0;
                    l rotateto( l.iwz_base, 0.3 );
                    q1_lever_hint( l );
                }
            }
            q1_sound( self, "zmb_shooting_gal_buzz" );
            q1_log( "LEVER wrong k=" + self.iwz_k + " name=" + q.lever_names[self.iwz_k] + " by=" + p.name + " wrong=" + q.wrong );
            q1_msg( p, "WRONG LEVER: THE FRAME SPRINGS BACK", 2.5 );
            level thread q1_burst( self.origin, 4, "wrong_lever" );
            continue;
        }
        self.iwz_pulled = 1;
        q.pulled++;
        self rotateto( self.iwz_base + ( 0, 0, 70 ), 0.3 );
        q1_sound( self, "trap_waterfall_valve" );
        q1_lever_hint( self );
        q1_log( "LEVER right k=" + self.iwz_k + " name=" + q.lever_names[self.iwz_k] + " by=" + p.name + " pulled=" + q.pulled );
        if ( q.pulled >= 3 )
        {
            q.road_set = 1;
            foreach ( l in q.levers )
                q1_lever_hint( l );
            q1_board( "047 - ROAD SET FOR 047" );
            q1_msg_all( "ROAD SET FOR 047: THE SIGNAL DROPS TO GREEN", 3 );
            q1_sound( self, "zmb_challenge_complete" );
            q1_log( "STEP2 done" );
            level thread q1_conductor_cycle();
        }
    }
}

// ---------------------------------------------------------------------------------------------- step 3: the Conductor

q1_conductor_cycle()
{
    level endon( "game_ended" );
    q = level.iwz_q1;
    wait 5;      // he steps out within 20 s of the road being set
    while ( q.handle_state == "none" )
    {
        if ( q.conductor_state != "walking" )
            q1_conductor_spawn();
        // he leaves when the round ends and comes back at the start of the next one; he cannot be lost
        msg = level scripts\engine\utility::waittill_any_return( "iwz_q1_conductor_dead", "spawn_wave_done", "iwz_test_round_end" );
        if ( q.handle_state != "none" )
            break;
        if ( msg == "spawn_wave_done" || msg == "iwz_test_round_end" )
        {
            q1_conductor_leave();
            level scripts\engine\utility::waittill_any_timeout( 60, "regular_wave_starting", "iwz_test_round_start" );
            q1_log( "CONDUCTOR back" );
        }
    }
}

q1_conductor_spawn()
{
    q = level.iwz_q1;
    m = q1_marker( "quest_conductor", "" );
    if ( !isdefined( m ) )
        return;
    sp = q1_spawner_near( m[3] );
    // he waits for a free agent (the 24 can be full of the clocks' bursts) and comes as soon as one is free: he cannot be lost
    z = undefined;
    waited = 0;
    while ( !isdefined( z ) )
    {
        if ( isdefined( sp ) )
            z = sp scripts\cp\zombies\zombies_spawning::spawn_wave_enemy( "generic_zombie", 1 );
        if ( !isdefined( z ) )
        {
            if ( waited == 5 )
                q1_log( "CONDUCTOR waiting_for_agent alive=" + q1_alive_zombies() );
            waited++;
            wait 1;
        }
    }
    z.is_reserved = 1;
    level.current_num_spawned_enemies--;
    z.dont_cleanup = 1;
    z.iwz_conductor = 1;
    h = scripts\cp\zombies\zombies_spawning::calculatezombiehealth( "generic_zombie" );
    z.maxhealth = h * 3;
    z.health = h * 3;
    z.movemode = "walk";
    q.conductor = z;
    q.conductor_state = "walking";
    q.conductor_spawns++;
    q1_sound( z, "zmb_challenge_start" );
    q1_board( "047 - THE CONDUCTOR IS ON THE PLATFORM" );
    q1_log( "CONDUCTOR spawned health=" + z.health + " at=" + z.origin + " spawns=" + q.conductor_spawns );
    z thread q1_conductor_death();
}

q1_conductor_death()
{
    self waittill( "death", attacker );
    q = level.iwz_q1;
    // a Conductor removed at a round end is not a kill (the state is set before the damage; agent fields do not survive it)
    if ( q.conductor_state == "leaving" )
    {
        q.conductor_state = "left";
        return;
    }
    q.conductor_state = "dead";
    by = "none";
    if ( isdefined( attacker ) && isplayer( attacker ) )
        by = attacker.name;
    q1_log( "CONDUCTOR dead by=" + by + " at=" + self.origin );
    q1_handle_drop( self.origin );
    level notify( "iwz_q1_conductor_dead" );
}

q1_conductor_leave()
{
    q = level.iwz_q1;
    z = q.conductor;
    if ( !isdefined( z ) || !isalive( z ) || q.conductor_state != "walking" )
        return;
    q.conductor_state = "leaving";
    z dodamage( z.health + 1000, z.origin );
    q1_board( "047 - THE CONDUCTOR WILL RETURN NEXT ROUND" );
    q1_log( "CONDUCTOR left (round ended)" );
}

// the Handle lies where it fell, lit, until a player takes it
q1_handle_drop( origin )
{
    q = level.iwz_q1;
    if ( isdefined( q.handle ) )
        q.handle delete();
    g = playerphysicstrace( origin + ( 0, 0, 24 ), origin - ( 0, 0, 200 ) );
    q.handle = q1_usable( "park_air_hockey_paddle", g + ( 0, 0, 6 ), 0, "iwz_q1_handle", "Take the Dead-Man's Handle" );
    q.handle_state = "dropped";
    q.carrier = undefined;
    q1_fx( "iwz_rail_spark", g );
    q1_board( "047 - THE DEAD-MAN'S HANDLE LIES ON THE GROUND" );
    q1_log( "HANDLE dropped at=" + g );
    q.handle thread q1_handle_use();
}

q1_handle_use()
{
    level endon( "game_ended" );
    self endon( "death" );
    q = level.iwz_q1;
    for ( ;; )
    {
        self waittill( "trigger", p );
        if ( !isplayer( p ) || q1_downed( p ) || q.handle_state != "dropped" )
            continue;
        q.handle_state = "carried";
        q.carrier = p;
        q1_local_sound( p, "zmb_item_pickup" );
        q1_msg( p, "YOU CARRY THE DEAD-MAN'S HANDLE: FIT IT IN THE CAB OF CAR 1", 4 );
        q1_board( "047 - HANDLE CARRIED - THE CAB OF CAR 1" );
        q1_log( "HANDLE taken by=" + p.name );
        level thread q1_carrier_watch( p );
        q.handle = undefined;
        self delete();
        return;
    }
}

// a carrier who goes down or leaves drops the Handle where they are
q1_carrier_watch( p )
{
    level endon( "game_ended" );
    q = level.iwz_q1;
    o = p.origin;
    for ( ;; )
    {
        if ( q.handle_state != "carried" )
            return;
        if ( !isdefined( p ) )
        {
            q1_log( "HANDLE carrier_left" );
            q1_handle_drop( o );
            return;
        }
        if ( !isdefined( q.carrier ) || q.carrier != p )
            return;
        if ( q1_downed( p ) || !isalive( p ) )
        {
            q1_log( "HANDLE carrier_down by=" + p.name );
            q1_handle_drop( p.origin );
            return;
        }
        o = p.origin;
        wait 0.25;
    }
}

// ---------------------------------------------------------------------------------------------- step 4 and the teleport

q1_spawn_cab()
{
    q = level.iwz_q1;
    m = q1_marker( "quest_cab", "" );
    if ( !isdefined( m ) )
        return;
    q.car_lo = m[5];
    q.car_hi = m[6];
    q.cab = q1_usable( "conduit_metal_outlet_switch", m[3] + ( 0, 0, 48 ), m[4], "iwz_q1_cab", "DEAD-MAN'S HANDLE REQUIRED" );
    t = q1_marker( "terminus_arrival", "" );
    if ( isdefined( t ) )
    {
        q.term_spot = t[3];
        q.term_yaw = t[4];
        q.term_lo = t[5];
        q.term_hi = t[6];
    }
    q.cab thread q1_cab_use();
    q1_log( "CAB placed at=" + q.cab.origin + " terminus=" + isdefined( q.term_spot ) );
}

q1_cab_use()
{
    level endon( "game_ended" );
    q = level.iwz_q1;
    for ( ;; )
    {
        self waittill( "trigger", p );
        if ( !isplayer( p ) || q1_downed( p ) )
            continue;
        if ( !q.armed )
        {
            if ( q.handle_state != "carried" || !isdefined( q.carrier ) || q.carrier != p )
            {
                q1_msg( p, "DEAD-MAN'S HANDLE REQUIRED", 2 );
                q1_local_sound( p, "purchase_deny" );
                continue;
            }
            if ( !q1_hold( p, self, 1.5 ) )
            {
                q1_msg( p, "HOLD USE TO FIT THE HANDLE", 1.5 );
                continue;
            }
            q.armed = 1;
            q.handle_state = "fitted";
            q.carrier = undefined;
            q1_sound( self, "zmb_packapunch_machine_on" );
            self sethintstring( "Use the Dead-Man's Handle: depart for the TERMINUS" );
            q1_board( "047 - TERMINUS - BOARDING" );
            q1_msg_all( "047 TERMINUS: BOARDING", 3 );
            q1_log( "STEP4 done armed=1 by=" + p.name );
            continue;
        }
        if ( q.tp_state != "idle" )
        {
            if ( q.tp_state == "cooldown" )
                q1_msg( p, "NOT IN SERVICE", 1.5 );
            continue;
        }
        level thread q1_trip( p );
    }
}

q1_in_car( p )
{
    q = level.iwz_q1;
    return isdefined( q.car_lo ) && q1_in_box( p, q.car_lo, q.car_hi );
}

q1_in_terminus( p )
{
    q = level.iwz_q1;
    return isdefined( q.term_lo ) && q1_in_box( p, q.term_lo, q.term_hi );
}

q1_trip( starter )
{
    level endon( "game_ended" );
    q = level.iwz_q1;
    q.tp_state = "boarding";
    q.cab sethintstring( "BOARDING: the doors close in 4 s" );
    q1_log( "TRIP boarding by=" + starter.name );
    for ( i = 0; i < 2; i++ )
    {
        q1_sound( q.cab, "zmb_wheel_spin_tick" );
        wait 2;
    }
    // every player inside car 1 goes, downed players included; zombies inside are put out on the platform, unhurt
    travellers = [];
    foreach ( p in level.players )
    {
        if ( isdefined( p ) && isalive( p ) && q1_in_car( p.origin ) && !isdefined( p.iwz_busy ) )
            travellers[travellers.size] = p;
    }
    pushed = 0;
    if ( isdefined( level.spawned_enemies ) )
    {
        foreach ( z in level.spawned_enemies )
        {
            if ( isdefined( z ) && isalive( z ) && q1_in_car( z.origin ) )
            {
                out = getclosestpointonnavmesh( ( z.origin[0], q.car_hi[1] + 70, q.car_lo[2] + 10 ) );
                if ( isdefined( out ) )
                    z setorigin( out, 1 );
                pushed++;
            }
        }
    }
    q.pushed_out += pushed;
    if ( travellers.size == 0 )
    {
        q.tp_state = "idle";
        q.cab sethintstring( "Use the Dead-Man's Handle: depart for the TERMINUS" );
        q1_log( "TRIP nobody_aboard pushed=" + pushed );
        return;
    }
    q.tp_state = "crossing";
    q.visits++;
    q.travellers = travellers.size;
    downed = 0;
    foreach ( p in travellers )
    {
        if ( q1_downed( p ) )
            downed++;
    }
    q1_log( "TRIP depart travellers=" + travellers.size + " downed=" + downed + " pushed=" + pushed + " visit=" + q.visits );
    slot = 0;
    foreach ( p in travellers )
    {
        p.iwz_busy = "terminus";
        p thread q1_cross( q.term_spot + ( 0, ( slot % 4 ) * 48 - 72, 0 ), ( 0, q.term_yaw, 0 ), 3 );
        slot++;
    }
    wait 3.2;
    q.tp_state = "away";
    q1_board( "047 - AT THE TERMINUS" );
    q1_log( "TRIP arrived travellers=" + travellers.size );
    level thread q1_spawn_pause();
    // the only running clock of the map: 23:59:19 to 23:59:59, 40 s; midnight never comes
    for ( s = 19; s <= 59; s++ )
    {
        if ( isdefined( q.term_clock ) )
            q.term_clock sethintstring( "23:59:" + s );
        wait 1;
    }
    q.tp_state = "returning";
    level notify( "iwz_q1_return" );
    back = 0;
    slot = 0;
    foreach ( p in level.players )
    {
        if ( isdefined( p ) && isalive( p ) && q1_in_terminus( p.origin ) )
        {
            c = ( q.car_lo + q.car_hi ) * 0.5;
            spot = ( q.car_lo[0] + 80 + ( slot % 4 ) * 110, c[1], q.car_lo[2] + 14 );
            p thread q1_cross( spot, ( 0, 90, 0 ), 1 );
            back++;
            slot++;
        }
    }
    wait 1.2;
    foreach ( p in level.players )
    {
        if ( isdefined( p ) && isdefined( p.iwz_busy ) && p.iwz_busy == "terminus" )
            p.iwz_busy = undefined;
    }
    q.returned += back;
    if ( isdefined( q.term_clock ) )
        q.term_clock sethintstring( "23:59:59" );
    q1_log( "TRIP returned players=" + back + " visit=" + q.visits );
    // 150 s not in service: 40 s away in every 190 at most
    q.tp_state = "cooldown";
    q.cab sethintstring( "NOT IN SERVICE" );
    q1_board( "047 - NOT IN SERVICE" );
    wait 150;
    q.tp_state = "idle";
    q.cab sethintstring( "Use the Dead-Man's Handle: depart for the TERMINUS" );
    q1_board( "047 - TERMINUS - BOARDING" );
    q1_log( "TRIP ready" );
}

// the crossing: white light, the portal sound, the player placed; zombies do not see a player in transit
q1_cross( dest, angles, seconds )
{
    self endon( "disconnect" );
    self scripts\cp\utility::adddamagemodifier( "iwz_q1_cross", 0.0, 0 );
    self.is_off_grid = 1;
    self playlocalsound( "zmb_portal_travel_lr" );
    self earthquakeforplayer( 0.3, seconds, self.origin, 200 );
    self scripts\cp\zombies\zombie_afterlife_arcade::add_white_screen();
    wait seconds;
    g = playerphysicstrace( dest + ( 0, 0, 32 ), dest - ( 0, 0, 64 ) );
    self dontinterpolate();
    self setvelocity( ( 0, 0, 0 ) );
    self setorigin( g );
    self setplayerangles( angles );
    self thread scripts\cp\zombies\zombie_afterlife_arcade::remove_white_screen( 0.4 );
    self scripts\cp\utility::removedamagemodifier( "iwz_q1_cross", 0 );
    self.is_off_grid = undefined;
    q1_log( "CROSS player=" + self.name + " at=" + self.origin + " zone=" + q1_zone_of( self.origin ) + " downed=" + q1_downed( self ) );
}

// while every player on his feet is at the Terminus the round's spawning pauses (stock level.zombies_paused); it resumes
// when one is back outside or the visit ends. A downed player left outside does not hold the pause.
q1_spawn_pause()
{
    level endon( "game_ended" );
    q = level.iwz_q1;
    t0 = gettime();
    while ( q.tp_state == "away" )
    {
        all = 1;
        n = 0;
        foreach ( p in level.players )
        {
            if ( !isdefined( p ) || !isalive( p ) || q1_downed( p ) )
                continue;
            n++;
            if ( !q1_in_terminus( p.origin ) )
                all = 0;
        }
        want = all && n > 0;
        if ( want && !q.paused )
        {
            if ( !scripts\engine\utility::is_true( level.zombies_paused ) )
            {
                level.zombies_paused = 1;
                q.paused = 1;
                t0 = gettime();
                q1_log( "PAUSE on alive=" + q1_alive_zombies() );
            }
        }
        else if ( !want && q.paused )
            q1_unpause( t0 );
        wait 0.5;
    }
    if ( q.paused )
        q1_unpause( t0 );
}

q1_unpause( t0 )
{
    q = level.iwz_q1;
    level.zombies_paused = 0;
    q.paused = 0;
    q.pause_seconds += int( ( gettime() - t0 ) / 1000 );
    q1_log( "PAUSE off alive=" + q1_alive_zombies() + " paused_s=" + q.pause_seconds );
}

q1_alive_zombies()
{
    n = 0;
    if ( isdefined( level.spawned_enemies ) )
    {
        foreach ( z in level.spawned_enemies )
        {
            if ( isdefined( z ) && isalive( z ) )
                n++;
        }
    }
    return n;
}

q1_spawn_terminus_clock()
{
    q = level.iwz_q1;
    m = q1_marker( "generator", "terminus_clock" );
    if ( !isdefined( m ) )
        return;
    q.term_clock = q1_usable( "com_fire_bell_iw6", m[3] + ( 0, 0, 120 ), m[4], "iwz_q1_terminus_clock", "23:59:19" );
}

// ---------------------------------------------------------------------------------------------- rounds and the end

q1_round_watch()
{
    level endon( "game_ended" );
    for ( ;; )
    {
        msg = level scripts\engine\utility::waittill_any_return( "spawn_wave_done", "regular_wave_starting" );
        q1_log( "ROUND " + msg + " wave=" + level.wave_num );
    }
}

// a match that ends during a crossing leaves nobody white-screened or protected
q1_end_cleanup()
{
    level waittill( "game_ended" );
    if ( isdefined( level.iwz_q1 ) && level.iwz_q1.paused )
        level.zombies_paused = 0;
    foreach ( p in level.players )
    {
        if ( isdefined( p ) && isdefined( p.iwz_busy ) && p.iwz_busy == "terminus" )
        {
            p.iwz_busy = undefined;
            p.is_off_grid = undefined;
        }
    }
}
