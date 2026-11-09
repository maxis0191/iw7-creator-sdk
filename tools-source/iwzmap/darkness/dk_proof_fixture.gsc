// Darkness probe 8 (g27 darkness build) (local private session only) on a darkness build with test effects (build-dk -TestVfx):
// 1 dark vision exposure sweep; 2 flashlight effects isolated (spawnfx in front of the camera, no attachment),
// stock controls; 3 attachment variants; 4 power light calibration under one light; 5 power-on transition;
// 6 lit views; 7 4 / 8 players frame time. Frames iwzdk_*.bmp (collected by the runner).
// fxperf phases: 1 dark solo, 2 dark 4p, 3 dark 8p, 4 transition, 5 lit solo, 6 lit 4p, 7 lit 8p, 9 end.
init()
{
    if ( getdvarint( "dedicated" ) || getdvar( "paris_iwz_mode" ) != "dkprobe8" )
        return;
    setdvar( "paris_iwz_fxphase", "0" );
    setdvar( "paris_iwz_dark_debug", "1" );
    // calibration power-light sets (dark_build --alt, iwz_power_<set>): off until the lit sweep
    foreach ( sn in [ "b", "c" ] )
    {
        foreach ( l in getentarray( "iwz_power_" + sn, "targetname" ) )
            l setlightintensity( 0 );
    }
    level.dk_flt = [];
    foreach ( n in [ "a", "b", "c", "d" ] )
        level.dk_flt[n] = loadfx( "vfx/iwz/vfx_iwz_flv_" + n );
    level.dkfx = [];
    foreach ( n in [ "vfx/iwz/vfx_iwz_flashlight_world", "vfx/iwz/vfx_iwz_fltest_hot", "vfx/iwz/vfx_iwz_fltest_head",
        "vfx/iwz/vfx_iwz_flashlight_view", "vfx/iw7/core/zombie/vfx_zmb_headlight", "vfx/iw7/_requests/coop/vfx_zb_thu_sparks" ] )
    {
        level.dkfx[n] = loadfx( n );
        print( "[IWZ dark] LOADFX " + n + " id=" + level.dkfx[n] );
    }
    level thread dk_main();
}

dk_log( s )
{
    print( "[IWZ dark] " + s + " t=" + gettime() );
}

dk_quiet()
{
    if ( isdefined( level.flag ) && isdefined( level.flag["pause_wave_progression"] ) )
        scripts\engine\utility::flag_set( "pause_wave_progression" );
    level.zombies_paused = 1;
    foreach ( a in scripts\cp\cp_agent_utils::getaliveagentsofteam( "axis" ) )
        a dodamage( a.health + 10000, a.origin );
}

dk_phase( id )
{
    setdvar( "paris_iwz_fxphase", "" + id );
    dk_log( "PHASE " + id );
}

dk_cap( player, name )
{
    wait 0.35;
    executecommand( "capture_frame iwzdk_" + name );
    wait 0.45;
    dk_log( "FRAME " + name + " origin=" + player.origin + " angles=" + player getplayerangles() + " fl=" + player.iwz_fl_on );
}

dk_place( p, o, yaw, pitch )
{
    p setorigin( o );
    p setplayerangles( ( pitch, yaw, 0 ) );
    p freezecontrols( 1 );
}

dk_cams_of( dvar )
{
    out = [];
    if ( getdvar( dvar ) == "" )
        return out;
    foreach ( c in strtok( getdvar( dvar ), "@" ) )
    {
        v = strtok( c, "," );
        s = spawnstruct();
        s.name = v[0];
        s.origin = ( float( v[1] ), float( v[2] ), float( v[3] ) );
        s.yaw = float( v[4] );
        s.pitch = float( v[5] );
        out[out.size] = s;
    }
    return out;
}

dk_fl( p, on )
{
    p.iwz_fl_enabled = on;
    p notify( "iwz_fl_toggle" );
    wait 0.4;
}

dk_vision( p, name )
{
    visionsetnaked( name, 0 );
    p visionsetnakedforplayer( name, 0 );
    wait 0.6;
}

dk_keep_health()
{
    self endon( "disconnect" );
    self endon( "dk_stop_health" );
    self.maxhealth = 100000;
    for ( ;; )
    {
        if ( isalive( self ) )
            self.health = self.maxhealth;
        wait 0.05;
    }
}

