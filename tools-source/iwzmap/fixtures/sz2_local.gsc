// Station Zero v2 local fixture (local private session only), staged as custom_scripts/cp/iwzmap_local.gsc.
// station_zero2.py fills the view, walk and probe markers from its tables.
// Modes (dvar paris_iwz_mode):
//   views  capture every view (capture_frame iwzv_<name>): +set paris_iwz_noweapons 1, paris_iwz_cmds "cg_draw2D 0"
//   walk   open every door through the stock purchase path, then move the player along the walk path in 16-unit
//          steps and check with engine traces: the step is not blocked (playerphysicstrace), there is floor under it
//          (bullettrace down), no horizontal ray escapes the world (8 bullettraces + 4 playerphysicstraces), there is
//          a ceiling; zone volumes contain their probe points. Every failure is printed as [IWZ local] WALKFAIL.

init()
{
    if ( getdvarint( "dedicated" ) || getdvar( "paris_iwz_mode" ) == "" )
        return;

    level thread iwz_main();
}

iwz_main()
{
    level waittill( "connected", player );
    while ( !isalive( player ) )
        wait 0.2;
    wait 6;
    player.ignoreme = 1;
    if ( getdvarint( "paris_iwz_noweapons" ) )
        player takeallweapons();
    print( "[IWZ local] SPAWNED; origin=" + player.origin );
    if ( getdvar( "paris_iwz_cmds" ) != "" )
    {
        cmds = strtok( getdvar( "paris_iwz_cmds" ), "|" );
        for ( i = 0; i < cmds.size; i++ )
            executecommand( cmds[i] );
        wait 1;
    }
    mode = getdvar( "paris_iwz_mode" );
    if ( mode == "views" )
        iwz_views( player );
    else if ( mode == "walk" )
        iwz_walk( player );
    print( "[IWZ local] DONE" );
}

iwz_views( player )
{
    views = [];
    //@VIEWS@
    only = getdvar( "paris_iwz_only" );
    for ( i = 0; i < views.size; i++ )
    {
        v = views[i];
        if ( only != "" && !issubstr( v.name, only ) )
            continue;
        player setorigin( v.origin );
        player setplayerangles( v.angles );
        player freezecontrols( 1 );
        if ( getdvarint( "paris_iwz_noweapons" ) )
            player takeallweapons();
        wait 2.5;
        executecommand( "capture_frame iwzv_" + v.name );
        wait 1;
        print( "[IWZ local] VIEW name=" + v.name + "; origin=" + player.origin + "; ground=" + player isonground() + "; angles=" + player getplayerangles() );
    }
}

iwz_view( name, x, y, z, yaw, pitch )
{
    v = spawnstruct();
    v.name = name;
    v.origin = ( x, y, z );
    v.angles = ( pitch, yaw, 0 );
    return v;
}

iwz_open_doors( player )
{
    opened = 0;
    seen = [];
    foreach ( s in level.all_interaction_structs )
    {
        if ( !isdefined( s.script_noteworthy ) || !issubstr( s.script_noteworthy, "debris_" ) || !isdefined( s.target ) )
            continue;
        if ( isdefined( seen[s.target] ) )
            continue;
        seen[s.target] = 1;
        scripts\cp\zombies\interaction_openareas::clear_debris( s, player );
        if ( isdefined( level.iwz_door_open ) )
            level.iwz_door_open[s.target] = 1;
        opened++;
        wait 0.2;
    }
    print( "[IWZ local] DOORS opened=" + opened );
}

