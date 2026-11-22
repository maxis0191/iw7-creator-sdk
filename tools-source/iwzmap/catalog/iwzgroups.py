"""Library groups for the asset library: name based, pure, no game data.

`iwzcat.guess_category` gives the fine category of a model (pipe, door, bench ...). This module adds the level a
section author picks from: a GROUP (architecture, structural, transit, retail, utilities, debris, furniture,
vegetation, vehicles, misc) and the classes that are kept out of the contact sheets (weapon, character, vfx).
The rules are ordered, first match wins, over the lower case model name. `group_of(name, fine)` returns
(group, subcategory). Tested by test_groups.py.
"""
import re

# excluded from the sheets and the picker by default (their own pipelines: weapons, characters, effects)
EXCLUDED = ('weapon', 'character', 'vfx', 'attachment')

# (group, subcategory, regex). Order matters: more specific first.
RULES = [
    # ---- excluded classes ------------------------------------------------------------------------------------
    ('vfx', 'vfx', r'^vfx_|_vfx_|^fx_|^vfx/|^tag_|empty_model|^invis_'),
    ('attachment', 'attachment', r'^attachment_|^cosmetic_|_complex_\d|^reticle|^tactical_|^lethal_|^super_|^equipment_|'
                                  r'_vm_|_vm$|_wm_|_wm$|^vmh_|^vm_|^wm_|^weapon_|^wpn_|^c4_|_grenade|^seeker|^exploding_|'
                                  r'^projectile|^proto|^ml/proto|^sentry_|^powerup|^care_package|^shock_|^venom|^ks_'),
    ('weapon', 'weapon', r'^weapon_|^wpn_|_mp$|_viewmodel|^gun_|nrgpistol'),
    ('character', 'character', r'^body_|^head_|^mp_.*(body|head)|_body_\d|^alien_|^fullbody|^viewhands|^viewmodel|zombie_body|_hair_|^c_|outfit|'
                               r'_torso|_leg_[lr]|_arm_[lr]|^zmb_(male|female)|^zmb_dlc\d_(male|female)|_head_\d|'
                               r'^zombie_|^zombies_(male|female|backpack)|^hero_|^player_|^robot_|^c6_|^c8_|^zom_(male|female)'),
    # ---- vehicles --------------------------------------------------------------------------------------------
    ('vehicles', 'car', r'^veh_|^vehicle_|_car_body|station_wagon|_truck|_bus_|^car_|_car_0|police_car|taxi'),
    ('debris', 'rubble', r'trash_?(can|bin)|trashbag|garbage|dumpster'),
    # ---- transit (metro, rail, signage of public transport) --------------------------------------------------
    ('transit', 'train', r'subway_car|subway_train|(^|_)train|_tram|railcar|locomotive|metro_'),
    ('transit', 'track', r'_rail_|_rails|railroad|_track_|tracks|rail_tie|railway'),
    ('transit', 'turnstile', r'turnstyle|turnstile|ticket_gate|fare_gate|gate_roller|park_turn'),
    ('transit', 'ticket', r'ticket|token_|fare_|booth'),
    ('transit', 'clock', r'clock'),
    ('transit', 'transit_map', r'_map_|^map_|subway_map|route_map|wayfinding|directory'),
    ('transit', 'platform', r'platform|bumpers?_|buffer_stop|yellow_line|tactile'),
    ('transit', 'bench', r'bench|waiting'),
    ('transit', 'sign', r'(^|_)sign(age|s)?($|_|\d)|placard|banner|billboard|poster|_logo|exit_|arrow_'),
    # ---- retail (shops, arcade) ------------------------------------------------------------------------------
    ('retail', 'arcade', r'arcade|jukebox|pinball|claw|astrocade|park_game|cabinet_game|game_machine'),
    ('retail', 'register', r'register|cash_|till|pos_|price|atm'),
    ('retail', 'vending', r'vending|soda|snack|dispenser|fortune_teller|gumball|token_machine|photo_booth|kiosk'),
    ('retail', 'neon', r'neon|marquee|lightbox|light_box'),
    ('retail', 'mannequin', r'mannequin|manikin|clothes|clothing|tshirt|garment|hanger|rack_cloth|shoe'),
    ('retail', 'shelf', r'shelf|shelves|shelving|display_case|showcase|gondola|concession|counter|stall|stand_|_stand|storefront|shop|store|market|grocery|pharmacy|bakery|popcorn|candy|(^|_)cart($|_|\d)'),
    ('retail', 'food', r'^food_|cookie|snack|soda|drink|beverage|bottle|can_|burger|pizza|fries|cup_|menu'),
    # ---- utilities --------------------------------------------------------------------------------------------
    ('utilities', 'light', r'(^|_)lights?($|_|\d)|lamp|lantern|bulb|fluorescent|sconce|chandelier|_flare|emergency_l|worklight|headlight|streetlight'),
    ('utilities', 'pipe', r'pipe|conduit|plumbing|valve|gutter|downspout|_duct|ducting|duct_'),
    ('utilities', 'cable', r'cable|wire|_cord|hose|cord_'),
    ('utilities', 'electrical', r'generator|transformer|power_box|breaker|fusebox|fuse_box|electric|elec_box|junction|_panel_box|switch|control_panel|(^|_)fans?($|_|\d)|circuit'),
    ('utilities', 'vent', r'vent|_fan_|exhaust|ac_unit|hvac|air_con'),
    ('utilities', 'machine', r'machine|console|computer|monitor|_tv|television|phone|radio|speaker|terminal|screen|projector|cctv|camera'),
    # ---- structural -------------------------------------------------------------------------------------------
    ('structural', 'stairs', r'stair|_steps|ladder|escalator|ramp'),
    ('structural', 'door', r'door|gate|shutter|hatch|portcullis'),
    ('structural', 'column', r'column|pillar|_post|beam|girder|support|_strut|truss|joist|_pole'),
    ('structural', 'arch', r'arch'),
    ('structural', 'railing', r'railing|handrail|guardrail|banister|balustrade|_rail'),
    ('structural', 'grate', r'grate|grating|grille|mesh|catwalk|walkway|manhole|drain'),
    ('structural', 'window', r'window|glass($|_|\d)|skylight'),
    ('structural', 'wall_piece', r'wall|facade|partition|panel|brick|_tile|cladding'),
    ('architecture', 'trim', r'trim|molding|moulding|_edge|_curb|_ledge|_cap_|baseboard|cornice|awning|canopy|ceiling|roof|floor|ground|_slab'),
    ('architecture', 'building', r'building|house|shed|structure|bridge|tunnel|stage|set_|_set$|fountain|statue|monument|fence|gate_'),
    # ---- debris and decay -------------------------------------------------------------------------------------
    ('debris', 'barricade', r'barricade|barrier|blockade|sandbag|cone|plank|board|tarp|scaffold|chain_link|chainlink|caution|tape'),
    ('debris', 'bodies', r'bone|skull|corpse|body_bag|cadaver|skeleton|remains|ghost'),
    ('debris', 'blood', r'blood|gore|gib|splat|entrails|guts'),
    ('debris', 'paper', r'paper|newspaper|litter|flyer|leaflet|book|magazine|document|note|sheet|poster_torn'),
    ('debris', 'rubble', r'rubble|debris|junk|trash|garbage|chunk|concrete_piece|brick_pile|rebar|broken|damaged|ruin|bags?_|_bag|bin_|_bin|dumpster'),
    ('debris', 'box', r'crate|box|barrel|drum|bucket|container|pallet|tank|suitcase|luggage|case_|bag|sack'),
    # ---- furniture --------------------------------------------------------------------------------------------
    ('furniture', 'seat', r'chair|stool|couch|sofa|seat|armchair|ottoman|booth_seat'),
    ('furniture', 'table', r'table|desk|workbench|bar_|podium'),
    ('furniture', 'storage', r'locker|cabinet|shelf|drawer|dresser|wardrobe|bookcase|filing'),
    ('furniture', 'decor', r'picture|painting|frame|mirror|curtain|rug|carpet|vase|lamp_shade|plant_pot|clock_|statue|trophy|toy|doll|teddy|bed|mattress|pillow|sink|toilet|bathroom|kitchen|stove|fridge|tv_'),
    # ---- vegetation -------------------------------------------------------------------------------------------
    ('vegetation', 'plant', r'tree|bush|foliage|plant|grass|ivy|leaf|leaves|weed|flower|moss|vine|shrub|palm|fern|vista_tree|rock|cliff|boulder|stone|snow|ice'),
]
RULES = [(g, s, re.compile(p)) for g, s, p in RULES]

