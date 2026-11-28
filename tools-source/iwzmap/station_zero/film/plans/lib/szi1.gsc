// I1 (28 Nov 2026): probes and one driver of the Arcade's gameplay plan (i1_arcade.json; "libraries": ["szi1"], forge --library-dir). One GL PROBE line each.

// i1_stand: where player 0 stands: ground (isonground), x, y, z, nav_d (distance to the closest point of the navigation mesh, -1 when the engine finds none),
// zone (the spawn volume the player touches, "none" outside every volume)
i1_stand( name )
{
    p = level.players[0];
    o = p.origin;
    gr = 0;
    if ( p isonground() )
        gr = 1;
    nd = -1;
    np = getclosestpointonnavmesh( o );
    if ( isdefined( np ) )
        nd = int( distance( np, o ) * 10 ) / 10.0;
    zn = "none";
    foreach ( v in getentarray( "spawn_volume", "targetname" ) )
    {
        if ( isdefined( v.basename ) && p istouching( v ) )
            zn = v.basename;
    }
    print( "[IWZ local] GL PROBE name=" + name + " ground=" + gr + " nav_d=" + nd + " zone=" + zn + " x=" + o[0] + " y=" + o[1] + " z=" + o[2] );
}

// i1_wheel_to: the stock magic wheel moved to `area` as the stock code moves it after its rolls (interaction_magicwheel.gsc _id_BC3E: the wheel of that
// area made usable, every other one out of order), then: active (area_name of level.current_active_wheel), x, y (its origin), wheels (every magic_wheel
// entity), areas (their area names). The base starts the wheel on platform_a (cp_iwz.gsc set_magic_wheel_starting_location), so the Arcade's position is
// out of order at the start of a match until the wheel moves there.
i1_wheel_to( name, area )
{
    f = getfunction( "scripts/cp/zombies/interaction_magicwheel", "_id_BC3E" );
    level thread [[ f ]]( area );
    wait 3;
    a = "none";
    x = 0;
    y = 0;
    if ( isdefined( level.current_active_wheel ) )
    {
        w = level.current_active_wheel;
        if ( isdefined( w.area_name ) )
            a = w.area_name;
        x = w.origin[0];
        y = w.origin[1];
    }
    n = 0;
    areas = "";
    foreach ( w in getentarray( "magic_wheel", "script_noteworthy" ) )
    {
        n++;
        if ( isdefined( w.area_name ) )
            areas = areas + w.area_name + ";";
        else
            areas = areas + "undefined;";
    }
    print( "[IWZ local] GL PROBE name=" + name + " active=" + a + " x=" + x + " y=" + y + " wheels=" + n + " areas=" + areas );
}
