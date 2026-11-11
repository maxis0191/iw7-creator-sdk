// BAKER'S DOZENS (Lodestar Exchange, 3000; bible 06-PERKS.md section 2). Every thirteenth bullet hit the owner lands
// on a zombie is punched: triple damage, it passes through two more zombies behind the first, and it pays the hit's
// points twice. Misses do not count and do not reset; wonder weapons, launchers and explosives neither count nor punch.
// A counter beside the ammunition shows the hits so far, amber at twelve. Called from cp_iwz_perks (zombie damage hook).

init()
{
    level.szp.bk_reach = 600;       // how far behind the first zombie the punch carries
    level.szp.bk_width = 36;        // how far off the line of the shot a zombie may stand and still be hit
    level.szp.bk_through = 2;
    level.szp.bk_bonus_floor = 20;  // the bible's fallback bonus when the game paid nothing for the hit (a kill pays its own)
}

give()
{
    self.szp_bk_count = 0;
    if ( !isdefined( self.szp_bk_hits ) )
        self.szp_bk_hits = 0;
    if ( !isdefined( self.szp_bk_punches ) )
        self.szp_bk_punches = 0;
    self hud_update( 0 );
}

take()
{
    self.szp_bk_count = 0;
    if ( isdefined( self.szp_bk_hud ) )
        self.szp_bk_hud.alpha = 0;
    scripts\cp\zombies\zombies_perk_machines::remove_zombies_perk_icon_and_index( "perk_machine_bakers" );
}

// self: the zombie being hit, before the damage is applied. Returns the damage to apply.
on_hit( p, damage, mod, weapon, point, dir, hitloc )
{
    if ( scripts\engine\utility::is_true( p.szp_bk_punching ) )
        return damage;
    if ( !isdefined( mod ) || !scripts\engine\utility::isbulletdamage( mod ) )
        return damage;
    if ( !scripts\cp\maps\cp_iwz\cp_iwz_perks::ordinary_weapon( weapon, mod ) )
        return damage;
    if ( !isalive( self ) || damage <= 0 )
        return damage;
    p.szp_bk_count++;
    p.szp_bk_hits++;
    if ( p.szp_bk_count < 13 )
    {
        p hud_update( 0 );
        return damage;
    }
    p.szp_bk_count = 0;
    p.szp_bk_punches++;
    punched = damage * 3;
    head = 0;
    if ( isdefined( hitloc ) && ( hitloc == "head" || hitloc == "helmet" || hitloc == "neck" ) )
        head = 1;
    print( "[IWZ perks] BAKERS_PUNCH player=" + p getentitynumber() + " base=" + damage + " punched=" + punched + " head=" + head + " weapon=" + weapon + " hits=" + p.szp_bk_hits + " punches=" + p.szp_bk_punches );
    p.szp_bk_last_base = damage;
    p.szp_bk_last_punched = punched;
    p punch_through( self, punched, mod, weapon, point, dir );      // first: the zombies behind pay their own hits
    p thread punch_points( self );                                  // then: the money this hit pays, read on the next frame
    p hud_update( 1 );
    return punched;
}

// the punch carries on through up to two zombies on the line of the shot, behind the first
punch_through( first, dmg, mod, weapon, point, dir )
{
    self endon( "disconnect" );
    if ( !isdefined( first ) || !isdefined( level.spawned_enemies ) )
        return;
    // the line of the shot: the damage direction, or from the shooter's eye to the first zombie
    d = ( 0, 0, 0 );
    if ( isdefined( dir ) )
        d = vectornormalize( ( dir[0], dir[1], 0 ) );
    if ( length( d ) < 0.5 )
        d = vectornormalize( ( first.origin[0] - self.origin[0], first.origin[1] - self.origin[1], 0 ) );
    if ( length( d ) < 0.5 )
        return;
    base = first.origin;
    hit = [];
    along = [];
    foreach ( z in level.spawned_enemies )
    {
        if ( !isdefined( z ) || z == first || !isalive( z ) )
            continue;
        v = z.origin - base;
        v = ( v[0], v[1], 0 );
        a = vectordot( v, d );
        if ( a <= 8 || a > level.szp.bk_reach )
            continue;
        side = length( v - d * a );
        if ( side > level.szp.bk_width )
            continue;
        hit[hit.size] = z;
        along[along.size] = a;
    }
    // nearest first (a few bodies at most: a plain selection)
    n = 0;
    tries = 0;
    self.szp_bk_punching = 1;
    while ( n < level.szp.bk_through && tries < hit.size )
    {
        tries++;
        best = -1;
        for ( i = 0; i < hit.size; i++ )
        {
            if ( along[i] < 0 )
                continue;
            if ( best < 0 || along[i] < along[best] )
                best = i;
        }
        if ( best < 0 )
            break;
        z = hit[best];
        along[best] = -1;
        if ( isdefined( z ) && isalive( z ) )
        {
            z.szp_bk_force = dmg;       // the stock multipliers already made dmg: the hook returns it as it is (no second headshot)
            z dodamage( dmg, z.origin + ( 0, 0, 40 ), self, self, mod, weapon );
            if ( isdefined( z ) )
                z.szp_bk_force = undefined;
            n++;
        }
    }
    self.szp_bk_punching = undefined;
    self.szp_bk_last_extra = n;
    print( "[IWZ perks] BAKERS_THROUGH player=" + self getentitynumber() + " extra=" + n + " damage=" + dmg );
}

