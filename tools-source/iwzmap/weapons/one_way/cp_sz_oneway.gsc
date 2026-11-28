// ONE WAY, wonder weapon of Station Zero: the game script of the mechanic.
// Design and numbers: docs/station-zero/weapons/one-way/DESIGN.md (sections 2 to 4). One implementation, used by the
// map module and by the test library (make_gamelab.py appends this file to the plan fixture).
//
//   issue    a bullet of the weapon does no damage: it books the zombie it hits on the next departure
//            (body = second class, head = first class; 3 tickets a zombie; a fourth is spent for nothing)
//   calm     a booked ordinary zombie flinches 0.6 s, then walks until the bell (the stock slow card's own call)
//   beat     the departure is re-issued every 6.0 s of the match's own time; nothing starts it or rings it early;
//            a ticket of the last 0.5 s is valid for the departure after
//   bell     every booked zombie takes the sum of its tickets, flat (rated by round, not scaled by anything)
//   taken    health covered: a kill credited to the owner
//   carried  health not covered: at most 6 a bell per owner, oldest ticket first, hidden and held, put back at the
//            next bell, down 1.5 s; for 12 s after that it is neither calmed nor carried
//   full     6 or more taken on one bell by one owner: 1 ticket back for 2 taken (upgraded: 2 for 3)
//   insta    while the Insta-Kill pickup runs, any ticket covers an ordinary zombie at the bell
//   leaves   a player who leaves cancels his tickets
//   upgraded every zombie taken for good comes back one bell later as an arrival: 3,970 to unbooked ordinary
//            zombies within 120 units, at most two arrivals a zombie a bell
// Hooks are chained (the previous function runs first). Lines "[SZ oneway] ..." are the trace the plans read.

ow_init()
{
    if ( isdefined( level.ow_on ) )
        return;
    level.ow_on = 1;
    level.ow_match = "szoneway";        // part of the weapon's name; a test sets a stock stand-in
    level.ow_force_up = 0;              // a test sets 1: every such weapon counts as upgraded
    level.ow_period = 6000;
    level.ow_closing = 500;
    level.ow_r2 = 3970;                 // second class, R24
    level.ow_r1 = 9920;                 // first class, 2.5 x
    level.ow_u2 = 8510;                 // upgraded second class, R32
    level.ow_u1 = 21270;
    level.ow_arrival = 3970;
    level.ow_arrival_radius = 120;
    level.ow_special_cap = 2000;
    level.ow_max_tix = 3;
    level.ow_carry_max = 6;
    level.ow_flinch_ms = 600;
    level.ow_immune_ms = 12000;
    level.ow_down_ms = 1500;
    level.ow_carried = [];
    level.ow_arrivals = [];
    level.ow_bells = 0;
    level.ow_keys = 0;
    level.ow_gone = [];
    level.ow_prev_damage = level.onzombiedamage_func;
    level.onzombiedamage_func = ::ow_damage;
    level.ow_prev_reward = level.eligable_for_reward_func;
    level.eligable_for_reward_func = ::ow_reward;
    level thread ow_clock();
    print( "[SZ oneway] INIT period=" + level.ow_period + " closing=" + level.ow_closing );
}

ow_is( weapon )
{
    return isdefined( weapon ) && isstring( weapon ) && issubstr( weapon, level.ow_match );
}

ow_upgraded( weapon )
{
    return level.ow_force_up || issubstr( weapon, "pap" );
}

ow_bullet( mod )
{
    return isdefined( mod ) && ( mod == "MOD_RIFLE_BULLET" || mod == "MOD_PISTOL_BULLET" || mod == "MOD_HEAD_SHOT" );
}

ow_head( hitloc )
{
    return isdefined( hitloc ) && ( hitloc == "head" || hitloc == "helmet" || hitloc == "neck" );
}

ow_ordinary()
{
    return isdefined( self.agent_type ) && self.agent_type == "generic_zombie";
}

// The departure a ticket issued at time t is valid for (the index of its bell).
ow_departure( t )
{
    dep = int( t / level.ow_period ) + 1;
    if ( level.ow_period - ( t % level.ow_period ) <= level.ow_closing )
        dep++;
    return dep;
}

