// IWZ custom map gameplay probe (local private session only): drives the stock zombies systems of the
// generated map through their own functions and prints "[IWZ game] ..." checkpoints:
//   CHASE    zombies close in on the (targetable) player
//   ROUND    killing the wave advances the round and awards points
//   DOOR     buying the first door (stock clear_debris) activates the generator zone
//   POWER    the stock generator interaction powers the perk machines
// Views listed in paris_iwz_views are captured along the way (capture_frame iwzgame<i>).

init()
{
    if (getdvarint("dedicated") || getdvar("paris_iwz_gameplay") == "")
        return;

    level thread iwz_game_run();
}

iwz_game_run()
{
    level waittill("connected", player);
    while (!isalive(player))
        wait 0.2;
    while (!scripts\engine\utility::flag("introscreen_over"))
        wait 0.2;
    wait 2;
    player.ignoreme = 0;
    print("[IWZ game] START origin=" + player.origin);

    // 1. chase: wait for zombies and measure their distance to the player
    deadline = gettime() + 60000;
    while (gettime() < deadline && (!isdefined(level.spawned_enemies) || level.spawned_enemies.size == 0))
        wait 0.5;
    first = iwz_nearest(player);
    wait 8;
    second = iwz_nearest(player);
    print("[IWZ game] CHASE zombies=" + level.spawned_enemies.size + " nearest_before=" + first + " nearest_after=" + second);
    iwz_capture(player, 0);

    // 2. round: kill every zombie of the wave with the player as attacker
    wave = level.wave_num;
    money = player scripts\cp\cp_persistence::get_player_currency();
    deadline = gettime() + 120000;
    while (gettime() < deadline && level.wave_num == wave)
    {
        if (isdefined(level.spawned_enemies))
        {
            foreach (zombie in level.spawned_enemies)
            {
                if (isdefined(zombie) && isalive(zombie))
                    zombie dodamage(zombie.health + 1000, zombie.origin, player, player, "MOD_RIFLE_BULLET", player getcurrentweapon());
            }
        }
        wait 0.5;
    }
    print("[IWZ game] ROUND wave_before=" + wave + " wave_after=" + level.wave_num + " money_before=" + money + " money_after=" + (player scripts\cp\cp_persistence::get_player_currency()));

    // 3a. door through the stock trigger path (like a player's Use): hall-side struct of the hall -> stair_a door
    trig = undefined;
    foreach (s in level.all_interaction_structs)
    {
        if (isdefined(s.script_noteworthy) && s.script_noteworthy == "debris_750" && isdefined(s.script_area) && s.script_area == "stair_a")
            trig = s;
    }
    if (isdefined(trig))
    {
        player scripts\cp\cp_persistence::set_player_currency(5000);
        before = player scripts\cp\cp_persistence::get_player_currency();
        dir = anglestoforward(trig.angles);
        // a player standing 72 units in front of the struct, looking at the door horizontally (the stock FOV test
        // measures from the feet: aiming the eye down at the low struct fails it)
        stand = (trig.origin[0] - dir[0] * 72, trig.origin[1] - dir[1] * 72, trig.origin[2] + 40);
        gt = bullettrace(stand, stand - (0, 0, 400), 0, undefined);
        player setorigin(gt["position"] + (0, 0, 1));
        face = vectortoangles(trig.origin - player.origin);
        player setplayerangles((0, face[1], 0));
        wait 1;
        fov = vectordot(anglestoforward(player getplayerangles()), vectornormalize(trig.origin - player.origin)) > cos(25);
        tr = bullettrace(player geteye(), trig.origin, 0, player);
        print("[IWZ game] DOORDIAG floor=" + gt["position"] + " player=" + player.origin + " onground=" + player isonground() + " fov=" + fov
            + " trace=" + tr["fraction"] + " hit=" + tr["position"] + " struct=" + trig.origin);
        usable = player scripts\cp\cp_interaction::_id_9C64(player, trig);
        if (!scripts\engine\utility::array_contains(level.current_interaction_structs, trig))
            scripts\cp\cp_interaction::add_to_current_interaction_list(trig);
        player scripts\cp\cp_interaction::set_interaction_point(trig);
        wait 0.3;
        player.interaction_trigger notify("trigger", player);
        wait 2.5;
        // the stock door_buy trigger_use of this door (what a player's Use fires on Spaceland doors)
        dt = undefined;
        alltrigs = getentarray("door_buy", "targetname");
        tinfo = "";
        st = "undef";
        if (isdefined(trig.target))
            st = trig.target;
        foreach (t in alltrigs)
        {
            tt = "undef";
            if (isdefined(t.target))
                tt = t.target;
            tn = "undef";
            if (isdefined(t.script_noteworthy))
                tn = t.script_noteworthy;
            tinfo = tinfo + t.origin + "/" + tt + "/" + tn + " ";
            if (isdefined(t.target) && t.target == trig.target)
                dt = t;
        }
        print("[IWZ game] DOORBUYTRIGS struct_target=" + st + " " + tinfo);
        mid = player scripts\cp\cp_persistence::get_player_currency();
        if (isdefined(dt) && mid == before)
        {
            dt notify("trigger", player);
            wait 2.5;
        }
        // second door (stair_b <- hall) through its door_buy trigger_use alone: nearest trigger to the doorway
        bt = undefined;
        foreach (t in alltrigs)
        {
            if (!isdefined(bt) || distance(t.origin, (-1208, 3304, 96)) < distance(bt.origin, (-1208, 3304, 96)))
                bt = t;
        }
        if (isdefined(bt))
        {
            player setorigin((-1140, 3304, 0));
            player setplayerangles((0, 180, 0));
            wait 0.5;
            b0 = player scripts\cp\cp_persistence::get_player_currency();
            bt notify("trigger", player);
            wait 3;
            b1 = player scripts\cp\cp_persistence::get_player_currency();
            bact = isdefined(level.spawn_volume_array["stair_b"]) && scripts\engine\utility::is_true(level.spawn_volume_array["stair_b"].active);
            print("[IWZ game] DOORBUYTRIG trigger=" + bt.origin + " paid=" + (b0 - b1) + " stair_b_active=" + bact + " trigger_deleted=" + !isdefined(bt));
        }
        print("[IWZ game] DOORBUY door_buy_triggers=" + alltrigs.size + " found=" + isdefined(dt) + " paid_struct_path=" + (before - mid)
            + " paid_trigger=" + (mid - player scripts\cp\cp_persistence::get_player_currency()));
        after = player scripts\cp\cp_persistence::get_player_currency();
        active = isdefined(level.spawn_volume_array["stair_a"]) && scripts\engine\utility::is_true(level.spawn_volume_array["stair_a"].active);
        print("[IWZ game] DOORTRIG usable=" + usable + " paid=" + (before - after) + " stair_a_active=" + active + " player=" + player.origin);
    }

    // 3. door: the stock purchase path of the first debris struct
    door = undefined;
    foreach (s in level.all_interaction_structs)
    {
        // a debris door whose zone (script_area: the zone on the other side) is still closed
        if (isdefined(s.script_noteworthy) && s.script_noteworthy == "debris_1000" && !isdefined(door) && isdefined(level.spawn_volume_array[s.script_area])
            && !scripts\engine\utility::is_true(level.spawn_volume_array[s.script_area].active))
            door = s;
    }
    if (isdefined(door))
    {
        scripts\cp\zombies\interaction_openareas::clear_debris(door, player);
        wait 2;
        active = isdefined(level.spawn_volume_array[door.script_area]) && scripts\engine\utility::is_true(level.spawn_volume_array[door.script_area].active);
        print("[IWZ game] DOOR area=" + door.script_area + " area_active=" + active + " generator_active=" + active);
    }
    else
        print("[IWZ game] DOOR missing");

    // 4. power: the stock generator interaction
    generator = undefined;
    foreach (s in level.all_interaction_structs)
    {
        if (isdefined(s.script_noteworthy) && s.script_noteworthy == "generator")
            generator = s;
    }
    if (isdefined(generator))
    {
        player setorigin(generator.origin + anglestoforward(generator.angles) * 48 + (0, 0, -40));
        wait 1;
        generator thread scripts\cp\zombies\zombie_power::generic_generator(generator, player);
        wait 6;
        powered = 0;
        foreach (s in level.all_interaction_structs)
        {
            if (isdefined(s.script_noteworthy) && issubstr(s.script_noteworthy, "perk_machine") && scripts\engine\utility::is_true(s.powered_on))
                powered++;
        }
        print("[IWZ game] POWER powered_perks=" + powered);
    }
    else
        print("[IWZ game] POWER missing");

    // 4b. Rat-a-tat (QA item 12): stock perk activation on its machine struct, then the stock ownership test
    player scripts\cp\cp_persistence::set_player_currency(5000);
    foreach (s in level.all_interaction_structs)
    {
        if (isdefined(s.script_noteworthy) && s.script_noteworthy == "perk_machine_rat_a_tat")
        {
            before = player scripts\cp\cp_persistence::get_player_currency();
            [[ level.interactions["perk_machine_rat_a_tat"].activation_func ]](s, player);
            // the perk is granted after the drinking animation
            for (t = 0; t < 40 && !(player scripts\cp\utility::has_zombie_perk("perk_machine_rat_a_tat")); t++)
                wait 0.25;
            print("[IWZ game] RATATAT paid=" + (before - player scripts\cp\cp_persistence::get_player_currency()) + " has=" + player scripts\cp\utility::has_zombie_perk("perk_machine_rat_a_tat"));
        }
    }

    // 4c. magic wheel: spin on the active wheel (stock trigger), then take the weapon
    w = level.current_active_wheel;
    if (isdefined(w))
    {
        player scripts\cp\cp_persistence::set_player_currency(5000);
        before = player scripts\cp\cp_persistence::get_player_currency();
        wb = player getweaponslistprimaries();
        player setorigin(w.origin + anglestoforward(w.angles) * 50 + (0, 0, 1));
        wait 0.5;
        w notify("trigger", player);
        // stock spin: 5 s rotation, then the won weapon (script_weapon w.weapon at the wheel_fx_spot) is made usable
        // for the spinning player; taking it is a Use on that weapon entity
        wait 6.5;
        spot = "none";
        if (isdefined(w.weapon))
            spot = "" + w.weapon.origin;
        print("[IWZ game] WHEELSPIN weapon_ent=" + isdefined(w.weapon) + " at=" + spot);
        if (isdefined(w.weapon))
        {
            player setorigin(w.weapon.origin + anglestoforward(w.angles) * 40 - (0, 0, 50));
            wait 0.3;
            w.weapon notify("trigger", player);
        }
        wait 2;
        wa = player getweaponslistprimaries();
        got = "";
        foreach (x in wa)
        {
            if (!scripts\engine\utility::array_contains(wb, x))
                got += x + " ";
        }
        print("[IWZ game] WHEEL paid=" + (before - player scripts\cp\cp_persistence::get_player_currency()) + " new_weapons=" + got + " current=" + player getcurrentweapon());
    }
    else
        print("[IWZ game] WHEEL no_active_wheel");

    // 4d. stairs: a zombie spawned at the bottom of each stair must climb to a player at the top
    iwz_stair_climb(player, "stair_a", (-600, 2470, -310), (-600, 3140, 0));
    iwz_stair_climb(player, "stair_b", (-1980, 3250, -380), (-1300, 3250, 0));

    // 5. PaP quest: the three relays (stock trigger notify; the 2 s Use hold is simulated by paris_iwz_autouse)
    for (i = 1; i <= 3; i++)
    {
        r = scripts\engine\utility::getstruct("iwz_relay_" + i, "targetname");
        if (!isdefined(r) || !isdefined(r.use))
        {
            print("[IWZ game] QUEST relay_missing i=" + i);
            continue;
        }
        player setorigin(r.origin + anglestoforward(r.angles) * 40);
        wait 0.5;
        r.use notify("trigger", player);
        wait 0.5;
    }
    wait 4;
    print("[IWZ game] QUEST relays_on=" + level.iwz_relays_on + " pap_open=" + isdefined(level.iwz_pap_open));
    a = (3104, 3960, -290);
    b = (3104, 4060, -290);
    got = playerphysicstrace(a, b);
    print("[IWZ game] SHUTTER passable=" + (distance(got, b) < 2) + " stopped=" + got);

    // 6. Third Rail trap: money, trigger, zombies moved into the pit must die
    player scripts\cp\cp_persistence::set_player_currency(5000);
    money = player scripts\cp\cp_persistence::get_player_currency();
    fb = scripts\engine\utility::getstruct("iwz_trap_third_rail_fusebox", "targetname");
    if (isdefined(fb) && isdefined(level.iwz_trap_use))
    {
        player setorigin(fb.origin + anglestoforward(fb.angles) * 48);
        wait 0.5;
        level.iwz_trap_use notify("trigger", player);
        wait 1;
        moved = 0;
        if (isdefined(level.spawned_enemies))
        {
            foreach (zombie in level.spawned_enemies)
            {
                if (isdefined(zombie) && isalive(zombie) && moved < 4)
                {
                    zombie setorigin((-1500 + moved * 300, 1300, -380));
                    moved++;
                }
            }
        }
        wait 3;
        alive = 0;
        foreach (zombie in level.spawned_enemies)
        {
            if (isdefined(zombie) && isalive(zombie) && zombie.origin[1] < 1600 && zombie.origin[2] < -350)
                alive++;
        }
        print("[IWZ game] TRAP money_before=" + money + " money_after=" + (player scripts\cp\cp_persistence::get_player_currency()) + " moved=" + moved + " alive_in_pit=" + alive);
    }
    else
        print("[IWZ game] TRAP missing");

    views = strtok(getdvar("paris_iwz_views"), ";");
    for (i = 0; i < views.size; i++)
    {
        v = strtok(views[i], ",");
        player setorigin((float(v[0]), float(v[1]), float(v[2])));
        player setplayerangles((float(v[4]), float(v[3]), 0));
        wait 2.5;
        iwz_capture(player, i + 1);
    }
    print("[IWZ game] DONE wave=" + level.wave_num + " zombies=" + level.spawned_enemies.size);
    print("[IWZ local] DONE");
}