iwz_walk( player )
{
    walk = [];
    //@WALK@
    probes = [];
    //@PROBES@
    wait 1;
    // zone volumes: every probe point must lie in its zone's spawn volume
    vol_fail = 0;
    foreach ( p in probes )
    {
        v = undefined;
        if ( isdefined( level.spawn_volume_array ) )
            v = level.spawn_volume_array[p.zone];
        if ( !isdefined( v ) )
        {
            print( "[IWZ local] WALKFAIL volume_missing zone=" + p.zone );
            vol_fail++;
            continue;
        }
        if ( !ispointinvolume( p.origin, v ) )
        {
            print( "[IWZ local] WALKFAIL volume_out zone=" + p.zone + " point=" + p.origin );
            vol_fail++;
        }
    }
    print( "[IWZ local] VOLUMES probes=" + probes.size + " fails=" + vol_fail );
    iwz_open_doors( player );
    wait 1;
    player freezecontrols( 1 );
    fails = 0;
    steps = 0;
    cur = walk[0];
    player setorigin( cur );
    wait 0.5;
    dirs = [];
    for ( a = 0; a < 360; a += 45 )
        dirs[dirs.size] = ( cos( a ), sin( a ), 0 );
    for ( k = 1; k < walk.size; k++ )
    {
        a = walk[k - 1];
        b = walk[k];
        seg = b - a;
        len = length( ( seg[0], seg[1], 0 ) );
        n = int( len / 16 ) + 1;
        for ( s = 1; s <= n; s++ )
        {
            t = s / n;
            target = a + seg * t;
            steps++;
            // 1. not blocked: player hull from the last point to this one, 18 above the floor (step height)
            from = cur + ( 0, 0, 18 );
            to = target + ( 0, 0, 18 );
            got = playerphysicstrace( from, to );
            if ( distance( got, to ) > 2 )
            {
                print( "[IWZ local] WALKFAIL blocked seg=" + k + " at=" + target + " stopped=" + got );
                fails++;
            }
            // 2. floor under the step (bullet and player traces)
            down = bullettrace( target + ( 0, 0, 40 ), target - ( 0, 0, 160 ), 0, player );
            if ( down["fraction"] >= 1 || abs( down["position"][2] - target[2] ) > 28 )
            {
                print( "[IWZ local] WALKFAIL floor seg=" + k + " at=" + target + " hit=" + down["position"] + " frac=" + down["fraction"] );
                fails++;
            }
            else
                target = ( target[0], target[1], down["position"][2] );
            // 3. ceiling above
            up = bullettrace( target + ( 0, 0, 40 ), target + ( 0, 0, 1200 ), 0, player );
            if ( up["fraction"] >= 1 )
            {
                print( "[IWZ local] WALKFAIL ceiling seg=" + k + " at=" + target );
                fails++;
            }
            // 4. no horizontal escape (every 4th step): rays must hit a wall within 5000
            if ( steps % 4 == 0 )
            {
                foreach ( dir in dirs )
                {
                    tr = bullettrace( target + ( 0, 0, 48 ), target + ( 0, 0, 48 ) + dir * 5000, 0, player );
                    if ( tr["fraction"] >= 1 )
                    {
                        print( "[IWZ local] WALKFAIL ray_escape seg=" + k + " at=" + target + " dir=" + dir );
                        fails++;
                    }
                }
                for ( d = 0; d < 4; d++ )
                {
                    dir = dirs[d * 2];
                    end = target + ( 0, 0, 24 ) + dir * 5000;
                    got = playerphysicstrace( target + ( 0, 0, 24 ), end );
                    if ( distance( got, end ) < 2 )
                    {
                        print( "[IWZ local] WALKFAIL player_escape seg=" + k + " at=" + target + " dir=" + dir );
                        fails++;
                    }
                }
            }
            cur = target;
            if ( steps % 8 == 0 )
            {
                player setorigin( cur );
                wait 0.05;
            }
            if ( fails > 400 )
                break;
        }
        player setorigin( b );
        wait 0.1;
        zone = "none";
        if ( isdefined( level.spawn_volume_array ) )
        {
            foreach ( name, v in level.spawn_volume_array )
            {
                if ( ispointinvolume( player.origin + ( 0, 0, 30 ), v ) )
                    zone = name;
            }
        }
        print( "[IWZ local] WALKPT k=" + k + " origin=" + player.origin + " ground=" + player isonground() + " zone=" + zone );
    }
    print( "[IWZ local] WALK steps=" + steps + " fails=" + fails );
}

iwz_probe( zone, x, y, z )
{
    p = spawnstruct();
    p.zone = zone;
    p.origin = ( x, y, z );
    return p;
}
