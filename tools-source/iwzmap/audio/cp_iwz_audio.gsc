// Station Zero (cp_iwz) audio: hidden-song easter egg and ambience. Shipped in the map zone as the rawfile
// scripts/cp/maps/cp_iwz/cp_iwz_audio.gsc; the level script cp_iwz.gsc calls it from main():
//
//   level thread scripts\cp\maps\cp_iwz\cp_iwz_audio::song_ee_init( ( x, y, z ), ( 0, yaw, 0 ) );
//   level thread scripts\cp\maps\cp_iwz\cp_iwz_audio::ambience_init( emitters, "amb_cp_zmb_basement_lr", zones );
//
// (audio_layout.py writes both calls, with every position, from the level generator's layout.json.)
// song_ee_init origin = the point the bear rests on (seat, rack, floor): p7_zm_teddybear's model origin is
// its centre (lod0 bounds z -14.2..13.9), so the model is raised by opts.model_offset (default 14.2).
//
// Aliases (map sound bank cp_iwz.all, built by x64-zt-extensions iw7-audio/iwz_audio_bank.py from
// iw7-creator-sdk tools-source/iwzmap/audio/station_zero_audio.json):
//   mus_iwz_abracadavre   the song, streamed, 2D music (stock wave-music row)
//   zmb_iwz_ee_hint_lp    BO1/BO3 hidden-song hint loop, 3D, 100-550 units
//   zmb_iwz_ee_activate   BO1/BO3 hidden-song activation sound, 3D
//
// Easter egg, as in BO1/BO2/BO3 (and the Chronicles maps' song structs): the bear hums the hint loop; a
// player presses Use on it (the bear is a usable entity with no prompt: HINT_NOICON and an empty hint
// string, as the BO3 song objects' trigger_use; the engine notifies "trigger" for the player's real Use
// press), the activation sound plays, the bear vanishes, and the song plays once for every player.
// Holding Use (usebuttonpressed polled for use_hold seconds) is a second route. Like Spaceland's own teddy bears (cp_zmb.gsc waitfordamage) a
// melee hit or a shot also counts when the model takes damage. The song follows Spaceland's
// play_hidden_song: the stock "add_hidden_song_to_playlist" notify stops any stock jukebox, 2.5 s later
// the song starts, "skip_song" ends it early; it plays per client with playlocalsound like the stock
// character-intro music, so the wave music (playsoundatpos on music_lr) keeps working beside it.
//
// Every step prints "[IWZ audio] <EVENT> ... t=<gettime>" so tests can align a capture with the script.

song_ee_init( origin, angles, opts )
{
    level endon( "game_ended" );

    if ( isdefined( level.iwz_song_ee ) )
        return;

    if ( !isdefined( opts ) )
        opts = spawnstruct();

    ee = spawnstruct();
    ee.origin = origin;                                        // resting point (base of the bear)
    ee.angles = ( 0, 0, 0 );
    if ( isdefined( angles ) )
        ee.angles = angles;
    ee.model_name = iwz_opt( opts.model, "p7_zm_teddybear" );
    ee.model_offset = iwz_opt( opts.model_offset, ( 0, 0, 14.2 ) );   // model origin above the resting point
    ee.target = ee.origin + ee.model_offset;                   // centre of the bear: hum, look, use, sound
    ee.song = iwz_opt( opts.song, "mus_iwz_abracadavre" );
    ee.hint_alias = iwz_opt( opts.hint_alias, "zmb_iwz_ee_hint_lp" );
    ee.activate_alias = iwz_opt( opts.activate_alias, "zmb_iwz_ee_activate" );
    ee.use_radius = iwz_opt( opts.use_radius, 96 );            // 2D reach: from a car aisle to the rack above the seat
    ee.use_hold = iwz_opt( opts.use_hold, 0.5 );          // seconds of Use held while looking at the bear
    ee.look_dot = iwz_opt( opts.look_dot, 0.85 );         // cosine of the look cone (about 32 degrees)
    ee.allow_damage = iwz_opt( opts.allow_damage, 1 );    // melee / shots, Spaceland style
    ee.song_delay = iwz_opt( opts.song_delay, 2.5 );      // Spaceland play_hidden_song delay
    ee.xp = iwz_opt( opts.xp, 0 );
    ee.done = 0;
    level.iwz_song_ee = ee;

    ee.model = spawn( "script_model", ee.target );
    ee.model.angles = ee.angles;
    ee.model setmodel( ee.model_name );

    // the hint loop lives on its own origin: hiding or deleting the model never cuts it short
    ee.hum = spawn( "script_origin", ee.target );
    ee.hum playloopsound( ee.hint_alias );
    print( "[IWZ audio] EE_ARMED origin=" + ee.origin + " target=" + ee.target + " model=" + ee.model_name + " hint=" + ee.hint_alias + " t=" + gettime() );

    if ( ee.allow_damage )
        ee.model thread iwz_ee_watch_damage( ee );

    ee.model thread iwz_ee_watch_trigger( ee );
    level thread iwz_ee_watch_use( ee );

    level waittill( "iwz_song_ee_activated", player, method );
    iwz_ee_activate( ee, player, method );
}

