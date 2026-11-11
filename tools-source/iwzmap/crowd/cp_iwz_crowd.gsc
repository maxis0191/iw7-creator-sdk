// Station Zero crowd (package E2 of the build plan): more zombies alive than the engine's 24 agent records.
//
// The stock round runs unchanged: its wave loop spawns engine agents (at most 24, a limit of the engine and of every
// client). When the round's alive cap is above 24, this module fills the rest of the cap with crowd bodies: one script
// model each (a full-body zombie model with no scriptable, so it costs none of the server's 2,048 reserved scriptable
// parts; server repository docs/ZOMBIE-CAPACITY.md), playing the stock zombie clips, moved along the navigation mesh to
// the nearest player, attacking by script and taking damage by script. A crowd body counts as a spawned enemy and its
// death as a round death through the stock loop's own counters, and it is listed by the stock list of enemies
// (scripts\cp\cp_agent_utils::get_alive_enemies, through level.dlc_get_non_agent_enemies).
//
// Nothing here is new to the client: a player on the official client sees the same crowd (models and clips of the map).
// What a crowd body does not have (stated, measured in docs/ZOMBIE-CAPACITY.md): dismemberment (that is the scriptable),
// blending between clips (a script model cuts between clips), bullet collision (a shot is tested by script from the
// shooter's eye against a head sphere and a torso capsule: instant-hit weapons only; explosions, traps and scripted
// weapons reach it through the engine's damage on the model or through the list of enemies).
//
// Dvars (server):
//   iwz_zombie_cap     0 = the cap table of 07-ENEMIES.md 2.3 (round and players); a number = that fixed alive cap;
//                      24 or less = the stock game (no crowd).
//   iwz_crowd_model    the crowd body model (default iwz_crowd_cop, the map's copy of police_officer_zombie with no
//                      scriptable).
//   iwz_crowd_log      1 = one line per crowd spawn and death in the server log (tests); status lines are always printed.

init()
{
    if ( isdefined( level.iwz_crowd ) )
        return;
    level.iwz_crowd = [];
    level.iwz_crowd_serial = 0;
    level.iwz_crowd_spawned = 0;
    level.iwz_crowd_killed = 0;
    level.iwz_crowd_recycled = 0;
    level.iwz_crowd_swings = 0;
    level.iwz_crowd_landed = 0;
    level.iwz_crowd_shots = 0;
    level.iwz_crowd_shot_hits = 0;
    level.iwz_crowd_paths = 0;
    level.iwz_crowd_nopath = 0;
    level.iwz_crowd_peak = 0;
    level.iwz_crowd_peak_total = 0;
    level.iwz_crowd_nukes = 0;
    level.iwz_crowd_model = getdvar( "iwz_crowd_model", "iwz_crowd_cop" );
    if ( level.iwz_crowd_model == "" )
        level.iwz_crowd_model = "iwz_crowd_cop";
    // movement: units a second per move mode (the stock clips' own root speed, measured in the game: see the README)
    level.iwz_crowd_speed = [];
    level.iwz_crowd_speed["walk"] = 34;
    level.iwz_crowd_speed["run"] = 110;
    level.iwz_crowd_speed["sprint"] = 190;
    level.iwz_crowd_clip = [];
    level.iwz_crowd_clip["walk"] = [ "iw7_cp_zom_walk_forward_01", "iw7_cp_zom_walk_forward_02" ];
    level.iwz_crowd_clip["run"] = [ "iw7_cp_zom_run_forward_01", "iw7_cp_zom_run_forward_02", "iw7_cp_zom_run_forward_03" ];
    level.iwz_crowd_clip["sprint"] = [ "iw7_cp_zom_sprint_forward_01", "iw7_cp_zom_sprint_forward_02", "iw7_cp_zom_sprint_forward_03" ];
    level.iwz_crowd_attack = [ "iw7_cp_zom_stand_attack_l_01", "iw7_cp_zom_stand_attack_r_01", "iw7_cp_zom_stand_attack_l_02", "iw7_cp_zom_stand_attack_r_02" ];
    level.iwz_crowd_death = [ "iw7_cp_zom_death_backward_1", "iw7_cp_zom_death_backward_2", "iw7_cp_zom_death_forward_1", "iw7_cp_zom_death_forward_2", "iw7_cp_zom_death_left_1", "iw7_cp_zom_death_right_1" ];
    // the stock list of enemies asks this hook for enemies that are not agents
    level.dlc_get_non_agent_enemies = ::iwz_crowd_alive;
    level thread iwz_crowd_supply();
    level thread iwz_crowd_move();
    level thread iwz_crowd_players();
    level thread iwz_crowd_status();
    print( "[IWZ crowd] READY model=" + level.iwz_crowd_model + " cap_dvar=" + getdvarint( "iwz_zombie_cap", 0 ) );
}

