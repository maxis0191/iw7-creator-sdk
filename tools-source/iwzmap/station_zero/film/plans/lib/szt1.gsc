// T1 (27 Nov 2026): the Terminus trip as one GL PROBE line ("libraries": ["szt1"], forge run --library-dir). Reads only; changes nothing.
// state: level.iwz_terminus.state; visits, riders, returned, refused, paused (the module's own pause), pause_s; zpaused: level.zombies_paused;
// alive: zombies alive (level.spawned_enemies); inside: player 0 is in the Terminus box of the arrival marker; car: player 0 is in car 1's box;
// offgrid, busy: player 0's is_off_grid and iwz_busy; ground: player 0 on the ground; x, y, z: player 0's origin.
t1_term( name )
{
    st = "none";
    visits = 0;
    riders = 0;
    returned = 0;
    refused = 0;
    paused = 0;
    pause_s = 0;
    inside = 0;
    car = 0;
    if ( isdefined( level.iwz_terminus ) )
    {
        t = level.iwz_terminus;
        st = t.state;
        visits = t.visits;
        riders = t.riders;
        returned = t.returned;
        refused = t.refused;
        paused = t.paused;
        pause_s = t.pause_seconds;
    }
    zp = 0;
    if ( isdefined( level.zombies_paused ) && level.zombies_paused )
        zp = 1;
    alive = 0;
    if ( isdefined( level.spawned_enemies ) )
    {
        foreach ( z in level.spawned_enemies )
        {
            if ( isdefined( z ) && isalive( z ) )
                alive++;
        }
    }
    p = level.players[0];
    o = p.origin;
    if ( isdefined( level.iwz_terminus ) && isdefined( level.iwz_terminus.term_lo ) )
    {
        t = level.iwz_terminus;
        if ( o[0] >= t.term_lo[0] && o[0] <= t.term_hi[0] && o[1] >= t.term_lo[1] && o[1] <= t.term_hi[1] && o[2] >= t.term_lo[2] && o[2] <= t.term_hi[2] )
            inside = 1;
        if ( o[0] >= t.car_lo[0] && o[0] <= t.car_hi[0] && o[1] >= t.car_lo[1] && o[1] <= t.car_hi[1] && o[2] >= t.car_lo[2] && o[2] <= t.car_hi[2] )
            car = 1;
    }
    og = 0;
    if ( isdefined( p.is_off_grid ) && p.is_off_grid )
        og = 1;
    busy = 0;
    if ( isdefined( p.iwz_busy ) )
        busy = 1;
    gr = 0;
    if ( p isonground() )
        gr = 1;
    print( "[IWZ local] GL PROBE name=" + name + " state=" + st + " visits=" + visits + " riders=" + riders + " returned=" + returned + " refused=" + refused
        + " paused=" + paused + " pause_s=" + pause_s + " zpaused=" + zp + " alive=" + alive + " inside=" + inside + " car=" + car + " offgrid=" + og
        + " busy=" + busy + " ground=" + gr + " x=" + o[0] + " y=" + o[1] + " z=" + o[2] );
}
