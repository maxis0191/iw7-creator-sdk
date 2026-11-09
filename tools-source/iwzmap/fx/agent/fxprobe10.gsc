// FX probe 9 (tint ladder of the dark variants; from probe 8 (from probe 6: horizontal view, effect on the view axis, two off frames) (local private session only): ambient FX in the dark d12 state, with and without the weapon flashlight
// aimed at them. Staged as custom_scripts/cp/iwzmap_local.gsc on a darkness build (cp_iwz_flashlight module).
// Stations (paris_iwz_fxstations "x,y,z,yaw,dist,set@..."): camera feet + yaw; each effect of the set is spawned dist
// units ahead (plus its own dz) and the view is turned onto it. Per effect and pass (flashlight on, then off):
// frames iwzd_s<s>_<name>_<fl|nofl>_off, _on0.._on2 (+1.5 / 2.5 / 3.5 s after the start).
init()
{
    if ( getdvarint( "dedicated" ) || getdvar( "paris_iwz_mode" ) != "fxprobe10" )
        return;
    level.fxp = [];
    // set 0: motes at the distance of the station (250 / 400 u), view horizontal
    fxp_add( 0, "motes", "vfx/iw7/levels/cp_disco/amb/vfx_amb_motes", 0, 0, ( 0, 0, 0 ) );
    fxp_add( 0, "motes_d15", "vfx/iwz/amb/vfx_amb_motes_d15", 0, 0, ( 0, 0, 0 ) );
    fxp_add( 0, "motes_d40", "vfx/iwz/amb/vfx_amb_motes_d40", 0, 0, ( 0, 0, 0 ) );
    fxp_add( 0, "glitter", "vfx/iw7/core/zombie/environment/vfx_cop_zmb_particle_dust", 0, 0, ( 0, 0, 0 ) );
    foreach ( f in level.fxp )
        print( "[IWZ local] FXPROBE_LOAD set=" + f.set + " name=" + f.name + " id=" + f.id );
    level thread fxp_main();
}

fxp_add( set, name, path, dz, oneshot, ang )
{
    f = spawnstruct();
    f.set = set;
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

fxp_flashlight( player, on )
{
    if ( on && !scripts\engine\utility::is_true( player.iwz_fl_on ) )
    {
        player scripts\cp\maps\cp_iwz\cp_iwz_flashlight::iwz_fl_attach( 0 );
        wait 1.5;
    }
    else if ( !on && scripts\engine\utility::is_true( player.iwz_fl_on ) )
    {
        player scripts\cp\maps\cp_iwz\cp_iwz_flashlight::iwz_fl_detach();
        wait 1.5;
    }
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
    print( "[IWZ local] SPAWNED; origin=" + player.origin + "; fl=" + player.iwz_fl_on );
    fxp_quiet();
    stations = strtok( getdvar( "paris_iwz_fxstations" ), "@" );
    for ( s = 0; s < stations.size; s++ )
    {
        v = strtok( stations[s], "," );
        cam = ( float( v[0] ), float( v[1] ), float( v[2] ) );
        yaw = float( v[3] );
        dist = float( v[4] );
        set = int( v[5] );
        for ( pass = 0; pass < 2; pass++ )
        {
            fl = ( pass == 0 );
            tagfl = "fl";
            if ( !fl )
                tagfl = "nofl";
            foreach ( f in level.fxp )
            {
                if ( f.set != set )
                    continue;
                fxp_quiet();
                o = cam + anglestoforward( ( 0, yaw, 0 ) ) * dist + ( 0, 0, 60 + f.dz );
                player setorigin( cam );
                player setplayerangles( ( 0, yaw, 0 ) );
                player freezecontrols( 1 );
                player takeallweapons();
                fxp_flashlight( player, fl );
                wait 2;
                tag = "iwzk_s" + s + "_" + f.name + "_" + tagfl;
                executecommand( "capture_frame " + tag + "_off" );
                wait 0.5;
                executecommand( "capture_frame " + tag + "_off1" );
                wait 0.3;
                ent = undefined;
                if ( f.oneshot )
                    level thread fxp_oneshots( f, o );
                else
                {
                    ent = spawnfx( f.id, o, f.fwd, f.up );
                    triggerfx( ent, -4 );
                }
                wait 1.5;
                for ( i = 0; i < 3; i++ )
                {
                    executecommand( "capture_frame " + tag + "_on" + i );
                    wait 1;
                }
                level notify( "fxp_stop" );
                if ( isdefined( ent ) )
                    ent delete();
                print( "[IWZ local] FXPROBE10 s=" + s + " name=" + f.name + " fl=" + fl + " origin=" + o + " cam=" + cam + " angles=" + player getplayerangles() + " flon=" + player.iwz_fl_on );
                wait 3;
            }
        }
    }
    fxp_flashlight( player, 1 );
    print( "[IWZ local] DONE" );
}

fxp_oneshots( f, o )
{
    level endon( "fxp_stop" );
    for ( ;; )
    {
        playfx( f.id, o, f.fwd, f.up );
        wait 0.5;
    }
}