iwz_nearest(player)
{
    best = 999999;
    if (!isdefined(level.spawned_enemies))
        return best;
    foreach (zombie in level.spawned_enemies)
    {
        if (isdefined(zombie) && isalive(zombie))
        {
            d = distance(zombie.origin, player.origin);
            if (d < best)
                best = int(d);
        }
    }
    return best;
}

iwz_capture(player, i)
{
    executecommand("capture_frame iwzgame" + i);
    wait 1;
    print("[IWZ game] FRAME i=" + i + " origin=" + player.origin);
}

// stair climb: the zone's spawner nearest the stair bottom spawns one zombie (stock spawn_wave_enemy); the player waits
// at the top; prints the closest approach and whether it got within 120 units within 35 s
iwz_stair_climb(player, zone, bottom, top)
{
    best = undefined;
    foreach (s in scripts\engine\utility::getstructarray(zone + "_spawner", "targetname"))
    {
        if (!isdefined(best) || distance(s.origin, bottom) < distance(best.origin, bottom))
            best = s;
    }
    if (!isdefined(best))
    {
        print("[IWZ game] STAIR " + zone + " no_spawner");
        return;
    }
    scripts\cp\zombies\zombies_spawning::activate_volume_by_name(zone);
    player setorigin(top);
    player.ignoreme = 0;
    wait 0.5;
    z = best scripts\cp\zombies\zombies_spawning::spawn_wave_enemy("generic_zombie", 1);
    if (!isdefined(z))
    {
        print("[IWZ game] STAIR " + zone + " spawn_failed spawner=" + best.origin);
        return;
    }
    start = z.origin;
    nearest = 99999;
    t0 = gettime();
    reached = 0;
    trail = "";
    tick = 0;
    while (gettime() - t0 < 35000 && isdefined(z) && isalive(z))
    {
        player.health = player.maxhealth;
        if (tick % 2 == 0)
            trail = trail + int(z.origin[0]) + "," + int(z.origin[1]) + "," + int(z.origin[2]) + " ";
        tick++;
        d = distance(z.origin, player.origin);
        if (d < nearest)
            nearest = int(d);
        if (d < 120)
        {
            reached = 1;
            break;
        }
        wait 0.5;
    }
    zend = (0, 0, 0);
    if (isdefined(z))
        zend = z.origin;
    print("[IWZ game] STAIRTRAIL " + zone + " " + trail);
    print("[IWZ game] STAIR " + zone + " reached=" + reached + " nearest=" + nearest + " seconds=" + int((gettime() - t0) / 1000) + " start=" + start + " end=" + zend);
    if (isdefined(z) && isalive(z))
        z dodamage(z.health + 1000, z.origin);
}