dk_bots( n )
{
    bots = [];
    for ( i = 0; i < n; i++ )
    {
        b = undefined;
        for ( k = 0; k < 10 && !isdefined( b ); k++ )
        {
            b = addbot( "IWZDark" + level.dk_botn, 0, 0, 0 );
            if ( !isdefined( b ) )
                wait 1;
        }
        level.dk_botn++;
        if ( !isdefined( b ) )
            break;
        for ( k = 0; k < 300 && isdefined( b ) && !b canspawntestclient(); k++ )
            wait 0.05;
        if ( isdefined( b ) && b canspawntestclient() )
            b spawntestclient();
        for ( k = 0; k < 200 && !isalive( b ); k++ )
            wait 0.1;
        if ( isalive( b ) )
        {
            b.ignoreme = 1;
            b thread dk_keep_health();
            bots[bots.size] = b;
        }
    }
    return bots;
}

dk_bot_fan( bots, c )
{
    f = anglestoforward( ( 0, c.yaw, 0 ) );
    r = anglestoright( ( 0, c.yaw, 0 ) );
    for ( i = 0; i < bots.size; i++ )
    {
        side = ( i % 4 ) - 1.5;
        row = int( i / 4 );
        o = c.origin + f * ( 120 + 90 * row ) + r * ( side * 90 );
        dk_place( bots[i], o, c.yaw + side * 12, 8 );
    }
}

// a test effect in front of the eye, pointing along the view (no attachment)
dk_fxtest( player, name, tag )
{
    a = player getplayerangles();
    o = player geteye() + anglestoforward( a ) * 30 + ( 0, 0, -10 );
    e = spawnfx( level.dkfx[name], o, anglestoforward( a ), anglestoup( a ) );
    triggerfx( e );
    wait 1.2;
    dk_cap( player, "fx_" + tag );
    e delete();
    wait 0.8;
}

