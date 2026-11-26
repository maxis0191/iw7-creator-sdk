// Round 8 copy of szaccept::sz_round_play (iw7-paris-server ops/gamelab/lib) with the anchor fixed in the Arcade corridor (-2000, 3900, 0) instead of sz_anchor(zone). Plan-local library; the original is untouched.
sz8_round_play( name, wave, zone, cap_s, stuck_s )
{
    t0 = gettime();
    level.stop_spawning = 0;
    start_wait = 12000;
    if ( wave <= 1 )
        start_wait = 40000;        // the first round starts some seconds after the match
    while ( ( !isdefined( level.wave_num ) || level.wave_num < wave ) && gettime() - t0 < start_wait )
    {
        wait 0.25;
    }
    started = 0;
    if ( isdefined( level.wave_num ) && level.wave_num == wave )
        started = 1;
    anchor = ( -2000, 3900, 0 );
    floor = playerphysicstrace( anchor + ( 0, 0, 8 ), anchor - ( 0, 0, 200 ) );
    self setorigin( floor );
    self setplayerangles( ( 0, 0, 0 ) );
    t1 = gettime();
    ents0 = getentarray().size;
    seen = [];
    zref = [];
    reached = 0;
    stuck = 0;
    other = 0;
    n_seen = 0;
    stuck_where = "";
    token = name + "_" + t1;       // this call: what a zombie carries from another round's call is not this round's
    stall = 0;
    while ( started && level.wave_num == wave && gettime() - t1 < cap_s * 1000 )
    {
        wait 0.5;
        alive_now = [];
        foreach ( z in scripts\cp\cp_agent_utils::getaliveagentsofteam( "axis" ) )
        {
            if ( !isalive( z ) )
                continue;
            k = z getentitynumber();
            alive_now[k] = 1;
            zref[k] = z;
            // (24 Nov 2026, FG2) the fields live on the agent, and the engine uses an agent again for the next zombie with its fields
            // intact: a zombie whose fields are of another call, or of a life that ended (sz_life_watch clears them at its death), is new.
            // Before, a zombie in an agent that had lived in an earlier round was not counted in `seen` and could still be "reached"
            // (reached 9 of seen 8).
            if ( !isdefined( z.szr_run ) || z.szr_run != token )
            {
                z.szr_run = token;
                z.szr_t = undefined;
                z.szr_o = undefined;
                z.szr_done = undefined;
                z.szr_other = undefined;
                z thread sz_life_watch( token );
            }
            // a zombie that was missing from the alive list for a tick was counted "other"; it is back, so it is not
            if ( isdefined( z.szr_other ) )
            {
                z.szr_other = undefined;
                other--;
            }
            // (24 Nov 2026, FG2) a zombie is counted once. dodamage does not always kill within the tick: the zombie was alive on the next
            // one and counted "reached" again (reached 50 of 37 seen, pct 122 to 144). It is damaged again, the same way, and not counted.
            if ( isdefined( z.szr_done ) )
            {
                if ( z.szr_done == 2 )
                    z dodamage( z.health + 1000, z.origin, self, self, "MOD_RIFLE_BULLET", self getcurrentweapon() );
                else
                    z dodamage( z.health + 1000, z.origin, undefined, undefined, "MOD_SUICIDE" );
                continue;
            }
            now = gettime();
            // (22 Nov 2026) the clock lives on the zombie, not on its entity number: numbers are reused, and a new zombie in a
            // dead one's number inherited its start time and was counted "stuck" at its spawner. A jump of more than 400 units
            // in half a second is the stock cleanup moving it to a spawner near the players: its clocks start again.
            if ( !isdefined( z.szr_t ) || ( isdefined( z.szr_o ) && distance( z.origin, z.szr_o ) > 400 ) )
            {
                if ( !isdefined( z.szr_t ) )
                {
                    n_seen++;
                    z.szr_spawn = z.origin;
                }
                z.szr_t = now;
                z.szr_trav = 0;
                z.szr_p0 = undefined;
                z.szr_best = undefined;
                z.szr_best_t = now;
                z.szr_d0 = z.origin;
                z.szr_d0_t = now;
            }
            else if ( isdefined( z.szr_o ) )
                z.szr_trav = z.szr_trav + distance( z.origin, z.szr_o );
            z.szr_o = z.origin;
            seen[k] = 1;
            // the navmesh path to the player the first time there is one (p0 of its line)
            if ( !isdefined( z.szr_p0 ) )
            {
                v = self sz_navdist( z.origin, self.origin );
                if ( v >= 0 )
                    z.szr_p0 = v;
            }
            // path measure: the shortest path to its goal so far; 64 units shorter restarts the clock. No goal: no sample.
            tg = z pathdisttogoal();
            if ( isdefined( z getpathgoalpos() ) && isdefined( tg ) && tg > 1 && ( !isdefined( z.szr_best ) || tg < z.szr_best - 64 ) )
            {
                z.szr_best = tg;
                z.szr_best_t = now;
            }
            // place measure: 64 units from where it stood when this clock started moves the anchor and restarts the clock
            if ( distance( z.origin, z.szr_d0 ) > 64 )
            {
                z.szr_d0 = z.origin;
                z.szr_d0_t = now;
            }
            // reached: within 110 on the ground plane and 96 in height (on a stair slope the 3D distance of a zombie at the
            // player's feet is 113..139: RC4 stair A census)
            dz = z.origin[2] - self.origin[2];
            if ( distance2d( z.origin, self.origin ) < 110 && dz < 96 && dz > -96 )
            {
                seen[k] = 2;
                z.szr_done = 2;
                reached++;
                z dodamage( z.health + 1000, z.origin, self, self, "MOD_RIFLE_BULLET", self getcurrentweapon() );
                continue;
            }
            // stuck: the rule above the function (a zombie milling in the crowd at the player, within 200, is not stuck)
            if ( now - z.szr_best_t > stuck_s * 1000 && now - z.szr_d0_t > stuck_s * 1000 && distance( z.origin, self.origin ) > 200 )
            {
                seen[k] = 3;
                z.szr_done = 3;
                stuck++;
                line = self sz_stuck_line( z, now );
                if ( stuck <= 8 )
                    print( "[IWZ local] GL PROBE name=" + name + "_stuck" + stuck + " wave=" + wave + " ms=" + ( now - t1 ) + " " + line );
                if ( stuck <= 3 )
                    stuck_where = stuck_where + line + "; ";
                z dodamage( z.health + 1000, z.origin, undefined, undefined, "MOD_SUICIDE" );
            }
        }
        foreach ( k in getarraykeys( seen ) )
        {
            if ( seen[k] == 1 && !isdefined( alive_now[k] ) )
            {
                seen[k] = 4;
                other++;
                if ( isdefined( zref[k] ) && isalive( zref[k] ) && isdefined( zref[k].szr_run ) && zref[k].szr_run == token )
                    zref[k].szr_other = 1;
            }
        }
    }
    if ( started && level.wave_num == wave )
    {
        stall = 1;
        print( "[IWZ local] GL PROBE name=" + name + "_stall wave=" + level.wave_num + " desired=" + sz_v( level.desired_enemy_deaths_this_wave )
            + " deaths=" + sz_v( level.current_enemy_deaths ) + " paused=" + sz_v( level.zombies_paused ) + " stop_spawning=" + sz_v( level.stop_spawning )
            + " spawned=" + sz_v( level.current_num_spawned_enemies ) + " max_static=" + sz_v( level.max_static_spawned_enemies ) + " alive=" + scripts\cp\cp_agent_utils::getaliveagentsofteam( "axis" ).size );
        // (22 Nov 2026) at a stall, every zombie still alive: where it is, how long it has lived, its path goal and the navmesh
        // path distance to the player (sz_navdist; -1: no path)
        j = 0;
        foreach ( z in scripts\cp\cp_agent_utils::getaliveagentsofteam( "axis" ) )
        {
            if ( !isalive( z ) )
                continue;
            j++;
            goal = "none";
            gp = z getpathgoalpos();
            if ( isdefined( gp ) )
                goal = "" + gp;
            pdp = self sz_navdist( z.origin, self.origin );
            age = -1;
            if ( isdefined( z.szr_t ) )
                age = gettime() - z.szr_t;
            print( "[IWZ local] GL PROBE name=" + name + "_left_" + j + " org=" + z.origin + " age_ms=" + age + " goal=" + goal + " path_to_player=" + pdp
                + " dist=" + int( distance( z.origin, self.origin ) ) + " player=" + self.origin );
        }
    }
    ms = gettime() - t1;
    // (22 Nov 2026) zombies the stock cleanup removed without reaching ("other") are respawned as new zombies near the players
    // and counted again: the share is of the zombies that stayed in play
    pct = 0;
    if ( n_seen - other > 0 )
        pct = int( reached * 100 / ( n_seen - other ) );
    print( "[IWZ local] GL PROBE name=" + name + " wave=" + wave + " started=" + started + " zone=" + zone + " seen=" + n_seen + " reached=" + reached + " stuck=" + stuck
        + " other=" + other + " pct=" + pct + " stall=" + stall + " ms=" + ms + " ents0=" + ents0 + " ents1=" + getentarray().size + " wave_now=" + level.wave_num
        + " stuck_at=\"" + stuck_where + "\"" );
}
