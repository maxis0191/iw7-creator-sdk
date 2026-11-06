// Station Zero level script: reuses the stock Spaceland zombies systems shipped in the zone.
main()
{
    level.iwz_custom_map = 1;
    scripts\mp\mp_agent::init_agent( "mp/default_agent_definition.csv" );
    scripts\mp\agents\zombie\zombie_agent::registerscriptedagent();
    level.coop_weapontable = "cp/cp_weapontable.csv";
    level.disable_zombie_exo_abilities = 1;
    scripts\cp\maps\cp_zmb\cp_zmb_player_character_setup::init_player_characters();
    level thread iwz_report();
}

iwz_report()
{
    wait 1;
    print( "[IWZ level] characters=" + level.player_character_info.size + " available=" + level.available_player_characters.size );
    for ( ;; )
    {
        p = level.players[0];
        state = "intro_over=" + scripts\engine\utility::flag( "introscreen_over" ) + " intro_done=" + isdefined( level.introscreen_done );
        if ( isdefined( p ) )
            state += " photosetup=" + isdefined( p.photosetup ) + " alive=" + isalive( p ) + " weapon=" + p getcurrentweapon() + " session=" + p.sessionstate + " origin=" + p.origin + " overlay=" + isdefined( p.introscreen_overlay );
        print( "[IWZ level] " + state );
        wait 2;
    }
}
