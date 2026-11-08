// Station Zero hero train / track kit proof (local private session only), staged as custom_scripts/cp/iwzmap_local.gsc.
// dvars:
//   paris_train_models  "group:model,x,y,z,yaw;..."  script_models spawned at load (the kit under test), by group
//   paris_train_views   "name,x,y,z,yaw,pitch[,group[,stance]];..." capture_frame iwzt_<name> with only that group shown (all
//                       groups when omitted), then (paris_train_ab 1)
//                       iwzt_<name>_off with the kit hidden: drawn / textured / lit evidence by frame difference
//   paris_train_traces  "name,x0,y0,z0,x1,y1,z1;..." bullettrace / playerphysicstrace / physicstrace results
//   paris_train_walk    "name,x0,y0,z0,x1,y1,z1;..." the player is moved in 4-unit steps with playerphysicstrace and
//                       reports where it stops (walk into the car, walls block)
//   paris_train_perf    seconds: frame-time sample (TICK lines carry gettime and the server frame) at the hero view
// Every result line starts with [IWZ train].

init()
{
    if ( getdvarint( "dedicated" ) || getdvar( "paris_train_models" ) == "" )
        return;
    level thread train_main();
}

train_main()
{
    level.train_models = [];
    specs = strtok( getdvar( "paris_train_models" ), ";" );
    for ( i = 0; i < specs.size; i++ )
    {
        gm = strtok( specs[i], ":" );
        v = strtok( gm[1], "," );
        m = spawn( "script_model", ( float( v[1] ), float( v[2] ), float( v[3] ) ) );
        m.angles = ( 0, float( v[4] ), 0 );
        m setmodel( v[0] );
        m.train_group = gm[0];
        level.train_models[level.train_models.size] = m;
        print( "[IWZ train] MODEL " + gm[0] + " " + v[0] + " origin=" + m.origin + " angles=" + m.angles );
    }
    // map-placed kit (IWZ_TRAIN generator): its script_models join the show/hide set as group "map"
    ents = getentarray( "script_model", "classname" );
    for ( i = 0; i < ents.size; i++ )
    {
        if ( isdefined( ents[i].model ) && getsubstr( ents[i].model, 0, 4 ) == "iwz_" )
        {
            ents[i].train_group = "map";
            level.train_models[level.train_models.size] = ents[i];
        }
    }
    print( "[IWZ train] KIT models=" + level.train_models.size );
    level waittill( "connected", player );
    print( "[IWZ train] CONNECTED t=" + gettime() );
    while ( !isalive( player ) )
        wait 0.2;
    wait 6;
    player.ignoreme = 1;
    player takeallweapons();
    print( "[IWZ train] SPAWNED origin=" + player.origin );
    if ( getdvar( "paris_iwz_cmds" ) != "" )
    {
        cmds = strtok( getdvar( "paris_iwz_cmds" ), "|" );
        for ( i = 0; i < cmds.size; i++ )
            executecommand( cmds[i] );
        wait 1;
    }
    train_traces();
    train_views( player );
    player unlink();
    train_walk( player );
    train_perf( player );
    player unlink();
    print( "[IWZ train] DONE" );
}

train_show( on, group )
{
    for ( i = 0; i < level.train_models.size; i++ )
    {
        if ( on && ( !isdefined( group ) || group == "" || level.train_models[i].train_group == group ) )
            level.train_models[i] show();
        else
            level.train_models[i] hide();
    }
}

