// Station Zero (cp_iwz) audio: hidden-song easter egg and ambience. Shipped in the map zone as the rawfile
// scripts/cp/maps/cp_iwz/cp_iwz_audio.gsc; the level script cp_iwz.gsc calls it from main():
//
//   level thread scripts\cp\maps\cp_iwz\cp_iwz_audio::song_ee_init( ( x, y, z ), ( 0, yaw, 0 ) );
//   level thread scripts\cp\maps\cp_iwz\cp_iwz_audio::ambience_init( emitters, "amb_cp_zmb_basement_lr" );
//
// Aliases (map sound bank cp_iwz.all, built by x64-zt-extensions iw7-audio/iwz_audio_bank.py from
// iw7-creator-sdk tools-source/iwzmap/audio/station_zero_audio.json):
//   mus_iwz_abracadavre   the song, streamed, 2D music (stock wave-music row)
//   zmb_iwz_ee_hint_lp    BO1/BO3 hidden-song hint loop, 3D, 100-550 units
//   zmb_iwz_ee_activate   BO1/BO3 hidden-song activation sound, 3D
//
// Easter egg, as in BO1/BO2/BO3 (and the Chronicles maps' song structs): the bear hums the hint loop; a
// player holds Use on it (no hint string: it stays hidden), the activation sound plays, the bear vanishes,
// and the song plays once for every player. Like Spaceland's own teddy bears (cp_zmb.gsc waitfordamage) a
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
    ee.origin = origin;
    ee.angles = ( 0, 0, 0 );
    if ( isdefined( angles ) )
        ee.angles = angles;
    ee.model_name = iwz_opt( opts.model, "p7_zm_teddybear" );
    ee.song = iwz_opt( opts.song, "mus_iwz_abracadavre" );
    ee.hint_alias = iwz_opt( opts.hint_alias, "zmb_iwz_ee_hint_lp" );
    ee.activate_alias = iwz_opt( opts.activate_alias, "zmb_iwz_ee_activate" );
    ee.use_radius = iwz_opt( opts.use_radius, 72 );
    ee.use_hold = iwz_opt( opts.use_hold, 0.5 );          // seconds of Use held while looking at the bear
    ee.look_dot = iwz_opt( opts.look_dot, 0.85 );         // cosine of the look cone (about 32 degrees)
    ee.allow_damage = iwz_opt( opts.allow_damage, 1 );    // melee / shots, Spaceland style
    ee.song_delay = iwz_opt( opts.song_delay, 2.5 );      // Spaceland play_hidden_song delay
    ee.xp = iwz_opt( opts.xp, 0 );
    ee.done = 0;
    level.iwz_song_ee = ee;

    ee.model = spawn( "script_model", ee.origin );
    ee.model.angles = ee.angles;
    ee.model setmodel( ee.model_name );

    // the hint loop lives on its own origin: hiding or deleting the model never cuts it short
    ee.hum = spawn( "script_origin", ee.origin + ( 0, 0, 8 ) );
    ee.hum playloopsound( ee.hint_alias );
    print( "[IWZ audio] EE_ARMED origin=" + ee.origin + " model=" + ee.model_name + " hint=" + ee.hint_alias + " t=" + gettime() );

    if ( ee.allow_damage )
        ee.model thread iwz_ee_watch_damage( ee );

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

// BO-style interaction: hold Use within reach while looking at the bear (no prompt, no trigger entity)
iwz_ee_watch_use( ee )
{
    level endon( "game_ended" );
    level endon( "iwz_song_ee_activated" );

    for (;;)
    {
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

    target = ee.origin + ( 0, 0, 8 );
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
    playsoundatpos( ee.origin + ( 0, 0, 8 ), ee.activate_alias );

    if ( isdefined( ee.model ) )
    {
        ee.model setcandamage( 0 );
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
// emitters: array of structs { alias, origin, random (0/1), min_wait, max_wait }
ambience_init( emitters, bed )
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

    if ( isdefined( bed ) && soundexists( bed ) )
    {
        level.iwz_ambience_bed = bed;
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

    if ( isdefined( level.iwz_ambience_bed ) )
    {
        foreach ( player in level.players )
        {
            if ( isdefined( player ) )
                player stoplocalsound( level.iwz_ambience_bed );
        }

        level.iwz_ambience_bed = undefined;
    }
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

    foreach ( player in level.players )
        player thread iwz_ambience_bed_player();

    for (;;)
    {
        level waittill( "connected", player );
        player thread iwz_ambience_bed_player();
    }
}

iwz_ambience_bed_player()
{
    self endon( "disconnect" );
    level endon( "iwz_ambience_stop" );

    for (;;)
    {
        while ( !isalive( self ) )
            wait 0.25;

        if ( !isdefined( level.iwz_ambience_bed ) )
            return;

        self stoplocalsound( level.iwz_ambience_bed );
        self playlocalsound( level.iwz_ambience_bed );
        self waittill( "spawned_player" );
    }
}
