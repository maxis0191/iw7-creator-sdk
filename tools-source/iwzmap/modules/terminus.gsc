// sz_modules: opt-in
// Station Zero: the trip to the Terminus (redesign PLAN decision 4, TERMINUS-AND-GAPS C; bible 04-PAP-QUEST.md section 3).
// Use in the cab of car 1 of the parked 23:47: 4 s boarding, every player inside car 1 travels (downed players too),
// zombies inside car 1 are put out on the platform, 3 s crossing, 40 s at the Terminus, back to car 1 for whoever is in
// the Terminus box, 150 s not in service. While every player on his feet is at the Terminus the round's spawning pauses
// (stock level.zombies_paused; only a pause this module set is released). The Terminus spawn volume is never activated
// (activation would publish its respawn points, zombies_spawning.gsc:2464-2516).
// Cut from modules/quest.gsc:704-1004 (the 19-zone line's Q1, proven headless there). Version 1: the trip is armed with
// the power (terminus_armed() is the hook the four-clock quest replaces), stock sounds, no board, no HUD.
// Places from the emitted marker table: "quest_cab" (car 1's box as area), "terminus_arrival" (the Terminus box as area,
// declared by the Terminus section). Without either marker the module logs one line and stays idle.
// Self-contained (no call into another module or the level script by path): the same file runs from the map zone
// (scripts/cp/maps/<map>/<map>_terminus.gsc, started by the level script) or as a server custom script.
// Every state change prints "[IWZ level] TERMINUS ..."; the whole state is in level.iwz_terminus.
// "sz_modules: opt-in" (first line): sz_modules.emit writes this module only when a map lists it (layout modules).
// Player text below marked PLACEHOLDER COPY is for the copy writer (B1-BASE.md lists it).

init()
{
    if ( getdvar( "mapname" ) != "cp_iwz" || isdefined( level.iwz_terminus ) )
        return;
    t = spawnstruct();
    level.iwz_terminus = t;
    t.state = "init";
    t.visits = 0;
    t.riders = 0;
    t.returned = 0;
    t.pushed_out = 0;
    t.paused = 0;
    t.pause_seconds = 0;
    t.refused = 0;
    t.events = 0;
    // the Terminus's own vision (T1, 27 Nov 2026): the station's lit vision (auto exposure -2.5 EV) keeps a bright paper room at a mean luma of 0.13.
    // The map document writes a darkness variant under this spare stock vision name (settings.build.darkness.args --variants/--alias; custom names do
    // not apply: darkness NOTES dk4/dk6). A map whose document does not alias it sets level.iwz_terminus_vision = "" before init: no vision change.
    t.vision = "cp_frontend";
    if ( isdefined( level.iwz_terminus_vision ) )
        t.vision = level.iwz_terminus_vision;
    t.markers = terminus_markers();
    level thread terminus_main();
}

// filled by the emit (sz_modules.py): [ kind, id, zone, origin, yaw ( , lo, hi ) ]
terminus_markers()
{
    m = [];
    //@MARKERS@
    return m;
}

terminus_marker( kind )
{
    foreach ( m in level.iwz_terminus.markers )
    {
        if ( m[0] == kind )
            return m;
    }
    return undefined;
}

terminus_log( text )
{
    level.iwz_terminus.events++;
    print( "[IWZ level] TERMINUS " + text + " t=" + gettime() );
}

// the hook of the four-clock quest (bible 04-PAP-QUEST section 2): version 1 arms the trip with the power
terminus_armed()
{
    return scripts\engine\utility::flag_exist( "power_on" ) && scripts\engine\utility::flag( "power_on" );
}

