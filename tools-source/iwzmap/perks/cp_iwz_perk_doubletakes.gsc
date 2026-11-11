// DOUBLE TAKES (Underpass Arcade photo booth, 3000; bible 06-PERKS.md section 2). When a zombie's hit leaves the owner
// alive under 35 % of health, a flash goes off and a still image of the owner stays where they stood for 4 s: zombies
// within 400 units go for the image, the owner moves 20 % faster for 1.5 s. Cooldown 60 s, the perk's icon dim while it
// recharges. The Night Inspector and the Rollers pass through the image. Called from cp_iwz_perks (player damage).
// level.szp.dt_mode "threshold" (the bible's rule) or "unhurt" (the bible's fallback: the first hit taken after 10 s
// unhurt), chosen by measuring what a hit does at each round.

init()
{
    level.szp.dt_mode = "threshold";
    level.szp.dt_threshold = 0.35;
    level.szp.dt_unhurt_ms = 10000;
    level.szp.dt_radius = 400;
    level.szp.dt_image_s = 4;
    level.szp.dt_speed = 1.2;
    level.szp.dt_speed_s = 1.5;
    level.szp.dt_cooldown_ms = 60000;
    // the image: a flat cut-out on a stand (the shooting gallery's civilian targets) until the hero looks deliver a
    // posed body per outfit (bible: "which is also the better joke")
    level.szp.dt_model = "zmb_civilian_target_02";
    precachemodel( level.szp.dt_model );
    level._effect["szp_dt_flash"] = loadfx( "vfx/iw7/core/zombie/vfx_zmb_neil_flash" );
}

give()
{
    if ( !isdefined( self.szp_dt_ready_at ) )
        self.szp_dt_ready_at = 0;
    if ( !isdefined( self.szp_dt_triggers ) )
        self.szp_dt_triggers = 0;
    self.szp_dt_last_hurt = 0;
    if ( gettime() < self.szp_dt_ready_at )
        self thread recharge( self.szp_dt_ready_at );
}

take()
{
    // the stock take has already cleared the bit of the icon shown (the dim one while recharging: self.sub_perks)
    self notify( "szp_dt_taken" );
    scripts\cp\zombies\zombies_perk_machines::remove_zombies_perk_icon_and_index( "perk_machine_double" );
    self.sub_perks["perk_machine_double"] = undefined;
}

// self: the owner, after a zombie's hit was applied. h0: health before the hit.
after_hurt( z, damage, h0 )
{
    now = gettime();
    last = self.szp_dt_last_hurt;
    self.szp_dt_last_hurt = now;
    if ( now < self.szp_dt_ready_at )
        return;
    if ( !isalive( self ) || scripts\engine\utility::is_true( self.inlaststand ) || self.health <= 0 )
        return;
    if ( level.szp.dt_mode == "unhurt" )
    {
        if ( now - last < level.szp.dt_unhurt_ms )
            return;
    }
    else
    {
        limit = self.maxhealth * level.szp.dt_threshold;
        if ( !( self.health < limit && h0 >= limit ) )
            return;
    }
    self thread trigger( h0 );
}

trigger( h0 )
{
    self endon( "disconnect" );
    self.szp_dt_ready_at = gettime() + level.szp.dt_cooldown_ms;
    self.szp_dt_triggers++;
    at = self.origin;
    yaw = self.angles[1];
    img = spawn( "script_model", at );
    img setmodel( level.szp.dt_model );
    img.angles = ( 0, yaw, 0 );
    img.targetname = "szp_double_image";
    playfx( level._effect["szp_dt_flash"], at + ( 0, 0, 56 ) );
    if ( soundexists( "zmb_photobooth_flash" ) )
        playsoundatpos( at, "zmb_photobooth_flash" );
    lured = [];
    if ( isdefined( level.spawned_enemies ) )
    {
        foreach ( z in level.spawned_enemies )
        {
            if ( !isdefined( z ) || !isalive( z ) || !scripts\cp\maps\cp_iwz\cp_iwz_perks::markable( z ) )
                continue;
            if ( distancesquared( z.origin, at ) > level.szp.dt_radius * level.szp.dt_radius )
                continue;
            z.szp_dt_d0 = distance( z.origin, at );
            lured[lured.size] = z;
            z thread lure( img, level.szp.dt_image_s );
        }
    }
    print( "[IWZ perks] DOUBLE_TRIGGER player=" + self getentitynumber() + " health0=" + h0 + " health1=" + self.health + " max=" + self.maxhealth
        + " lured=" + lured.size + " mode=" + level.szp.dt_mode + " triggers=" + self.szp_dt_triggers );
    self thread speed_boost( level.szp.dt_speed, level.szp.dt_speed_s );
    self thread recharge( self.szp_dt_ready_at );
    wait 3.5;
    // after 3.5 s: how many lured zombies closed on the image
    toward = 0;
    alive = 0;
    foreach ( z in lured )
    {
        if ( !isdefined( z ) || !isalive( z ) )
            continue;
        alive++;
        // went for the image: 30 units nearer it than at the flash (a round-1 zombie walks about 34 units a second)
        if ( z.szp_dt_d0 - distance( z.origin, img.origin ) >= 30 )
            toward++;
    }
    self.szp_dt_lured_n = alive;
    self.szp_dt_nearer = toward;
    print( "[IWZ perks] DOUBLE_LURE player=" + self getentitynumber() + " alive=" + alive + " nearer_image=" + toward + " owner_moved=" + int( distance( at, self.origin ) ) );
    wait level.szp.dt_image_s - 3.5;
    img delete();
}

