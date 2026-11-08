// IWZ weapon flashlight: every player carries a tight warm spot light on the weapon, seen by every player
// (the beam pool on walls, floors and zombies). IW7 has no flashlight builtin: the light is a particle spot light
// (vfx/iwz/vfx_iwz_flashlight_world, made by darkness/make_vfx_light.py from a stock cp_disco spot light) bolted to
// the player's weapon tag with playfxontag, so it follows the weapon (aim, sway, ADS) on every client.
// Optional split (level.iwz_fl_split = 1): the owner sees a camera-space copy (vfx_iwz_flashlight_view) and the other
// players the weapon copy, through playfxontagforclients (one call per viewer, refreshed when someone connects).
// Life: on at spawn, re-attached after every weapon change (the weapon model and its tag are replaced), after last
// stand / revive / Pack-a-Punch / late join (spawned_player), off at death. After power-on (flag "power_on"): kept
// (level.iwz_fl_after_power = "on", default) or switched off with a click once the station lights are done ("off").
// Debug dvar (prints only): paris_iwz_dark_debug 1.

init()
{
    level.iwz_fl_world = loadfx( "vfx/iwz/vfx_iwz_flashlight_world" );
    level.iwz_fl_view = loadfx( "vfx/iwz/vfx_iwz_flashlight_view" );
    if ( !isdefined( level.iwz_fl_tag ) )
        level.iwz_fl_tag = "tag_flash";
    if ( !isdefined( level.iwz_fl_view_tag ) )
        level.iwz_fl_view_tag = "tag_eye";
    if ( !isdefined( level.iwz_fl_split ) )
        level.iwz_fl_split = 0;
    if ( !isdefined( level.iwz_fl_after_power ) )
        level.iwz_fl_after_power = "on";
    level.iwz_fl_click = "amb_iwz_flashlight_click";
    level thread iwz_fl_connect();
    level thread iwz_fl_power();
}

iwz_fl_log( s )
{
    if ( getdvarint( "paris_iwz_dark_debug" ) )
        print( "[IWZ flashlight] " + s + " t=" + gettime() );
}

iwz_fl_connect()
{
    for ( ;; )
    {
        level waittill( "connected", p );
        p.iwz_fl_enabled = 1;
        if ( level.iwz_fl_after_power == "off" && scripts\engine\utility::flag_exist( "iwz_power_lights_done" ) && scripts\engine\utility::flag( "iwz_power_lights_done" ) )
            p.iwz_fl_enabled = 0;
        p thread iwz_fl_player();
        // split mode: every lit player re-sends its weapon light so the new viewer gets a copy
        if ( level.iwz_fl_split )
        {
            foreach ( q in level.players )
            {
                if ( isdefined( q ) && q != p )
                    q notify( "iwz_fl_refresh" );
            }
        }
    }
}

iwz_fl_player()
{
    self endon( "disconnect" );
    for ( ;; )
    {
        self waittill( "spawned_player" );
        self thread iwz_fl_life();
    }
}

iwz_fl_life()
{
    self endon( "disconnect" );
    self notify( "iwz_fl_life" );
    self endon( "iwz_fl_life" );
    self thread iwz_fl_death_watch();
    wait 0.3;
    self iwz_fl_attach( 1 );
    for ( ;; )
    {
        ev = self scripts\engine\utility::waittill_any_return( "weapon_change", "iwz_fl_refresh", "iwz_fl_toggle", "revive", "last_stand" );
        // the new weapon model is attached a frame after the notify
        wait 0.1;
        if ( !isalive( self ) )
            continue;
        self iwz_fl_attach( ev != "iwz_fl_toggle" );
    }
}

iwz_fl_death_watch()
{
    self endon( "disconnect" );
    self endon( "iwz_fl_life" );
    self waittill( "death" );
    self iwz_fl_detach();
}

// (re)attach: kill this player's copies first so a refresh never doubles the light
iwz_fl_attach( click )
{
    self iwz_fl_detach();
    if ( !scripts\engine\utility::is_true( self.iwz_fl_enabled ) )
        return;
    tag = level.iwz_fl_tag;
    w = self getcurrentweapon();
    if ( !isdefined( w ) || w == "none" )
        tag = "tag_eye";        // no weapon (fists / perk drinking / afterlife hands): light from the eye
    self.iwz_fl_tag_used = tag;
    if ( !level.iwz_fl_split )
        playfxontag( level.iwz_fl_world, self, tag );
    else
    {
        playfxontagforclients( level.iwz_fl_view, self, level.iwz_fl_view_tag, self );
        foreach ( q in level.players )
        {
            if ( isdefined( q ) && q != self )
                playfxontagforclients( level.iwz_fl_world, self, tag, q );
        }
    }
    self.iwz_fl_on = 1;
    if ( click && isdefined( level.iwz_fl_click ) && soundexists( level.iwz_fl_click ) )
        playsoundatpos( self geteye(), level.iwz_fl_click );
    iwz_fl_log( "ON " + self.name + " tag=" + tag + " weapon=" + w );
}

iwz_fl_detach()
{
    if ( !scripts\engine\utility::is_true( self.iwz_fl_on ) )
        return;
    tag = self.iwz_fl_tag_used;
    if ( !level.iwz_fl_split )
        killfxontag( level.iwz_fl_world, self, tag );
    else
    {
        killfxontag( level.iwz_fl_view, self, level.iwz_fl_view_tag );
        killfxontag( level.iwz_fl_world, self, tag );
    }
    self.iwz_fl_on = 0;
    iwz_fl_log( "OFF " + self.name );
}

// after the station lights are on: keep the flashlights (default) or switch them off once
iwz_fl_power()
{
    level endon( "game_ended" );
    if ( level.iwz_fl_after_power != "off" )
        return;
    while ( !scripts\engine\utility::flag_exist( "iwz_power_lights_done" ) )
        wait 0.5;
    scripts\engine\utility::flag_wait( "iwz_power_lights_done" );
    foreach ( p in level.players )
    {
        if ( !isdefined( p ) )
            continue;
        p.iwz_fl_enabled = 0;
        if ( isalive( p ) )
        {
            p iwz_fl_detach();
            if ( isdefined( level.iwz_fl_click ) && soundexists( level.iwz_fl_click ) )
                playsoundatpos( p geteye(), level.iwz_fl_click );
        }
    }
}