// ---- the list of enemies ------------------------------------------------------------------------------------------

iwz_crowd_alive()
{
    out = [];
    foreach ( b in level.iwz_crowd )
    {
        if ( isdefined( b ) && b.iwz_hp > 0 )
            out[out.size] = b;
    }
    return out;
}

iwz_crowd_count()
{
    n = 0;
    foreach ( b in level.iwz_crowd )
    {
        if ( isdefined( b ) && b.iwz_hp > 0 )
            n++;
    }
    return n;
}

iwz_crowd_agents()
{
    n = 0;
    foreach ( a in scripts\cp\cp_agent_utils::getaliveagentsofteam( "axis" ) )
    {
        if ( isalive( a ) )
            n++;
    }
    return n;
}

// ---- the cap ----------------------------------------------------------------------------------------------------------

// Alive cap for this round and these players (07-ENEMIES.md 2.3); iwz_zombie_cap overrides it.
iwz_crowd_cap()
{
    fixed = getdvarint( "iwz_zombie_cap", 0 );
    if ( fixed > 0 )
        return fixed;
    w = 1;
    if ( isdefined( level.wave_num ) )
        w = level.wave_num;
    n = level.players.size;
    row = 0;
    if ( w >= 25 )
        row = 4;
    else if ( w >= 20 )
        row = 3;
    else if ( w >= 15 )
        row = 2;
    else if ( w >= 10 )
        row = 1;
    table = [];
    table[0] = [ 24, 24, 24, 24 ];
    table[1] = [ 24, 28, 32, 36 ];
    table[2] = [ 30, 36, 44, 48 ];
    table[3] = [ 38, 46, 56, 62 ];
    table[4] = [ 47, 58, 70, 78 ];
    col = n - 1;
    if ( col < 0 )
        col = 0;
    if ( col > 3 )
        col = 3;
    return table[row][col];
}

// ---- the supplier: crowd bodies beyond the agents, from the stock spawners -------------------------------------------

iwz_crowd_supply()
{
    level endon( "game_ended" );
    for ( ;; )
    {
        wait 0.5;
        iwz_crowd_nuke_check();
        // bodies that were deleted leave the list
        kept = [];
        foreach ( b in level.iwz_crowd )
        {
            if ( isdefined( b ) )
                kept[kept.size] = b;
        }
        level.iwz_crowd = kept;
        cap = iwz_crowd_cap();
        crowd = iwz_crowd_count();
        agents = iwz_crowd_agents();
        if ( crowd > level.iwz_crowd_peak )
            level.iwz_crowd_peak = crowd;
        if ( agents + crowd > level.iwz_crowd_peak_total )
            level.iwz_crowd_peak_total = agents + crowd;
        if ( cap <= 24 )
            continue;           // the stock game: the agents hold the cap alone
        // the stock loop compares its spawned count (agents and crowd) with this; the engine still stops agents at 24
        if ( level.max_static_spawned_enemies > 0 )
            level.max_static_spawned_enemies = cap;
        if ( level.stop_spawning || scripts\engine\utility::is_true( level.zombies_paused ) || scripts\engine\utility::is_true( level.nuke_zombies_paused ) )
            continue;
        if ( !isdefined( level.active_spawners ) || level.active_spawners.size == 0 )
            continue;
        // a special round of the stock game (its event waves: clowns, goons) keeps its own enemies and count
        if ( !iwz_crowd_ordinary_round() )
            continue;
        owed = level.desired_enemy_deaths_this_wave - level.current_enemy_deaths - level.current_num_spawned_enemies;
        // the 24 agent records stay the agents' (ordinary zombies and specials): the crowd holds the rest of the cap
        room = cap - 24 - crowd;
        if ( cap - agents - crowd < room )
            room = cap - agents - crowd;
        n = owed;
        if ( room < n )
            n = room;
        if ( n > 2 )
            n = 2;              // two a pass, from two spawners
        for ( i = 0; i < n; i++ )
        {
            sp = iwz_crowd_spawner( 2000 );
            if ( !isdefined( sp ) )
                break;
            q = getclosestpointonnavmesh( sp.origin );
            if ( !isdefined( q ) )
                continue;
            b = iwz_crowd_body( q, sp );
            if ( !isdefined( b ) )
                break;
        }
    }
}

