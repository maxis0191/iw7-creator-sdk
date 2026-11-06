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
    level.magic_wheel_spin_hint = &"CP_ZMB_INTERACTIONS_SPIN_WHEEL";
    scripts\cp\maps\cp_zmb\cp_zmb_player_character_setup::init_player_characters();
    scripts\cp\maps\cp_zmb\cp_zmb::setup_generic_zombie_model_list();
    scripts\cp\zombies\interaction_magicwheel::set_magic_wheel_starting_location( //@WHEEL@ );
    level.iwz_door_open = [];
    level thread iwz_door_purchases();
    level thread iwz_door_barriers();
    level thread iwz_zone_links();
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

// door collision stand-in: until a door is bought, players cannot cross its plane (either direction)
iwz_door_barriers()
{
    level endon( "game_ended" );
    doors = [];
    //@DOORS@
    level.iwz_doors = doors;

    for ( ;; )
    {
        foreach ( door in doors )
        {
            if ( isdefined( level.iwz_door_open[door.target] ) )
                continue;

            foreach ( player in level.players )
            {
                p = player.origin;
                along = p[door.axis];
                across = p[1 - door.axis];

                if ( across < door.lo - 24 || across > door.hi + 24 || p[2] < door.z0 - 64 || p[2] > door.z1 + 32 )
                    continue;

                d = along - door.plane;
                key = player getentitynumber();
                if ( !isdefined( door.side[key] ) || abs( d ) > 40 )
                {
                    if ( d > 24 )
                        door.side[key] = 1;
                    else if ( d < -24 )
                        door.side[key] = -1;
                    continue;
                }

                s = door.side[key];
                if ( d * s < 20 )
                {
                    q = door.plane + s * 22;
                    if ( door.axis == 0 )
                        player setorigin( ( q, p[1], p[2] ) );
                    else
                        player setorigin( ( p[0], q, p[2] ) );
                }
            }
        }

        wait 0.05;
    }
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
        state += " zombies=" + zombies + " active_volumes=" + volumes + " wave=" + wave + " interactions=" + interactions;
        if ( zombies > 0 && isdefined( level.spawned_enemies[0] ) )
            state += " first_zombie=" + level.spawned_enemies[0].origin;
        print( "[IWZ level] " + state );
        wait 5;
    }
}
