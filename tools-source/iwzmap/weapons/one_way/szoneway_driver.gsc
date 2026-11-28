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
// A tag with several zombies and head=0: one script hit with a bullet's means of death per ticket
// (dodamage, the same stock callback and hook, no hit location), because a real bullet into zombies standing
// together reaches the nearest one, not the aimed one (measured 28 Nov). Hits are one server frame apart.
owt_issue( name, tag, per, head, limit )
{
    w = self getcurrentweapon();
    zs = self owt_tagged( tag );
    aimed = 0;
    shots = 0;
    before = 0;
    if ( isdefined( self.ow_stats ) && isdefined( self.ow_stats["issued"] ) )
        before = self.ow_stats["issued"];
    bone = "j_spine4";
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
            if ( zs.size > 1 && !head )
                z dodamage( 1, end, self, self, "MOD_RIFLE_BULLET", w );
            else
            {
                dir = vectornormalize( self geteye() - end );
                magicbullet( w, end + dir * 48, end - dir * 8, self );
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