ow_stat( owner, key, n )
{
    if ( !isdefined( owner ) )
        return;
    if ( !isdefined( owner.ow_stats ) )
        owner.ow_stats = [];
    if ( !isdefined( owner.ow_stats[key] ) )
        owner.ow_stats[key] = 0;
    owner.ow_stats[key] += n;
}

// level.onzombiedamage_func( inflictor, attacker, damage, flags, mod, weapon, point, dir, hitloc, timeoffset, model, part )
ow_damage( inflictor, attacker, damage, flags, mod, weapon, point, dir, hitloc, timeoffset, modelindex, partname )
{
    if ( isdefined( level.ow_prev_damage ) )
        damage = self [[ level.ow_prev_damage ]]( inflictor, attacker, damage, flags, mod, weapon, point, dir, hitloc, timeoffset, modelindex, partname );
    // the bell's own damage, and an arrival's: exactly the rated amount, whatever the callback made of it
    if ( isdefined( self.ow_due ) )
    {
        due = self.ow_due;
        self.ow_due = undefined;
        return due;
    }
    if ( isdefined( self.ow_carry ) )
        return 0;                       // a carried zombie is not on the platform
    if ( !ow_is( weapon ) || !ow_bullet( mod ) || !isdefined( attacker ) || !isplayer( attacker ) )
        return damage;
    self ow_issue( attacker, weapon, ow_head( hitloc ) );
    return 0;
}

// A ticket pays no hit points; kill rewards take another path and stay.
ow_reward( a, b, mod, weapon, e, f )
{
    if ( ow_is( weapon ) && ow_bullet( mod ) )
        return 0;
    if ( isdefined( level.ow_prev_reward ) )
        return [[ level.ow_prev_reward ]]( a, b, mod, weapon, e, f );
    return 1;
}

ow_issue( owner, weapon, head )
{
    t = gettime();
    if ( !isdefined( self.ow_tix ) )
        self.ow_tix = [];
    if ( self.ow_tix.size >= level.ow_max_tix )
    {
        ow_stat( owner, "wasted", 1 );
        print( "[SZ oneway] WASTED victim=" + self getentitynumber() + " owner=" + owner getentitynumber() );
        return;
    }
    up = ow_upgraded( weapon );
    value = level.ow_r2;
    if ( up )
        value = level.ow_u2;
    if ( head )
    {
        value = level.ow_r1;
        if ( up )
            value = level.ow_u1;
    }
    if ( !isdefined( owner.ow_key ) )
    {
        level.ow_keys++;
        owner.ow_key = level.ow_keys;
        level thread ow_owner_watch( owner, owner.ow_key );
    }
    tix = spawnstruct();
    tix.owner = owner;
    tix.key = owner.ow_key;
    tix.value = value;
    tix.head = head;
    tix.up = up;
    tix.weapon = weapon;
    tix.time = t;
    tix.dep = ow_departure( t );
    self.ow_tix[self.ow_tix.size] = tix;
    ow_stat( owner, "issued", 1 );
    if ( head )
        ow_stat( owner, "first", 1 );
    print( "[SZ oneway] ISSUE victim=" + self getentitynumber() + " owner=" + owner getentitynumber() + " head=" + head + " up=" + up + " value=" + value + " dep=" + tix.dep + " held=" + self.ow_tix.size + " t=" + t );
    if ( self ow_ordinary() )
        self thread ow_calm();
}

// Flinch, then walk until the bell. A zombie put back less than 12 s ago is ticketed but not calmed.
ow_calm()
{
    self endon( "death" );
    if ( isdefined( self.ow_immune ) && gettime() < self.ow_immune )
        return;
    self notify( "ow_calm" );
    self endon( "ow_calm" );
    self.stunned = 1;
    self.stun_hit_time = gettime() + level.ow_flinch_ms;
    wait level.ow_flinch_ms / 1000;
    self.stunned = undefined;
    if ( isdefined( self.ow_carry ) || isdefined( self.ow_walk ) )
        return;
    if ( isdefined( self.asm ) && isdefined( self.asm.cur_move_mode ) )
        self.ow_walk = self.asm.cur_move_mode;
    else
        self.ow_walk = self.movemode;
    if ( isdefined( self.ow_walk ) && self.ow_walk != "walk" && self.ow_walk != "slow_walk" )
        self scripts\asm\asm_bb::bb_requestmovetype( "walk" );
    print( "[SZ oneway] CALM victim=" + self getentitynumber() + " from=" + self.ow_walk );
}