dk_main()
{
    level waittill( "connected", player );
    while ( !isalive( player ) )
        wait 0.2;
    wait 8;
    player.ignoreme = 1;
    player thread dk_keep_health();
    level.dk_botn = 0;
    executecommand( "cg_draw2D 0" );
    dk_quiet();
    cams = dk_cams_of( "paris_iwz_dkcams" );
    level.dk_first_weapon = player getcurrentweapon();
    dk_log( "SPAWNED cams=" + cams.size + " vision=" + level.iwz_dark_vision + " lights=" + getentarray( "iwz_power", "targetname" ).size +
        " fl=" + player.iwz_fl_on + " weapon=" + player getcurrentweapon() );
    dk_phase( 1 );

    w = cams[0];
    dk_place( player, w.origin, w.yaw, w.pitch );
    wait 1.5;
    dk_cap( player, "fl_start" );
    // the light follows the view: frames 0.1 s and 0.6 s after a 30 deg turn, and pitched down
    player setplayerangles( ( w.pitch, w.yaw + 30, 0 ) );
    wait 0.1;
    executecommand( "capture_frame iwzdk_fl_turn_01" );
    wait 0.5;
    dk_cap( player, "fl_turn_06" );
    player setplayerangles( ( w.pitch + 25, w.yaw, 0 ) );
    wait 0.5;
    dk_cap( player, "fl_pitch" );
    // pitch proof (follow carrier): looking 30 degrees up the pool must climb the wall, then level again
    player setplayerangles( ( w.pitch - 30, w.yaw, 0 ) );
    wait 0.5;
    dk_cap( player, "fl_pitch_up" );
    player setplayerangles( ( w.pitch, w.yaw, 0 ) );
    wait 0.5;
    dk_cap( player, "fl_level" );
    // (d13) penumbra / brightness variants through the module itself (level.iwz_fl_world swapped, normal attach /
    // detach): wall at the hall camera and the floor pitched down, against off frames from the same spots
    dk_fl( player, 0 );
    wait 1;
    dk_cap( player, "flv_off" );
    player setplayerangles( ( w.pitch + 25, w.yaw, 0 ) );
    wait 0.6;
    dk_cap( player, "flv_off_floor" );
    player setplayerangles( ( w.pitch, w.yaw, 0 ) );
    vnames = [ "def" ];
    vfx = [ level.iwz_fl_worlds[0] ];
    foreach ( n, fx in level.dk_flt )
    {
        vnames[vnames.size] = n;
        vfx[vfx.size] = fx;
    }
    for ( k = 0; k < vnames.size; k++ )
    {
        level.iwz_fl_world = vfx[k];
        dk_fl( player, 1 );
        wait 1.6;
        dk_cap( player, "flv_" + vnames[k] );
        player setplayerangles( ( w.pitch + 25, w.yaw, 0 ) );
        wait 0.6;
        dk_cap( player, "flv_" + vnames[k] + "_floor" );
        player setplayerangles( ( w.pitch, w.yaw, 0 ) );
        dk_fl( player, 0 );
        wait 0.8;
    }
    level.iwz_fl_world = level.iwz_fl_worlds[0];
    // (d14) the module light without and with its halo cone (soft edge)
    if ( isdefined( level.iwz_fl_halo ) )
    {
        foreach ( hv in [ 0, 1 ] )
        {
            level.iwz_fl_halo = hv;
            dk_fl( player, 1 );
            wait 1.6;
            dk_cap( player, "flh" + hv );
            player setplayerangles( ( w.pitch + 25, w.yaw, 0 ) );
            wait 0.6;
            dk_cap( player, "flh" + hv + "_floor" );
            player setplayerangles( ( w.pitch, w.yaw, 0 ) );
            dk_fl( player, 0 );
            wait 0.8;
        }
    }
    dk_cap( player, "flv_off2" );
    dk_fl( player, 1 );
    wait 0.5;
    if ( getdvarint( "paris_iwz_dkshort" ) )
    {
        for ( i = 1; i < cams.size; i++ )
        {
            c = cams[i];
            dk_place( player, c.origin, c.yaw, c.pitch );
            wait 1.5;
            dk_cap( player, "pre_" + c.name );
        }
        if ( getdvarint( "paris_iwz_dkfltest" ) )
            dk_fltest( player, cams[0] );
        if ( getdvar( "paris_iwz_dkvsweep" ) != "" )
            dk_vsweep( player, cams );
        if ( getdvarint( "paris_iwz_dkc2" ) )
            dk_client2( player, cams );
        if ( getdvarint( "paris_iwz_dkdown" ) )
            dk_down( player, cams[0] );
        if ( getdvarint( "paris_iwz_dklit" ) )
            dk_litcheck( player );
        dk_log( "DONE short" );
        return;
    }
    // 2. flashlight toggles (each re-attach uses the next copy) and a weapon switch
    for ( r = 0; r < 3; r++ )
    {
        dk_fl( player, 0 );
        dk_cap( player, "tog" + r + "_off" );
        dk_fl( player, 1 );
        wait 0.3;
        dk_cap( player, "tog" + r + "_on" );
    }
    player giveweapon( "iw7_m4_zm" );
    player switchtoweapon( "iw7_m4_zm" );
    wait 3;
    dk_cap( player, "wswitch_m4" );
    dk_log( "WEAPON " + player getcurrentweapon() + " fl=" + player.iwz_fl_on + " carrier=" + isdefined( player.iwz_fl_carrier ) );
    player switchtoweapon( level.dk_first_weapon );
    wait 3;
    dk_cap( player, "wswitch_back" );
    dk_log( "WEAPON " + player getcurrentweapon() + " fl=" + player.iwz_fl_on + " carrier=" + isdefined( player.iwz_fl_carrier ) );
    if ( getdvarint( "paris_iwz_dkfltest" ) )
        dk_fltest( player, cams[0] );
    if ( getdvar( "paris_iwz_dkvsweep" ) != "" )
        dk_vsweep( player, cams );

    // dark views with the module flashlight (other zones)
    for ( i = 1; i < cams.size; i++ )
    {
        c = cams[i];
        dk_quiet();
        dk_place( player, c.origin, c.yaw, c.pitch );
        wait 1.2;
        dk_cap( player, "pre_" + c.name );
        player setplayerangles( ( c.pitch, c.yaw + 35, 0 ) );
        wait 0.4;
        dk_cap( player, "pre_" + c.name + "_side" );
    }

    if ( getdvarint( "paris_iwz_dkc2" ) )
        dk_client2( player, cams );
    fxcams = dk_cams_of( "paris_iwz_dkfxcams" );
    foreach ( c in fxcams )
    {
        dk_quiet();
        dk_place( player, c.origin, c.yaw, c.pitch );
        wait 1.5;
        dk_cap( player, "prefx_" + c.name );
    }

    // 7a. 4 and 8 player lights in the dark
    t = cams[0];
    dk_place( player, t.origin, t.yaw, t.pitch );
    bots = dk_bots( 3 );
    dk_bot_fan( bots, t );
    wait 2;
    dk_phase( 2 );
    wait 6;
    dk_cap( player, "pre_bots" + ( bots.size + 1 ) );
    more = dk_bots( 4 );
    foreach ( b in more )
        bots[bots.size] = b;
    dk_bot_fan( bots, t );
    wait 2;
    dk_phase( 3 );
    wait 6;
    dk_cap( player, "pre_bots" + ( bots.size + 1 ) );
    dk_log( "BOTS players=" + level.players.size );
    // a bot's beam seen from the side
    dk_place( player, t.origin + anglestoright( ( 0, t.yaw, 0 ) ) * 300 + anglestoforward( ( 0, t.yaw, 0 ) ) * 150, t.yaw + 120, 8 );
    wait 1.2;
    dk_cap( player, "pre_bots_side" );
    foreach ( b in bots )
        dk_log( "BOTFL " + b.name + " fl=" + b.iwz_fl_on + " weapon=" + b getcurrentweapon() );
    foreach ( b in bots )
        b setorigin( b.origin + ( 0, 0, -3000 ) );

    // zombies in the dark: waves on, the player targetable (health refilled), frames while they are in view
    dk_place( player, t.origin, t.yaw, t.pitch );
    if ( isdefined( level.flag ) && isdefined( level.flag["pause_wave_progression"] ) )
        scripts\engine\utility::flag_clear( "pause_wave_progression" );
    level.zombies_paused = 0;
    player.ignoreme = 0;
    shots = 0;
    for ( k = 0; k < 50 && shots < 6; k++ )
    {
        wait 0.5;
        nd = 99999;
        nz = undefined;
        foreach ( a in scripts\cp\cp_agent_utils::getaliveagentsofteam( "axis" ) )
        {
            d = distance( a.origin, player.origin );
            if ( d < nd )
            {
                nd = d;
                nz = a;
            }
        }
        if ( isdefined( nz ) && nd < 900 )
        {
            // face the nearest zombie: it walks into the flashlight cone
            v = vectortoangles( nz.origin + ( 0, 0, 40 ) - player geteye() );
            player setplayerangles( ( v[0], v[1], 0 ) );
            wait 0.2;
            dk_cap( player, "zmb_" + shots );
            dk_log( "ZOMBIE shot=" + shots + " dist=" + nd );
            player setplayerangles( ( v[0], v[1] + 20, 0 ) );
            wait 0.2;
            dk_cap( player, "zmb_" + shots + "_edge" );
            shots++;
        }
    }
    player.ignoreme = 1;
    dk_quiet();

    // 5. power on and the transition from a fixed camera
    v = strtok( getdvar( "paris_iwz_dktrans" ), "," );
    dk_place( player, ( float( v[1] ), float( v[2] ), float( v[3] ) ), float( v[4] ), float( v[5] ) );
    wait 1.5;
    generator = undefined;
    foreach ( s in level.all_interaction_structs )
    {
        if ( isdefined( s.script_noteworthy ) && s.script_noteworthy == "generator" )
            generator = s;
    }
    dk_phase( 4 );
    t0 = gettime();
    if ( isdefined( generator ) )
        generator thread scripts\cp\zombies\zombie_power::generic_generator( generator, player );
    else
        scripts\engine\utility::flag_set( "power_on" );
    for ( k = 0; k < 60; k++ )
    {
        executecommand( "capture_frame iwzdk_trans_" + k );
        dk_log( "TRANS k=" + k + " dt=" + ( gettime() - t0 ) );
        wait 0.25;
    }
    while ( !scripts\engine\utility::flag( "iwz_power_lights_done" ) && gettime() - t0 < 30000 )
        wait 0.5;
    wait 6;

    // 6. lit
    dk_phase( 5 );
    foreach ( c in cams )
    {
        dk_place( player, c.origin, c.yaw, c.pitch );
        wait 1.5;
        dk_cap( player, "post_" + c.name );
    }
    // the lit-state flashlight (module "dim": ~30 % copy after the lights are done) on / off at two lit views
    foreach ( ci in [ 0, 1 ] )
    {
        dk_place( player, cams[ci].origin, cams[ci].yaw, cams[ci].pitch );
        dk_fl( player, 0 );
        wait 1;
        dk_cap( player, "litfl_off_" + cams[ci].name );
        dk_fl( player, 1 );
        wait 1.6;
        dk_cap( player, "litfl_on_" + cams[ci].name );
    }
    foreach ( c in fxcams )
    {
        dk_place( player, c.origin, c.yaw, c.pitch );
        wait 1.5;
        dk_cap( player, "postfx_" + c.name );
    }
    foreach ( c in dk_cams_of( "paris_iwz_dklitcams" ) )
    {
        dk_place( player, c.origin, c.yaw, c.pitch );
        wait 1.5;
        dk_cap( player, "lit_" + c.name );
    }
    // lit vision variants (paris_iwz_dklitsweep, fast-adapting): the same lit views under each, then the map vision
    if ( getdvar( "paris_iwz_dklitsweep" ) != "" )
    {
        foreach ( vn in strtok( getdvar( "paris_iwz_dklitsweep" ), "," ) )
        {
            dk_vision( player, vn );
            foreach ( c in dk_cams_of( "paris_iwz_dklitcams" ) )
            {
                dk_place( player, c.origin, c.yaw, c.pitch );
                wait 1.5;
                dk_cap( player, "ls_" + vn + "_" + c.name );
            }
        }
        dk_vision( player, "" );
    }
    dk_place( player, t.origin, t.yaw, t.pitch );
    four = [];
    for ( i = 0; i < 3 && i < bots.size; i++ )
        four[four.size] = bots[i];
    dk_bot_fan( four, t );
    wait 2;
    dk_phase( 6 );
    wait 6;
    dk_cap( player, "post_bots4" );
    dk_bot_fan( bots, t );
    wait 2;
    dk_phase( 7 );
    wait 6;
    dk_cap( player, "post_bots" + ( bots.size + 1 ) );
    dk_phase( 9 );
    foreach ( b in bots )
        b setorigin( b.origin + ( 0, 0, -3000 ) );
    if ( getdvarint( "paris_iwz_dkdown" ) )
        dk_down( player, t );
    dk_log( "DONE" );
}

