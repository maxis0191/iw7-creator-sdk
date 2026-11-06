// IWZ asset preview booth (local private session only; staged by the runner as custom_scripts/cp/iwzmap_local.gsc).
// Holds the protected local player at each camera of paris_iwz_cam ("x,y,z,yaw,pitch[,rel]|..."; rel = from the spawn), then for every model of
// paris_iwz_pv0..paris_iwz_pv9 (comma lists of "model:midx:midy:midz:radius" from the catalog): spawns one
// script_model centred in front of the eye at a distance fitted to its size, logs getpointinbounds, captures the frame
// (capture_frame iwzpv<i>) and deletes it. Background frames iwzbg<k> (no model) are taken first, every
// 10 models and last, for the difference mask of preview_analyze.py. One model at a time keeps the snapshot
// entity count low.

init()
{
    if (getdvarint("dedicated") || getdvar("paris_iwz_cam") == "")
        return;
    level.iwz_pv = [];
    for (k = 0; k < 10; k++)
    {
        s = getdvar("paris_iwz_pv" + k);
        if (s == "")
            continue;
        parts = strtok(s, ",");
        foreach (m in parts)
            level.iwz_pv[level.iwz_pv.size] = m;
    }
    precachemodel("tag_origin");
    foreach (m in level.iwz_pv)
        precachemodel(strtok(m, ":")[0]);
    print("[IWZ local] PREVIEW ARMED models=" + level.iwz_pv.size);
    level thread iwz_pv_watch();
}

iwz_pv_watch()
{
    level waittill("connected", player);
    player thread iwz_pv_run();
}

iwz_pv_bg(k)
{
    wait 0.6;
    executecommand("capture_frame iwzbg" + k);
    wait 0.5;
    print("[IWZ local] BG k=" + k + "; t=" + gettime());
}

iwz_pv_run()
{
    self endon("disconnect");
    while (!isalive(self))
        wait 0.2;
    if (isdefined(level.flag) && scripts\engine\utility::flag_exist("introscreen_over"))
        while (!scripts\engine\utility::flag("introscreen_over"))
            wait 0.1;
    wait 3;
    self.ignoreme = 1;
    self takeallweapons();
    spawn_origin = self.origin;
    print("[IWZ local] SPAWNED; origin=" + spawn_origin);
    cams = strtok(getdvar("paris_iwz_cam"), "|");
    anchor = spawn("script_model", spawn_origin);
    anchor setmodel("tag_origin");
    bg = 0;
    for (ci = 0; ci < cams.size; ci++)
    {
        c = strtok(cams[ci], ",");
        cam = (float(c[0]), float(c[1]), float(c[2]));
        if (c.size > 5 && c[5] == "rel")
            cam = spawn_origin + cam;
        yaw = float(c[3]);
        pitch = float(c[4]);
        self unlink();
        anchor.origin = cam;
        anchor.angles = (pitch, yaw, 0);
        self setorigin(cam);
        self setplayerangles((pitch, yaw, 0));
        self playerlinkto(anchor, undefined, 1, 0, 0, 0, 0, 0);
        self freezecontrols(1);
        wait 2;
        self takeallweapons();
        self disableweapons();
        self setplayerangles((pitch, yaw, 0));
        wait 1;
        bg = self iwz_pv_cam(ci, bg);
    }
    print("[IWZ local] DONE");
}

iwz_pv_cam(ci, bg)
{
    eye = self geteye();
    ang = self getplayerangles();
    fwd = anglestoforward(ang);
    print("[IWZ local] PREVIEW CAM ci=" + ci + "; eye=" + eye + "; angles=" + ang + "; fov=" + getdvarfloat("cg_fov") + "; fovscale=" + getdvarfloat("cg_fovScale"));
    fill = getdvarfloat("paris_iwz_fill");
    if (fill <= 0)
        fill = 0.30;
    self iwz_pv_bg(bg);
    bg++;
    for (i = 0; i < level.iwz_pv.size; i++)
    {
        // entry "model:midx:midy:midz:radius" (catalog bounds centre in model space and half diagonal)
        f = strtok(level.iwz_pv[i], ":");
        m = f[0];
        mid = (float(f[1]), float(f[2]), float(f[3]));
        r = float(f[4]);
        n = ci * 1000 + i;
        d = r / fill;
        if (d < r + 24)
            d = r + 24;
        yaw = ang[1] + 150;
        target = eye + fwd * d;
        c = cos(yaw);
        s = sin(yaw);
        e = spawn("script_model", target - (mid[0] * c - mid[1] * s, mid[0] * s + mid[1] * c, mid[2]));
        e.angles = (0, yaw, 0);
        e setmodel(m);
        self takeallweapons();
        self disableweapons();
        wait 1.4;
        lo = e getpointinbounds(-1, -1, -1);
        hi = e getpointinbounds(1, 1, 1);
        executecommand("capture_frame iwzpv" + n);
        wait 0.45;
        print("[IWZ local] PV n=" + n + "; model=" + m + "; origin=" + e.origin + "; angles=" + e.angles + "; lo=" + lo + "; hi=" + hi + "; d=" + d + "; eye=" + self geteye() + "; bg=" + bg);
        e delete();
        if ((i + 1) % 10 == 0 || i == level.iwz_pv.size - 1)
        {
            self iwz_pv_bg(bg);
            bg++;
        }
    }
    return bg;
}
