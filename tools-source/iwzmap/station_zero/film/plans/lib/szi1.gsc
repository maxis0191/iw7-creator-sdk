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

// i1_reach: can a player in the hall use a wall buy behind a counter? The player's hull is traced from (x, y0) toward (x, y1) at z 1 (playerphysicstrace:
// clips count) to where it stops; reach = distance from the eye there (stop + 60) to the interaction struct of `kind` nearest (x, y1); use_radius = the
// dvar player_useRadius (the use range of the player_use_trigger the stock interactions move to the struct). stop_y, reach, use_radius, sx, sy, sz.
i1_reach( name, kind, x, y0, y1 )
{
    stop = playerphysicstrace( ( x, y0, 1 ), ( x, y1, 1 ) );
    best = undefined;
    foreach ( s in level.current_interaction_structs )
    {
        if ( isdefined( s ) && isdefined( s.script_noteworthy ) && s.script_noteworthy == kind )
        {
            if ( !isdefined( best ) || distance( s.origin, ( x, y1, 0 ) ) < distance( best.origin, ( x, y1, 0 ) ) )
                best = s;
        }
    }
    r = -1;
    o = ( 0, 0, 0 );
    if ( isdefined( best ) )
    {
        o = best.origin;
        r = int( distance( stop + ( 0, 0, 60 ), o ) );
    }
    print( "[IWZ local] GL PROBE name=" + name + " stop_y=" + stop[1] + " reach=" + r + " use_radius=" + getdvarfloat( "player_useRadius" ) + " sx=" + o[0] + " sy=" + o[1]
        + " sz=" + o[2] );
}

// i1_buy: a purchase from where player 0 STANDS (the plan puts him there with `tp`; this never moves him). The lab's `use` step teleports the
// player in front of the struct along the struct's yaw: for D4's hall struct (yaw 180, facing the door) that is 4 units past the door plane and
// 36 from the struct, and inside the Heel & Key stall for the marksman buy. On a client the stock monitor (cp_interaction.gsc
// move_to_closest_interaction) clears the player's interaction point when his origin is within 75 of the struct (:232), so that purchase
// charged nothing; a headless bot runs no monitor and bought anyway.
// Here: the struct of `kind` nearest (nx, ny, nz); wait up to 4 s for the stock monitor to pick it (a client: hint=1, the prompt shows);
// without a monitor (headless) the monitor's own rule is applied at the player's real position: refused when his origin is within 75 of the
// struct or when another struct is the nearest one the monitor would offer; else the interaction point is set as the monitor sets it. Then
// the player's interaction trigger fires (the Use button's effect). Prints found, hint, route, d (origin to struct), eye_d (eye to the use
// trigger the monitor placed), use_radius, money0, money1, spent, has (wall weapons: the stock variant test), weapons0, weapons1, x, y.
i1_buy( name, kind, nx, ny, nz, seconds )
{
    p = level.players[0];
    o = p.origin;
    near = ( nx, ny, nz );
    s = undefined;
    foreach ( st in level.current_interaction_structs )
    {
        if ( isdefined( st ) && isdefined( st.script_noteworthy ) && st.script_noteworthy == kind )
        {
            if ( !isdefined( s ) || distance( st.origin, near ) < distance( s.origin, near ) )
                s = st;
        }
    }
    found = 0;
    hint = 0;
    route = "none";
    d = -1;
    eye_d = -1;
    m0 = p scripts\cp\cp_persistence::get_player_currency();
    w0 = p getweaponslistprimaries().size;
    if ( isdefined( s ) )
    {
        found = 1;
        d = int( distance( o, s.origin ) );
        t0 = gettime();
        while ( gettime() - t0 < 4000 )
        {
            if ( isdefined( p.last_interaction_point ) && p.last_interaction_point == s )
            {
                hint = 1;
                break;
            }
            wait 0.05;
        }
        route = "monitor";
        if ( !hint )
        {
            route = "direct";
            if ( d <= 75 )
                route = "refused_within_75";
            else
            {
                closest = scripts\engine\utility::get_array_of_closest( o, level.current_interaction_structs, undefined, 10, 750, 1 );
                first = undefined;
                foreach ( c in closest )
                {
                    if ( isdefined( c ) && distance( o, c.origin ) > 75 )
                    {
                        first = c;
                        break;
                    }
                }
                if ( !isdefined( first ) || first != s )
                    route = "refused_not_nearest";
            }
            if ( route == "direct" )
            {
                if ( !isdefined( p.interaction_trigger ) )
                    p.interaction_trigger = scripts\cp\cp_interaction::get_player_interaction_trigger();
                p.last_interaction_point = undefined;
                p scripts\cp\cp_interaction::set_interaction_point( s );
                wait 0.3;
            }
        }
        if ( route == "monitor" || route == "direct" )
        {
            if ( isdefined( p.interaction_trigger ) )
                eye_d = int( distance( p geteye(), p.interaction_trigger.origin ) );
            wait 0.15;
            p.interaction_trigger notify( "trigger", p );
            wait seconds;
        }
    }
    m1 = p scripts\cp\cp_persistence::get_player_currency();
    has = -1;
    if ( isdefined( s ) && scripts\cp\cp_interaction::interaction_is_weapon_buy( s ) )
        has = p scripts\cp\cp_weapon::has_weapon_variation( s.script_noteworthy );
    print( "[IWZ local] GL PROBE name=" + name + " found=" + found + " hint=" + hint + " route=" + route + " d=" + d + " eye_d=" + eye_d
        + " use_radius=" + getdvarfloat( "player_useRadius" ) + " money0=" + m0 + " money1=" + m1 + " spent=" + ( m0 - m1 ) + " has=" + has
        + " weapons0=" + w0 + " weapons1=" + p getweaponslistprimaries().size + " x=" + p.origin[0] + " y=" + p.origin[1] );
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
