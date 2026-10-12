"""Verify text archive hashes and optionally a clean reconstructed Git tree. Read-only."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent


def git(repository, *args):
    return subprocess.check_output(['git', '-C', str(repository), *args])


def safe_file(relative):
    path = (ROOT / relative).resolve(strict=True)
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError('Archive member outside its root')
    return path


def verify(repository=None):
    manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
    if manifest['schema'] != 'iw7.gsc-tool-source-archive/1':
        raise ValueError('Unknown archive schema')
    members = manifest['patches'] + manifest['licenses']
    for entry in members:
        raw = safe_file(entry['path']).read_bytes()
        if len(raw) != entry['bytes'] or hashlib.sha256(raw).hexdigest() != entry['sha256']:
            raise ValueError('Archive hash/length mismatch: ' + entry['path'])
        raw.decode('utf-8')
        if b'\x00' in raw or b'GIT binary patch' in raw:
            raise ValueError('Text-only archive required')
    if len({entry['path'] for entry in members}) != len(members):
        raise ValueError('Duplicate archive member')
    result = {'archive_hashes_verified': True, 'patches': len(manifest['patches']),
              'git_tree_verified': False, 'commit_id_reproduced': False,
              'binary_reproducibility_verified': False, 'native_executed': False}
    if repository is not None:
        repository = Path(repository).resolve(strict=True)
        if git(repository, 'status', '--porcelain', '--untracked-files=all').strip():
            raise ValueError('Reconstructed repository must be clean')
        subprocess.run(['git', '-C', str(repository), 'merge-base', '--is-ancestor',
                        manifest['base_revision'], 'HEAD'], check=True)
        tree = git(repository, 'rev-parse', 'HEAD^{tree}').decode().strip()
        if tree != manifest['source_tree_oid']:
            raise ValueError('Reconstructed Git tree differs')
        for entry in manifest['changed_source_blobs']:
            blob = git(repository, 'cat-file', 'blob', 'HEAD:' + entry['path'])
            if hashlib.sha256(blob).hexdigest() != entry['sha256']:
                raise ValueError('Reconstructed source blob differs: ' + entry['path'])
        head = git(repository, 'rev-parse', 'HEAD').decode().strip()
        result.update(git_tree_verified=True, reconstructed_revision=head,
                      source_tree_oid=tree, commit_id_reproduced=head == manifest['source_revision'])
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path)
    print(json.dumps(verify(parser.parse_args().repository), indent=2))
