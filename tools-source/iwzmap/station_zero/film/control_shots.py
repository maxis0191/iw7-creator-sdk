r"""control_shots: one live session of a document: power on, frames, then console-command variants in the SAME session (worker C1, 28 Nov 2026).

    python control_shots.py <folder> <doc> --cams a,b [--cmd name="set r_ssao MDAO"] [--cmd ...] [--settle-s 10] [--clean-after]

<folder>/base/<cam>.png first (as the session starts: the client's own settings), then for each --cmd: the console command is executed in the
game (`hud studio_cmd <command>`: the live script's executecommand, studio/live.py CMD_OP), 3 s, and <folder>/<name>/<cam>.png. The commands
run in order and are NOT undone between variants (write an explicit undo variant). The session is stopped at the end; --clean-after removes the
document's live and work folders and its build server (light_measure.clean_doc). Writes <folder>/shots.json (every answer).
Environment as light_measure.shoot: STUDIO_ROOT, STUDIO_CONFIG, IWZ_SDK, IWZ_ZONETOOL_EXE.
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.environ.get('STUDIO_ROOT', r'C:\studio'))
import light_measure as LM  # noqa: E402


def shots(sub, doc, cams, log, key):
    os.makedirs(sub, exist_ok=True)
    for c in cams:
        r = LM.studio('live', 'shot', doc, '--clean', '--camera', c, '--out', os.path.join(sub, c + '.png'))
        log['%s_%s' % (key, c)] = {x: r.get(x) for x in ('ok', 'settled', 'error', 'stale', 'stderr', 'camera_ack', 'pose')}


def main(argv):
    folder, doc = argv[0], argv[1]
    opt = {'--cams': None, '--settle-s': '10'}
    cmds, clean_after = [], False
    i = 2
    while i < len(argv):
        if argv[i] == '--cmd':
            name, cmd = argv[i + 1].split('=', 1)
            cmds.append((name, cmd))
            i += 2
        elif argv[i] == '--clean-after':
            clean_after = True
            i += 1
        else:
            opt[argv[i]] = argv[i + 1]
            i += 2
    cams = opt['--cams'].split(',')
    os.makedirs(folder, exist_ok=True)
    log = {'doc': doc, 'cams': cams, 'cmds': cmds, 't0': time.time()}
    t = time.time()
    log['start'] = LM.studio('live', 'start', doc, '--idle-min', '30')
    log['start_s'] = round(time.time() - t, 1)
    try:
        if not (log['start'] or {}).get('ok'):
            log['aborted'] = 'start failed'
            return
        LM._keep_compile_log(folder)
        log['power'] = LM.studio('live', 'power', doc, 'on')
        if not log['power'].get('ok'):
            log['aborted'] = 'power failed'
            return
        time.sleep(float(opt['--settle-s']))
        shots(os.path.join(folder, 'base'), doc, cams, log, 'base')
        if cmds:
            from studio import live as LV
            link = LV.attach(doc)
            for name, cmd in cmds:
                log['cmd_' + name] = link.send(['hud %s %s' % (LV.CMD_OP, cmd)], timeout=5.0)
                time.sleep(3.0)
                shots(os.path.join(folder, name), doc, cams, log, name)
    finally:
        log['stop'] = LM.studio('live', 'stop', doc)
        if clean_after:
            log['cleaned'] = LM.clean_doc(doc)
        log['t1'] = time.time()
        json.dump(log, open(os.path.join(folder, 'shots.json'), 'w', encoding='utf-8'), indent=1, default=str)
        bad = [k for k, v in log.items() if isinstance(v, dict) and 'settled' in v and (not v.get('ok') or v.get('stale'))]
        print(json.dumps({'folder': folder, 'start_ok': (log.get('start') or {}).get('ok'), 'start_s': log.get('start_s'), 'aborted': log.get('aborted'),
                          'failed_or_stale': bad, 'seconds': round(log['t1'] - log['t0'])}, indent=1))


if __name__ == '__main__':
    main(sys.argv[1:])