terminus_main()
{
    level endon( "game_ended" );
    t = level.iwz_terminus;
    level thread terminus_end_cleanup();
    cab = terminus_marker( "quest_cab" );
    arr = terminus_marker( "terminus_arrival" );
    if ( !isdefined( cab ) || cab.size < 7 || !isdefined( arr ) || arr.size < 7 )
    {
        t.state = "no_terminus";
        terminus_log( "IDLE cab=" + ( isdefined( cab ) && cab.size >= 7 ) + " terminus=" + ( isdefined( arr ) && arr.size >= 7 ) + " (no trip: a marker or its area box is missing)" );
        return;
    }
    t.car_lo = cab[5];
    t.car_hi = cab[6];
    t.term_spot = arr[3];
    t.term_yaw = arr[4];
    t.term_lo = arr[5];
    t.term_hi = arr[6];
    t.sounds = [];
    names = [ "zmb_wheel_spin_tick", "zmb_portal_travel_lr", "purchase_deny" ];
    foreach ( n in names )
        t.sounds[n] = soundexists( n );
    wait 1;
    t.cab = spawn( "script_model", cab[3] + ( 0, 0, 48 ) );
    t.cab setmodel( "tag_origin" );
    t.cab.angles = ( 0, cab[4], 0 );
    t.cab.targetname = "iwz_terminus_cab";
    t.cab makeusable();
    t.cab sethintstring( &"COOP_INTERACTIONS_REQUIRES_POWER" );
    t.state = "unarmed";
    terminus_log( "CAB placed at=" + t.cab.origin + " car=" + t.car_lo + ".." + t.car_hi + " terminus=" + t.term_lo + ".." + t.term_hi );
    t.cab thread terminus_cab_use();
    while ( !terminus_armed() )
        wait 0.5;
    t.state = "idle";
    t.cab sethintstring( "Press ^3[{+activate}]^7 to depart for the Terminus" );     // PLACEHOLDER COPY
    // the projector runs once the trip is armed: reels turning, door open (as cp_final does at init, cp_final_weapon_upgrade.gsc:37-38; cp_zmb only after
    // its alien fuses, cp_zmb_ufo.gsc:1185-1196). The stock purchase sequence drives the door itself and ends at open_idle.
    mach = getent( "pap_machine", "targetname" );
    if ( isdefined( mach ) )
    {
        mach setscriptablepartstate( "reels", "on" );
        mach setscriptablepartstate( "door", "open_idle" );
    }
    terminus_log( "ARMED machine=" + isdefined( mach ) );
}

terminus_sound( ent, alias )
{
    if ( isdefined( level.iwz_terminus.sounds[alias] ) && level.iwz_terminus.sounds[alias] )
        ent playsound( alias );
}

terminus_downed( p )
{
    return scripts\engine\utility::is_true( p.inlaststand );
}

terminus_in_box( p, lo, hi )
{
    return p[0] >= lo[0] && p[0] <= hi[0] && p[1] >= lo[1] && p[1] <= hi[1] && p[2] >= lo[2] && p[2] <= hi[2];
}

terminus_in_car( p )
{
    t = level.iwz_terminus;
    return terminus_in_box( p, t.car_lo, t.car_hi );
}

terminus_in_terminus( p )
{
    t = level.iwz_terminus;
    return terminus_in_box( p, t.term_lo, t.term_hi );
}

terminus_cab_use()
{
    level endon( "game_ended" );
    t = level.iwz_terminus;
    for ( ;; )
    {
        self waittill( "trigger", p );
        if ( !isplayer( p ) )
            continue;
        why = "";
        if ( terminus_downed( p ) )
            why = "downed";
        else if ( !terminus_armed() )
            why = "unarmed";
        else if ( t.state != "idle" )
            why = t.state;
        if ( why != "" )
        {
            t.refused++;
            if ( t.sounds["purchase_deny"] )
                p playlocalsound( "purchase_deny" );
            terminus_log( "REFUSED by=" + p.name + " why=" + why );
            continue;
        }
        level thread terminus_trip( p );
    }
}