// the punched hit pays its points twice: whatever the game paid for it, once more (a kill pays its own kill reward and
// the bonus is then the bible's floor)
punch_points( z )
{
    self endon( "disconnect" );
    m0 = self scripts\cp\cp_persistence::get_player_currency();
    wait 0.05;
    paid = self scripts\cp\cp_persistence::get_player_currency() - m0;
    bonus = paid;
    if ( !isdefined( z ) || !isalive( z ) || bonus <= 0 )
        bonus = level.szp.bk_bonus_floor;
    self scripts\cp\cp_persistence::give_player_currency( bonus, undefined, undefined, 1, "bonus" );
    self.szp_bk_last_paid = paid;
    self.szp_bk_last_bonus = bonus;
    print( "[IWZ perks] BAKERS_POINTS player=" + self getentitynumber() + " paid=" + paid + " bonus=" + bonus );
}

hud_update( punched )
{
    if ( !isdefined( self.szp_bk_hud ) )
    {
        e = newclienthudelem( self );
        e.horzalign = "right";
        e.vertalign = "bottom";
        e.alignx = "right";
        e.aligny = "bottom";
        e.x = -236;
        e.y = -22;
        e.fontscale = 1.6;
        e.archived = 1;
        e.hidewheninmenu = 1;
        e.sort = 20;
        self.szp_bk_hud = e;
    }
    e = self.szp_bk_hud;
    e.alpha = 1;
    if ( punched )
    {
        e.color = ( 1, 0.35, 0.25 );
        e setvalue( 13 );
        self thread hud_after_punch();
        return;
    }
    e setvalue( self.szp_bk_count );
    if ( self.szp_bk_count == 12 )
        e.color = ( 1, 0.72, 0.18 );
    else
        e.color = ( 0.95, 0.92, 0.85 );
}

hud_after_punch()
{
    self endon( "disconnect" );
    self notify( "szp_bk_after_punch" );
    self endon( "szp_bk_after_punch" );
    wait 0.6;
    if ( isdefined( self.szp_bk_hud ) && scripts\cp\maps\cp_iwz\cp_iwz_perks::has( self, "perk_machine_bakers" ) )
        self hud_update( 0 );
}

state()
{
    c = -1;
    if ( isdefined( self.szp_bk_count ) )
        c = self.szp_bk_count;
    h = 0;
    if ( isdefined( self.szp_bk_hits ) )
        h = self.szp_bk_hits;
    k = 0;
    if ( isdefined( self.szp_bk_punches ) )
        k = self.szp_bk_punches;
    s = "bakers_count=" + c + " bakers_hits=" + h + " bakers_punches=" + k;
    if ( isdefined( self.szp_bk_last_base ) )
        s += " bakers_last_base=" + self.szp_bk_last_base + " bakers_last_punched=" + self.szp_bk_last_punched;
    if ( isdefined( self.szp_bk_last_extra ) )
        s += " bakers_last_extra=" + self.szp_bk_last_extra;
    if ( isdefined( self.szp_bk_last_bonus ) )
        s += " bakers_last_paid=" + self.szp_bk_last_paid + " bakers_last_bonus=" + self.szp_bk_last_bonus;
    return s;
}
