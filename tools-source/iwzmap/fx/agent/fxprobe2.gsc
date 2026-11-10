// FX probe 1 (local private session only): which stock FX render in a usermap, through which call.
// Staged as custom_scripts/cp/iwzmap_local.gsc. Each probe: off frame, spawn, 3 on frames, delete.
init()
{
    if ( getdvarint( "dedicated" ) || getdvar( "paris_iwz_mode" ) != "fxprobe" )
        return;
    level.fxp = [];
    fxp_add( "dust", "vfx/iw7/core/zombie/environment/vfx_cop_zmb_particle_dust", 50, 0, ( 0, 263, 0 ) );
    fxp_add( "dustmd", "vfx/iw7/core/zombie/vfx_zmb_dust_motes_md", 50, 0, ( 0, 0, 0 ) );
    fxp_add( "drips", "vfx/iw7/core/zombie/environment/vfx_zmb_drips_parent", 150, 0, ( 0, 0, 0 ) );
    fxp_add( "waterdrip", "vfx/iw7/core/zombie/vfx_zmb_water_drip", 150, 0, ( 0, 0, 0 ) );
    fxp_add( "fogbright", "vfx/iw7/core/zombie/environment/vfx_knee_high_fog_bright", 2, 0, ( 0, 0, 0 ) );
    fxp_add( "fogbri", "vfx/iw7/_requests/coop/vfx_zmb_grd_fog_bri", 2, 0, ( 0, 0, 0 ) );
    fxp_add( "fogdar", "vfx/iw7/_requests/coop/vfx_zmb_grd_fog_dar", 2, 0, ( 0, 0, 0 ) );
    fxp_add( "fogtunnel", "vfx/iw7/_requests/coop/vfx_zmb_grd_fog_tunnel", 2, 0, ( 0, 0, 0 ) );
    fxp_add( "riverfog", "vfx/iw7/_requests/coop/vfx_zmb_river_fog", 2, 0, ( 0, 0, 0 ) );
    fxp_add( "smkhang", "vfx/iw7/core/zombie/vfx_zmb_smk_ambient_hang_med", 40, 0, ( 270, 0, 0 ) );
    fxp_add( "lingersmk", "vfx/iw7/_requests/coop/vfx_zb_linger_smk_af", 2, 0, ( 270, 0, 0 ) );
    fxp_add( "windowsmk", "vfx/iw7/core/zombie/environment/vfx_zmb_window_smk", 30, 0, ( 0, 0, 0 ) );
    fxp_add( "genidle", "vfx/iw7/_requests/coop/generator_idle", 30, 0, ( 0, 0, 0 ) );
    fxp_add( "sparks", "vfx/iw7/core/zombie/vfx_zmb_console_sparks", 50, 1, ( 0, 90, 0 ) );
    fxp_add( "sparkrobot", "vfx/iw7/core/zombie/vfx_zmb_spark_robot", 50, 1, ( 0, 90, 0 ) );
    fxp_add( "thusparks", "vfx/iw7/_requests/coop/vfx_zb_thu_sparks", 50, 1, ( 0, 90, 0 ) );
    fxp_add( "lightcone", "vfx/iw7/core/zombie/vfx_zom_light_cone_01", 150, 0, ( 300, 180, 180 ) );
    fxp_add( "wedge", "vfx/iw7/core/zombie/vfx_zmb_light_wedge_01", 120, 0, ( 339, 181, 0 ) );
    fxp_add( "strobe", "vfx/iw7/core/zombie/vfx_zmb_light_strobe_01", 80, 0, ( 0, 90, 0 ) );
    fxp_add( "glowred", "vfx/iw7/core/zombie/weapon/shredder/zmb_part_glow_red", 50, 0, ( 0, 0, 0 ) );
    fxp_add( "dustfall", "vfx/iw7/levels/sa_common/vfx_sa_falling_dust_rumble_ch", 150, 1, ( 0, 0, 0 ) );
    fxp_add( "firetrash", "vfx/iw7/core/zombie/vfx_zmb_fire_trash_01", 2, 0, ( 0, 0, 0 ) );
    fxp_add( "candyfire", "vfx/iw7/_requests/coop/zmb_candypile_fire", 2, 0, ( 0, 0, 0 ) );
    fxp_add( "groundfire", "vfx/iw7/core/zombie/robot/vfx_ground_fire_linger", 2, 0, ( 0, 0, 0 ) );
    fxp_add( "moths", "vfx/iw7/core/zombie/environment/vfx_zb_moth_b", 60, 0, ( 0, 0, 0 ) );
    foreach ( f in level.fxp )
        print( "[IWZ local] FXPROBE_LOAD name=" + f.name + " id=" + f.id + " path=" + f.path );
    level thread fxp_main();
}