ow_uncalm()
{
    if ( !isdefined( self.ow_walk ) )
        return;
    mode = self.ow_walk;
    self.ow_walk = undefined;
    if ( isalive( self ) && mode != "walk" && mode != "slow_walk" )
        self scripts\asm\asm_bb::bb_requestmovetype( mode );
}

// The beat belongs to the match: bell n rings at n * period of the match's own clock.
ow_clock()
{
    level endon( "game_ended" );
    for ( ;; )
    {
        t = gettime();
        left = level.ow_period - ( t % level.ow_period );
        wait left / 1000;
        dep = int( ( gettime() + 25 ) / level.ow_period );
        level ow_bell( dep );
    }
}

// A player who leaves cancels his tickets (his carried are put back at the next bell like any other).
ow_owner_watch( owner, key )
{
    level endon( "game_ended" );
    owner waittill( "disconnect" );
    level.ow_gone[key] = 1;
    print( "[SZ oneway] LEFT key=" + key );
}

ow_owner_of( tix )
{
    // whoever issued most; the first to issue if equal
    best = undefined;
    bestn = 0;
    foreach ( a in tix )
    {
        if ( !isdefined( a.owner ) )
            continue;
        n = 0;
        foreach ( b in tix )
        {
            if ( isdefined( b.owner ) && b.owner == a.owner )
                n++;
        }
        if ( n > bestn )
        {
            best = a.owner;
            bestn = n;
        }
    }
    return best;
}

