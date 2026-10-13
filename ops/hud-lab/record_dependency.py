"""Record one observed missing PAK after confirmed owned-tool restoration. No launch."""
import argparse
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent


def record(run):
    run = Path(run).resolve()
    state = json.loads((run / 'state.local.json').read_text(encoding='utf-8-sig'))
    if not (state['Restored'] and state['StockPreserved'] and
            state['RestorationStatus'] == 'Confirmed' and not state['RetainedLeaseToken']):
        raise ValueError('Refuse dependency update before confirmed restoration/release')
    reports = list(run.glob('hud-offline-*.stall.json'))
    if len(reports) != 1:
        raise ValueError('Require one exact offline diagnostic')
    report = json.loads(reports[0].read_text(encoding='utf-8-sig'))
    if (not report['FatalDialogObserved'] or report['Phase'] != 'hud-offline' or
            report['Identity']['SHA256'] != state['ToolSHA256'] or
            state['ToolSource'] != 'fab935826c898806855376662a8a03317b3ad8f1'):
        raise ValueError('Missing owned-tool fatal correlation')
    dialog = Path(report['Dialog'])
    if dialog.resolve().parent != run:
        raise ValueError('Dialog evidence outside exact run')
    text = dialog.read_text()
    match = re.search(r'^Could not find asset file (assetfile[1-9][0-9]*\.pak)\r?$', text, re.M)
    if not match:
        raise ValueError('No exact missing PAK diagnostic')
    path = 'zone/' + match[1]
    manifest_path = HERE / 'bootstrap-dependencies.json'
    manifest = json.loads(manifest_path.read_text())
    if any(d['relative'] == path for d in manifest['dependencies']):
        raise ValueError('Already staged dependency failed; investigate path/integrity instead')
    manifest['dependencies'].append({'relative': path, 'phase': 'cp_zmb',
                                     'observed_run': run.name, 'fatal_message': match[0].strip()})
    manifest['failures'].append({'run': run.name, 'kind': 'missing-' + match[1],
                                'restored': True, 'inventory_verified': False})
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    return path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True)
    print(record(parser.parse_args().run))