fxp_add( name, path, dz, oneshot, ang )
{
    f = spawnstruct();
    f.name = name;
    f.path = path;
    f.dz = dz;
    f.oneshot = oneshot;
    f.fwd = anglestoforward( ang );
    f.up = anglestoup( ang );
    f.id = loadfx( path );
    level.fxp[level.fxp.size] = f;
}

fxp_quiet()
{
    if ( isdefined( level.flag ) && isdefined( level.flag["pause_wave_progression"] ) )
        scripts\engine\utility::flag_set( "pause_wave_progression" );
    level.zombies_paused = 1;
    foreach ( a in scripts\cp\cp_agent_utils::getaliveagentsofteam( "axis" ) )
        a dodamage( a.health + 10000, a.origin );
}

fxp_main()
{
    level waittill( "connected", player );
    while ( !isalive( player ) )
        wait 0.2;
    wait 12;
    player.ignoreme = 1;
    player takeallweapons();
    executecommand( "cg_draw2D 0" );
    print( "[IWZ local] SPAWNED; origin=" + player.origin );
    executecommand( "dvardump" );
    fxp_quiet();
    stations = strtok( getdvar( "paris_iwz_fxstations" ), "@" );
    home = player.origin;
    homeyaw = player getplayerangles()[1];
    for ( s = 0; s < stations.size; s++ )
    {
        v = strtok( stations[s], "," );
        if ( v[0] == "spawn" )
        {
            cam = home;
            yaw = homeyaw;
        }
        else
        {
            cam = ( float( v[0] ), float( v[1] ), float( v[2] ) );
            yaw = float( v[3] );
        }
        n = int( v[4] );
        player setorigin( cam );
        player setplayerangles( ( 0, yaw, 0 ) );
        player freezecontrols( 1 );
        player takeallweapons();
        wait 3;
        for ( k = 0; k < level.fxp.size && k < n; k++ )
        {
            f = level.fxp[k];
            fxp_quiet();
            o = cam + anglestoforward( ( 0, yaw, 0 ) ) * 170 + ( 0, 0, f.dz );
            player takeallweapons();
            wait 1.2;
            tag = "iwzp_s" + s + "_" + f.name;
            executecommand( "capture_frame " + tag + "_off" );
            wait 0.6;
            ent = undefined;
            if ( f.oneshot )
                level thread fxp_oneshots( f, o );
            else
            {
                ent = spawnfx( f.id, o, f.fwd, f.up );
                triggerfx( ent, -4 );
            }
            wait 2.5;
            for ( i = 0; i < 3; i++ )
            {
                executecommand( "capture_frame " + tag + "_on" + i );
                wait 0.6;
            }
            level notify( "fxp_stop" );
            if ( isdefined( ent ) )
                ent delete();
            print( "[IWZ local] FXPROBE s=" + s + " name=" + f.name + " id=" + f.id + " origin=" + o + " cam=" + cam + " yaw=" + yaw );
            wait 2;
        }
    }
    print( "[IWZ local] DONE" );
}

fxp_oneshots( f, o )
{
    level endon( "fxp_stop" );
    for ( ;; )
    {
        playfx( f.id, o, f.fwd, f.up );
        wait 0.3;
    }
}
