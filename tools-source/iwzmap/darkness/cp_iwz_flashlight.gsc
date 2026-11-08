// IWZ flashlight: every player carries a tight warm spot light, seen by every player (the pool on walls, floors and
// zombies). IW7 has no flashlight builtin: the light is a particle spot light (vfx/iwz/vfx_iwz_flashlight_world, made by
// darkness/make_vfx_light.py from the stock cp_disco train front light: one LIGHT_SPOT emitter, no sprite) played
// with playfxontag, which every client receives.
// Carrier (level.iwz_fl_mode):
//   "link"   (default) a tag_origin script model linked to the player's tag_eye: the light follows the view (head aim)
//            on every client and survives weapon switches, Pack-a-Punch, last stand and revive without re-attaching;
//   "follow" the same model moved to the eye / view angles every server frame (fallback if a link misbehaves);
//   "tag"    the effect on the weapon's tag_flash (follows weapon sway / ADS; runs dk6-dk9: lost after a weapon switch).
// Every attach spawns a NEW carrier: the same effect replayed on the same entity / tag soon after a kill stays dark
// (runs dk3 / dk4), a fresh entity never has that state. Off = carrier deleted.
// Life: on at every spawn (late join, return from the afterlife / self-revive spawn), off at death and disconnect.
// After power-on: kept (level.iwz_fl_after_power = "on", default) or switched off once the lights are done ("off").
// Private test dvars: paris_iwz_fl_mode (overrides the mode), paris_iwz_dark_debug 1 (prints).

init()
{
    // six identical copies (only the "tag" mode rotates them: see the kill / replay note above)
    level.iwz_fl_worlds = [];
    foreach ( s in [ "", "_b", "_c", "_d", "_e", "_f" ] )
        level.iwz_fl_worlds[level.iwz_fl_worlds.size] = loadfx( "vfx/iwz/vfx_iwz_flashlight_world" + s );
    level.iwz_fl_world = level.iwz_fl_worlds[0];
    if ( !isdefined( level.iwz_fl_mode ) )
        level.iwz_fl_mode = "link";
    if ( getdvar( "paris_iwz_fl_mode" ) != "" )
        level.iwz_fl_mode = getdvar( "paris_iwz_fl_mode" );
    if ( !isdefined( level.iwz_fl_tag ) )
        level.iwz_fl_tag = "tag_flash";
    if ( !isdefined( level.iwz_fl_link_tag ) )
        level.iwz_fl_link_tag = "tag_eye";
    if ( !isdefined( level.iwz_fl_link_offset ) )
        level.iwz_fl_link_offset = ( 6, -4, -6 );   // forward, left, up from the eye: the light sits low and right
    if ( !isdefined( level.iwz_fl_after_power ) )
        level.iwz_fl_after_power = "on";
    level.iwz_fl_click = "amb_iwz_flashlight_click";
    iwz_fl_log( "LOAD world=" + level.iwz_fl_world + " mode=" + level.iwz_fl_mode );
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
    }
}

iwz_fl_player()
{
    self endon( "disconnect" );
    self thread iwz_fl_disconnect_watch();
    for ( ;; )
    {
        self waittill( "spawned_player" );
        self thread iwz_fl_life();
    }
}

iwz_fl_disconnect_watch()
{
    carrier_holder = self;
    self waittill( "disconnect" );
    if ( isdefined( carrier_holder.iwz_fl_carrier ) )
        carrier_holder.iwz_fl_carrier delete();
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
        if ( ev == "weapon_change" || ev == "last_stand" || ev == "revive" )
        {
            // only the weapon-tag carrier depends on the weapon model: the new model replaces the old one later
            if ( level.iwz_fl_mode != "tag" )
                continue;
            wait 0.8;
        }
        else
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

iwz_fl_attach( click )
{
    if ( scripts\engine\utility::is_true( self.iwz_fl_on ) )
    {
        self iwz_fl_detach();
        wait 0.1;
    }
    if ( !scripts\engine\utility::is_true( self.iwz_fl_enabled ) || !isalive( self ) )
        return;
    if ( level.iwz_fl_mode == "tag" )
        self iwz_fl_attach_tag();
    else
    {
        c = spawn( "script_model", self geteye() );
        c setmodel( "tag_origin" );
        c.angles = self getplayerangles();
        self.iwz_fl_carrier = c;
        if ( level.iwz_fl_mode == "link" )
            c linkto( self, level.iwz_fl_link_tag, level.iwz_fl_link_offset, ( 0, 0, 0 ) );
        else
            c thread iwz_fl_follow( self );
        wait 0.05;
        if ( !isdefined( c ) )
            return;
        self.iwz_fl_fx = level.iwz_fl_world;
        playfxontag( self.iwz_fl_fx, c, "tag_origin" );
    }
    self.iwz_fl_on = 1;
    if ( click && isdefined( level.iwz_fl_click ) && soundexists( level.iwz_fl_click ) )
        playsoundatpos( self geteye(), level.iwz_fl_click );
    iwz_fl_log( "ON " + self.name + " mode=" + level.iwz_fl_mode + " weapon=" + self getcurrentweapon() );
}

// the carrier at the eye, turned with the view, every server frame (fallback mode "follow")
iwz_fl_follow( p )
{
    self endon( "death" );
    p endon( "disconnect" );
    for ( ;; )
    {
        a = p getplayerangles();
        self.origin = p geteye() + anglestoforward( a ) * level.iwz_fl_link_offset[0] + anglestoright( a ) * ( 0 - level.iwz_fl_link_offset[1] ) +
            anglestoup( a ) * level.iwz_fl_link_offset[2];
        self.angles = a;
        wait 0.05;
    }
}

// weapon tag mode: the effect on the weapon's tag_flash, rotating copies by oldest kill (fallback tag_eye with no weapon)
iwz_fl_attach_tag()
{
    tag = level.iwz_fl_tag;
    if ( !isdefined( self.iwz_fl_killed ) )
        self.iwz_fl_killed = [];
    best = 0;
    for ( k = 0; k < level.iwz_fl_worlds.size; k++ )
    {
        if ( !isdefined( self.iwz_fl_killed[k] ) )
        {
            best = k;
            break;
        }
        if ( self.iwz_fl_killed[k] < self.iwz_fl_killed[best] )
            best = k;
    }
    self.iwz_fl_k = best;
    self.iwz_fl_fx = level.iwz_fl_worlds[best];
    w = self getcurrentweapon();
    if ( !isdefined( w ) || w == "none" )
        tag = "tag_eye";
    self.iwz_fl_tag_used = tag;
    playfxontag( self.iwz_fl_fx, self, tag );
}

iwz_fl_detach()
{
    if ( !scripts\engine\utility::is_true( self.iwz_fl_on ) )
        return;
    if ( level.iwz_fl_mode == "tag" )
    {
        killfxontag( self.iwz_fl_fx, self, self.iwz_fl_tag_used );
        if ( isdefined( self.iwz_fl_k ) )
            self.iwz_fl_killed[self.iwz_fl_k] = gettime();
    }
    else if ( isdefined( self.iwz_fl_carrier ) )
    {
        // stop the emission first (a deleted bolt entity can leave its last particle for up to its 1 s life)
        killfxontag( self.iwz_fl_fx, self.iwz_fl_carrier, "tag_origin" );
        self.iwz_fl_carrier delete();
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
