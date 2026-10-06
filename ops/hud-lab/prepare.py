"""Stage original source only. Never invokes ZoneTool, installs or deploys assets."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat

HERE = Path(__file__).resolve().parent
LUA = "ui_scripts/paris_lab_hud/__init__.lua"
ZONE = "paris_lab_hud"


def no_links(path):
    for ancestor in (path, *path.parents):
        if ancestor.exists() or ancestor.is_symlink():
            info = ancestor.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
                raise ValueError('Linked output or ancestor refused')


def prepare(output):
    output = Path(os.path.abspath(output))
    no_links(output)
    if output.exists():
        raise ValueError('Fresh output directory required; existing files are never replaced')
    lua = (HERE / LUA).read_bytes()
    csv = (HERE / (ZONE + '.csv')).read_bytes()
    template = json.loads((HERE / 'package.plan.json').read_text(encoding='utf-8'))
    digest = hashlib.sha256(lua).hexdigest()
    if template['closure']['nodes'][0]['sha256'] != digest:
        raise ValueError('Tracked source differs from package plan; update the plan explicitly')
    output.mkdir(parents=True)
    targets = {'zonetool/' + ZONE + '/' + LUA: lua, 'zone_source/' + ZONE + '.csv': csv}
    provenance = {'schema': 'iw7.hud-source/1', 'zone': ZONE, 'built': False, 'deployed': False,
                  'source_files': []}
    for relative, payload in targets.items():
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
        provenance['source_files'].append({'path': relative, 'bytes': len(payload),
                                          'sha256': hashlib.sha256(payload).hexdigest()})
    (output / 'package.plan.json').write_text(json.dumps(template, indent=2) + '\n', encoding='utf-8')
    (output / 'source-provenance.json').write_text(json.dumps(provenance, indent=2) + '\n', encoding='utf-8')
    return provenance


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.output), indent=2))