ow_bell( dep )
{
    t = gettime();
    zombies = scripts\cp\cp_agent_utils::getaliveagentsofteam( "axis" );
    // 1. the carried of the bell before are put back
    back = 0;
    keep = [];
    foreach ( z in level.ow_carried )
    {
        if ( !isdefined( z ) || !isalive( z ) )
            continue;
        if ( z.ow_carry <= dep )
        {
            z thread ow_put_back();
            back++;
        }
        else
            keep[keep.size] = z;
    }
    level.ow_carried = keep;
    // 2. arrivals of what was taken for good one bell ago (upgraded)
    arrivals = level.ow_arrivals;
    level.ow_arrivals = [];
    // 3. every booked zombie whose ticket is for this bell
    booked = [];
    foreach ( z in zombies )
    {
        if ( !isdefined( z.ow_tix ) || z.ow_tix.size == 0 || isdefined( z.ow_carry ) )
            continue;
        now = [];
        later = [];
        foreach ( x in z.ow_tix )
        {
            if ( !isdefined( x.owner ) || isdefined( level.ow_gone[x.key] ) )
                continue;               // its owner left: the ticket is cancelled
            if ( x.dep <= dep )
                now[now.size] = x;
            else
                later[later.size] = x;
        }
        z.ow_tix = later;
        if ( now.size == 0 )
            continue;
        z.ow_now = now;
        booked[booked.size] = z;
    }
    taken = [];
    carried = [];
    stayed = 0;
    foreach ( z in booked )
    {
        now = z.ow_now;
        z.ow_now = undefined;
        owner = ow_owner_of( now );
        sum = 0;
        up = 0;
        first = now[0].time;
        foreach ( x in now )
        {
            sum += x.value;
            if ( x.up )
                up = 1;
            if ( x.time < first )
                first = x.time;
        }
        ordinary = z ow_ordinary();
        if ( !ordinary )
            sum = int( min( sum, level.ow_special_cap ) );
        else if ( isdefined( level.insta_kill ) && level.insta_kill )
            sum = int( max( sum, z.health ) );      // Insta-Kill: any ticket is enough
        if ( z.ow_tix.size == 0 )
            z ow_uncalm();
        health = z.health;
        id = z getentitynumber();
        origin = z.origin;
        key = owner getentitynumber();
        if ( sum >= health )
        {
            if ( !isdefined( taken[key] ) )
                taken[key] = 0;
            taken[key]++;
            ow_stat( owner, "taken", 1 );
            if ( up )
            {
                a = spawnstruct();
                a.origin = origin;
                a.owner = owner;
                a.key = owner.ow_key;
                a.weapon = now[0].weapon;
                level.ow_arrivals[level.ow_arrivals.size] = a;
            }
            print( "[SZ oneway] TAKEN victim=" + id + " owner=" + key + " sum=" + sum + " health=" + health + " tickets=" + now.size + " dep=" + dep );
            z ow_rated( sum, origin, owner, now[0].weapon );
            continue;
        }
        z ow_rated( sum, origin, owner, now[0].weapon );
        if ( !isalive( z ) )
            continue;
        immune = isdefined( z.ow_immune ) && t < z.ow_immune;
        if ( !isdefined( carried[key] ) )
            carried[key] = [];
        if ( ordinary && !immune )
        {
            c = spawnstruct();
            c.z = z;
            c.first = first;
            c.owner = owner;
            c.sum = sum;
            carried[key][carried[key].size] = c;
        }
        else
        {
            stayed++;
            ow_stat( owner, "stayed", 1 );
            if ( ordinary )
                z thread ow_flinch();
            print( "[SZ oneway] STAYED victim=" + id + " owner=" + key + " sum=" + sum + " left=" + z.health + " ordinary=" + ordinary + " immune=" + immune + " dep=" + dep );
        }
    }
    // six cars: the oldest tickets are carried, the others stay
    ncarried = 0;
    foreach ( list in carried )
    {
        n = 0;
        while ( list.size > 0 )
        {
            oldest = 0;
            for ( i = 1; i < list.size; i++ )
            {
                if ( list[i].first < list[oldest].first )
                    oldest = i;
            }
            c = list[oldest];
            rest = [];
            for ( i = 0; i < list.size; i++ )
            {
                if ( i != oldest )
                    rest[rest.size] = list[i];
            }
            list = rest;
            if ( n < level.ow_carry_max )
            {
                n++;
                ncarried++;
                ow_stat( c.owner, "carried", 1 );
                c.z ow_carry_away( dep + 1 );
                print( "[SZ oneway] CARRIED victim=" + c.z getentitynumber() + " owner=" + c.owner getentitynumber() + " sum=" + c.sum + " left=" + c.z.health + " back=" + ( dep + 1 ) );
            }
            else
            {
                stayed++;
                ow_stat( c.owner, "stayed", 1 );
                c.z thread ow_flinch();
                print( "[SZ oneway] STAYED victim=" + c.z getentitynumber() + " owner=" + c.owner getentitynumber() + " sum=" + c.sum + " left=" + c.z.health + " ordinary=1 immune=0 full=1 dep=" + dep );
            }
        }
    }
    // full train: one ticket back for two taken (upgraded: two for three), per owner
    ntaken = 0;
    foreach ( p in level.players )
    {
        key = p getentitynumber();
        if ( !isdefined( taken[key] ) )
            continue;
        ntaken += taken[key];
        if ( taken[key] >= 6 )
            p ow_refund( taken[key] );
    }
    // arrivals
    nkilled = 0;
    if ( arrivals.size > 0 )
        nkilled = ow_arrive( arrivals, dep );
    if ( booked.size > 0 || back > 0 || arrivals.size > 0 )
    {
        level.ow_bells++;
        print( "[SZ oneway] BELL dep=" + dep + " t=" + t + " booked=" + booked.size + " taken=" + ntaken + " carried=" + ncarried + " stayed=" + stayed + " back=" + back + " arrivals=" + arrivals.size + " arrival_kills=" + nkilled );
    }
    level notify( "ow_bell", dep );
}

// Exactly `amount` to this zombie, credited to `owner`. The stock callback can return before it reaches the hook
// (retail gametype_zombie.gsc: explosive touch on a special, a frozen zombie, a meteor hit), so the amount asked
// is never left on the zombie for the next hit of another weapon.
ow_rated( amount, origin, owner, weapon )
{
    self.ow_due = amount;
    self dodamage( amount, origin, owner, owner, "MOD_UNKNOWN", weapon );
    if ( isdefined( self ) )
        self.ow_due = undefined;
}

ow_flinch()
{
    self endon( "death" );
    self.stunned = 1;
    self.stun_hit_time = gettime() + level.ow_flinch_ms;
    wait level.ow_flinch_ms / 1000;
    self.stunned = undefined;
}

