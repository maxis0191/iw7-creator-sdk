// Station Zero, package E2: the alive cap of ordinary zombies (iw7-creator-sdk docs/station-zero/07-ENEMIES.md 2.3), as
// real engine agents spawned by the stock wave loop. The cap climbs with the round and the players, up to 78 (four
// players, round 25 and later). It is bounded by the agent records the server engine has: dvar agent_capacity, set by
// a server started with -agent-capacity <n> (iw7-mod-components agent_capacity.cpp; server docs/ZOMBIE-CAPACITY.md).
// A stock server has 24 records and no such dvar: the cap stays 24, the stock game. A reserve of records is kept for the
// specials and bosses the stock game and later packages spawn as agents (iwz_cap_reserve, default 22: 100 = 78 + 22).
// Dvar iwz_zombie_cap: 0 = the table; a number = that fixed cap (tests). Every change is printed "[IWZ level] CAP ...".
// Self-contained (no call by path): runs from the map zone or as a server custom script.

init()
{
    if ( getdvar( "mapname" ) != "cp_iwz" || isdefined( level.iwz_cap ) )
        return;
    s = spawnstruct();
    level.iwz_cap = s;
    s.engine = getdvarint( "agent_capacity", 24 );
    s.reserve = getdvarint( "iwz_cap_reserve", 22 );
    s.current = 24;
    s.changes = 0;
    print( "[IWZ level] CAP READY engine_agents=" + s.engine + " reserve=" + s.reserve + " fixed=" + getdvarint( "iwz_zombie_cap", 0 ) );
    level thread iwz_cap_loop();
}

// The design cap for this round and these players (07-ENEMIES.md 2.3).
iwz_cap_design()
{
    fixed = getdvarint( "iwz_zombie_cap", 0 );
    if ( fixed > 0 )
        return fixed;
    w = 1;
    if ( isdefined( level.wave_num ) )
        w = level.wave_num;
    row = 0;
    if ( w >= 25 )
        row = 4;
    else if ( w >= 20 )
        row = 3;
    else if ( w >= 15 )
        row = 2;
    else if ( w >= 10 )
        row = 1;
    table = [];
    table[0] = [ 24, 24, 24, 24 ];
    table[1] = [ 24, 28, 32, 36 ];
    table[2] = [ 30, 36, 44, 48 ];
    table[3] = [ 38, 46, 56, 62 ];
    table[4] = [ 47, 58, 70, 78 ];
    col = level.players.size - 1;
    if ( col < 0 )
        col = 0;
    if ( col > 3 )
        col = 3;
    return table[row][col];
}

// What the engine can hold: never more ordinary zombies than records minus the reserve, never fewer than the stock 24.
iwz_cap_now()
{
    s = level.iwz_cap;
    cap = iwz_cap_design();
    room = s.engine - s.reserve;
    if ( cap > room )
        cap = room;
    if ( cap < 24 )
        cap = 24;
    return cap;
}

// The stock round start writes level.max_static_spawned_enemies (get_max_static_enemies: 24) and its wave loop spawns
// up to it; this puts the map's cap there in every ordinary round. Special rounds (max 0 or the stock event waves) keep
// their own numbers.
iwz_cap_loop()
{
    level endon( "game_ended" );
    s = level.iwz_cap;
    for ( ;; )
    {
        wait 0.25;
        if ( !isdefined( level.max_static_spawned_enemies ) || level.max_static_spawned_enemies <= 0 )
            continue;
        if ( !iwz_cap_ordinary_round() )
            continue;
        cap = iwz_cap_now();
        if ( level.max_static_spawned_enemies != cap )
        {
            level.max_static_spawned_enemies = cap;
            if ( cap != s.current )
            {
                s.current = cap;
                s.changes++;
                print( "[IWZ level] CAP SET cap=" + cap + " wave=" + level.wave_num + " players=" + level.players.size + " engine_agents=" + s.engine );
            }
        }
    }
}

// An ordinary round spawns generic zombies; the stock special rounds (clowns, goons) list other types.
iwz_cap_ordinary_round()
{
    if ( !isdefined( level.static_enemy_types ) )
        return 0;
    foreach ( t in level.static_enemy_types )
    {
        if ( t == "generic_zombie" )
            return 1;
    }
    return 0;
}