// downed / self-revive: health refill stopped, one lethal hit, frames and module state every second
dk_down( player, w )
{
    dk_quiet();
    dk_place( player, w.origin, w.yaw, w.pitch );
    wait 1;
    player notify( "dk_stop_health" );
    player.maxhealth = 100;
    player.health = 100;
    wait 0.1;
    player.ignoreme = 1;
    player dodamage( 1000, player.origin );
    for ( k = 0; k < 24; k++ )
    {
        wait 1;
        st = "?";
        if ( isdefined( player.inlaststand ) )
            st = "" + player.inlaststand;
        dk_log( "DOWN k=" + k + " alive=" + isalive( player ) + " laststand=" + st + " fl=" + player.iwz_fl_on + " carrier=" +
            isdefined( player.iwz_fl_carrier ) + " weapon=" + player getcurrentweapon() );
        if ( k % 3 == 0 )
            executecommand( "capture_frame iwzdk_down_" + k );
    }
    player thread dk_keep_health();
}

// flashlight carrier test: link offsets (eye + forward 6 / 24 / 36) at 1.5 s and 4 s after attach, an M4 switch,
// follow mode (turn lag) and the weapon-tag mode, all against an off frame from the same spot
dk_fltest( player, w )
{
    dk_quiet();
    dk_place( player, w.origin, w.yaw, w.pitch );
    dk_fl( player, 0 );
    wait 1;
    dk_cap( player, "ft_off" );
    offs = [ ( 6, -4, -6 ), ( 24, -4, -6 ), ( 36, -6, -8 ) ];
    for ( i = 0; i < offs.size; i++ )
    {
        level.iwz_fl_link_offset = offs[i];
        dk_fl( player, 1 );
        wait 1.1;
        dk_cap( player, "ft_o" + i + "_15" );
        wait 2.5;
        dk_cap( player, "ft_o" + i + "_40" );
        dk_fl( player, 0 );
        wait 0.6;
    }
    level.iwz_fl_link_offset = offs[1];
    dk_fl( player, 1 );
    player giveweapon( "iw7_m4_zm" );
    player switchtoweapon( "iw7_m4_zm" );
    wait 3;
    dk_cap( player, "ft_m4_o1" );
    dk_log( "FLTEST m4 weapon=" + player getcurrentweapon() + " on=" + player.iwz_fl_on );
    dk_fl( player, 0 );
    wait 0.8;
    dk_cap( player, "ft_m4_off" );
    level.iwz_fl_mode = "follow";
    dk_fl( player, 1 );
    wait 1.1;
    dk_cap( player, "ft_follow_15" );
    player setplayerangles( ( w.pitch, w.yaw + 30, 0 ) );
    wait 0.1;
    executecommand( "capture_frame iwzdk_ft_follow_turn01" );
    wait 0.6;
    dk_cap( player, "ft_follow_turn07" );
    player setplayerangles( ( w.pitch, w.yaw, 0 ) );
    dk_fl( player, 0 );
    wait 0.6;
    level.iwz_fl_mode = "tag";
    dk_fl( player, 1 );
    wait 1.1;
    dk_cap( player, "ft_tag_15" );
    wait 2.5;
    dk_cap( player, "ft_tag_40" );
    dk_fl( player, 0 );
    wait 0.6;
    level.iwz_fl_mode = "link";
    dk_fl( player, 1 );
    dk_log( "FLTEST done" );
}

