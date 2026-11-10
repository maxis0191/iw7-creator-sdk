// IWZ flashlight: every player carries a tight warm spot light, seen by every player (the pool on walls, floors and
// zombies). IW7 has no flashlight builtin: the light is a particle spot light (vfx/iwz/vfx_iwz_flashlight_world, made by
// darkness/make_vfx_light.py from the stock cp_disco train front light: one LIGHT_SPOT emitter, no sprite,
// particle life raised from 1 s to 100000 s with --life: the stock particle is never re-spawned) played
// with playfxontag, which every client receives.
// Carrier (level.iwz_fl_mode):
//   "follow" (default) a tag_origin script model moved to the eye + offset along the view angles every server frame:
//            the cone follows view yaw AND pitch (FX agent probe6 / probe9: lit steam, ceiling drips and floor effects
//            are only lit when the cone points at them), independent of the weapon model (switch, Pack-a-Punch, last
//            stand, revive need no re-attach);
//   "link"   the same model linked to the player's tag_eye: smooth, but tag_eye does not pitch with the view (the pool
//            stays level when looking up / down, runs dk15 / probe6);
//   "tag"    the effect on the weapon's tag_flash (follows weapon sway / ADS).
// Every attach spawns a NEW carrier: the same effect replayed on the same entity / tag soon after a kill stays dark
// (runs dk3 / dk4), a fresh entity never has that state. Off = carrier deleted.
// Life: on at every spawn (late join, return from the afterlife / self-revive spawn), off at death and disconnect.
// After power-on (level.iwz_fl_after_power): "dim" (default) swaps every light to vfx/iwz/vfx_iwz_flashlight_lit (the
// same light at ~30 % brightness) once the station lights are done, "on" keeps it, "off" switches it off.
// Private test dvars: paris_iwz_fl_mode (overrides the mode), paris_iwz_dark_debug 1 (prints).