iwz_opt( value, fallback )
{
    if ( isdefined( value ) )
        return value;

    return fallback;
}

// BO-style interaction through the engine's Use: the bear model is usable without any prompt; a player's Use
// press while the engine picks the bear as the looked-at usable entity notifies "trigger". The module's own
// reach / look cone / line of sight check is applied on top (the engine's use radius is wider).
iwz_ee_watch_trigger( ee )
{
    level endon( "game_ended" );
    level endon( "iwz_song_ee_activated" );
    self makeusable();
    self setcursorhint( "HINT_NOICON" );
    self sethintstring( "" );
    ee.use_trigger = self;
    print( "[IWZ audio] EE_USABLE ent=" + self getentitynumber() + " t=" + gettime() );

    for (;;)
    {
        self waittill( "trigger", player );

        if ( !isdefined( player ) || !isplayer( player ) || !isalive( player ) )
            continue;

        if ( !iwz_ee_in_reach( ee, player ) )
        {
            print( "[IWZ audio] EE_TRIGGER_REFUSED by=" + player.name + " t=" + gettime() );
            continue;
        }

        level notify( "iwz_song_ee_activated", player, "use_trigger" );
        return;
    }
}

// second route: hold Use within reach while looking at the bear (button polled every 0.05 s)
iwz_ee_watch_use( ee )
{
    level endon( "game_ended" );
    level endon( "iwz_song_ee_activated" );

    for (;;)
    {
        if ( !isdefined( level.players ) )
        {
            wait 0.05;
            continue;
        }

        foreach ( player in level.players )
        {
            if ( !isdefined( player ) || !isalive( player ) )
                continue;

            if ( !iwz_ee_can_use( ee, player ) )
            {
                player.iwz_ee_hold = 0;
                continue;
            }

            if ( !isdefined( player.iwz_ee_hold ) )
                player.iwz_ee_hold = 0;

            player.iwz_ee_hold += 0.05;

            if ( player.iwz_ee_hold >= ee.use_hold )
            {
                method = "use";
                if ( !player usebuttonpressed() )
                    method = "use_scripted";
                level notify( "iwz_song_ee_activated", player, method );
                return;
            }
        }

        wait 0.05;
    }
}

iwz_ee_can_use( ee, player )
{
    // iwz_ee_use_override: a script (test fixture, scripted sequence) holds Use for the player; every other
    // condition below (reach, look cone, line of sight, hold time) still applies
    if ( !player usebuttonpressed() && !scripts\engine\utility::is_true( player.iwz_ee_use_override ) )
        return 0;

    return iwz_ee_in_reach( ee, player );
}

// within reach of the bear, looking at it (about 32 degrees), nothing in between
iwz_ee_in_reach( ee, player )
{
    target = ee.target;
    eye = player geteye();

    if ( distance( eye, target ) > ee.use_radius + 48 || distance2d( player.origin, ee.origin ) > ee.use_radius )
        return 0;

    look = anglestoforward( player getplayerangles() );
    if ( vectordot( look, vectornormalize( target - eye ) ) < ee.look_dot )
        return 0;

    trace = bullettrace( eye, target, 0, player );
    if ( trace["fraction"] < 0.98 && distance( trace["position"], target ) > 24 )
        return 0;

    return 1;
}