// exposure ladder: each vision of paris_iwz_dkvsweep (comma list; the variants adapt fast) applied for 4 s, frames
// at the hall wall (cams[0]) and the platform (cams[1]) with the flashlight off, then the module's dark vision again
dk_vsweep( player, cams )
{
    names = strtok( getdvar( "paris_iwz_dkvsweep" ), "," );
    dk_fl( player, 0 );
    foreach ( n in names )
    {
        dk_vision( player, n );
        for ( i = 0; i < 2 && i < cams.size; i++ )
        {
            dk_place( player, cams[i].origin, cams[i].yaw, cams[i].pitch );
            wait 3.5;
            dk_cap( player, "vs_" + n + "_" + cams[i].name );
        }
    }
    dk_vision( player, level.iwz_dark_vision );
    dk_fl( player, 1 );
    dk_log( "VSWEEP done" );
}

// other players' lights: the runner's second real client (-SecondClient) joins; it stands beside and ahead of the host
// with its own module flashlight; host frames with its light on / off (host light off), both on, and a side view across
// its beam. Bots never get spawned_player, so they cannot show this (runs dk10 .. dk15).
dk_client2( host, cams )
{
    c2 = undefined;
    for ( k = 0; k < 300 && !isdefined( c2 ); k++ )
    {
        foreach ( p in level.players )
        {
            if ( isdefined( p ) && p != host && !isbot( p ) && isalive( p ) )
                c2 = p;
        }
        if ( !isdefined( c2 ) )
            wait 0.5;
    }
    if ( !isdefined( c2 ) )
    {
        print( "[IWZ local] CLIENT2 none after 150 s players=" + level.players.size );
        dk_log( "CLIENT2 none players=" + level.players.size );
        return;
    }
    print( "[IWZ local] CLIENT2 joined name=" + c2.name );
    wait 2;
    c2.ignoreme = 1;
    c2 thread dk_keep_health();
    c2 freezecontrols( 1 );
    dk_quiet();
    foreach ( ci in [ 0, 1 ] )
    {
        t = cams[ci];
        f = anglestoforward( ( 0, t.yaw, 0 ) );
        r = anglestoright( ( 0, t.yaw, 0 ) );
        dk_place( host, t.origin, t.yaw, t.pitch );
        // beside and ahead of the host, aimed 25 degrees to the host's left: its beam and pool sit left of centre
        c2 setorigin( t.origin + f * 90 + r * 70 );
        c2 setplayerangles( ( t.pitch + 5, t.yaw + 25, 0 ) );
        dk_fl( host, 0 );
        c2.iwz_fl_enabled = 1;
        c2 notify( "iwz_fl_toggle" );
        wait 2;
        dk_cap( host, "c2_on_" + t.name );
        dk_log( "CLIENT2 " + t.name + " fl=" + c2.iwz_fl_on + " carrier=" + isdefined( c2.iwz_fl_carrier ) + " origin=" + c2.origin );
        c2.iwz_fl_enabled = 0;
        c2 notify( "iwz_fl_toggle" );
        wait 1.5;
        dk_cap( host, "c2_off_" + t.name );
        c2.iwz_fl_enabled = 1;
        c2 notify( "iwz_fl_toggle" );
        dk_fl( host, 1 );
        wait 1.6;
        dk_cap( host, "c2_both_" + t.name );
        // side view: the host 250 to the right, looking back across the client's beam
        dk_place( host, t.origin + r * 250 + f * 40, t.yaw + 60, t.pitch );
        dk_fl( host, 0 );
        wait 1.6;
        dk_cap( host, "c2_side_" + t.name );
        dk_fl( host, 1 );
    }
    // out of the host's way for the rest of the probe (behind the start camera), light still on
    c2 setorigin( cams[0].origin - anglestoforward( ( 0, cams[0].yaw, 0 ) ) * 120 );
    level.dk_c2 = c2;
}

