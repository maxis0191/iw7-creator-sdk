// Darkness probe 6 (final proof) (local private session only) on a darkness build with test effects (build-dk -TestVfx):
// 1 dark vision exposure sweep; 2 flashlight effects isolated (spawnfx in front of the camera, no attachment),
// stock controls; 3 attachment variants; 4 power light calibration under one light; 5 power-on transition;
// 6 lit views; 7 4 / 8 players frame time. Frames iwzdk_*.bmp (collected by the runner).
// fxperf phases: 1 dark solo, 2 dark 4p, 3 dark 8p, 4 transition, 5 lit solo, 6 lit 4p, 7 lit 8p, 9 end.
init()
{
    if ( getdvarint( "dedicated" ) || getdvar( "paris_iwz_mode" ) != "dkprobe6" )
        return;
    setdvar( "paris_iwz_fxphase", "0" );
    setdvar( "paris_iwz_dark_debug", "1" );
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
    dk_log( "WEAPON " + player getcurrentweapon() + " fl=" + player.iwz_fl_on + " k=" + player.iwz_fl_k );
    player switchtoweapon( level.dk_first_weapon );
    wait 3;
    dk_cap( player, "wswitch_back" );
    dk_log( "WEAPON " + player getcurrentweapon() + " fl=" + player.iwz_fl_on + " k=" + player.iwz_fl_k );

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
    foreach ( c in fxcams )
    {
        dk_place( player, c.origin, c.yaw, c.pitch );
        wait 1.5;
        dk_cap( player, "postfx_" + c.name );
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
    dk_log( "DONE" );
}