iwz_ee_watch_damage( ee )
{
    level endon( "game_ended" );
    level endon( "iwz_song_ee_activated" );
    self setcandamage( 1 );
    self.maxhealth = 100000;
    self.health = self.maxhealth;

    for (;;)
    {
        self waittill( "damage", amount, attacker, direction, point, type );

        if ( isdefined( attacker ) && isplayer( attacker ) )
        {
            level notify( "iwz_song_ee_activated", attacker, "damage_" + tolower( iwz_opt( type, "unknown" ) ) );
            return;
        }

        self.health = self.maxhealth;
    }
}

iwz_ee_activate( ee, player, method )
{
    if ( ee.done )
        return;

    ee.done = 1;
    name = "unknown";
    if ( isdefined( player ) && isdefined( player.name ) )
        name = player.name;

    print( "[IWZ audio] EE_ACTIVATED by=" + name + " method=" + method + " t=" + gettime() );
    ee.hum stoploopsound();
    playsoundatpos( ee.target, ee.activate_alias );

    if ( isdefined( ee.model ) )
    {
        ee.model setcandamage( 0 );
        ee.model makeunusable();
        ee.model hide();
    }

    level thread iwz_play_hidden_song( ee );
    wait 2;
    ee.hum delete();

    if ( isdefined( ee.model ) )
        ee.model delete();
}

// cp_zmb.gsc play_hidden_song, for a 2D streamed song played to every client
iwz_play_hidden_song( ee )
{
    level endon( "game_ended" );
    level notify( "add_hidden_song_to_playlist" );
    wait( ee.song_delay );

    if ( !soundexists( ee.song ) )
    {
        print( "[IWZ audio] SONG_MISSING alias=" + ee.song + " t=" + gettime() );
        return;
    }

    length = lookupsoundlength( ee.song );
    level.iwz_song_playing = 1;
    listeners = [];

    foreach ( player in level.players )
    {
        if ( !isdefined( player ) )
            continue;

        player playlocalsound( ee.song );
        listeners[listeners.size] = player;

        if ( ee.xp > 0 )
            player scripts\cp\cp_persistence::give_player_xp( ee.xp, 1 );
    }

    print( "[IWZ audio] SONG_START alias=" + ee.song + " length_ms=" + length + " players=" + listeners.size + " t=" + gettime() );
    level notify( "iwz_song_started" );
    reason = level scripts\engine\utility::waittill_any_timeout( length / 1000, "skip_song", "game_ended" );

    if ( isdefined( reason ) && reason != "timeout" )
    {
        foreach ( player in listeners )
        {
            if ( isdefined( player ) )
                player stoplocalsound( ee.song );
        }
    }
    else
        reason = "end";

    level.iwz_song_playing = 0;
    print( "[IWZ audio] SONG_END reason=" + reason + " t=" + gettime() );
}

// Ambience: looping 3D emitters, random one-shot emitters and a 2D room tone bed per client.
// emitters: array of structs { alias, origin, random (0/1), min_wait, max_wait } (ambience_emitter)
// bed: default 2D bed alias; zones: optional array of ambience_zone structs, the first zone holding the
// player selects its bed (checked twice a second, "[IWZ audio] BED ..." on every change).
ambience_init( emitters, bed, zones )
{
    level endon( "game_ended" );
    level.iwz_ambience = [];

    if ( isdefined( emitters ) )
    {
        foreach ( e in emitters )
        {
            if ( !soundexists( e.alias ) )
            {
                print( "[IWZ audio] AMB_MISSING alias=" + e.alias );
                continue;
            }

            if ( scripts\engine\utility::is_true( e.random ) )
            {
                level thread iwz_ambience_random( e );
                continue;
            }

            ent = spawn( "script_origin", e.origin );
            ent playloopsound( e.alias );
            level.iwz_ambience[level.iwz_ambience.size] = ent;
        }
    }

    print( "[IWZ audio] AMB_START emitters=" + level.iwz_ambience.size + " t=" + gettime() );

    level.iwz_ambience_zones = [];
    if ( isdefined( zones ) )
    {
        foreach ( z in zones )
        {
            if ( isdefined( z.bed ) && !soundexists( z.bed ) )
            {
                print( "[IWZ audio] AMB_MISSING alias=" + z.bed + " zone=" + z.name );
                z.bed = undefined;
            }
            level.iwz_ambience_zones[level.iwz_ambience_zones.size] = z;
        }
    }

    if ( isdefined( bed ) && !soundexists( bed ) )
        bed = undefined;

    if ( isdefined( bed ) || level.iwz_ambience_zones.size )
    {
        level.iwz_ambience_bed = bed;
        level.iwz_ambience_beds_on = 1;
        level thread iwz_ambience_bed_watch();
    }

    level waittill( "iwz_ambience_stop" );

    foreach ( ent in level.iwz_ambience )
    {
        if ( isdefined( ent ) )
        {
            ent stoploopsound();
            ent delete();
        }
    }

    level.iwz_ambience = [];
    print( "[IWZ audio] AMB_STOP t=" + gettime() );
}

