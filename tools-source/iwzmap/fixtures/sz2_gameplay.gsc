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

    // 3. door: the stock purchase path of the first debris struct
    door = undefined;
    foreach (s in level.all_interaction_structs)
    {
        // a debris door whose zone (script_area: the zone on the other side) is still closed
        if (isdefined(s.script_noteworthy) && s.script_noteworthy == "debris_750" && !isdefined(door) && isdefined(level.spawn_volume_array[s.script_area])
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
