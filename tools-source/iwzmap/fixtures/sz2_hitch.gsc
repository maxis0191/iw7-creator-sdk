// Station Zero streaming-hitch probe (private local fixture; QA g25t: ~2.8 s freeze on the first approach to the hero
// car, ~1.9 s at the first door purchase in the hall). The fxperf DLL (IW7_FXPERF) records frame times per phase from
// the dvar paris_iwz_fxphase; the run's sampler records client CPU and disk reads next to the HITCH markers.
//   phase 0  idle at the start (hall)             phase 1  first look at the hero car from the deck
//   phase 2  first door purchase in the hall       phase 3  the car again (second approach, warm)
//   phase 4  a second door purchase (warm)
init()
{
    if ( getdvarint( "dedicated" ) || getdvar( "paris_iwz_mode" ) != "hitch" )
        return;
    level thread iwz_hitch();
}

iwz_hitch_phase( p )
{
    setdvar( "paris_iwz_fxphase", p );
    print( "[IWZ local] HITCH phase=" + p + " time=" + gettime() );
}

iwz_hitch_door( player, skip )
{
    n = 0;
    foreach ( s in level.all_interaction_structs )
    {
        if ( !isdefined( s.script_noteworthy ) || !issubstr( s.script_noteworthy, "debris_" ) || !isdefined( s.target ) )
            continue;
        if ( distance2d( s.origin, ( -400, 3800, 0 ) ) > 1400 )
            continue;      // hall doors only
        if ( n == skip )
        {
            print( "[IWZ local] HITCH door=" + s.script_noteworthy + " at=" + s.origin );
            scripts\cp\zombies\interaction_openareas::clear_debris( s, player );
            return;
        }
        n++;
    }
}

iwz_hitch()
{
    setdvar( "paris_iwz_fxphase", -1 );
    level waittill( "connected", player );
    while ( !isalive( player ) )
        wait 0.2;
    wait 6;
    player.ignoreme = 1;
    player takeallweapons();
    player freezecontrols( 1 );
    print( "[IWZ local] SPAWNED; origin=" + player.origin );
    player setorigin( ( -300, 3900, 0 ) );
    player setplayerangles( ( 0, 90, 0 ) );
    iwz_hitch_phase( 0 );
    wait 10;
    // the car fills the view from the deck (car x 32..568, y 1421..1555; deck at y 1800)
    player setorigin( ( 300, 1820, -320 ) );
    player setplayerangles( ( 5, 270, 0 ) );
    iwz_hitch_phase( 1 );
    wait 10;
    player setorigin( ( -600, 3400, 0 ) );
    player setplayerangles( ( 0, 270, 0 ) );
    wait 1;
    iwz_hitch_phase( 2 );
    iwz_hitch_door( player, 0 );
    wait 10;
    player setorigin( ( 300, 1820, -320 ) );
    player setplayerangles( ( 5, 270, 0 ) );
    iwz_hitch_phase( 3 );
    wait 8;
    player setorigin( ( -600, 3400, 0 ) );
    iwz_hitch_phase( 4 );
    iwz_hitch_door( player, 1 );
    wait 8;
    iwz_hitch_phase( 5 );
    print( "[IWZ local] DONE" );
}