terminus_trip( starter )
{
    level endon( "game_ended" );
    t = level.iwz_terminus;
    t.state = "boarding";
    t.cab sethintstring( "BOARDING" );     // PLACEHOLDER COPY
    terminus_log( "BOARDING by=" + starter.name );
    for ( i = 0; i < 2; i++ )
    {
        terminus_sound( t.cab, "zmb_wheel_spin_tick" );
        wait 2;
    }
    // every player inside car 1 goes, downed players included; zombies inside are put out on the platform, unhurt
    riders = [];
    foreach ( p in level.players )
    {
        if ( isdefined( p ) && isalive( p ) && terminus_in_car( p.origin ) && !isdefined( p.iwz_busy ) )
            riders[riders.size] = p;
    }
    pushed = 0;
    if ( isdefined( level.spawned_enemies ) )
    {
        foreach ( z in level.spawned_enemies )
        {
            if ( isdefined( z ) && isalive( z ) && terminus_in_car( z.origin ) )
            {
                out = getclosestpointonnavmesh( ( z.origin[0], t.car_hi[1] + 70, t.car_lo[2] + 10 ) );
                if ( isdefined( out ) )
                    z setorigin( out, 1 );
                pushed++;
            }
        }
    }
    t.pushed_out += pushed;
    if ( riders.size == 0 )
    {
        t.state = "idle";
        t.cab sethintstring( "Press ^3[{+activate}]^7 to depart for the Terminus" );     // PLACEHOLDER COPY
        terminus_log( "NOBODY_ABOARD pushed=" + pushed );
        return;
    }
    t.state = "crossing";
    t.visits++;
    t.riders = riders.size;
    downed = 0;
    foreach ( p in riders )
    {
        if ( terminus_downed( p ) )
            downed++;
    }
    t.cab sethintstring( "" );
    terminus_log( "DEPART riders=" + riders.size + " downed=" + downed + " pushed=" + pushed + " visit=" + t.visits );
    slot = 0;
    foreach ( p in riders )
    {
        p.iwz_busy = "terminus";
        p thread terminus_cross( t.term_spot + ( 0, ( slot % 4 ) * 48 - 72, 0 ), ( 0, t.term_yaw, 0 ), 3, 1 );
        slot++;
    }
    wait 3.2;
    t.state = "away";
    terminus_log( "ARRIVED riders=" + riders.size );
    level thread terminus_pause_watch();
    wait 40;
    t.state = "returning";
    level notify( "iwz_terminus_return" );
    back = 0;
    slot = 0;
    c = ( t.car_lo + t.car_hi ) * 0.5;
    foreach ( p in level.players )
    {
        if ( isdefined( p ) && isalive( p ) && terminus_in_terminus( p.origin ) )
        {
            p.iwz_busy = "terminus";
            p thread terminus_cross( ( t.car_lo[0] + 80 + ( slot % 4 ) * 110, c[1], t.car_lo[2] + 14 ), ( 0, 90, 0 ), 1, 0 );
            back++;
            slot++;
        }
    }
    wait 1.2;
    foreach ( p in level.players )
        terminus_release( p );
    t.returned += back;
    terminus_log( "RETURNED players=" + back + " visit=" + t.visits );
    // 150 s not in service: 40 s away in every 190 at most
    t.state = "cooldown";
    t.cab sethintstring( "NOT IN SERVICE" );     // PLACEHOLDER COPY
    wait 150;
    t.state = "idle";
    t.cab sethintstring( "Press ^3[{+activate}]^7 to depart for the Terminus" );     // PLACEHOLDER COPY
    terminus_log( "READY" );
}

// the crossing: white light, the portal sound, the player placed. Going out, the stock protections (no damage, off the
// zombies' grid: zombies_spawning.gsc _id_FF55 and zombie_agent.gsc:234 drop an is_off_grid player as a target) stay on
// for the whole stay, as in the stock hidden room (zombie_fast_travel.gsc:672-688); coming back they end on arrival.
terminus_cross( dest, angles, seconds, outward )
{
    self endon( "disconnect" );
    self scripts\cp\utility::adddamagemodifier( "iwz_terminus", 0.0, 0 );
    self.is_off_grid = 1;
    if ( level.iwz_terminus.sounds["zmb_portal_travel_lr"] )
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
    if ( outward && level.iwz_terminus.vision != "" )
    {
        self.iwz_terminus_vision = 1;
        self visionsetnakedforplayer( level.iwz_terminus.vision, 0.4 );
    }
    if ( !outward )
        terminus_release( self );
    terminus_log( "CROSS player=" + self.name + " out=" + outward + " at=" + self.origin + " downed=" + terminus_downed( self ) );
}

