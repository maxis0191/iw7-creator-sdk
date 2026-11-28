// Test driver of ONE WAY: plan-callable functions (the gamelab `call` step runs them on the tested player).
// make_gamelab.py appends cp_sz_oneway.gsc and this file into ops/gamelab/lib/szoneway.gsc of a private gamelab folder.
// Every function prints one "[IWZ local] GL PROBE name=<name> ..." line; plans read it as probe:<name>.<key>.

// start the mechanic on a stock stand-in weapon (any weapon whose name contains `match`); up=1: counts as upgraded
owt_start( name, match, up )
{
    ow_init();
    level.ow_match = match;
    level.ow_force_up = up;
    print( "[IWZ local] GL PROBE name=" + name + " match=" + match + " up=" + up + " hooked=" + isdefined( level.onzombiedamage_func ) + " reward=" + isdefined( level.eligable_for_reward_func ) + " period=" + level.ow_period );
}

// what the tested player holds: the weapon in the hands, its clip and reserve, and the player's place and view
owt_held( name )
{
    w = self getcurrentweapon();
    print( "[IWZ local] GL PROBE name=" + name + " weapon=" + getweaponbasename( w ) + " oneway=" + issubstr( getweaponbasename( w ), "szoneway" ) + " clip=" + self getweaponammoclip( w ) + " stock=" + self getweaponammostock( w ) + " x=" + int( self.origin[0] ) + " y=" + int( self.origin[1] ) + " z=" + int( self.origin[2] ) + " yaw=" + int( self.angles[1] ) );
}

// a key of the JOINED client (forge run --joined): "keydown:attack", "keyup:usereload"... The runner relays the CLIREQ line to the
// client, whose binding dispatch presses the key (docs/NETLAB.md "Client requests"; ops/gamelab/lib/capacity.gsc cap_client_key)
owt_key( name, action )
{
    print( "[IWZ local] CLIREQ " + action + " t=" + gettime() );
    print( "[IWZ local] GL PROBE name=" + name + " key=" + action );
}

owt_tagged( tag )
{
    out = [];
    foreach ( z in level.gl_z )
    {
        if ( isdefined( z ) && isalive( z ) && isdefined( z.gl_tag ) && z.gl_tag == tag )
            out[out.size] = z;
    }
    return out;
}

// wait until `ms` milliseconds are left before the next bell (so a plan issues at a known place of the beat)
owt_sync( name, ms )
{
    for ( ;; )
    {
        left = level.ow_period - ( gettime() % level.ow_period );
        if ( left <= ms && left > ms - 100 )
            break;
        wait 0.05;
    }
    print( "[IWZ local] GL PROBE name=" + name + " left=" + left + " t=" + gettime() );
}

// `per` tickets a zombie, the first `limit` zombies of the tag (0 = all). A tag with ONE zombie, or head=1: one real
// bullet of the held weapon per ticket, fired from 48 units in front of the zombie at its chest (head=1: its head).
// A tag with several zombies that owt_spread has NOT set apart, and head=0: one script hit with a bullet's means of
// death per ticket (dodamage, the same stock callback and hook), because a real bullet into zombies standing
// together reaches the nearest one, not the aimed one. Measured 28 Nov: such a script hit reaches the callback with
// a HEAD hit location, so it is a first-class ticket; second-class tickets on several zombies need owt_spread and
// real bullets. Hits are one server frame apart.
owt_issue( name, tag, per, head, limit )
{
    w = self getcurrentweapon();
    zs = self owt_tagged( tag );
    aimed = 0;
    shots = 0;
    before = 0;
    if ( isdefined( self.ow_stats ) && isdefined( self.ow_stats["issued"] ) )
        before = self.ow_stats["issued"];
    bone = "j_spinelower";          // low in the trunk and fired level: never the head of a leaning zombie
    if ( head )
        bone = "j_head";
    foreach ( z in zs )
    {
        if ( limit > 0 && aimed >= limit )
            break;
        aimed++;
        for ( i = 0; i < per; i++ )
        {
            if ( !isalive( z ) )
                break;
            end = z gettagorigin( bone );
            if ( zs.size > 1 && !head && !isdefined( z.owt_apart ) )
                z dodamage( 1, end, self, self, "MOD_RIFLE_BULLET", w );
            else
            {
                dir = self geteye() - end;
                if ( !head )
                    dir = ( dir[0], dir[1], 0 );
                dir = vectornormalize( dir );
                magicbullet( w, end + dir * 30, end - dir * 8, self );
            }
            shots++;
            wait 0.05;
        }
    }
    wait 0.1;
    after = 0;
    if ( isdefined( self.ow_stats ) && isdefined( self.ow_stats["issued"] ) )
        after = self.ow_stats["issued"];
    print( "[IWZ local] GL PROBE name=" + name + " weapon=" + w + " aimed=" + aimed + " shots=" + shots + " issued=" + ( after - before ) + " left=" + ( level.ow_period - ( gettime() % level.ow_period ) ) );
}

