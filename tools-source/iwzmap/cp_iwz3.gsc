// Station Zero (cp_iwz), generated from a scene description by scenegen.py: the stock IW7 zombies systems shipped in
// the zone. scenegen.py fills the door, zone link, initial zone, magic wheel and trap markers from the scene.
main()
{
    level.iwz_custom_map = 3;
    scripts\mp\mp_agent::init_agent( "mp/default_agent_definition.csv" );
    scripts\mp\agents\zombie\zombie_agent::registerscriptedagent();
    scripts\mp\agents\zombie_brute\zombie_brute_agent::registerscriptedagent();     // Spaceland registerscriptedagents()
    level.coop_weapontable = "cp/cp_weapontable.csv";
    level.disable_zombie_exo_abilities = 1;
    level.use_adjacent_volumes = 1;
    scripts\mp\agents\zombie_clown\zombie_clown::zombie_clown_init();      // Spaceland main(): clown event waves (QA g11 stall)
    level.spawn_fx_func = scripts\cp\maps\cp_zmb\cp_zmb::cp_zmb_spawn_fx_func;
    //@INITIAL@
    level.map_interaction_func = ::iwz_register_interactions;
    level.wait_for_interaction_func = scripts\cp\maps\cp_zmb\cp_zmb_interactions::zmb_wait_for_interaction_triggered;
    level.player_interaction_monitor = scripts\cp\maps\cp_zmb\cp_zmb_interactions::zmb_player_interaction_monitor;
    level.magic_wheel_spin_hint = &"CP_ZMB_INTERACTIONS_SPIN_WHEEL";
    scripts\cp\maps\cp_zmb\cp_zmb_player_character_setup::init_player_characters();
    scripts\cp\maps\cp_zmb\cp_zmb::setup_generic_zombie_model_list();
    scripts\cp\zombies\interaction_magicwheel::set_magic_wheel_starting_location( //@WHEEL@ );
    // the stock Spaceland DJ booth system starts on every map; without its booth it loops on an undefined level.dj
    // (782 runtime errors in run g5-gameplay-a): give it a parked stand-in entity
    level.dj = spawn( "script_model", ( 0, 0, -3000 ) );
    level.dj setmodel( "tag_origin" );
    // Spaceland main() weapon tables the stock perk/last-stand code reads (missing: Rat-a-tat purchase failed in
    // give_rat_a_tat_perk -> getweapontoswitchbackto -> array_contains( undefined ), QA report item 12)
    level.additional_laststand_weapon_exclusion = [ "iw7_cpbasketball_mp", "iw7_cpskeeball_mp", "iw7_cpclowntoothball_mp", "iw7_horseracepistol_zm_blue", "iw7_horseracepistol_zm_yellow", "iw7_horseracepistol_zm_red", "iw7_horseracepistol_zm_green", "iw7_shootgallery_zm", "iw7_blackholegun_mp", "iw7_penetrationrail_mp", "iw7_atomizer_mp", "iw7_glr_mp", "iw7_claw_mp", "iw7_steeldragon_mp", "iw7_shootgallery_zm_blue", "iw7_shootgallery_zm_yellow", "iw7_shootgallery_zm_red", "iw7_shootgallery_zm_green" ];
    level.last_stand_weapons = [ "iw7_g18_zm", "iw7_mag_zm", "iw7_g18_zmr", "iw7_g18_zml", "iw7_g18c_zm", "iw7_revolver_zm", "iw7_revolver_zmr", "iw7_revolver_zmr_explosive", "iw7_revolver_zml", "iw7_revolver_zml_single", "iw7_emc_zm", "iw7_emc_zmr", "iw7_emc_zmr_burst", "iw7_emc_zml", "iw7_emc_zml_spread", "iw7_nrg_zm", "iw7_nrg_zmr", "iw7_nrg_zmr_smart", "iw7_nrg_zml", "iw7_nrg_zml_charge", "iw7_dischord_zm", "iw7_headcutter_zm", "iw7_shredder_zm", "iw7_facemelter_zm", "iw7_dischord_zm_pap1", "iw7_headcutter_zm_pap1", "iw7_shredder_zm_pap1", "iw7_facemelter_zm_pap1" ];
    level.alt_mode_weapons_allowed = [ "iw7_g18_zm", "iw7_g18_zmr" ];
    level.pap_1_camo = "camo01";
    level.pap_2_camo = "camo04";
    level.no_pap_camos = [ "axe", "iw7_axe_zm", "forgefreeze" ];
    // the stock magic wheel plays this when a wheel moves; Spaceland loads it in its own fx script (QA g13: playfx undefined)
    level._effect["vfx_magicwheel_fire"] = loadfx( "vfx/iw7/_requests/coop/vfx_magicwheel_fire.vfx" );
    level._effect["iwz_rail_arc"] = loadfx( "vfx/iw7/_requests/coop/vfx_mini_grey_shock_arc.vfx" );
    level._effect["iwz_rail_spark"] = loadfx( "vfx/iw7/core/zombie/vfx_zmb_console_sparks.vfx" );
    // voice state flags vo_is_playing reads (QA g18: ~1,150 vo_is_playing errors per run from player_pain_vo /
    // codecallback_playerdamage and the trap); Spaceland's zmb_vo_init sets them to 0. g19 called the full Spaceland
    // VO set-up (zmb_vo_init, cac VO prefixes, area VO) and players spawned without their start weapon: only the
    // two flags are kept
    level.announcer_vo_playing = 0;
    level.player_vo_playing = 0;
    // per-map ranked leaderboard rows are keyed by level.script and the ranked player data has no cp_iwz row
    // (update_highest_wave_lb / updateleaderboardstats errors). g19 replaced those functions with replacefunc from the
    // level script and players then spawned without their start weapon (the Paris loadout also uses replacefunc):
    // the map no longer replaces stock functions; the leaderboard errors stay (stock code, no guard on level.script).
    // Director's Cut (Paris module): the PaP "fuses" loop reads this list on maps the stock tables do not list
    if ( !isdefined( level.player_pap_machines ) )
        level.player_pap_machines = [];
    level.iwz_door_open = [];
    level thread iwz_door_purchases();
    level thread iwz_zone_links();
    level thread iwz_wheel_cleanup();
    level thread iwz_third_rail();
    //@DARK@
    level thread iwz_door_dressing();
    level thread iwz_hide_door_blockers();
    level thread iwz_report();
    //@AUDIO@
}

// door purchases: wrap the stock debris activation so the barrier knows which door was bought
iwz_door_purchases()
{
    level endon( "game_ended" );
    names = [ "debris_750", "debris_1000", "debris_1250", "debris_1500" ];
    level.iwz_debris_orig = [];
    for ( i = 0; i < 600; i++ )
    {
        if ( isdefined( level.interactions ) && isdefined( level.interactions["debris_750"] ) )
            break;
        wait 0.1;
    }
    foreach ( n in names )
    {
        if ( !isdefined( level.interactions ) || !isdefined( level.interactions[n] ) )
            continue;
        level.iwz_debris_orig[n] = level.interactions[n].activation_func;
        level.interactions[n].activation_func = ::iwz_debris_bought;
    }
    print( "[IWZ level] DOOR_HOOKS " + level.iwz_debris_orig.size );
}

iwz_debris_bought( s, p )
{
    if ( isdefined( s ) && isdefined( s.target ) )
    {
        level.iwz_door_open[s.target] = 1;
        print( "[IWZ level] DOOR_BOUGHT " + s.target + " area=" + s.script_area );
    }
    [[ level.iwz_debris_orig[s.script_noteworthy] ]]( s, p );
}

// door table (generated); door collision is the script_brushmodel targets of each door (stock clear_debris)
iwz_door_table()
{
    doors = [];
    //@DOORS@
    return doors;
}

iwz_door( name, target, axis, plane, lo, hi, z0, z1 )
{
    door = spawnstruct();
    door.name = name;
    door.target = target;
    door.axis = axis;      // 0: the door plane is x = plane, 1: y = plane
    door.plane = plane;
    door.lo = lo;
    door.hi = hi;
    door.z0 = z0;
    door.z1 = z1;
    door.side = [];
    return door;
}

// zones joined without a door: adjacent for spawn scoring, and activated together
iwz_zone_links()
{
    level endon( "game_ended" );
    links = [];
    //@LINKS@
    for ( i = 0; i < 600 && !isdefined( level.spawn_volume_array ); i++ )
        wait 0.1;
    // the adjacency table (level._id_186E) exists once the stock spawning init sets this flag
    while ( !scripts\engine\utility::flag_exist( "init_adjacent_volumes_done" ) )
        wait 0.1;
    scripts\engine\utility::flag_wait( "init_adjacent_volumes_done" );
    foreach ( l in links )
    {
        scripts\cp\zombies\zombies_spawning::update_volume_adjacency_by_name( l[0], l[1] );
        scripts\cp\zombies\zombies_spawning::update_volume_adjacency_by_name( l[1], l[0] );
    }
    for ( ;; )
    {
        foreach ( l in links )
        {
            a = level.spawn_volume_array[l[0]];
            b = level.spawn_volume_array[l[1]];
            if ( !isdefined( a ) || !isdefined( b ) )
                continue;
            if ( scripts\engine\utility::is_true( a.active ) && !scripts\engine\utility::is_true( b.active ) )
            {
                scripts\cp\zombies\zombies_spawning::activate_volume_by_name( l[1] );
                print( "[IWZ level] ZONE_LINK " + l[0] + " -> " + l[1] );
            }
            else if ( scripts\engine\utility::is_true( b.active ) && !scripts\engine\utility::is_true( a.active ) )
            {
                scripts\cp\zombies\zombies_spawning::activate_volume_by_name( l[0] );
                print( "[IWZ level] ZONE_LINK " + l[1] + " -> " + l[0] );
            }
        }
        wait 0.5;
    }
}

iwz_report()
{
    wait 1;
    print( "[IWZ level] characters=" + level.player_character_info.size + " available=" + level.available_player_characters.size );

    for ( ;; )
    {
        p = level.players[0];
        state = "intro_over=" + scripts\engine\utility::flag( "introscreen_over" );
        if ( isdefined( p ) )
            state += " alive=" + isalive( p ) + " weapon=" + p getcurrentweapon() + " origin=" + p.origin;
        zombies = 0;
        if ( isdefined( level.spawned_enemies ) )
            zombies = level.spawned_enemies.size;
        volumes = 0;
        if ( isdefined( level.active_spawn_volumes ) )
            volumes = level.active_spawn_volumes.size;
        wave = -1;
        if ( isdefined( level.wave_num ) )
            wave = level.wave_num;
        interactions = 0;
        if ( isdefined( level.all_interaction_structs ) )
            interactions = level.all_interaction_structs.size;
        state += " zombies=" + zombies + " active_volumes=" + volumes + " wave=" + wave + " interactions=" + interactions;
        if ( zombies > 0 && isdefined( level.spawned_enemies[0] ) )
            state += " first_zombie=" + level.spawned_enemies[0].origin;
        print( "[IWZ level] " + state );
        wait 5;
    }
}

// parked template magic wheels (no zone) get a spinner model from the stock init at the closest spinner struct:
// delete those spinners so only the generated wheels show one
iwz_wheel_cleanup()
{
    level endon( "game_ended" );
    for ( i = 0; i < 300 && !isdefined( level._id_B163 ); i++ )
        wait 0.1;
    wait 3;
    if ( !isdefined( level._id_B163 ) )
        return;
    removed = 0;
    kept = 0;
    foreach ( w in level._id_B163 )
    {
        if ( isdefined( w.area_name ) )
        {
            kept++;
            continue;
        }
        if ( isdefined( w._id_10A03 ) )
            w._id_10A03 delete();
        removed++;
    }
    print( "[IWZ level] WHEELS kept=" + kept + " parked_spinners_removed=" + removed );
}





// Third Rail trap: fuse box on the platform (750, needs power): arcs along the rails for 25 s kill zombies in the
// track pit (players in the pit take damage), 60 s cooldown
iwz_third_rail()
{
    level endon( "game_ended" );
    box = scripts\engine\utility::getstruct( "iwz_trap_third_rail_fusebox", "targetname" );
    if ( !isdefined( box ) )
        return;
    level.iwz_trap_min = //@TRAPMIN@;
    level.iwz_trap_max = //@TRAPMAX@;
    level.iwz_trap_rail_y = //@TRAPRAILY@;
    level.iwz_trap_rail_z = //@TRAPRAILZ@;       // conductor rail top (arcs and sparks run along it)
    wait 1;
    level.iwz_trap_use = spawn( "script_model", box.origin + anglestoforward( box.angles ) * 12 + ( 0, 0, 36 ) );
    use = level.iwz_trap_use;
    use setmodel( "tag_origin" );
    use makeusable();
    use sethintstring( &"COOP_INTERACTIONS_REQUIRES_POWER" );
    while ( !scripts\engine\utility::flag_exist( "power_on" ) )
        wait 0.5;
    scripts\engine\utility::flag_wait( "power_on" );
    for ( ;; )
    {
        use sethintstring( &"ZOMBIE_CRAFTING_SOUVENIRS_HINT_ELECTRICTRAP" );
        use waittill( "trigger", p );
        if ( !p scripts\cp\cp_persistence::player_has_enough_currency( 750 ) )
        {
            p playlocalsound( "purchase_deny" );
            continue;
        }
        p scripts\cp\cp_persistence::take_player_currency( 750, 1, "trap" );
        use makeunusable();
        print( "[IWZ level] TRAP_ON by=" + p.name );
        iwz_third_rail_run( p, 25 );
        print( "[IWZ level] TRAP_COOLDOWN" );
        wait 60;
        use makeusable();
    }
}

iwz_third_rail_run( owner, seconds )
{
    kills = 0;
    lo = level.iwz_trap_min;
    hi = level.iwz_trap_max;
    end = gettime() + seconds * 1000;
    next_fx = 0;
    while ( gettime() < end )
    {
        if ( gettime() >= next_fx )
        {
            for ( x = lo[0] + 128; x < hi[0]; x += 384 )
            {
                playfx( level._effect["iwz_rail_arc"], ( x, level.iwz_trap_rail_y, level.iwz_trap_rail_z ) );
                playfx( level._effect["iwz_rail_spark"], ( x + 192, level.iwz_trap_rail_y, level.iwz_trap_rail_z - 2 ) );
            }
            next_fx = gettime() + 1200;
        }
        if ( isdefined( level.spawned_enemies ) )
        {
            foreach ( z in level.spawned_enemies )
            {
                if ( isdefined( z ) && isalive( z ) && iwz_in_box( z.origin, lo, hi ) )
                {
                    z dodamage( z.health + 1000, z.origin );      // no attacker: trap kills skip the usermap leaderboard
                    kills++;
                }
            }
        }
        foreach ( pl in level.players )
        {
            if ( isalive( pl ) && iwz_in_box( pl.origin, lo, hi ) )
                pl dodamage( 20, pl.origin );
        }
        wait 0.25;
    }
    print( "[IWZ level] TRAP_DONE kills=" + kills );
}

iwz_in_box( p, lo, hi )
{
    return p[0] >= lo[0] && p[0] <= hi[0] && p[1] >= lo[1] && p[1] <= hi[1] && p[2] >= lo[2] - 8 && p[2] <= hi[2];
}



// Spaceland's interaction registry, minus the init functions of Spaceland systems this map has no structs for
// (cryobomb, forgefreeze, gator teeth, ark quest, scrambler, DJ quest parts...: one-off init runtime errors in every
// run). Kept: every interaction that has a struct here, and the wheel / Pack-a-Punch / power / perk families.
iwz_register_interactions()
{
    scripts\cp\maps\cp_zmb\cp_zmb_interactions::register_interactions();
    used = [];
    foreach ( s in level.all_interaction_structs )
    {
        if ( isdefined( s.script_noteworthy ) )
            used[s.script_noteworthy] = 1;
    }
    keep = [ "wheel", "pap", "upgrade", "perk", "debris", "generator", "power", "laststand", "lost_and_found", "afterlife" ];
    disabled = "";
    names = getarraykeys( level.interactions );
    foreach ( n in names )
    {
        i = level.interactions[n];
        if ( isdefined( used[n] ) || !isdefined( i.init_func ) )
            continue;
        k = 0;
        foreach ( w in keep )
        {
            if ( issubstr( n, w ) )
                k = 1;
        }
        if ( k )
            continue;
        i.init_func = undefined;
        disabled += n + " ";
    }
    print( "[IWZ level] INTERACTIONS registered=" + names.size + " init_disabled=" + disabled );
}




// door dressing (g26): barricades and boarding planks in front of each closed door's blocker brushes; they go when the
// door's blockers are gone (the stock purchase deletes them)
// (g27 review BLOQUANT 2: the white placeholder block behind the barricades) the door blockers are template brush
// sub-models kept for their collision; they also render (a white block in every closed door). Hidden at load: hide()
// keeps the collision, the stock purchase makes them non-solid as before.
iwz_hide_door_blockers()
{
    wait 0.5;
    n = 0;
    foreach ( d in iwz_door_table() )
    {
        foreach ( e in getentarray( d.target, "targetname" ) )
        {
            if ( isdefined( e.classname ) && e.classname == "script_brushmodel" )
            {
                e hide();
                n++;
            }
        }
    }
    print( "[IWZ level] DOOR_BLOCKERS_HIDDEN " + n );
}

iwz_door_dressing()
{
    level endon( "game_ended" );
    wait 2;
    groups = [];
    foreach ( m in getentarray( "script_model", "classname" ) )
    {
        if ( !isdefined( m.targetname ) || getsubstr( m.targetname, 0, 14 ) != "iwz_doordress_" )
            continue;
        groups[m.targetname] = 1;
    }
    foreach ( name, unused in groups )
        level thread iwz_door_dressing_watch( name, getsubstr( name, 14 ) );
}

iwz_door_dressing_watch( name, blockers )
{
    level endon( "game_ended" );
    // (g27, QA g26c) the stock purchase only makes the blocker brushes non-solid, it never deletes them: the door is
    // open when the debris purchase hook (iwz_debris_bought) has flagged its target; blockers gone stays a fallback
    for ( ;; )
    {
        if ( isdefined( level.iwz_door_open ) && isdefined( level.iwz_door_open[blockers] ) )
            break;
        if ( getentarray( blockers, "targetname" ).size == 0 )
            break;
        wait 0.25;
    }
    n = 0;
    foreach ( m in getentarray( name, "targetname" ) )
    {
        m delete();
        n++;
    }
    print( "[IWZ level] DOOR_DRESSING_REMOVED " + blockers + " models=" + n );
}