// a player back from the Terminus (or left behind by a match end): protections off, free for the Post and the emotes
terminus_release( p )
{
    if ( !isdefined( p ) || !isdefined( p.iwz_busy ) || p.iwz_busy != "terminus" )
        return;
    p.iwz_busy = undefined;
    p.is_off_grid = undefined;
    p scripts\cp\utility::removedamagemodifier( "iwz_terminus", 0 );
    terminus_vision_restore( p );
}

// back to the station's own vision: the dark one while the darkness module holds it (level.vision_set_override), else the lit one it released to
// (the map's own vision, or the private test dvar paris_iwz_lit_vision, as cp_iwz_darkness.gsc iwz_dark_vision_release)
terminus_vision_restore( p )
{
    if ( !isdefined( p.iwz_terminus_vision ) )
        return;
    p.iwz_terminus_vision = undefined;
    v = getdvar( "paris_iwz_lit_vision" );
    if ( isdefined( level.vision_set_override ) )
        v = level.vision_set_override;
    p visionsetnakedforplayer( v, 0.5 );
}

// while every player on his feet is at the Terminus the round's spawning pauses (stock level.zombies_paused); it resumes
// when one is back outside or the visit ends. A downed player left outside does not hold the pause; a late joiner
// spawns in the station and stands outside, so the pause drops. Only a pause this module set is released.
terminus_pause_watch()
{
    level endon( "game_ended" );
    t = level.iwz_terminus;
    t0 = gettime();
    while ( t.state == "away" )
    {
        all = 1;
        n = 0;
        foreach ( p in level.players )
        {
            if ( !isdefined( p ) || !isalive( p ) || terminus_downed( p ) )
                continue;
            n++;
            if ( !terminus_in_terminus( p.origin ) )
                all = 0;
        }
        want = all && n > 0;
        if ( want && !t.paused )
        {
            if ( !scripts\engine\utility::is_true( level.zombies_paused ) )
            {
                level.zombies_paused = 1;
                t.paused = 1;
                t0 = gettime();
                terminus_log( "PAUSE on alive=" + terminus_alive_zombies() );
            }
        }
        else if ( !want && t.paused )
            terminus_unpause( t0 );
        if ( t.paused )
            terminus_hold_zombies();
        wait 0.5;
    }
    if ( t.paused )
        terminus_unpause( t0 );
}

terminus_unpause( t0 )
{
    t = level.iwz_terminus;
    level.zombies_paused = 0;
    t.paused = 0;
    t.pause_seconds += int( ( gettime() - t0 ) / 1000 );
    terminus_log( "PAUSE off alive=" + terminus_alive_zombies() + " paused_s=" + t.pause_seconds );
}

// while our pause holds, the zombies alive wait instead of being recycled: the stock far-zombie cleanup (zombies_spawning.gsc, the loop that kills
// agents far from every player) skips one whose delay_cleanup_until is in the future (:3560). Measured 27 Nov 2026 (t1_trip, compressed time): without
// this the four zombies alive at arrival were gone 20 to 35 s into the stay. A rolling 2 s hold, renewed each tick: it lapses by itself after the pause.
terminus_hold_zombies()
{
    if ( !isdefined( level.spawned_enemies ) )
        return;
    until = gettime() + 2000;
    foreach ( z in level.spawned_enemies )
    {
        if ( isdefined( z ) && isalive( z ) && ( !isdefined( z.delay_cleanup_until ) || z.delay_cleanup_until < until ) )
            z.delay_cleanup_until = until;
    }
}

terminus_alive_zombies()
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

// a match that ends during a visit leaves no pause of ours and nobody protected or busy
terminus_end_cleanup()
{
    level waittill( "game_ended" );
    t = level.iwz_terminus;
    if ( t.paused )
    {
        level.zombies_paused = 0;
        t.paused = 0;
    }
    foreach ( p in level.players )
        terminus_release( p );
}