// An ordinary round: the stock round start lists the generic zombie as its enemy type (an event wave lists others).
iwz_crowd_ordinary_round()
{
    if ( !isdefined( level.static_enemy_types ) )
        return 0;
    foreach ( t in level.static_enemy_types )
    {
        if ( t == "generic_zombie" )
            return 1;
    }
    return 0;
}

// A random active stock spawner within range of a player, else any active one.
iwz_crowd_spawner( range )
{
    near = [];
    foreach ( sp in level.active_spawners )
    {
        foreach ( p in level.players )
        {
            if ( isdefined( p ) && distancesquared( sp.origin, p.origin ) < range * range )
            {
                near[near.size] = sp;
                break;
            }
        }
    }
    if ( near.size > 0 )
        return near[randomint( near.size )];
    return level.active_spawners[randomint( level.active_spawners.size )];
}

// The health and move mode of the round's own zombies (read from a living agent), else from the round number.
iwz_crowd_round_health()
{
    foreach ( a in scripts\cp\cp_agent_utils::getaliveagentsofteam( "axis" ) )
    {
        if ( isalive( a ) && isdefined( a.maxhealth ) && a.maxhealth > 0 && a.maxhealth < 100000 && !isdefined( a.is_suicide_bomber ) )
            return a.maxhealth;
    }
    w = 1;
    if ( isdefined( level.wave_num ) )
        w = level.wave_num;
    return 150 + w * 100;
}

iwz_crowd_round_mode()
{
    foreach ( a in scripts\cp\cp_agent_utils::getaliveagentsofteam( "axis" ) )
    {
        if ( isalive( a ) && isdefined( a.movemode ) && isdefined( level.iwz_crowd_speed[a.movemode] ) )
            return a.movemode;
    }
    w = 1;
    if ( isdefined( level.wave_num ) )
        w = level.wave_num;
    if ( w <= 3 )
        return "walk";
    if ( w <= 7 )
        return "run";
    return "sprint";
}

iwz_crowd_body( pos, sp )
{
    yaw = 0;
    p = iwz_crowd_target( pos );
    if ( isdefined( p ) )
        yaw = vectortoyaw( p.origin - pos );
    b = spawn( "script_model", pos );
    if ( !isdefined( b ) )
        return undefined;
    b.angles = ( 0, yaw, 0 );
    b setmodel( level.iwz_crowd_model );
    level.iwz_crowd_serial++;
    b.iwz_id = level.iwz_crowd_serial;
    b.iwz_hp = iwz_crowd_round_health();
    b.iwz_maxhp = b.iwz_hp;
    b.iwz_mode = iwz_crowd_round_mode();
    b.iwz_state = "move";
    b.iwz_clip = "";
    b.iwz_path = undefined;
    b.iwz_pi = 0;
    b.iwz_repath = 0;
    b.iwz_last = pos;
    b.iwz_still = 0;
    b.iwz_spawner = "none";
    if ( isdefined( sp.script_noteworthy ) )
        b.iwz_spawner = sp.script_noteworthy;
    else if ( isdefined( sp.targetname ) )
        b.iwz_spawner = sp.targetname;
    b.health = 999999;          // the engine's health never ends a body: the module counts its own
    b setcandamage( 1 );
    b iwz_crowd_play( iwz_crowd_pick( level.iwz_crowd_clip[b.iwz_mode] ) );
    b thread iwz_crowd_damage();
    level.iwz_crowd[level.iwz_crowd.size] = b;
    level.current_num_spawned_enemies++;
    level.iwz_crowd_spawned++;
    if ( getdvarint( "iwz_crowd_log", 0 ) )
        print( "[IWZ crowd] SPAWN n=" + level.iwz_crowd_spawned + " id=" + b.iwz_id + " spawner=" + b.iwz_spawner + " at=" + pos + " hp=" + b.iwz_hp
            + " mode=" + b.iwz_mode + " wave=" + level.wave_num + " agents=" + iwz_crowd_agents() + " crowd=" + iwz_crowd_count() );
    return b;
}

iwz_crowd_pick( list )
{
    return list[randomint( list.size )];
}

iwz_crowd_play( clip )
{
    if ( self.iwz_clip == clip )
        return;
    self.iwz_clip = clip;
    self scriptmodelplayanim( clip, 1 );
}

// ---- movement: along the navigation mesh to the nearest player -----------------------------------------------------

