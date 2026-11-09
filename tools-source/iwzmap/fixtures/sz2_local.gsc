// Station Zero v2 local fixture (local private session only), staged as custom_scripts/cp/iwzmap_local.gsc.
// station_zero2.py fills the view, walk and probe markers from its tables.
// Modes (dvar paris_iwz_mode):
//   views  capture every view (capture_frame iwzv_<name>): +set paris_iwz_noweapons 1, paris_iwz_cmds "cg_draw2D 0"
//   walk   open every door through the stock purchase path, then move the player along the walk path in 16-unit
//          steps and check with engine traces: the step is not blocked (playerphysicstrace), there is floor under it
//          (bullettrace down), no horizontal ray escapes the world (8 bullettraces + 4 playerphysicstraces), there is
//          a ceiling; zone volumes contain their probe points. Every failure is printed as [IWZ local] WALKFAIL.
// Options (g27): paris_iwz_dvarprobe "a|b|c" prints [IWZ local] DVAR name=..; value=..; exists=.. for each name (an
//          IW7 dvar is found by the hash of its name: a wrong name reads empty); views mode with paris_iwz_ab "cmd|cmd"
//          captures every view twice: iwzv_<name> as is, then iwzv_<name>_b after the commands (A/B), then runs
//          paris_iwz_ab_reset "cmd|cmd".

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
    if ( getdvar( "paris_iwz_dvarprobe" ) != "" )
    {
        names = strtok( getdvar( "paris_iwz_dvarprobe" ), "|" );
        for ( i = 0; i < names.size; i++ )
        {
            v = getdvar( names[i] );
            print( "[IWZ local] DVAR name=" + names[i] + "; value=" + v + "; exists=" + ( v != "" ) );
        }
    }
    mode = getdvar( "paris_iwz_mode" );
    if ( mode == "views" )
    {
        iwz_views( player );
        iwz_fx_views( player );
    }
    else if ( mode == "walk" )
        iwz_walk( player );
    else if ( mode == "walkcap" )
        iwz_walkcap( player );
    else if ( mode == "stairprobe" )
        iwz_stairprobe( player );
    print( "[IWZ local] DONE" );
}

// walkthrough capture: every navmesh point of a 256-unit grid, 4 yaws, eye height; part "k/n" of the list
iwz_walkcap( player )
{
    wc = [];
    //@WALKCAP@
    part = strtok( getdvar( "paris_iwz_wc_part" ), "/" );
    k = 0;
    n = 1;
    if ( part.size == 2 )
    {
        k = int( part[0] );
        n = int( part[1] );
    }
    count = 0;
    last = ( 0, 0, 0 );
    player freezecontrols( 1 );
    if ( getdvarint( "paris_iwz_noweapons" ) )
        player takeallweapons();
    for ( i = 0; i < wc.size; i++ )
    {
        if ( ( int( i / 4 ) % n ) != k )
            continue;
        v = wc[i];
        if ( distance( v.origin, last ) > 1 )
        {
            player setorigin( v.origin );
            last = v.origin;
            wait 1.2;
        }
        player setplayerangles( v.angles );
        wait 0.6;
        executecommand( "capture_frame iwzv_" + v.name );
        wait 0.3;
        count++;
        print( "[IWZ local] WC name=" + v.name + "; origin=" + player.origin + "; ground=" + player isonground() );
    }
    print( "[IWZ local] WALKCAP part=" + k + "/" + n + " frames=" + count + " of " + wc.size );
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
        if ( getdvar( "paris_iwz_ab" ) != "" )
        {
            ab = strtok( getdvar( "paris_iwz_ab" ), "|" );
            for ( k = 0; k < ab.size; k++ )
                executecommand( ab[k] );
            wait 2;
            if ( getdvar( "paris_iwz_dvarprobe" ) != "" )      // did the B commands take (cheat-protected dvars refuse with sv_cheats 0)
            {
                names = strtok( getdvar( "paris_iwz_dvarprobe" ), "|" );
                for ( k = 0; k < names.size; k++ )
                    print( "[IWZ local] DVAR_B name=" + names[k] + "; value=" + getdvar( names[k] ) );
            }
            executecommand( "capture_frame iwzv_" + v.name + "_b" );
            wait 1;
            print( "[IWZ local] VIEW_B name=" + v.name + "_b; cmds=" + getdvar( "paris_iwz_ab" ) );
            if ( getdvar( "paris_iwz_ab_reset" ) != "" )
            {
                ab = strtok( getdvar( "paris_iwz_ab_reset" ), "|" );
                for ( k = 0; k < ab.size; k++ )
                    executecommand( ab[k] );
                wait 1;
            }
        }
    }
}