// the zombie goes to the image (the stock crafted boombox's way of drawing zombies: scripted mode and a goal), then is
// let go
lure( img, seconds )
{
    self endon( "death" );
    self.szp_dt_lured = 1;
    self.og_goalradius = self.goalradius;
    self.scripted_mode = 1;
    self.goalradius = 48;
    self setgoalpos( img.origin );
    wait seconds;
    if ( isdefined( self.og_goalradius ) )
        self.goalradius = self.og_goalradius;
    self.og_goalradius = undefined;
    self.scripted_mode = 0;
    self.szp_dt_lured = undefined;
}

// the dim icon while it recharges: the perk's HUD bit is swapped for the row "perk_machine_double_cd" (the stock way a
// perk shows a variant, as Change Chews does with self.sub_perks)
recharge( until )
{
    self endon( "disconnect" );
    self endon( "szp_dt_taken" );
    self notify( "szp_dt_recharge" );
    self endon( "szp_dt_recharge" );
    self set_bit( "perk_machine_double", 0 );
    self.sub_perks["perk_machine_double"] = "perk_machine_double_cd";
    self set_bit( "perk_machine_double_cd", 1 );
    while ( gettime() < until )
        wait 0.5;
    self set_bit( "perk_machine_double_cd", 0 );
    self.sub_perks["perk_machine_double"] = undefined;
    self set_bit( "perk_machine_double", 1 );
    print( "[IWZ perks] DOUBLE_READY player=" + self getentitynumber() );
}

set_bit( name, on )
{
    b = int( tablelookup( "cp/zombies/zombie_perks_bit_mask_table.csv", 1, name, 0 ) );
    if ( b <= 0 )
        return;
    self setclientomnvarbit( "zm_active_perks", b - 1, on );
}

// one speed scale at a time for the perks of this map: the latest end wins, then the scale goes back to 1
speed_boost( scale, seconds )
{
    self endon( "disconnect" );
    until = gettime() + int( seconds * 1000 );
    if ( !isdefined( self.szp_speed_until ) || until > self.szp_speed_until )
        self.szp_speed_until = until;
    self setmovespeedscale( scale );
    print( "[IWZ perks] SPEED player=" + self getentitynumber() + " scale=" + scale + " s=" + seconds );
    while ( gettime() < self.szp_speed_until )
        wait 0.05;
    self setmovespeedscale( 1.0 );
}

state()
{
    r = 1;
    if ( isdefined( self.szp_dt_ready_at ) && gettime() < self.szp_dt_ready_at )
        r = 0;
    n = 0;
    if ( isdefined( self.szp_dt_triggers ) )
        n = self.szp_dt_triggers;
    left = 0;
    if ( !r )
        left = self.szp_dt_ready_at - gettime();
    l = -1;
    k = -1;
    if ( isdefined( self.szp_dt_lured_n ) )
    {
        l = self.szp_dt_lured_n;
        k = self.szp_dt_nearer;
    }
    return "double_ready=" + r + " double_triggers=" + n + " double_cooldown_ms=" + left + " double_lured=" + l + " double_nearer_image=" + k;
}
