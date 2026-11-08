"""Minimal stdio MCP client for GrayWolf (BO3 asset exporter), stdlib only.

    python graywolf_mcp.py list
    python graywolf_mcp.py call <tool> '<json arguments>'          (an image result is saved to $GW_IMAGE_OUT)
    python graywolf_mcp.py station-zero <bo3 install> <out dir>    (the Station Zero easter-egg sources)

GrayWolf writes under %LOCALAPPDATA%\\GrayWolf\\mcp\\<out_name>\\bo3 and those folders can vanish later:
station-zero copies every export into <out dir> at once. Set GRAYWOLF_EXE to override the executable.
"""
import base64
import json
import os
import shutil
import subprocess
import sys

EXE = os.environ.get('GRAYWOLF_EXE', r'C:\Users\ezvalo\Documents\IW7-Runtime\tools\graywolf-0.8.0\GrayWolf.exe')

# Station Zero easter egg, from the BO3 data (zone, filter) -> sounds/models used by the map
STATION_ZERO = [
    # Abracadavre (BO1 Ascension) as BO3 Chronicles ships it: alias mus_abracadavre_intro / mus_egg
    ('iwz-audio-cosmo', {'zones': ['zm_cosmodrome'], 'kinds': ['sound'], 'name_filter': ['abracadavre'],
                         'audio_format': 'flac', 'sound_aliases': True}),
    # hidden-song hint loop and activation (zm_common zmb_egg_loop / zmb_egg_activate)
    ('iwz-audio-common-egg', {'zones': ['zm_common'], 'kinds': ['sound'], 'name_filter': ['meteor_affirm', 'meteor_loop'],
                              'audio_format': 'flac'}),
    # Chronicles song-struct aliases zmb_ee_mus_lp / zmb_ee_mus_activate (alias table of the patch zone)
    ('iwz-audio-cosmo-patch', {'zones': ['zm_cosmodrome_patch'], 'kinds': ['sound'], 'audio_format': 'flac',
                               'sound_aliases': True}),
    # the BO3 teddy bear (zm_levelcommon is the smallest zone holding it)
    ('iwz-teddy', {'zones': ['zm_levelcommon'], 'assets': ['model:p7_zm_teddybear'], 'image_format': 'png',
                   'model_format': ['cast']}),
]


class Client:
    def __init__(self):
        self.p = subprocess.Popen([EXE, 'mcp'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                  cwd=os.path.dirname(EXE))
        self.next_id = 1
        self.request('initialize', {'protocolVersion': '2024-11-05', 'capabilities': {},
                                    'clientInfo': {'name': 'iwz-audio', 'version': '1'}})
        self.send({'jsonrpc': '2.0', 'method': 'notifications/initialized'})

    def send(self, obj):
        self.p.stdin.write((json.dumps(obj) + '\n').encode())
        self.p.stdin.flush()

    def request(self, method, params):
        rid = self.next_id
        self.next_id += 1
        self.send({'jsonrpc': '2.0', 'id': rid, 'method': method, 'params': params})
        while True:
            line = self.p.stdout.readline()
            if not line:
                raise SystemExit('graywolf closed the connection')
            msg = json.loads(line)
            if msg.get('id') == rid:
                if 'error' in msg:
                    raise SystemExit(json.dumps(msg['error']))
                return msg['result']

    def call(self, tool, args):
        res = self.request('tools/call', {'name': tool, 'arguments': args})
        texts, images = [], []
        for c in res.get('content', []):
            if c.get('type') == 'text':
                texts.append(c['text'])
            elif c.get('type') == 'image':
                images.append(base64.b64decode(c['data']))
        return texts, images

    def close(self):
        self.p.stdin.close()
        self.p.terminate()


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    c = Client()
    try:
        if argv[0] == 'list':
            for t in c.request('tools/list', {})['tools']:
                print('==', t['name'])
                print(t.get('description', ''))
        elif argv[0] == 'call':
            texts, images = c.call(argv[1], json.loads(argv[2]) if len(argv) > 2 else {})
            for t in texts:
                print(t)
            for i, img in enumerate(images):
                out = os.environ.get('GW_IMAGE_OUT', 'preview%d.png' % i)
                with open(out, 'wb') as f:
                    f.write(img)
                print('image ->', out)
        elif argv[0] == 'station-zero':
            install, out = argv[1], argv[2]
            os.makedirs(out, exist_ok=True)
            for name, args in STATION_ZERO:
                texts, _ = c.call('graywolf_export', dict(args, install=install, out_name=name, wait=True))
                result = json.loads(texts[0])
                if result.get('state') != 'done' or result.get('failures'):
                    raise SystemExit('%s: %s' % (name, texts[0]))
                dest = os.path.join(out, name)
                if os.path.isdir(dest):
                    shutil.rmtree(dest)
                shutil.copytree(result['out'], dest)
                print('%s: %d files, %d bytes -> %s' % (name, result['files'], result['bytes'], dest))
        else:
            print(__doc__)
            return 2
    finally:
        c.close()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
