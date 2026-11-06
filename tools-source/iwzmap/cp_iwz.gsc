// Station Zero (cp_iwz): original compact zombies map on the stock IW7 zombies systems shipped in the zone.
// Zones: arrival (start), generator (power, behind a 750 door), platform (Pack-a-Punch, behind a 1000 door).
main()
{
    level.iwz_custom_map = 1;
    scripts\mp\mp_agent::init_agent( "mp/default_agent_definition.csv" );
    scripts\mp\agents\zombie\zombie_agent::registerscriptedagent();
    level.coop_weapontable = "cp/cp_weapontable.csv";
    level.disable_zombie_exo_abilities = 1;
    level.initial_active_volumes = [ "arrival" ];
    level.map_interaction_func = scripts\cp\maps\cp_zmb\cp_zmb_interactions::register_interactions;
    scripts\cp\maps\cp_zmb\cp_zmb_player_character_setup::init_player_characters();
    scripts\cp\maps\cp_zmb\cp_zmb::setup_generic_zombie_model_list();
    level thread iwz_door_barriers();
    level thread iwz_report();
}

// door collision stand-in: until the zone behind a door is bought, players cannot cross its plane
iwz_door_barriers()
{
    level endon( "game_ended" );
    doors = [];
    doors[0] = iwz_door( "generator", 0, 1024, 5232, 5392 );    // arrival east wall (x = 1024)
    doors[1] = iwz_door( "platform", 1, 5696, 1840, 2000 );     // generator north wall (y = 5696)

    for ( ;; )
    {
        foreach ( door in doors )
        {
            if ( door.open )
                continue;

            volume = undefined;
            if ( isdefined( level.spawn_volume_array ) && isdefined( level.spawn_volume_array[door.area] ) )
                volume = level.spawn_volume_array[door.area];

            if ( isdefined( volume ) && scripts\engine\utility::is_true( volume.active ) )
            {
                door.open = 1;
                print( "[IWZ level] DOOR_OPEN " + door.area );
                continue;
            }

            foreach ( player in level.players )
            {
                p = player.origin;
                along = p[door.axis];
                across = p[1 - door.axis];

                if ( across < door.lo - 16 || across > door.hi + 16 )
                    continue;

                if ( along > door.plane - 14 && along < door.plane + 160 )
                {
                    if ( door.axis == 0 )
                        player setorigin( ( door.plane - 18, p[1], p[2] ) );
                    else
                        player setorigin( ( p[0], door.plane - 18, p[2] ) );
                }
            }
        }

        wait 0.05;
    }
}

iwz_door( area, axis, plane, lo, hi )
{
    door = spawnstruct();
    door.area = area;
    door.axis = axis;      // 0: the door plane is x = plane, 1: y = plane
    door.plane = plane;
    door.lo = lo;
    door.hi = hi;
    door.open = 0;
    return door;
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
        wait 2;
    }
}