// The nearest player a zombie can go for (alive, not in last stand), else the nearest player.
iwz_crowd_target( pos )
{
    best = undefined;
    bd = 0;
    foreach ( p in level.players )
    {
        if ( !isdefined( p ) || !isalive( p ) || scripts\engine\utility::is_true( p.inlaststand ) || scripts\engine\utility::is_true( p.ignoreme ) )
            continue;
        d = distancesquared( pos, p.origin );
        if ( !isdefined( best ) || d < bd )
        {
            best = p;
            bd = d;
        }
    }
    return best;
}

// One pass over the crowd every 0.25 s: a body follows its path (asked of the engine's path finder, at most 8 paths a
// pass), keeps 30 units from other bodies, attacks within reach. A body that has not moved for 10 s and is far from
// every player goes back to the round (recycled: it is spawned again near the players), as the stock game does with
// zombies that cannot reach anyone.
iwz_crowd_move()
{
    level endon( "game_ended" );
    pass = 0;
    for ( ;; )
    {
        wait 0.25;
        pass++;
        budget = 8;
        bodies = iwz_crowd_alive();
        foreach ( b in bodies )
        {
            if ( b.iwz_state != "move" )
                continue;
            p = iwz_crowd_target( b.origin );
            if ( !isdefined( p ) )
            {
                b iwz_crowd_play( "iw7_cp_zom_walk_forward_01" );
                continue;
            }
            d = distance( b.origin, p.origin );
            if ( d <= 56 && abs( b.origin[2] - p.origin[2] ) < 48 )
            {
                b thread iwz_crowd_swing( p );
                continue;
            }
            if ( budget > 0 && ( !isdefined( b.iwz_path ) || b.iwz_pi >= b.iwz_path.size || pass >= b.iwz_repath ) )
            {
                budget--;
                b.iwz_repath = pass + 8 + randomint( 4 );       // a new path every 2 to 3 s
                path = p findpath( b.origin, p.origin );
                level.iwz_crowd_paths++;
                if ( isdefined( path ) && path.size > 0 )
                {
                    b.iwz_path = path;
                    b.iwz_pi = 0;
                }
                else
                {
                    level.iwz_crowd_nopath++;
                    b.iwz_path = [ p.origin ];
                    b.iwz_pi = 0;
                }
            }
            if ( !isdefined( b.iwz_path ) )
                continue;
            step = level.iwz_crowd_speed[b.iwz_mode] * 0.25;
            if ( d < 160 )
                goal = p.origin;            // the last stretch: straight at the player
            else
            {
                while ( b.iwz_pi < b.iwz_path.size && distance2d( b.origin, b.iwz_path[b.iwz_pi] ) < step )
                    b.iwz_pi++;
                if ( b.iwz_pi >= b.iwz_path.size )
                    goal = p.origin;
                else
                    goal = b.iwz_path[b.iwz_pi];
            }
            flat = ( goal[0] - b.origin[0], goal[1] - b.origin[1], 0 );
            if ( length( flat ) < 1 )
                continue;
            want = b.origin + vectornormalize( flat ) * step;
            // keep apart from the other bodies (a soft push)
            foreach ( o in bodies )
            {
                if ( o == b )
                    continue;
                gap = distance2d( want, o.origin );
                if ( gap < 30 && gap > 0.1 )
                    want = want + vectornormalize( ( want[0] - o.origin[0], want[1] - o.origin[1], 0 ) ) * ( 30 - gap ) * 0.5;
            }
            q = getclosestpointonnavmesh( want );
            if ( !isdefined( q ) )
                q = want;
            b.angles = ( 0, vectortoyaw( flat ), 0 );
            b moveto( q, 0.25 );
            b iwz_crowd_play( iwz_crowd_pick_once( b ) );
            if ( distance( q, b.iwz_last ) < 2 )
                b.iwz_still++;
            else
                b.iwz_still = 0;
            b.iwz_last = q;
            if ( b.iwz_still >= 40 && d > 1500 )
                b thread iwz_crowd_recycle();
        }
    }
}

// The move clip of a body is chosen once (a body keeps its gait).
iwz_crowd_pick_once( b )
{
    if ( !isdefined( b.iwz_gait ) )
        b.iwz_gait = iwz_crowd_pick( level.iwz_crowd_clip[b.iwz_mode] );
    return b.iwz_gait;
}