// power on (stock generator routine) and the lit comparison views (paris_iwz_dklitcams), prefix lit2_
dk_litcheck( player )
{
    dk_quiet();
    generator = undefined;
    foreach ( s in level.all_interaction_structs )
    {
        if ( isdefined( s.script_noteworthy ) && s.script_noteworthy == "generator" )
            generator = s;
    }
    t0 = gettime();
    if ( isdefined( generator ) )
        generator thread scripts\cp\zombies\zombie_power::generic_generator( generator, player );
    else
        scripts\engine\utility::flag_set( "power_on" );
    while ( !scripts\engine\utility::flag( "iwz_power_lights_done" ) && gettime() - t0 < 30000 )
        wait 0.5;
    wait 6;
    dk_log( "LITCHECK scale=" + getdvar( "paris_iwz_dark_scale" ) );
    lx = getdvarint( "paris_iwz_dklitx" );
    if ( lx )
    {
        // the g27 lit views are weaponless and without a flashlight
        dk_fl( player, 0 );
        player takeallweapons();
        // a lit vision for the whole check (fast adaptation, so each view settles: run dk21 showed the map vision's
        // tonemapAdaptSpeed 0.01 makes every frame depend on the views before it)
        if ( getdvar( "paris_iwz_dklitvision" ) != "" )
        {
            dk_vision( player, getdvar( "paris_iwz_dklitvision" ) );
            wait 2;
        }
    }
    cams = dk_cams_of( "paris_iwz_dklitcams" );
    // long view lists are split over paris_iwz_dklitcams2 / 3 (dvar length)
    foreach ( dn in [ "paris_iwz_dklitcams2", "paris_iwz_dklitcams3" ] )
    {
        foreach ( c in dk_cams_of( dn ) )
            cams[cams.size] = c;
    }
    sub = [];
    subn = strtok( getdvar( "paris_iwz_dklitsub" ), "," );
    foreach ( c in cams )
    {
        foreach ( n in subn )
        {
            if ( c.name == n )
                sub[sub.size] = c;
        }
    }
    if ( lx && sub.size )
    {
        dk_place( player, sub[0].origin, sub[0].yaw, sub[0].pitch );
        wait 1;
        dk_cap( player, "drift_a_" + sub[0].name );
    }
    // per-zone power-light presets (run dk19): paris_iwz_dkzonepresets "zone:pct,zone:pct,...|..." (zones not listed
    // stay 100), each under the lit vision paris_iwz_dkzonevision ("" = the map's own); frames zp<k>_<view>
    if ( lx && getdvar( "paris_iwz_dkzonepresets" ) != "" && !getdvarint( "paris_iwz_dkzoneafter" ) )
    {
        dk_zone_presets( player, sub );
        return;
    }
    foreach ( c in cams )
    {
        dk_place( player, c.origin, c.yaw, c.pitch );
        wait 1.5;
        dk_cap( player, "lit2_" + c.name );
    }
    if ( !lx )
        return;
    dk_place( player, sub[0].origin, sub[0].yaw, sub[0].pitch );
    wait 1.5;
    dk_cap( player, "drift_b_" + sub[0].name );
    // (d14 verification) the 45 views at the build default first, then the runtime alternatives
    if ( getdvar( "paris_iwz_dkzonepresets" ) != "" && getdvarint( "paris_iwz_dkzoneafter" ) )
    {
        dk_zone_presets( player, sub );
        return;
    }
    // the map's own vision applied explicitly (level + player): equal to the released state if the hand-back is exact
    visionsetnaked( level.script, 0 );
    player visionsetnakedforplayer( level.script, 0 );
    dk_lit_sub( player, sub, "lre_" );
    visionsetnaked( "", 0 );
    player visionsetnakedforplayer( "", 0 );
    // lit vision candidates (fast-adapting variants under spare stock names)
    foreach ( vn in strtok( getdvar( "paris_iwz_dklitsweep" ), "," ) )
    {
        dk_vision( player, vn );
        dk_lit_sub( player, sub, "ls_" + vn + "_" );
    }
    dk_vision( player, "" );
    // power-light sets and scales at runtime: paris_iwz_dklitsets "a:60|b:100|a:40+b:60" (a = the module's lights,
    // b / c = calibration sets; percent of each light's on intensity); frames set_<combo>_<view>
    foreach ( combo in strtok( getdvar( "paris_iwz_dklitsets" ), "|" ) )
    {
        dk_set_all( 0 );
        tag = "";
        foreach ( part in strtok( combo, "+" ) )
        {
            kv = strtok( part, ":" );
            dk_set( kv[0], float( kv[1] ) / 100 );
            tag = tag + kv[0] + kv[1];
        }
        dk_log( "LITSET " + tag );
        dk_lit_sub( player, sub, "set_" + tag + "_" );
    }
    dk_set_all( 0 );
    dk_set( "a", 1 );
    dk_place( player, sub[0].origin, sub[0].yaw, sub[0].pitch );
    wait 2;
    dk_cap( player, "drift_c_" + sub[0].name );
    dk_log( "LITX done" );
}