# fine category (iwzcat.guess_category) -> group, used when no name rule matches
FINE_TO_GROUP = {
    'vfx_model': ('vfx', 'vfx'), 'character': ('character', 'character'), 'weapon': ('weapon', 'weapon'),
    'vehicle': ('vehicles', 'car'), 'train': ('transit', 'train'), 'track': ('transit', 'track'),
    'turnstile': ('transit', 'turnstile'), 'ticket': ('transit', 'ticket'), 'sign': ('transit', 'sign'),
    'light': ('utilities', 'light'), 'pipe': ('utilities', 'pipe'), 'cable': ('utilities', 'cable'),
    'generator': ('utilities', 'electrical'), 'vent': ('utilities', 'vent'), 'stairs': ('structural', 'stairs'),
    'door': ('structural', 'door'), 'window': ('structural', 'window'), 'column': ('structural', 'column'),
    'arch': ('structural', 'arch'), 'trim': ('architecture', 'trim'), 'wall': ('structural', 'wall_piece'),
    'floor': ('architecture', 'trim'), 'ceiling': ('architecture', 'trim'), 'bench': ('transit', 'bench'),
    'table': ('furniture', 'table'), 'storage': ('furniture', 'storage'), 'trash': ('debris', 'rubble'),
    'container': ('debris', 'box'), 'barrier': ('debris', 'barricade'), 'machine': ('utilities', 'machine'),
    'foliage': ('vegetation', 'plant'), 'rock': ('vegetation', 'plant'),
}


def group_of(name, fine=None):
    """-> (group, subcategory). `fine` is the iwzcat fine category when known."""
    n = name.lower().replace('/', '_')
    for g, s, rx in RULES:
        if rx.search(n):
            return g, s
    if fine in FINE_TO_GROUP:
        return FINE_TO_GROUP[fine]
    return 'misc', 'misc'