iwz_fx_views( player )
{
    fxviews = [];
    flkviews = [];
    //@FXVIEWS@
    // flickering lamps: lamp held on, then held off (paris_iwz_flickertest), then free
    for ( pass = 0; pass < 2 && getdvar( "paris_iwz_only" ) == ""; pass++ )
    {
        setdvar( "paris_iwz_flickertest", pass + 1 );
        wait 0.5;
        for ( i = 0; i < flkviews.size; i++ )
        {
            v = flkviews[i];
            player setorigin( v.origin );
            player setplayerangles( v.angles );
            wait 1.2;
            executecommand( "capture_frame iwzv_" + v.name + ( pass ? "_off" : "_on" ) );
            wait 0.7;
        }
    }
    setdvar( "paris_iwz_flickertest", 0 );
    wait 4;
    toggles = -1;
    if ( isdefined( level.iwz_flicker_toggles ) )
        toggles = level.iwz_flicker_toggles;
    print( "[IWZ local] FLICKER views=" + flkviews.size + " toggles_after_release=" + toggles );
    if ( !fxviews.size || getdvar( "paris_iwz_only" ) != "" )
        return;
    for ( pass = 0; pass < 2; pass++ )
    {
        if ( pass == 1 )
        {
            setdvar( "paris_iwz_fxhold", 0 );
            wait 4;
        }
        for ( i = 0; i < fxviews.size; i++ )
        {
            v = fxviews[i];
            player setorigin( v.origin );
            player setplayerangles( v.angles );
            wait 1.5;
            executecommand( "capture_frame iwzv_" + v.name + ( pass ? "_on" : "_off" ) );
            wait 0.7;
        }
    }
    print( "[IWZ local] FXVIEWS " + fxviews.size );
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

// (g27b, QA g27: zombie climbs die mid-stair) stair probe: paris_iwz_sp = "label sx sy sz gx gy gz cx cy/..." per case.
// The player waits at g, a stock-spawned zombie is placed on the navmesh at s and walks to him. Every 0.25 s:
// SP_T origin, speed from the last sample, distance to the player, navmesh point under it and its offset. Before each
// case the navmesh is sampled on a 9 x 9 grid (16 apart) around c: SP_NAV sample -> navmesh point, clearance above it
// (playerphysicstrace 2 -> 72 up), path distance to the next sample east / north (getpathdist; -1 = no path).
// SP_END / SP_DEATH: how the case ended (reach, death with attacker / means, timeout).
iwz_stairprobe( player )
{
    iwz_open_doors( player );
    wait 2;
    cases = strtok( getdvar( "paris_iwz_sp" ), "/" );     // "/" between cases: ";" would split the console command
    for ( c = 0; c < cases.size; c++ )
    {
        t = strtok( cases[c], " " );
        if ( t.size < 9 )
            continue;
        label = t[0];
        src = ( float( t[1] ), float( t[2] ), float( t[3] ) );
        goal = ( float( t[4] ), float( t[5] ), float( t[6] ) );
        iwz_sp_navgrid( label, float( t[7] ), float( t[8] ), src[2], goal[2] );
        iwz_sp_case( player, label, src, goal );
    }
}

iwz_sp_navgrid( label, cx, cy, z0, z1 )
{
    zm = ( z0 + z1 ) / 2;
    for ( i = -4; i <= 4; i++ )
    {
        for ( j = -4; j <= 4; j++ )
        {
            p = ( cx + i * 16, cy + j * 16, zm );
            q = getclosestpointonnavmesh( p );
            if ( !isdefined( q ) )
            {
                print( "[IWZ local] SP_NAV case=" + label + " at=" + p + " nav=none" );
                continue;
            }
            up = playerphysicstrace( q + ( 0, 0, 2 ), q + ( 0, 0, 72 ) );
            qe = getclosestpointonnavmesh( p + ( 16, 0, 0 ) );
            qn = getclosestpointonnavmesh( p + ( 0, 16, 0 ) );
            de = -2;
            dn = -2;
            if ( isdefined( qe ) )
                de = getpathdist( q, qe );
            if ( isdefined( qn ) )
                dn = getpathdist( q, qn );
            print( "[IWZ local] SP_NAV case=" + label + " at=" + p + " nav=" + q + " clear=" + ( up[2] - q[2] ) + " path_e=" + de + " path_n=" + dn );
        }
        wait 0.05;
    }
}

iwz_sp_case( player, label, src, goal )
{
    if ( isdefined( level.spawned_enemies ) )
        foreach ( e in level.spawned_enemies )
            if ( isalive( e ) )
                e dodamage( e.health + 1000, e.origin, e, e, "MOD_SUICIDE" );
    wait 0.3;
    player setorigin( goal + ( 0, 0, 4 ) );
    player setvelocity( ( 0, 0, 0 ) );
    player freezecontrols( 1 );
    player.ignoreme = 0;
    best = undefined;
    bd = 999999;
    foreach ( vname, v in level.spawn_volume_array )
    {
        if ( !isdefined( v.spawners ) )
            continue;
        foreach ( sp in v.spawners )
        {
            d = distance( sp.origin, src );
            if ( d < bd )
            {
                bd = d;
                best = sp;
            }
        }
    }
    if ( !isdefined( best ) )
    {
        print( "[IWZ local] SP_END case=" + label + " result=no_spawner" );
        return;
    }
    z = best scripts\cp\zombies\zombies_spawning::spawn_wave_enemy( "generic_zombie", 1 );
    if ( !isdefined( z ) )
    {
        print( "[IWZ local] SP_END case=" + label + " result=no_zombie" );
        return;
    }
    z.is_reserved = 1;
    level.current_num_spawned_enemies--;
    deadline = gettime() + 8000;
    while ( isalive( z ) && isdefined( z.hasplayedvignetteanim ) && !z.hasplayedvignetteanim && gettime() < deadline )
        wait 0.1;
    if ( isalive( z ) )
        z setorigin( getclosestpointonnavmesh( src ), 1 );
    z thread iwz_sp_death( label );
    start = gettime();
    last = z.origin;
    result = "timeout";
    while ( gettime() - start < 40000 )
    {
        wait 0.25;
        if ( !isalive( z ) )
        {
            result = "died";
            break;
        }
        q = getclosestpointonnavmesh( z.origin );
        off = -999;
        if ( isdefined( q ) )
            off = z.origin[2] - q[2];
        d = distance( z.origin, player.origin );
        print( "[IWZ local] SP_T case=" + label + " t=" + ( gettime() - start ) + " pos=" + z.origin + " speed=" + int( distance( z.origin, last ) * 4 )
            + " dz=" + int( ( z.origin[2] - last[2] ) * 4 ) + " dist=" + int( d ) + " nav=" + q + " nav_off=" + off );
        last = z.origin;
        if ( d < 64 )
        {
            result = "reached";
            break;
        }
    }
    print( "[IWZ local] SP_END case=" + label + " result=" + result + " ms=" + ( gettime() - start ) + " spawner=" + best.origin );
    if ( isalive( z ) )
        z dodamage( z.health + 1000, z.origin, z, z, "MOD_SUICIDE" );
    player freezecontrols( 0 );
    wait 1;
}

iwz_sp_death( label )
{
    p = self.origin;
    self waittill( "death", attacker, mod );
    who = "none";
    if ( isdefined( attacker ) )
    {
        who = "other";
        if ( attacker == self )
            who = "self";
        else if ( isplayer( attacker ) )
            who = "player";
    }
    print( "[IWZ local] SP_DEATH case=" + label + " at=" + self.origin + " attacker=" + who + " mod=" + mod );
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
    // istouching (the stock player-zone test) with the player standing on each probe
    touch_fail = 0;
    foreach ( p in probes )
    {
        v = level.spawn_volume_array[p.zone];
        if ( !isdefined( v ) )
            continue;
        player setorigin( p.origin - ( 0, 0, 40 ) );
        wait 0.1;
        if ( !( player istouching( v ) ) )
        {
            print( "[IWZ local] WALKFAIL touch_out zone=" + p.zone + " point=" + p.origin );
            touch_fail++;
        }
    }
    print( "[IWZ local] TOUCH probes=" + probes.size + " fails=" + touch_fail );
    doors = [];
    //@DOORS@
    player setorigin( walk[0] );
    wait 0.5;
    iwz_door_checks( doors, "closed" );
    iwz_open_doors( player );
    wait 1;
    iwz_door_checks( doors, "open" );
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
            // 4. no horizontal escape (every 4th step): rays must hit a wall within 9000
            if ( steps % 4 == 0 )
            {
                foreach ( dir in dirs )
                {
                    tr = bullettrace( target + ( 0, 0, 48 ), target + ( 0, 0, 48 ) + dir * 9000, 0, player );
                    if ( tr["fraction"] >= 1 )
                    {
                        print( "[IWZ local] WALKFAIL ray_escape seg=" + k + " at=" + target + " dir=" + dir );
                        fails++;
                    }
                }
                for ( d = 0; d < 4; d++ )
                {
                    dir = dirs[d * 2];
                    end = target + ( 0, 0, 24 ) + dir * 9000;
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

// door collision: player hull traces through each door at 3 points across its span, 30 above the sill
iwz_door_checks( doors, state )
{
    blocked_total = 0;
    foreach ( d in doors )
    {
        blocked = 0;
        for ( k = 1; k <= 3; k++ )
        {
            s = d.lo + ( d.hi - d.lo ) * k / 4;
            if ( d.axis == 0 )
            {
                a = ( d.plane - 48, s, d.z0 + 30 );
                b = ( d.plane + 48, s, d.z0 + 30 );
            }
            else
            {
                a = ( s, d.plane - 48, d.z0 + 30 );
                b = ( s, d.plane + 48, d.z0 + 30 );
            }
            got = playerphysicstrace( a, b );
            back = playerphysicstrace( b, a );
            if ( distance( got, b ) > 2 && distance( back, a ) > 2 )
                blocked++;
        }
        blocked_total += blocked;
        ok = ( state == "closed" && blocked == 3 ) || ( state == "open" && blocked == 0 );
        if ( d.name == "pap_shutter" && state == "open" )
            ok = blocked == 3;
        print( "[IWZ local] DOORCHECK " + state + " door=" + d.name + " blocked=" + blocked + "/3 ok=" + ok );
        if ( !ok )
            print( "[IWZ local] WALKFAIL door_" + state + " door=" + d.name + " blocked=" + blocked );
    }
}

iwz_door( name, axis, plane, lo, hi, z0, z1 )
{
    d = spawnstruct();
    d.name = name;
    d.axis = axis;
    d.plane = plane;
    d.lo = lo;
    d.hi = hi;
    d.z0 = z0;
    d.z1 = z1;
    return d;
}

iwz_probe( zone, x, y, z )
{
    p = spawnstruct();
    p.zone = zone;
    p.origin = ( x, y, z );
    return p;
}
