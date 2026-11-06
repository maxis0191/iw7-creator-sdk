// Station Zero v2 (cp_iwz): generated metro station on the stock IW7 zombies systems shipped in the zone.
// Template: station_zero2.py fills the door, zone link, initial zone and magic wheel markers from its data tables.
main()
{
    level.iwz_custom_map = 2;
    scripts\mp\mp_agent::init_agent( "mp/default_agent_definition.csv" );
    scripts\mp\agents\zombie\zombie_agent::registerscriptedagent();
    level.coop_weapontable = "cp/cp_weapontable.csv";
    level.disable_zombie_exo_abilities = 1;
    level.use_adjacent_volumes = 1;
    level.spawn_fx_func = scripts\cp\maps\cp_zmb\cp_zmb::cp_zmb_spawn_fx_func;
    //@INITIAL@
    level.map_interaction_func = scripts\cp\maps\cp_zmb\cp_zmb_interactions::register_interactions;
    level.wait_for_interaction_func = scripts\cp\maps\cp_zmb\cp_zmb_interactions::zmb_wait_for_interaction_triggered;
    level.player_interaction_monitor = scripts\cp\maps\cp_zmb\cp_zmb_interactions::zmb_player_interaction_monitor;
    level.magic_wheel_spin_hint = &"CP_ZMB_INTERACTIONS_SPIN_WHEEL";
    scripts\cp\maps\cp_zmb\cp_zmb_player_character_setup::init_player_characters();
    scripts\cp\maps\cp_zmb\cp_zmb::setup_generic_zombie_model_list();
    scripts\cp\zombies\interaction_magicwheel::set_magic_wheel_starting_location( //@WHEEL@ );
    level._effect["iwz_relay_red"] = loadfx( "vfx/iw7/core/zombie/weapon/shredder/zmb_part_glow_red.vfx" );
    level._effect["iwz_relay_green"] = loadfx( "vfx/iw7/core/zombie/weapon/dischord/zmb_part_glow_green.vfx" );
    level._effect["iwz_rail_arc"] = loadfx( "vfx/iw7/_requests/coop/vfx_mini_grey_shock_arc.vfx" );
    level._effect["iwz_rail_spark"] = loadfx( "vfx/iw7/core/zombie/vfx_zmb_console_sparks.vfx" );
    level.iwz_door_open = [];
    level thread iwz_door_purchases();
    level thread iwz_zone_links();
    level thread iwz_wheel_cleanup();
    level thread iwz_pap_quest();
    level thread iwz_third_rail();
    level thread iwz_report();
}

// door purchases: wrap the stock debris activation so the barrier knows which door was bought
iwz_door_purchases()
{
    level endon( "game_ended" );
    names = [ "debris_750", "debris_1000", "debris_1250" ];
    level.iwz_debris_orig = [];
    for ( i = 0; i < 600; i++ )
    {
        if ( isdefined( level.interactions ) && isdefined( level.interactions["debris_750"] ) )
            break;
        wait 0.1;
    }
    foreach ( n in names )
    {
        if ( !isdefined( level.interactions ) || !isdefined( level.interactions[n] ) )
            continue;
        level.iwz_debris_orig[n] = level.interactions[n].activation_func;
        level.interactions[n].activation_func = ::iwz_debris_bought;
    }
    print( "[IWZ level] DOOR_HOOKS " + level.iwz_debris_orig.size );
}

iwz_debris_bought( s, p )
{
    if ( isdefined( s ) && isdefined( s.target ) )
    {
        level.iwz_door_open[s.target] = 1;
        print( "[IWZ level] DOOR_BOUGHT " + s.target + " area=" + s.script_area );
    }
    [[ level.iwz_debris_orig[s.script_noteworthy] ]]( s, p );
}

// door table (generated); door collision is the script_brushmodel targets of each door (stock clear_debris)
iwz_door_table()
{
    doors = [];
    //@DOORS@
    return doors;
}

iwz_door( name, target, axis, plane, lo, hi, z0, z1 )
{
    door = spawnstruct();
    door.name = name;
    door.target = target;
    door.axis = axis;      // 0: the door plane is x = plane, 1: y = plane
    door.plane = plane;
    door.lo = lo;
    door.hi = hi;
    door.z0 = z0;
    door.z1 = z1;
    door.side = [];
    return door;
}

// zones joined without a door: adjacent for spawn scoring, and activated together
iwz_zone_links()
{
    level endon( "game_ended" );
    links = [];
    //@LINKS@
    for ( i = 0; i < 600 && !isdefined( level.spawn_volume_array ); i++ )
        wait 0.1;
    foreach ( l in links )
    {
        scripts\cp\zombies\zombies_spawning::update_volume_adjacency_by_name( l[0], l[1] );
        scripts\cp\zombies\zombies_spawning::update_volume_adjacency_by_name( l[1], l[0] );
    }
    for ( ;; )
    {
        foreach ( l in links )
        {
            a = level.spawn_volume_array[l[0]];
            b = level.spawn_volume_array[l[1]];
            if ( !isdefined( a ) || !isdefined( b ) )
                continue;
            if ( scripts\engine\utility::is_true( a.active ) && !scripts\engine\utility::is_true( b.active ) )
            {
                scripts\cp\zombies\zombies_spawning::activate_volume_by_name( l[1] );
                print( "[IWZ level] ZONE_LINK " + l[0] + " -> " + l[1] );
            }
            else if ( scripts\engine\utility::is_true( b.active ) && !scripts\engine\utility::is_true( a.active ) )
            {
                scripts\cp\zombies\zombies_spawning::activate_volume_by_name( l[0] );
                print( "[IWZ level] ZONE_LINK " + l[1] + " -> " + l[0] );
            }
        }
        wait 0.5;
    }
}

iwz_report()
{
    wait 1;
    print( "[IWZ level] characters=" + level.player_character_info.size + " available=" + level.available_player_characters.size );

    for ( ;; )
    {
        p = level.players[0];
        state = "intro_over=" + scripts\engine\utility::flag( "introscreen_over" );
        if ( isdefined( p ) )
            state += " alive=" + isalive( p ) + " weapon=" + p getcurrentweapon() + " origin=" + p.origin;
        zombies = 0;
        if ( isdefined( level.spawned_enemies ) )
            zombies = level.spawned_enemies.size;
        volumes = 0;
        if ( isdefined( level.active_spawn_volumes ) )
            volumes = level.active_spawn_volumes.size;
        wave = -1;
        if ( isdefined( level.wave_num ) )
            wave = level.wave_num;
        interactions = 0;
        if ( isdefined( level.all_interaction_structs ) )
            interactions = level.all_interaction_structs.size;
        if ( isdefined( level.iwz_relays_on ) )
            state += " relays=" + level.iwz_relays_on;
        state += " zombies=" + zombies + " active_volumes=" + volumes + " wave=" + wave + " interactions=" + interactions;
        if ( zombies > 0 && isdefined( level.spawned_enemies[0] ) )
            state += " first_zombie=" + level.spawned_enemies[0].origin;
        print( "[IWZ level] " + state );
        wait 5;
    }
}

// parked template magic wheels (no zone) get a spinner model from the stock init at the closest spinner struct:
// delete those spinners so only the generated wheels show one
iwz_wheel_cleanup()
{
    level endon( "game_ended" );
    for ( i = 0; i < 300 && !isdefined( level._id_B163 ); i++ )
        wait 0.1;
    wait 3;
    if ( !isdefined( level._id_B163 ) )
        return;
    removed = 0;
    kept = 0;
    foreach ( w in level._id_B163 )
    {
        if ( isdefined( w.area_name ) )
        {
            kept++;
            continue;
        }
        if ( isdefined( w._id_10A03 ) )
            w._id_10A03 delete();
        removed++;
    }
    print( "[IWZ level] WHEELS kept=" + kept + " parked_spinners_removed=" + removed );
}

// Pack-a-Punch quest: after power, three signal relays (hold Use 2 s) turn from red to green; all three green
// open the PaP shutter in the control room (script_brushmodel collision + rolling gate models). Level state:
// survives player death and joins.
iwz_pap_quest()
{
    level endon( "game_ended" );
    level.iwz_relays_on = 0;
    relays = [];
    for ( i = 1; i <= 3; i++ )
    {
        s = scripts\engine\utility::getstruct( "iwz_relay_" + i, "targetname" );
        if ( isdefined( s ) )
            relays[relays.size] = s;
    }
    wait 1;
    foreach ( s in relays )
    {
        s.lamp = spawnfx( level._effect["iwz_relay_red"], s.origin + anglestoforward( s.angles ) * 6 + ( 0, 0, 30 ) );
        triggerfx( s.lamp );
        s.use = spawn( "script_model", s.origin + ( 0, 0, 24 ) );
        s.use setmodel( "tag_origin" );
        s.use makeusable();
        s.use sethintstring( &"COOP_INTERACTIONS_REQUIRES_POWER" );
    }
    print( "[IWZ level] RELAYS " + relays.size );
    while ( !scripts\engine\utility::flag_exist( "power_on" ) )
        wait 0.5;
    scripts\engine\utility::flag_wait( "power_on" );
    foreach ( s in relays )
    {
        s.use sethintstring( &"COOP_INTERACTIONS_GENERATOR_ON" );
        s thread iwz_relay_wait();
    }
    while ( level.iwz_relays_on < relays.size )
        level waittill( "iwz_relay_on" );
    iwz_open_pap_shutter();
}

iwz_open_pap_shutter()
{
    if ( isdefined( level.iwz_pap_open ) )
        return;
    level.iwz_pap_open = 1;
    shutter = getentarray( "iwz_pap_shutter", "targetname" );
    if ( shutter.size )
        playsoundatpos( shutter[0].origin, "zmb_sliding_door_open" );
    foreach ( e in shutter )
    {
        if ( e.classname == "script_brushmodel" )
        {
            e connectpaths();
            e notsolid();
        }
        else
            e movez( 180, 3 );
    }
    print( "[IWZ level] PAP_OPEN relays=" + level.iwz_relays_on + " shutter_ents=" + shutter.size );
}

iwz_relay_wait()
{
    level endon( "game_ended" );
    for ( ;; )
    {
        self.use waittill( "trigger", p );
        held = 0;
        if ( getdvarint( "paris_iwz_autouse" ) )      // private test fixture only: the Use hold is simulated
            held = 2;
        while ( isdefined( p ) && isalive( p ) && p usebuttonpressed() && distance( p.origin, self.use.origin ) < 128 && held < 2 )
        {
            wait 0.1;
            held += 0.1;
        }
        if ( held >= 1.95 )
            break;
    }
    iwz_relay_on( self );
}

iwz_relay_on( s )
{
    if ( isdefined( s.on ) )
        return;
    s.on = 1;
    s.use makeunusable();
    if ( isdefined( s.lamp ) )
        s.lamp delete();
    s.lamp = spawnfx( level._effect["iwz_relay_green"], s.origin + anglestoforward( s.angles ) * 6 + ( 0, 0, 30 ) );
    triggerfx( s.lamp );
    playsoundatpos( s.origin, "purchase_generic" );
    level.iwz_relays_on++;
    print( "[IWZ level] RELAY_ON " + s.targetname + " count=" + level.iwz_relays_on );
    level notify( "iwz_relay_on" );
}

// Third Rail trap: fuse box on the platform (750, needs power): arcs along the rails for 25 s kill zombies in the
// track pit (players in the pit take damage), 60 s cooldown
iwz_third_rail()
{
    level endon( "game_ended" );
    box = scripts\engine\utility::getstruct( "iwz_trap_third_rail_fusebox", "targetname" );
    if ( !isdefined( box ) )
        return;
    level.iwz_trap_min = //@TRAPMIN@;
    level.iwz_trap_max = //@TRAPMAX@;
    level.iwz_trap_rail_y = //@TRAPRAILY@;
    wait 1;
    level.iwz_trap_use = spawn( "script_model", box.origin + anglestoforward( box.angles ) * 12 + ( 0, 0, 36 ) );
    use = level.iwz_trap_use;
    use setmodel( "tag_origin" );
    use makeusable();
    use sethintstring( &"COOP_INTERACTIONS_REQUIRES_POWER" );
    while ( !scripts\engine\utility::flag_exist( "power_on" ) )
        wait 0.5;
    scripts\engine\utility::flag_wait( "power_on" );
    for ( ;; )
    {
        use sethintstring( &"ZOMBIE_CRAFTING_SOUVENIRS_HINT_ELECTRICTRAP" );
        use waittill( "trigger", p );
        if ( !p scripts\cp\cp_persistence::player_has_enough_currency( 750 ) )
        {
            p playlocalsound( "purchase_deny" );
            continue;
        }
        p scripts\cp\cp_persistence::take_player_currency( 750, 1, "trap" );
        use makeunusable();
        print( "[IWZ level] TRAP_ON by=" + p.name );
        iwz_third_rail_run( p, 25 );
        print( "[IWZ level] TRAP_COOLDOWN" );
        wait 60;
        use makeusable();
    }
}

iwz_third_rail_run( owner, seconds )
{
    kills = 0;
    lo = level.iwz_trap_min;
    hi = level.iwz_trap_max;
    end = gettime() + seconds * 1000;
    next_fx = 0;
    while ( gettime() < end )
    {
        if ( gettime() >= next_fx )
        {
            for ( x = lo[0] + 128; x < hi[0]; x += 384 )
            {
                playfx( level._effect["iwz_rail_arc"], ( x, level.iwz_trap_rail_y, lo[2] + 12 ) );
                playfx( level._effect["iwz_rail_spark"], ( x + 192, level.iwz_trap_rail_y, lo[2] + 10 ) );
            }
            next_fx = gettime() + 1200;
        }
        if ( isdefined( level.spawned_enemies ) )
        {
            foreach ( z in level.spawned_enemies )
            {
                if ( isdefined( z ) && isalive( z ) && iwz_in_box( z.origin, lo, hi ) )
                {
                    z dodamage( z.health + 1000, z.origin, owner, owner, "MOD_UNKNOWN" );
                    kills++;
                }
            }
        }
        foreach ( pl in level.players )
        {
            if ( isalive( pl ) && iwz_in_box( pl.origin, lo, hi ) )
                pl dodamage( 20, pl.origin );
        }
        wait 0.25;
    }
    print( "[IWZ level] TRAP_DONE kills=" + kills );
}

iwz_in_box( p, lo, hi )
{
    return p[0] >= lo[0] && p[0] <= hi[0] && p[1] >= lo[1] && p[1] <= hi[1] && p[2] >= lo[2] - 8 && p[2] <= hi[2];
}