ambience_stop()
{
    level notify( "iwz_ambience_stop" );
    level.iwz_ambience_beds_on = 0;
    players = [];
    if ( isdefined( level.players ) )
        players = level.players;

    foreach ( player in players )
    {
        if ( isdefined( player ) && isdefined( player.iwz_bed ) )
        {
            player iwz_bed_stop();
            player.iwz_bed = undefined;
        }
    }

    level.iwz_ambience_bed = undefined;
}

// own thread: an engine refusal of the zone or of a part name ends this thread only, not the area watch
iwz_set_audio_zone( audio_zone )
{
    // the engine's own zone bed ("ambient" part) stays silent in a usermap (runs f1/f3): the zone's bed is
    // played by iwz_ambience_bed_player; only reverb, mix and filter come from the sound zone
    self setclienttriggeraudiozonepartialwithfade( audio_zone, 1.0, "reverb", "mix", "filter" );
    print( "[IWZ audio] AZONE_SET player=" + self.name + " audio_zone=" + audio_zone + " t=" + gettime() );
}

// a zone of the ambience: axis-aligned box mins..maxs, 2D bed alias (undefined: the default bed)
ambience_zone( name, mins, maxs, bed )
{
    z = spawnstruct();
    z.name = name;
    z.mins = mins;
    z.maxs = maxs;
    z.bed = bed;
    return z;
}

// an area mapped to a sound zone of the bank (reverb, mix, filter): the player is switched to it with
// setclienttriggeraudiozonepartialwithfade when entering the area; bed: the 2D bed alias the module plays there
// (audio_layout.py passes the sound zone's ambience alias)
ambience_audio_zone( name, mins, maxs, audio_zone, bed )
{
    z = spawnstruct();
    z.name = name;
    z.mins = mins;
    z.maxs = maxs;
    z.audio_zone = audio_zone;
    z.bed = bed;
    return z;
}

ambience_zone_at( origin )
{
    if ( !isdefined( level.iwz_ambience_zones ) )
        return undefined;

    foreach ( z in level.iwz_ambience_zones )
    {
        if ( origin[0] >= z.mins[0] && origin[0] <= z.maxs[0] && origin[1] >= z.mins[1] && origin[1] <= z.maxs[1] && origin[2] >= z.mins[2] && origin[2] <= z.maxs[2] )
            return z;
    }

    return undefined;
}

ambience_emitter( alias, origin, random, min_wait, max_wait )
{
    e = spawnstruct();
    e.alias = alias;
    e.origin = origin;
    e.random = iwz_opt( random, 0 );
    e.min_wait = iwz_opt( min_wait, 6 );
    e.max_wait = iwz_opt( max_wait, 18 );
    return e;
}

iwz_ambience_random( e )
{
    level endon( "game_ended" );
    level endon( "iwz_ambience_stop" );

    for (;;)
    {
        wait( randomfloatrange( e.min_wait, e.max_wait ) );
        playsoundatpos( e.origin, e.alias );
    }
}