train_views( player )
{
    if ( getdvar( "paris_train_views" ) == "" )
        return;
    views = strtok( getdvar( "paris_train_views" ), ";" );
    for ( i = 0; i < views.size; i++ )
    {
        v = strtok( views[i], "," );
        player unlink();
        player setorigin( ( float( v[1] ), float( v[2] ), float( v[3] ) ) );
        // hold the player at the view point (no fall where the kit has no clip, e.g. inside a spawned car)
        if ( !isdefined( level.train_anchor ) )
            level.train_anchor = spawn( "script_origin", player.origin );
        level.train_anchor.origin = ( float( v[1] ), float( v[2] ), float( v[3] ) );
        player playerlinkto( level.train_anchor );
        player setplayerangles( ( float( v[5] ), float( v[4] ), 0 ) );
        player freezecontrols( 1 );
        player takeallweapons();
        group = "";
        if ( v.size > 6 )
            group = v[6];
        stance = "stand";
        if ( v.size > 7 )
            stance = v[7];
        player setstance( stance );
        train_show( 1, group );
        wait 2.5;
        executecommand( "capture_frame iwzt_" + v[0] );
        wait 1;
        print( "[IWZ train] VIEW " + v[0] + " origin=" + player.origin + " angles=" + player getplayerangles() + " eye=" + player geteye() );
        if ( getdvarint( "paris_train_ab" ) )
        {
            train_show( 0 );
            player takeallweapons();
            wait 1.5;
            executecommand( "capture_frame iwzt_" + v[0] + "_off" );
            wait 1;
            train_show( 1, group );
        }
    }
}

train_traces()
{
    if ( getdvar( "paris_train_traces" ) == "" )
        return;
    rows = strtok( getdvar( "paris_train_traces" ), ";" );
    for ( i = 0; i < rows.size; i++ )
    {
        v = strtok( rows[i], "," );
        a = ( float( v[1] ), float( v[2] ), float( v[3] ) );
        b = ( float( v[4] ), float( v[5] ), float( v[6] ) );
        bt = bullettrace( a, b, 0, undefined );
        pp = playerphysicstrace( a, b );
        ph = physicstrace( a, b );
        print( "[IWZ train] TRACE " + v[0] + " bullet_frac=" + bt["fraction"] + " bullet_pos=" + bt["position"] + " player_end=" + pp + " physics_end=" + ph );
    }
}

train_walk( player )
{
    if ( getdvar( "paris_train_walk" ) == "" )
        return;
    rows = strtok( getdvar( "paris_train_walk" ), ";" );
    for ( i = 0; i < rows.size; i++ )
    {
        v = strtok( rows[i], "," );
        a = ( float( v[1] ), float( v[2] ), float( v[3] ) );
        b = ( float( v[4] ), float( v[5] ), float( v[6] ) );
        player setorigin( a );
        wait 0.3;
        d = distance( a, b );
        steps = int( d / 4 ) + 1;
        pos = player.origin;
        blocked = 0;
        for ( k = 1; k <= steps; k++ )
        {
            want = a + ( b - a ) * ( k / steps );
            want = ( want[0], want[1], pos[2] );
            // flat move 2 units up; if that hits, a step of up to 18 units (as a player steps up)
            lift = 2;
            end = playerphysicstrace( pos + ( 0, 0, lift ), want + ( 0, 0, lift ) );
            if ( distance( end, want + ( 0, 0, lift ) ) > 0.5 )
            {
                lift = 18;
                end = playerphysicstrace( pos + ( 0, 0, lift ), want + ( 0, 0, lift ) );
            }
            if ( distance( end, want + ( 0, 0, lift ) ) > 0.5 )
            {
                blocked = 1;
                pos = end - ( 0, 0, lift );
                break;
            }
            // settle on the floor below (steps up to 18 units, like a player's step height)
            down = playerphysicstrace( want + ( 0, 0, lift ), want - ( 0, 0, 64 ) );
            pos = down;
        }
        player setorigin( pos );
        wait 0.2;
        print( "[IWZ train] WALK " + v[0] + " blocked=" + blocked + " stop=" + pos + " from=" + a + " to=" + b + " ground=" + player isonground() );
    }
}

train_perf( player )
{
    secs = getdvarint( "paris_train_perf" );
    if ( !secs )
        return;
    views = strtok( getdvar( "paris_train_views" ), ";" );
    v = strtok( views[0], "," );
    player setorigin( ( float( v[1] ), float( v[2] ), float( v[3] ) ) );
    player setplayerangles( ( float( v[5] ), float( v[4] ), 0 ) );
    for ( pass = 0; pass < 2; pass++ )
    {
        train_show( pass == 0 );
        wait 1;
        print( "[IWZ train] PERF_BEGIN shown=" + ( pass == 0 ) + " t=" + gettime() );
        executecommand( "cg_drawfps 1" );
        wait secs;
        print( "[IWZ train] PERF_END shown=" + ( pass == 0 ) + " t=" + gettime() );
    }
    train_show( 1 );
}