iwz_crowd_recycle()
{
    if ( self.iwz_hp <= 0 )
        return;
    self.iwz_hp = 0;
    self.iwz_state = "gone";
    level.iwz_crowd_recycled++;
    level.current_num_spawned_enemies--;        // back to the round's quota: the supplier makes it again near a player
    self notify( "iwz_gone" );
    self delete();
}

// The stock standing swing: a hit at its contact time if the player is still in reach.
iwz_crowd_swing( p )
{
    self endon( "iwz_gone" );
    self endon( "iwz_dying" );
    self.iwz_state = "attack";
    self.angles = ( 0, vectortoyaw( p.origin - self.origin ), 0 );
    self.iwz_clip = "";
    self iwz_crowd_play( iwz_crowd_pick( level.iwz_crowd_attack ) );
    level.iwz_crowd_swings++;
    wait 0.5;
    if ( isdefined( p ) && isalive( p ) && distance( self.origin, p.origin ) <= 72 && !scripts\engine\utility::is_true( p.inlaststand ) )
    {
        level.iwz_crowd_landed++;
        p dodamage( 40, self.origin, self, self, "MOD_MELEE" );
    }
    wait 0.9;
    if ( self.iwz_state == "attack" )
    {
        self.iwz_state = "move";
        self.iwz_clip = "";
    }
}

// ---- damage and death -----------------------------------------------------------------------------------------------

// Damage the engine gives the model (explosions, scripted weapons, traps that damage what the list of enemies holds).
iwz_crowd_damage()
{
    self endon( "iwz_gone" );
    self endon( "iwz_dying" );
    for ( ;; )
    {
        self waittill( "damage", amount, attacker, dir, point, type );
        self.health = 999999;
        zone = "torso";
        if ( isdefined( point ) && point[2] - self.origin[2] > 58 )
            zone = "head";
        self iwz_crowd_take( amount, attacker, zone, type );
    }
}

iwz_crowd_take( amount, attacker, zone, type )
{
    if ( self.iwz_hp <= 0 )
        return;
    if ( zone == "head" )
        amount = amount * 2;
    self.iwz_hp = self.iwz_hp - amount;
    if ( isdefined( attacker ) && isplayer( attacker ) )
        attacker scripts\cp\cp_persistence::give_player_currency( 10, undefined, undefined, 1, "hit" );
    if ( self.iwz_hp <= 0 )
        self thread iwz_crowd_die( attacker, zone, type );
}

iwz_crowd_die( attacker, zone, type )
{
    self notify( "iwz_dying" );
    self setcandamage( 0 );
    self.iwz_state = "dead";
    self.iwz_hp = 0;
    level.iwz_crowd_killed++;
    level.current_num_spawned_enemies--;
    if ( !scripts\engine\utility::flag( "pause_wave_progression" ) )
        level.current_enemy_deaths++;
    if ( isdefined( attacker ) && isplayer( attacker ) )
    {
        pts = 60;
        if ( zone == "head" )
            pts = 100;
        attacker scripts\cp\cp_persistence::give_player_currency( pts, undefined, undefined, 1, "kill" );
        // the stock power-up drop rule of a zombie kill
        self scripts\cp\loot::update_enemy_killed_event( "generic_zombie", self.origin, attacker );
    }
    if ( getdvarint( "iwz_crowd_log", 0 ) )
    {
        who = "other";
        if ( isdefined( attacker ) && isplayer( attacker ) )
            who = "player";
        t = "none";
        if ( isdefined( type ) )
            t = type;
        print( "[IWZ crowd] DEATH id=" + self.iwz_id + " zone=" + zone + " type=" + t + " by=" + who + " at=" + self.origin + " killed=" + level.iwz_crowd_killed );
    }
    level notify( "iwz_crowd_killed", self );
    self.iwz_clip = "";
    self iwz_crowd_play( iwz_crowd_pick( level.iwz_crowd_death ) );
    wait 1.6;
    self notify( "iwz_gone" );
    self delete();
}

// The stock nuke kills the agents it lists itself (getaliveagentsofteam): crowd bodies die with it.
iwz_crowd_nuke_check()
{
    if ( scripts\engine\utility::is_true( level.nuke_zombies_paused ) )
    {
        if ( !scripts\engine\utility::is_true( level.iwz_crowd_in_nuke ) )
        {
            level.iwz_crowd_in_nuke = 1;
            level.iwz_crowd_nukes++;
            foreach ( b in iwz_crowd_alive() )
                b thread iwz_crowd_die( undefined, "torso", "MOD_EXPLOSIVE" );
        }
    }
    else
        level.iwz_crowd_in_nuke = 0;
}

