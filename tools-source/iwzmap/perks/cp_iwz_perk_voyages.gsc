// BON VOYAGES (the Parlour, 2000; bible 06-PERKS.md section 2). For the owner: Capsule Post postage at half price,
// traps the owner buys at half price and a trap the owner bought does not hurt them, and after any arrival (Capsule Post
// or the 23:47's return) the weapon is already up and the owner moves 20 % faster for 4 s. It adds no damage and no
// health. The prices and the trap rule are read by the other packages through level.iwz_price_func and
// level.iwz_trap_hurts_func (cp_iwz_perks); an arrival is reported through level.iwz_arrival_func.

init()
{
    level.szp.bv_speed = 1.2;
    level.szp.bv_speed_s = 4;
}

give()
{
    if ( !isdefined( self.szp_bv_arrivals ) )
        self.szp_bv_arrivals = 0;
}

take()
{
    scripts\cp\zombies\zombies_perk_machines::remove_zombies_perk_icon_and_index( "perk_machine_voyage" );
}

// self: the owner, just arrived (how: "capsule", "train", or a test's name)
on_arrival( how )
{
    self endon( "disconnect" );
    self.szp_bv_arrivals++;
    w = self getcurrentweapon();
    if ( isdefined( w ) && w != "none" )
        self switchtoweaponimmediate( w );        // weapon up at once, no raise
    print( "[IWZ perks] VOYAGE_ARRIVAL player=" + self getentitynumber() + " how=" + how + " weapon=" + w + " arrivals=" + self.szp_bv_arrivals );
    self scripts\cp\maps\cp_iwz\cp_iwz_perk_doubletakes::speed_boost( level.szp.bv_speed, level.szp.bv_speed_s );
}

state()
{
    n = 0;
    if ( isdefined( self.szp_bv_arrivals ) )
        n = self.szp_bv_arrivals;
    return "voyage_arrivals=" + n + " voyage_trap_price=" + scripts\cp\maps\cp_iwz\cp_iwz_perks::price( self, 750, "trap" ) + " voyage_postage_price=" + scripts\cp\maps\cp_iwz\cp_iwz_perks::price( self, 500, "postage" );
}