iwz_ambience_bed_watch()
{
    level endon( "game_ended" );
    level endon( "iwz_ambience_stop" );

    // the level script calls this from main(), before level.players exists: players present then are
    // picked up here, later ones by the "connected" notify
    while ( !isdefined( level.players ) )
        wait 0.05;

    foreach ( player in level.players )
        player thread iwz_ambience_bed_player();

    for (;;)
    {
        level waittill( "connected", player );
        player thread iwz_ambience_bed_player();
    }
}

// one bed per player: the bed of the zone the player stands in (else the default bed), restarted after a
// respawn, switched when the player crosses into a zone with another bed
// A per-player 2D bed: the bank ships it as a NONLOOPING clip (seamless loop + its first bed_overlap seconds,
// faded in over the head and out over the tail: iwz_audio_bank.py "retrigger_overlap"), started again every
// (length - bed_overlap) seconds so consecutive copies cross-fade back into the loop. playlocalsound refuses a
// looping alias (script runtime error, silence) and the engine's sound-zone bed stays silent in a usermap.
// A second playlocalsound of an alias still playing restarts it (run f7: the tail was cut, a 1 s dip), so the
// copies alternate between <alias> and its twin <alias>_b (the bank tool writes the twin row).
iwz_bed_loop( alias )
{
    self endon( "disconnect" );
    self endon( "iwz_bed_stop" );
    level endon( "game_ended" );
    level endon( "iwz_ambience_stop" );
    overlap = iwz_opt( level.iwz_bed_overlap, 2.0 );
    period = lookupsoundlength( alias ) / 1000.0 - overlap;
    if ( period < 1.0 )
        period = 1.0;

    twin = alias + "_b";
    if ( !soundexists( twin ) )
        twin = alias;

    current = alias;
    for (;;)
    {
        self playlocalsound( current );
        wait( period );
        if ( current == alias )
            current = twin;
        else
            current = alias;
    }
}

iwz_bed_stop()
{
    self notify( "iwz_bed_stop" );
    if ( isdefined( self.iwz_bed ) )
    {
        self stoplocalsound( self.iwz_bed );
        if ( soundexists( self.iwz_bed + "_b" ) )
            self stoplocalsound( self.iwz_bed + "_b" );
    }
}

iwz_ambience_bed_player()
{
    self endon( "disconnect" );
    level endon( "iwz_ambience_stop" );
    self.iwz_bed = undefined;
    zone_name = "";

    for (;;)
    {
        if ( !isalive( self ) )
        {
            if ( isdefined( self.iwz_bed ) )
                self iwz_bed_stop();

            self.iwz_bed = undefined;
            zone_name = "";
            wait 0.25;
            continue;
        }

        want = level.iwz_ambience_bed;
        name = "none";
        z = ambience_zone_at( self.origin );
        if ( isdefined( z ) )
        {
            name = z.name;
            if ( isdefined( z.bed ) )
                want = z.bed;

            if ( isdefined( z.audio_zone ) && ( !isdefined( self.iwz_audio_zone ) || self.iwz_audio_zone != z.audio_zone ) )
            {
                self.iwz_audio_zone = z.audio_zone;
                print( "[IWZ audio] AZONE player=" + self.name + " zone=" + name + " audio_zone=" + z.audio_zone + " t=" + gettime() );
                self thread iwz_set_audio_zone( z.audio_zone );
            }
        }

        same = isdefined( want ) && isdefined( self.iwz_bed ) && want == self.iwz_bed;
        if ( !same && ( isdefined( want ) || isdefined( self.iwz_bed ) ) )
        {
            if ( isdefined( self.iwz_bed ) )
                self iwz_bed_stop();

            self.iwz_bed = want;
            if ( isdefined( want ) )
                self thread iwz_bed_loop( want );

            shown = "none";
            if ( isdefined( want ) )
                shown = want;
            print( "[IWZ audio] BED player=" + self.name + " zone=" + name + " bed=" + shown + " t=" + gettime() );
        }
        else if ( name != zone_name )
            print( "[IWZ audio] ZONE player=" + self.name + " zone=" + name + " t=" + gettime() );

        zone_name = name;
        wait 0.5;
    }
}
