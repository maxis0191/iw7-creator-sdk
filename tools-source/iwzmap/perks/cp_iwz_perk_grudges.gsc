// SOUR GRUDGES (the Boneyard, 2500; bible 06-PERKS.md section 2). The zombie that last hit the owner is marked for
// 6 s (a green fume over its head, seen by the owner only). The owner kills it inside the 6 s with an ordinary weapon:
// the next hit the owner takes within 8 s does no damage (a green rim at the screen edge while it holds). One mark at a
// time, one forgiven hit at a time. The Night Inspector and the Rollers are never marked; a wonder-weapon kill earns
// nothing. Called from cp_iwz_perks (player damage callback).

init()
{
    level.szp.sg_mark_ms = 6000;
    level.szp.sg_shield_ms = 8000;
    level._effect["szp_grudge_mark"] = loadfx( "vfx/iw7/core/zombie/vfx_souvenir_glow_green" );
}

give()
{
    if ( !isdefined( self.szp_sg_forgiven ) )
        self.szp_sg_forgiven = 0;
    if ( !isdefined( self.szp_sg_earned ) )
        self.szp_sg_earned = 0;
    if ( !isdefined( self.szp_sg_marks ) )
        self.szp_sg_marks = 0;
    self.szp_sg_shield_until = 0;
}

take()
{
    self notify( "szp_sg_mark_end" );
    self.szp_sg_shield_until = 0;
    self clear_mark();
    self rim( 0 );
    scripts\cp\zombies\zombies_perk_machines::remove_zombies_perk_icon_and_index( "perk_machine_grudge" );
}

// self: the owner, before the damage of a zombie's hit is applied. Returns the damage to apply.
on_hurt( z, damage )
{
    now = gettime();
    if ( isdefined( self.szp_sg_shield_until ) && now < self.szp_sg_shield_until )
    {
        self.szp_sg_shield_until = 0;
        self.szp_sg_forgiven++;
        self rim( 0 );
        print( "[IWZ perks] GRUDGE_FORGIVEN player=" + self getentitynumber() + " damage=" + damage + " forgiven=" + self.szp_sg_forgiven );
        return 0;
    }
    if ( scripts\cp\maps\cp_iwz\cp_iwz_perks::markable( z ) )
        self mark( z );
    return damage;
}

mark( z )
{
    self notify( "szp_sg_mark_end" );
    self clear_mark();
    self.szp_sg_mark = z;
    self.szp_sg_mark_until = gettime() + level.szp.sg_mark_ms;
    self.szp_sg_marks++;
    playfxontagforclients( level._effect["szp_grudge_mark"], z, "j_head", self );
    z.szp_sg_fx_owner = self;
    print( "[IWZ perks] GRUDGE_MARK player=" + self getentitynumber() + " zombie=" + z getentitynumber() + " type=" + z.agent_type );
    self thread watch_mark( z );
}

clear_mark()
{
    if ( isdefined( self.szp_sg_mark ) && isalive( self.szp_sg_mark ) )
        stopfxontag( level._effect["szp_grudge_mark"], self.szp_sg_mark, "j_head" );
    self.szp_sg_mark = undefined;
}

watch_mark( z )
{
    self endon( "disconnect" );
    self endon( "szp_sg_mark_end" );
    self thread mark_timeout( z );
    z waittill( "death", killer, mod, weapon );
    inside = isdefined( self.szp_sg_mark_until ) && gettime() <= self.szp_sg_mark_until;
    mine = isdefined( killer ) && killer == self;
    // the killing weapon: the death's own, else the owner's last hit on this zombie (map hook)
    if ( !isdefined( weapon ) && mine && isdefined( self.szp_last_hit_ent ) && self.szp_last_hit_ent == z )
        weapon = self.szp_last_hit_weapon;
    ordinary = scripts\cp\maps\cp_iwz\cp_iwz_perks::ordinary_weapon( weapon, mod );
    self.szp_sg_mark = undefined;
    if ( inside && mine && ordinary && scripts\cp\maps\cp_iwz\cp_iwz_perks::has( self, "perk_machine_grudge" ) )
    {
        self.szp_sg_shield_until = gettime() + level.szp.sg_shield_ms;
        self.szp_sg_earned++;
        self rim( 1 );
        self thread shield_timeout( self.szp_sg_shield_until );
        print( "[IWZ perks] GRUDGE_EARNED player=" + self getentitynumber() + " weapon=" + weapon + " earned=" + self.szp_sg_earned );
    }
    else
    {
        if ( !isdefined( weapon ) )
            weapon = "none";
        print( "[IWZ perks] GRUDGE_NO_REWARD player=" + self getentitynumber() + " inside=" + inside + " mine=" + mine + " ordinary=" + ordinary + " weapon=" + weapon );
    }
    self notify( "szp_sg_mark_end" );
}

mark_timeout( z )
{
    self endon( "disconnect" );
    self endon( "szp_sg_mark_end" );
    wait level.szp.sg_mark_ms / 1000;
    print( "[IWZ perks] GRUDGE_MARK_EXPIRED player=" + self getentitynumber() );
    self clear_mark();
    self notify( "szp_sg_mark_end" );
}

shield_timeout( until )
{
    self endon( "disconnect" );
    wait level.szp.sg_shield_ms / 1000;
    if ( isdefined( self.szp_sg_shield_until ) && self.szp_sg_shield_until == until )
    {
        self.szp_sg_shield_until = 0;
        self rim( 0 );
        print( "[IWZ perks] GRUDGE_SHIELD_EXPIRED player=" + self getentitynumber() );
    }
}

// the green rim: four thin bars on the screen edges, the owner's only
rim( on )
{
    if ( !isdefined( self.szp_sg_rim ) )
    {
        self.szp_sg_rim = [];
        // horzalign/vertalign "fullscreen": x, y, w, h in the 640 x 480 virtual screen
        r = [ [ 0, 0, 640, 6 ], [ 0, 474, 640, 6 ], [ 0, 0, 6, 480 ], [ 634, 0, 6, 480 ] ];
        foreach ( b in r )
        {
            e = newclienthudelem( self );
            e.horzalign = "fullscreen";
            e.vertalign = "fullscreen";
            e.alignx = "left";
            e.aligny = "top";
            e.x = b[0];
            e.y = b[1];
            e setshader( "white", b[2], b[3] );
            e.color = ( 0.45, 0.95, 0.35 );
            e.alpha = 0;
            e.archived = 1;
            e.hidewheninmenu = 1;
            e.sort = 5;
            self.szp_sg_rim[self.szp_sg_rim.size] = e;
        }
    }
    a = 0;
    if ( on )
        a = 0.45;
    foreach ( e in self.szp_sg_rim )
        e.alpha = a;
}

state()
{
    m = -1;
    if ( isdefined( self.szp_sg_mark ) && isalive( self.szp_sg_mark ) )
        m = self.szp_sg_mark getentitynumber();
    sh = 0;
    if ( isdefined( self.szp_sg_shield_until ) && gettime() < self.szp_sg_shield_until )
        sh = 1;
    f = 0;
    if ( isdefined( self.szp_sg_forgiven ) )
        f = self.szp_sg_forgiven;
    e = 0;
    if ( isdefined( self.szp_sg_earned ) )
        e = self.szp_sg_earned;
    return "grudge_mark=" + m + " grudge_shield=" + sh + " grudge_forgiven=" + f + " grudge_earned=" + e;
}
