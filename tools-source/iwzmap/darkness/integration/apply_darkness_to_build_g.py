"""Darkness integration for the level builder's level\\tools\\build-g.ps1 (darkness agent, 2026-11-10).

Writes a patched copy (default: <input> -> <input>.darkness.ps1) that adds:
  -Darkness            IWZ_DARK=1 generator, dark split of the layout lights (dark_build.py: emergency bake, named
                       power lights, corridor fill), the dark bake list, the flashlight effects, build-sz2 -Darkness
                       with the dark / lit vision args, and the darkness zonetool (named scriptable lights);
  -DarkZoneFill        the lit-state fill (default: the Station Zero corridor zones);
  -DarkZoneTool        the zonetool with named scriptable lights (x64-zt codex/iwzmap-darkness, door-brushmodels
                       1a8323f merged).
Prerequisite: the SDK worktree used as $S carries codex/iwzmap-darkness (darkness\\ tools, build-sz2 -Darkness,
the IWZ_DARK generator hooks); that branch contains codex/iwzmap-station-zero-v2.

usage: python apply_darkness_to_build_g.py <build-g.ps1> [<out.ps1>]
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def snip(name):
    return open(os.path.join(HERE, name), encoding='utf-8').read()


def insert_after(s, anchor, text):
    if s.count(anchor) != 1:
        raise SystemExit('anchor not found exactly once: %r' % anchor[:70])
    i = s.index(anchor) + len(anchor)
    return s[:i] + text + s[i:]


def insert_before(s, anchor, text):
    if s.count(anchor) != 1:
        raise SystemExit('anchor not found exactly once: %r' % anchor[:70])
    i = s.index(anchor)
    return s[:i] + text + s[i:]


def main():
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else src[:-4] + '.darkness.ps1'
    s = open(src, encoding='utf-8-sig', newline='').read()
    nl = '\r\n' if '\r\n' in s else '\n'
    s = s.replace('\r\n', '\n')
    # 1. parameters
    head_end = s.index(')\n')
    s = s[:head_end] + snip('params.ps1.txt').rstrip('\n') + s[head_end:]
    # 2. generator: IWZ_DARK before the first generator call
    s = insert_before(s, 'python -I "$S\\station_zero2.py" "$D\\cp_zmb" $src | Select-Object -Last 1\nif(-not $SkipPick){',
                      snip('generator.ps1.txt'))
    # 3. dark split after the gates (before the bake / bake reuse): rewrites lights.txt with the named power lights
    s = insert_after(s, 'if($GateOnly){ Write-Output "gate-only: $src"; return }\n', snip('darksplit.ps1.txt'))
    # 4. the bake bakes the dark list
    s = insert_after(s, "  & $PY -I \"$B\\layout_lights.py\" $src $lj @($LightArgs -split ' ' | Where-Object { $_ })\n",
                     "  if($Darkness){ $lj=$DarkLights }     # darkness: emergency lights + cue glows only\n")
    # 5. flashlight effects, dark / lit visions and the zonetool before the final build-sz2 call
    s = insert_before(s, '& "$S\\build-sz2.ps1" -Src $build -UmOut $um -ZoneToolExe $Z -KeepSubmodels @A\n',
                      snip('effects.ps1.txt'))
    open(out, 'w', encoding='utf-8', newline='').write(s.replace('\n', nl))
    print('wrote', out)


if __name__ == '__main__':
    main()
