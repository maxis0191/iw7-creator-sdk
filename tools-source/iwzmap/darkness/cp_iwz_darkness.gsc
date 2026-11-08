// IWZ darkness module: the station is dark until the power is switched on, then its lights come on bank by bank.
//
// Map side (generated, see tools-source/iwzmap/darkness/README.md):
//   - the lightmap / light grid hold the DARK state only (emergency lamps, amber cues, a faint ambient floor);
//   - every station light is a script-switchable primary light: map entity light_spot, targetname "iwz_power",
//     script_noteworthy "<bank index>|<zone>|<on intensity>|<kind>" (kind: lamp_cool, lamp_warm, work_light, flicker,
//     extra), compiled into a scriptable light slot by the IW7 map compiler (lights.txt name= / group=);
//   - fluorescent fittings of those lights are script_models "iwz_power_fixture" (script_noteworthy = zone) shown
//     with their unlit model before power and their lit model after (model names below);
//   - flickering lamps ("iwz_flicker" models of the level script) are taken over by this module (level.iwz_dark).
// Power: the stock Spaceland flag "power_on". Timeline (agreed with the audio module, darkness\NOTES.md): banks from
// 2.65 s after the flag, one per zone in bank order, 0.8..1.3 s apart; each bank sends
// level notify( "iwz_light_bank_on", <zone> ) at its start (audio: relay thunk, tube strikes 0.12 s later), its
// lights strike with 2..4 stutters over 0.15..0.9 s and stay on. After the last bank: flag "iwz_power_lights_done".
// Debug dvar (prints only): paris_iwz_dark_debug 1 -> "[IWZ dark] ..." lines with gettime() stamps.
// Calibration dvar (private tests): paris_iwz_dark_scale <float> multiplies every on intensity (default 1).

init()
{
    level.iwz_dark = 1;
    level.iwz_light_banks_external = 1;      // the audio power sequence follows this module's bank notifies
    scripts\engine\utility::flag_init( "iwz_power_lights_done" );
    level.iwz_dark_fixture_off = "mp_dart_lightfluo";
    level.iwz_dark_fixture_on = "mp_dart_lightfluo_on";
    level.iwz_dark_lights = [];
    level.iwz_dark_banks = [];
    foreach ( l in getentarray( "iwz_power", "targetname" ) )
    {
        p = strtok( l.script_noteworthy, "|" );
        if ( p.size < 4 )
            continue;
        l.iwz_bank = int( p[0] );
        l.iwz_zone = p[1];
        l.iwz_on = float( p[2] );
        l.iwz_kind = p[3];
        l setlightintensity( 0 );
        level.iwz_dark_lights[level.iwz_dark_lights.size] = l;
        if ( !isdefined( level.iwz_dark_banks[l.iwz_bank] ) )
            level.iwz_dark_banks[l.iwz_bank] = [];
        level.iwz_dark_banks[l.iwz_bank][level.iwz_dark_banks[l.iwz_bank].size] = l;
    }
    // fittings: each follows its nearest power light of the same zone
    foreach ( f in getentarray( "iwz_power_fixture", "targetname" ) )
    {
        p = strtok( f.script_noteworthy, "|" );
        f.iwz_zone = p[0];
        f.iwz_off = level.iwz_dark_fixture_off;
        f.iwz_on = level.iwz_dark_fixture_on;
        if ( p.size >= 3 )
        {
            f.iwz_off = p[1];
            f.iwz_on = p[2];
        }
        f setmodel( f.iwz_off );
        best = undefined;
        bd = 1000000000.0;
        foreach ( l in level.iwz_dark_lights )
        {
            d = distancesquared( l.origin, f.origin );
            if ( l.iwz_zone == f.iwz_zone && d < bd )
            {
                bd = d;
                best = l;
            }
        }
        if ( isdefined( best ) )
        {
            if ( !isdefined( best.iwz_fixtures ) )
                best.iwz_fixtures = [];
            best.iwz_fixtures[best.iwz_fixtures.size] = f;
        }
    }
    // flickering lamps stay dead until their bank is on
    level.iwz_dark_flicker = getentarray( "iwz_flicker", "targetname" );
    foreach ( m in level.iwz_dark_flicker )
    {
        m.iwz_off = level.iwz_dark_fixture_off;
        m.iwz_on = level.iwz_dark_fixture_on;
        m setmodel( m.iwz_off );
    }
    iwz_dark_log( "INIT lights=" + level.iwz_dark_lights.size + " banks=" + level.iwz_dark_banks.size + " fixtures=" +
        getentarray( "iwz_power_fixture", "targetname" ).size + " flicker=" + level.iwz_dark_flicker.size );
    level thread iwz_dark_power();
}

iwz_dark_log( s )
{
    if ( getdvarint( "paris_iwz_dark_debug" ) )
        print( "[IWZ dark] " + s + " t=" + gettime() );
}

iwz_dark_scale()
{
    s = getdvarfloat( "paris_iwz_dark_scale" );
    if ( s <= 0 )
        return 1.0;
    return s;
}

