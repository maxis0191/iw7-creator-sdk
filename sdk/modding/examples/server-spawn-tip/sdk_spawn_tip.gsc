// Original editable server-only example. Candidate source, runtime unverified.
// Opt in with sdk_spawn_tip_enable=1 on an authorized test dedicated.
init()
{
    if (!getdvarint("dedicated") || !getdvarint("sdk_spawn_tip_enable") ||
        getdvar("mapname") != "cp_zmb") return;
    if (isdefined(level.sdk_spawn_tip_started)) return;
    level.sdk_spawn_tip_started = true;
    level thread connections();
}

connections()
{
    level endon("game_ended");
    for (;;)
    {
        level waittill("connected", player);
        if (isdefined(player)) player thread first_spawn_tip();
    }
}

first_spawn_tip()
{
    self endon("disconnect");
    level endon("game_ended");
    self waittill("spawned_player");
    wait 5;
    // Edit this English message for your server, then requalify the new source.
    self iprintln("Team tip: keep an escape route open before you start firing.");
}