owt_get( key )
{
    if ( isdefined( self.ow_stats ) && isdefined( self.ow_stats[key] ) )
        return self.ow_stats[key];
    return 0;
}

// the owner's counters, ammunition and points
owt_stat( name )
{
    w = self getcurrentweapon();
    print( "[IWZ local] GL PROBE name=" + name + " issued=" + self owt_get( "issued" ) + " first=" + self owt_get( "first" ) + " wasted=" + self owt_get( "wasted" ) + " taken=" + self owt_get( "taken" ) + " carried=" + self owt_get( "carried" ) + " stayed=" + self owt_get( "stayed" ) + " full=" + self owt_get( "full" ) + " refund=" + self owt_get( "refund" ) + " arrivals=" + self owt_get( "arrivals" ) + " arrival_kills=" + self owt_get( "arrival_kills" ) + " bells=" + level.ow_bells + " clip=" + self getweaponammoclip( w ) + " stock=" + self getweaponammostock( w ) + " money=" + self scripts\cp\cp_persistence::get_player_currency() );
}

// the plan's zombies of a tag: how many live, are booked, are carried (hidden), walk; tickets held; health range
owt_z( name, tag )
{
    zs = self owt_tagged( tag );
    booked = 0;
    tickets = 0;
    carried = 0;
    walk = 0;
    immune = 0;
    hmin = -1;
    hmax = 0;
    foreach ( z in zs )
    {
        if ( isdefined( z.ow_tix ) && z.ow_tix.size > 0 )
        {
            booked++;
            tickets += z.ow_tix.size;
        }
        if ( isdefined( z.ow_carry ) )
            carried++;
        if ( isdefined( z.ow_walk ) )
            walk++;
        if ( isdefined( z.ow_immune ) && gettime() < z.ow_immune )
            immune++;
        if ( hmin < 0 || z.health < hmin )
            hmin = z.health;
        if ( z.health > hmax )
            hmax = z.health;
    }
    print( "[IWZ local] GL PROBE name=" + name + " alive=" + zs.size + " booked=" + booked + " tickets=" + tickets + " carried=" + carried + " walk=" + walk + " immune=" + immune + " hmin=" + hmin + " hmax=" + hmax );
}

// wait for the next bell that the script rings (level notify), then 0.3 s for deaths to settle
owt_bell( name )
{
    level waittill( "ow_bell", dep );
    wait 0.3;
    print( "[IWZ local] GL PROBE name=" + name + " dep=" + dep + " bells=" + level.ow_bells + " t=" + gettime() );
}

// mean ground speed of the tag's zombies over `seconds` (units a second), and their move modes: calm is measured
owt_speed( name, tag, seconds )
{
    zs = self owt_tagged( tag );
    from = [];
    foreach ( i, z in zs )
        from[i] = z.origin;
    wait seconds;
    sum = 0;
    n = 0;
    modes = "";
    foreach ( i, z in zs )
    {
        if ( !isalive( z ) )
            continue;
        sum += distance2d( from[i], z.origin ) / seconds;
        n++;
        mode = "none";
        if ( isdefined( z.asm ) && isdefined( z.asm.cur_move_mode ) )
            mode = z.asm.cur_move_mode;
        else if ( isdefined( z.movemode ) )
            mode = z.movemode;
        if ( !issubstr( modes, mode ) )
            modes = modes + mode + "+";
    }
    mean = 0;
    if ( n > 0 )
        mean = sum / n;
    print( "[IWZ local] GL PROBE name=" + name + " n=" + n + " speed=" + int( mean ) + " modes=" + modes );
}