iwz_dark_set( l, on )
{
    if ( on )
        l setlightintensity( l.iwz_on * iwz_dark_scale() );
    else
        l setlightintensity( 0 );
    if ( isdefined( l.iwz_fixtures ) )
    {
        foreach ( f in l.iwz_fixtures )
        {
            if ( on )
                f setmodel( f.iwz_on );
            else
                f setmodel( f.iwz_off );
        }
    }
}

iwz_dark_power()
{
    level endon( "game_ended" );
    while ( !scripts\engine\utility::flag_exist( "power_on" ) )
        wait 0.5;
    scripts\engine\utility::flag_wait( "power_on" );
    iwz_dark_log( "POWER_ON" );
    wait 2.65;      // generator spin-up, breakers and hum (audio module)
    for ( b = 0; b < level.iwz_dark_banks.size; b++ )
    {
        if ( !isdefined( level.iwz_dark_banks[b] ) || !level.iwz_dark_banks[b].size )
            continue;
        zone = level.iwz_dark_banks[b][0].iwz_zone;
        level notify( "iwz_light_bank_on", zone );
        iwz_dark_log( "BANK " + b + " " + zone + " lights=" + level.iwz_dark_banks[b].size );
        foreach ( l in level.iwz_dark_banks[b] )
            l thread iwz_dark_strike();
        foreach ( m in level.iwz_dark_flicker )
        {
            if ( iwz_dark_zone_of( m.origin ) == zone )
                m thread iwz_dark_flicker_lamp();
        }
        wait( randomfloatrange( 0.8, 1.3 ) );
    }
    // flicker lamps outside every bank's zone start with the last bank
    foreach ( m in level.iwz_dark_flicker )
    {
        if ( !isdefined( m.iwz_flicker_on ) )
            m thread iwz_dark_flicker_lamp();
    }
    wait 0.9;
    scripts\engine\utility::flag_set( "iwz_power_lights_done" );
    level notify( "iwz_power_lights_done" );
    iwz_dark_log( "LIGHTS_DONE" );
}

// a tube striking: 0.12 s after the relay, 2..4 short on/off stutters, then on
iwz_dark_strike()
{
    level endon( "game_ended" );
    wait( 0.12 + randomfloatrange( 0.0, 0.25 ) );
    n = randomintrange( 2, 5 );
    for ( i = 0; i < n; i++ )
    {
        iwz_dark_set( self, 1 );
        wait( randomfloatrange( 0.03, 0.09 ) );
        iwz_dark_set( self, 0 );
        wait( randomfloatrange( 0.04, 0.16 ) );
    }
    iwz_dark_set( self, 1 );
    if ( self.iwz_kind == "flicker" )
        self thread iwz_dark_flicker_light();
}

// a power light of kind "flicker" keeps stuttering after power-on (light pool and its fitting together)
iwz_dark_flicker_light()
{
    level endon( "game_ended" );
    for ( ;; )
    {
        wait( randomfloatrange( 1.5, 5.0 ) );
        n = randomintrange( 2, 6 );
        for ( i = 0; i < n; i++ )
        {
            iwz_dark_set( self, 0 );
            wait( randomfloatrange( 0.04, 0.12 ) );
            iwz_dark_set( self, 1 );
            wait( randomfloatrange( 0.05, 0.2 ) );
        }
    }
}

// level flicker models (iwz_flicker): their light is the nearest "flicker" power light, switched with the model
iwz_dark_flicker_lamp()
{
    level endon( "game_ended" );
    self.iwz_flicker_on = 1;
    best = undefined;
    bd = 1000000000.0;
    foreach ( l in level.iwz_dark_lights )
    {
        d = distancesquared( l.origin, self.origin );
        if ( l.iwz_kind == "flicker" && d < bd )
        {
            bd = d;
            best = l;
        }
    }
    if ( isdefined( best ) && bd < 160 * 160 )
    {
        // the light's own flicker thread drives the fitting
        if ( !isdefined( best.iwz_fixtures ) )
            best.iwz_fixtures = [];
        best.iwz_fixtures[best.iwz_fixtures.size] = self;
        self setmodel( level.iwz_dark_fixture_on );
        return;
    }
    // no light of its own: model-only flicker (as the level script did)
    self setmodel( level.iwz_dark_fixture_on );
    for ( ;; )
    {
        wait( randomfloatrange( 1.5, 5.0 ) );
        n = randomintrange( 2, 6 );
        for ( i = 0; i < n; i++ )
        {
            self setmodel( level.iwz_dark_fixture_off );
            wait( randomfloatrange( 0.04, 0.12 ) );
            self setmodel( level.iwz_dark_fixture_on );
            wait( randomfloatrange( 0.05, 0.2 ) );
        }
    }
}

iwz_dark_zone_of( o )
{
    best = "";
    bd = 1000000000000.0;
    foreach ( l in level.iwz_dark_lights )
    {
        d = distancesquared( l.origin, o );
        if ( d < bd )
        {
            bd = d;
            best = l.iwz_zone;
        }
    }
    return best;
}