// ---- shots: every shot of a player is tested against the crowd (bullets do not collide with a script model) ----------

iwz_crowd_players()
{
    level endon( "game_ended" );
    foreach ( p in level.players )
        p thread iwz_crowd_shots();
    for ( ;; )
    {
        level waittill( "connected", p );
        p thread iwz_crowd_shots();
    }
}

iwz_crowd_shots()
{
    self endon( "disconnect" );
    self notify( "iwz_crowd_shots" );
    self endon( "iwz_crowd_shots" );
    for ( ;; )
    {
        self waittill( "weapon_fired", weapon );
        if ( level.iwz_crowd.size == 0 )
            continue;
        level.iwz_crowd_shots++;
        eye = self geteye();
        fwd = anglestoforward( self getplayerangles() );
        best = undefined;
        bestd = 0;
        zone = "none";
        foreach ( b in iwz_crowd_alive() )
        {
            z = b iwz_crowd_ray( eye, fwd );
            if ( z == "none" )
                continue;
            d = distance( eye, b.origin );
            if ( !isdefined( best ) || d < bestd )
            {
                best = b;
                bestd = d;
                zone = z;
            }
        }
        if ( !isdefined( best ) )
            continue;
        tr = bullettrace( eye, eye + fwd * ( bestd - 16 ), 0, self );
        if ( tr["fraction"] < 0.98 )
            continue;           // a wall stood between the shooter and the body
        level.iwz_crowd_shot_hits++;
        best iwz_crowd_take( iwz_crowd_shot_damage( weapon ), self, zone, "MOD_RIFLE_BULLET" );
    }
}

// A head sphere (radius 7 at 64 units) and a torso capsule (radius 13 from 20 to 56 units) on the body's upright axis.
iwz_crowd_ray( eye, fwd )
{
    c = self.origin + ( 0, 0, 64 );
    t = vectordot( c - eye, fwd );
    if ( t > 0 && distance( eye + fwd * t, c ) <= 7 )
        return "head";
    for ( z = 20; z <= 56; z = z + 6 )
    {
        c = self.origin + ( 0, 0, z );
        t = vectordot( c - eye, fwd );
        if ( t > 0 && distance( eye + fwd * t, c ) <= 13 )
            return "torso";
    }
    return "none";
}

// Damage of one shot by weapon class (a table: script cannot read a weapon's damage); upgraded weapons count double.
iwz_crowd_shot_damage( weapon )
{
    if ( !isdefined( weapon ) )
        return 100;
    c = scripts\cp\utility::coop_getweaponclass( weapon );
    dmg = 100;
    if ( c == "weapon_pistol" )
        dmg = 80;
    else if ( c == "weapon_smg" )
        dmg = 90;
    else if ( c == "weapon_assault" )
        dmg = 120;
    else if ( c == "weapon_lmg" )
        dmg = 130;
    else if ( c == "weapon_shotgun" )
        dmg = 400;
    else if ( c == "weapon_sniper" || c == "weapon_dmr" )
        dmg = 500;
    if ( issubstr( weapon, "pap" ) )
        dmg = dmg * 2;
    return dmg;
}

// ---- status -----------------------------------------------------------------------------------------------------------

iwz_crowd_status()
{
    level endon( "game_ended" );
    for ( ;; )
    {
        wait 5;
        a = iwz_crowd_agents();
        c = iwz_crowd_count();
        if ( c == 0 && level.iwz_crowd_spawned == 0 )
            continue;
        print( "[IWZ crowd] STATUS wave=" + level.wave_num + " cap=" + iwz_crowd_cap() + " agents=" + a + " crowd=" + c + " total=" + ( a + c )
            + " peak_crowd=" + level.iwz_crowd_peak + " peak_total=" + level.iwz_crowd_peak_total + " spawned=" + level.iwz_crowd_spawned
            + " killed=" + level.iwz_crowd_killed + " recycled=" + level.iwz_crowd_recycled + " swings=" + level.iwz_crowd_swings
            + " landed=" + level.iwz_crowd_landed + " shots=" + level.iwz_crowd_shots + " shot_hits=" + level.iwz_crowd_shot_hits
            + " paths=" + level.iwz_crowd_paths + " nopath=" + level.iwz_crowd_nopath + " nukes=" + level.iwz_crowd_nukes
            + " ents=" + getentarray().size + " desired=" + level.desired_enemy_deaths_this_wave + " deaths=" + level.current_enemy_deaths
            + " counted=" + level.current_num_spawned_enemies );
    }
}