dk_set( sn, s )
{
    if ( sn == "a" )
    {
        foreach ( l in level.iwz_dark_lights )
            l setlightintensity( l.iwz_on * s );
        return;
    }
    foreach ( l in getentarray( "iwz_power_" + sn, "targetname" ) )
        l setlightintensity( float( strtok( l.script_noteworthy, "|" )[2] ) * s );
}

dk_set_all( s )
{
    foreach ( sn in [ "a", "b", "c" ] )
        dk_set( sn, s );
}

dk_lit_sub( player, sub, prefix )
{
    foreach ( c in sub )
    {
        dk_place( player, c.origin, c.yaw, c.pitch );
        wait 1.5;
        dk_cap( player, prefix + c.name );
    }
}

dk_zone_presets( player, sub )
{
    zv = getdvar( "paris_iwz_dkzonevision" );
    if ( zv != "" )
        dk_vision( player, zv );
    presets = strtok( getdvar( "paris_iwz_dkzonepresets" ), "|" );
    for ( k = 0; k < presets.size; k++ )
    {
        zs = [];
        pv = zv;
        foreach ( part in strtok( presets[k], "," ) )
        {
            kv = strtok( part, ":" );
            if ( kv[0] == "v" )
                pv = kv[1];
            else
                zs[kv[0]] = float( kv[1] ) / 100;
        }
        // per-preset lit vision ("v:<name>", "v:map" = the map's own)
        if ( pv == "map" )
            dk_vision( player, "" );
        else if ( pv != "" )
            dk_vision( player, pv );
        foreach ( l in level.iwz_dark_lights )
        {
            // lamps take the zone key; fill lights (kind "fill") take "fill_<zone>", then "fill" (absent = 100)
            s = 1.0;
            if ( isdefined( l.iwz_kind ) && l.iwz_kind == "fill" )
            {
                if ( isdefined( zs["fill_" + l.iwz_zone] ) )
                    s = zs["fill_" + l.iwz_zone];
                else if ( isdefined( zs["fill"] ) )
                    s = zs["fill"];
            }
            else if ( isdefined( zs[l.iwz_zone] ) )
                s = zs[l.iwz_zone];
            l setlightintensity( l.iwz_on * s );
        }
        dk_log( "ZONEPRESET " + k + " " + presets[k] );
        dk_lit_sub( player, sub, "zp" + k + "_" );
    }
    dk_log( "ZONEPRESETS done" );
}