ow_refund( n )
{
    w = undefined;
    foreach ( have in self getweaponslistprimaries() )
    {
        if ( ow_is( have ) )
            w = have;
    }
    if ( !isdefined( w ) )
        return;
    back = int( n / 2 );
    if ( ow_upgraded( w ) )
        back = int( n * 2 / 3 );
    stock = self getweaponammostock( w );
    self setweaponammostock( w, stock + back );
    got = self getweaponammostock( w ) - stock;
    ow_stat( self, "full", 1 );
    ow_stat( self, "refund", got );
    print( "[SZ oneway] FULL owner=" + self getentitynumber() + " taken=" + n + " back=" + back + " got=" + got + " stock=" + stock + "->" + self getweaponammostock( w ) );
}

// Carried one stop: off the platform (hidden, held, ignored, undamaged), alive for the round count.
ow_carry_away( back )
{
    self.ow_carry = back;
    self.ow_place = self.origin;
    self.ow_was_scripted = self.scripted_mode;
    self.ow_was_ignoreall = self.ignoreall;
    self.ow_was_ignoreme = self.ignoreme;
    self.stunned = undefined;
    self.scripted_mode = 1;
    self.ignoreall = 1;
    self.ignoreme = 1;
    self.goalradius = 16;
    self setgoalpos( self.origin );
    self hide();
    level.ow_carried[level.ow_carried.size] = self;
}

// Where a carried zombie is put back: its place, unless a player stands within 96 units of it.
ow_place_for( place )
{
    if ( ow_far_from_players( place, 96 ) )
        return place;
    for ( ring = 128; ring <= 256; ring += 64 )
    {
        for ( yaw = 0; yaw < 360; yaw += 45 )
        {
            spot = getclosestpointonnavmesh( place + anglestoforward( ( 0, yaw, 0 ) ) * ring );
            if ( isdefined( spot ) && ow_far_from_players( spot, 96 ) )
                return spot;
        }
    }
    return place;
}

ow_far_from_players( spot, d )
{
    foreach ( p in level.players )
    {
        if ( isalive( p ) && distancesquared( p.origin, spot ) < d * d )
            return 0;
    }
    return 1;
}

ow_put_back()
{
    self endon( "death" );
    spot = ow_place_for( self.ow_place );
    moved = distance( spot, self.ow_place );
    self setorigin( spot );
    self setgoalpos( spot );
    self show();
    self.ow_carry = undefined;
    self.ow_immune = gettime() + level.ow_immune_ms;
    self.stunned = 1;
    self.stun_hit_time = gettime() + level.ow_down_ms;
    print( "[SZ oneway] BACK victim=" + self getentitynumber() + " moved=" + int( moved ) + " health=" + self.health );
    wait level.ow_down_ms / 1000;
    self.stunned = undefined;
    self.scripted_mode = self.ow_was_scripted;
    self.ignoreall = self.ow_was_ignoreall;
    self.ignoreme = self.ow_was_ignoreme;
    self ow_uncalm();
}

// Upgraded: where a zombie was taken for good, unbooked ordinary zombies within 120 units take the arrival.
ow_arrive( arrivals, dep )
{
    killed = 0;
    zombies = scripts\cp\cp_agent_utils::getaliveagentsofteam( "axis" );
    foreach ( z in zombies )
        z.ow_arr = 0;
    foreach ( a in arrivals )
    {
        if ( !isdefined( a.owner ) || isdefined( level.ow_gone[a.key] ) )
            continue;
        hit = 0;
        foreach ( z in zombies )
        {
            if ( !isalive( z ) || !z ow_ordinary() || isdefined( z.ow_carry ) )
                continue;
            if ( isdefined( z.ow_tix ) && z.ow_tix.size > 0 )
                continue;
            if ( z.ow_arr >= 2 )
                continue;
            if ( distancesquared( z.origin, a.origin ) > level.ow_arrival_radius * level.ow_arrival_radius )
                continue;
            z.ow_arr++;
            hit++;
            health = z.health;
            z ow_rated( level.ow_arrival, a.origin, a.owner, a.weapon );
            if ( isalive( z ) )
                z thread ow_flinch();
            else
            {
                killed++;
                ow_stat( a.owner, "arrival_kills", 1 );
            }
        }
        ow_stat( a.owner, "arrivals", 1 );
        print( "[SZ oneway] ARRIVAL at=" + a.origin + " owner=" + a.owner getentitynumber() + " hit=" + hit + " dep=" + dep );
    }
    return killed;
}