init()
{
    // six identical copies (only the "tag" mode rotates them: see the kill / replay note above)
    level.iwz_fl_worlds = [];
    foreach ( s in [ "", "_b", "_c", "_d", "_e", "_f" ] )
        level.iwz_fl_worlds[level.iwz_fl_worlds.size] = loadfx( "vfx/iwz/vfx_iwz_flashlight_world" + s );
    level.iwz_fl_world = level.iwz_fl_worlds[0];
    level.iwz_fl_world_lit = loadfx( "vfx/iwz/vfx_iwz_flashlight_lit" );
    // halo: a wide, dim, unshadowed cone on the same carrier (follow / link). The particle spot light ignores its inner
    // cone angle (run dk16: 32/12, 40/2 and 56/0 all end in a hard rim), so the soft edge is built from two cones.
    level.iwz_fl_halo_world = loadfx( "vfx/iwz/vfx_iwz_flashlight_halo" );
    level.iwz_fl_halo_world_lit = loadfx( "vfx/iwz/vfx_iwz_flashlight_halo_lit" );
    if ( !isdefined( level.iwz_fl_halo ) )
        level.iwz_fl_halo = 1;
    if ( getdvar( "paris_iwz_fl_halo" ) != "" )
        level.iwz_fl_halo = getdvarint( "paris_iwz_fl_halo" );
    if ( !isdefined( level.iwz_fl_mode ) )
        level.iwz_fl_mode = "follow";
    if ( getdvar( "paris_iwz_fl_mode" ) != "" )
        level.iwz_fl_mode = getdvar( "paris_iwz_fl_mode" );
    if ( !isdefined( level.iwz_fl_tag ) )
        level.iwz_fl_tag = "tag_flash";
    if ( !isdefined( level.iwz_fl_link_tag ) )
        level.iwz_fl_link_tag = "tag_eye";
    if ( !isdefined( level.iwz_fl_link_offset ) )
        level.iwz_fl_link_offset = ( 24, -4, -6 );  // forward, left, up from the eye: ahead of the viewmodel hands (at
                                                    // forward 6 it lit the hands and the body shadowed it, run dk10)
    if ( !isdefined( level.iwz_fl_after_power ) )
        level.iwz_fl_after_power = "dim";
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
    c = undefined;
    for ( ;; )
    {
        // keep a reference that survives the player entity: the carrier changes at every attach
        ev = self scripts\engine\utility::waittill_any_return( "disconnect", "iwz_fl_carrier_set" );
        if ( ev == "disconnect" )
            break;
        c = carrier_holder.iwz_fl_carrier;
    }
    if ( isdefined( c ) )
    {
        killfxontag( level.iwz_fl_world, c, "tag_origin" );
        foreach ( h in [ level.iwz_fl_halo_world, level.iwz_fl_halo_world_lit ] )
            killfxontag( h, c, "tag_origin" );
        c thread iwz_fl_dispose();
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
        ev = self scripts\engine\utility::waittill_any_return( "weapon_change", "iwz_fl_refresh", "iwz_fl_toggle", "revive", "last_stand", "iwz_fl_swap" );
        if ( ev == "weapon_change" || ev == "last_stand" || ev == "revive" )
        {
            // only the weapon-tag carrier depends on the weapon model: the new model replaces the old one later
            if ( level.iwz_fl_mode != "tag" )
                continue;
            wait 0.8;
        }
        else if ( ev == "iwz_fl_swap" )
        {
            // another effect for a light that is on (the dim lit-state copy after power-on): no click
            if ( !scripts\engine\utility::is_true( self.iwz_fl_on ) )
                continue;
        }
        else
            wait 0.1;
        if ( !isalive( self ) )
            continue;
        self iwz_fl_attach( ev != "iwz_fl_toggle" && ev != "iwz_fl_swap" );
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
        self notify( "iwz_fl_carrier_set" );
        if ( level.iwz_fl_mode == "link" )
            c linkto( self, level.iwz_fl_link_tag, level.iwz_fl_link_offset, ( 0, 0, 0 ) );
        else
            c thread iwz_fl_follow( self );
        wait 0.05;
        if ( !isdefined( c ) )
            return;
        self.iwz_fl_fx = level.iwz_fl_world;
        playfxontag( self.iwz_fl_fx, c, "tag_origin" );
        self.iwz_fl_hfx = undefined;
        if ( level.iwz_fl_halo )
        {
            self.iwz_fl_hfx = level.iwz_fl_halo_world;
            if ( level.iwz_fl_world == level.iwz_fl_world_lit )
                self.iwz_fl_hfx = level.iwz_fl_halo_world_lit;
            playfxontag( self.iwz_fl_hfx, c, "tag_origin" );
        }
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
        // the light particle lives 100000 s: kill it, then take the carrier under the map before deleting it, so a
        // particle the kill missed (entity deleted in the same frame, run dk13) is left where nobody sees it
        c = self.iwz_fl_carrier;
        self.iwz_fl_carrier = undefined;
        killfxontag( self.iwz_fl_fx, c, "tag_origin" );
        if ( isdefined( self.iwz_fl_hfx ) )
            killfxontag( self.iwz_fl_hfx, c, "tag_origin" );
        c thread iwz_fl_dispose();
    }
    self.iwz_fl_on = 0;
    iwz_fl_log( "OFF " + self.name );
}

iwz_fl_dispose()
{
    self endon( "death" );
    wait 0.25;
    self unlink();
    self.origin = self.origin + ( 0, 0, -20000 );
    wait 0.25;
    self delete();
}

// after the station lights are on: dim the flashlights (default; link / follow carriers), keep them, or switch them off
iwz_fl_power()
{
    level endon( "game_ended" );
    if ( level.iwz_fl_after_power == "on" )
        return;
    while ( !scripts\engine\utility::flag_exist( "iwz_power_lights_done" ) )
        wait 0.5;
    scripts\engine\utility::flag_wait( "iwz_power_lights_done" );
    if ( level.iwz_fl_after_power == "dim" )
    {
        // later spawns (late join, afterlife return) attach the dim copy too
        level.iwz_fl_world = level.iwz_fl_world_lit;
        foreach ( p in level.players )
        {
            if ( isdefined( p ) )
                p notify( "iwz_fl_swap" );
        }
        iwz_fl_log( "DIM after power" );
        return;
    }
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