// One case, self-contained whatever the plan's pace: wait until `ms` are left before the bell, issue `per` tickets to
// the first `limit` zombies of the tag (0 = all), print <name>_issue and <name>_booked, wait for the next bell, print
// <name>_stat and <name>_z.
owt_case( name, tag, per, head, limit, ms )
{
    self owt_sync( name + "_sync", ms );
    self owt_issue( name + "_issue", tag, per, head, limit );
    self owt_z( name + "_booked", tag );
    self owt_bell( name + "_bell" );
    self owt_stat( name + "_stat" );
    self owt_z( name + "_z", tag );
}

// the bell after: <name>_stat and <name>_z once it has rung
owt_after( name, tag )
{
    self owt_bell( name + "_bell" );
    self owt_stat( name + "_stat" );
    self owt_z( name + "_z", tag );
}

// the tag's zombies are asked to move in a mode by the stock call (a test's way to have runners at wave 1)
owt_mode( name, tag, mode )
{
    zs = self owt_tagged( tag );
    foreach ( z in zs )
        z scripts\asm\asm_bb::bb_requestmovetype( mode );
    print( "[IWZ local] GL PROBE name=" + name + " n=" + zs.size + " mode=" + mode );
}

// the tag's zombies are set apart on a grid in front of the player (`cols` across, `gap` units between them) and held
// there (the stock boombox's way: scripted mode, a goal at their feet), so that a real bullet fired from 30 units in
// front of one reaches that one first
owt_spread( name, tag, cols, gap )
{
    zs = self owt_tagged( tag );
    fwd = anglestoforward( ( 0, self.angles[1], 0 ) );
    right = anglestoright( ( 0, self.angles[1], 0 ) );
    placed = 0;
    foreach ( i, z in zs )
    {
        col = i % cols;
        row = int( i / cols );
        spot = self.origin + fwd * ( 260 + row * gap ) + right * ( ( col - ( cols - 1 ) / 2 ) * gap );
        q = getclosestpointonnavmesh( spot );
        if ( isdefined( q ) )
            spot = q;
        z.scripted_mode = 1;
        z.goalradius = 16;
        z setorigin( spot );
        z setgoalpos( spot );
        z.owt_apart = 1;
        placed++;
    }
    wait 0.5;
    near = 100000;
    for ( i = 0; i < zs.size; i++ )
    {
        for ( j = i + 1; j < zs.size; j++ )
        {
            d = distance2d( zs[i].origin, zs[j].origin );
            if ( d < near )
                near = d;
        }
    }
    print( "[IWZ local] GL PROBE name=" + name + " placed=" + placed + " nearest=" + int( near ) );
}

// Is a carried zombie off the platform for a player and for a bullet? For the PLACE of the first carried zombie of
// the tag and for the first one that is not carried (the control): the player's own collision hull pushed through it
// (playerphysicstrace, 60 units each side), and a bullet trace through its chest. frac 1 = nothing in the way.
owt_pass( name, tag )
{
    zs = self owt_tagged( tag );
    c = undefined;
    o = undefined;
    foreach ( z in zs )
    {
        if ( isdefined( z.ow_carry ) && !isdefined( c ) )
            c = z;
        if ( !isdefined( z.ow_carry ) && !isdefined( o ) )
            o = z;
    }
    line = "[IWZ local] GL PROBE name=" + name + " carried_found=" + isdefined( c ) + " other_found=" + isdefined( o );
    if ( isdefined( c ) )
        line = line + " carried_hull=" + self owt_hull( c.ow_place ) + " carried_bullet=" + self owt_ray( c.ow_place ) + " carried_under=" + int( c.ow_place[2] - c.origin[2] );
    if ( isdefined( o ) )
        line = line + " other_hull=" + self owt_hull( o.origin ) + " other_bullet=" + self owt_ray( o.origin );
    print( line );
}

owt_hull( at )
{
    side = anglestoright( ( 0, self.angles[1], 0 ) );
    a = at + side * 60 + ( 0, 0, 4 );
    b = at - side * 60 + ( 0, 0, 4 );
    end = playerphysicstrace( a, b );
    return int( 100 * distance( a, end ) / distance( a, b ) );
}

owt_ray( at )
{
    side = anglestoright( ( 0, self.angles[1], 0 ) );
    a = at + side * 60 + ( 0, 0, 44 );
    b = at - side * 60 + ( 0, 0, 44 );
    tr = bullettrace( a, b, 1, self );
    return int( 100 * tr["fraction"] );
}
