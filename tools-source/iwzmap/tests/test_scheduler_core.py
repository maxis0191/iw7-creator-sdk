"""scheduler.ps1: where the map tools find the resource scheduler core, and the guard that refuses an old one.

The guard reads the core's text only. These tests give it synthetic cores in a temp folder (and, inside a composed
workspace, the real pinned core); nothing here dot-sources a core, takes a lease or touches the scheduler's state.
"""
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

IWZMAP = Path(__file__).resolve().parents[1]
ROOT = IWZMAP.parents[1]
SCRIPT = IWZMAP / 'scheduler.ps1'

OLD = 'function Enter-IW7ResourceLease { }\nfunction Exit-IW7ResourceLease { }\n'
QUEUE_ONLY = OLD + 'function Assert-IW7QueueTurn { }\n'
NEW = QUEUE_ONLY + '    function Test-IW7TicketCanFit { }\n'
# a core that only names the functions in a comment or a call is still old
MENTION = OLD + '# Assert-IW7QueueTurn and Test-IW7TicketCanFit come later\nAssert-IW7QueueTurn\n'


def run(script, *args, env_extra=None):
    env = {k: v for k, v in os.environ.items() if k not in ('IW7_RESOURCE_SCHEDULER', 'IWZ_COMPONENTS')}
    env.update(env_extra or {})
    return subprocess.run(['pwsh', '-NoLogo', '-NoProfile', '-NonInteractive', '-File', str(script), *args],
                          capture_output=True, text=True, env=env, timeout=120)


class SchedulerCoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def core(self, name, text):
        path = self.tmp / name
        path.write_text(text, encoding='utf-8')
        return path

    def test_old_core_is_refused(self):
        r = run(SCRIPT, str(self.core('old.ps1', OLD)))
        self.assertNotEqual(r.returncode, 0)
        err = ' '.join(r.stderr.split())
        self.assertIn('Refused', err)
        self.assertIn('waiting order', err)
        self.assertIn('fit rule', err)
        self.assertIn('old.ps1', err)
        self.assertEqual(r.stdout.strip(), '')

    def test_waiting_order_without_fit_rule_is_refused(self):
        r = run(SCRIPT, str(self.core('queue.ps1', QUEUE_ONLY)))
        self.assertNotEqual(r.returncode, 0)
        err = ' '.join(r.stderr.split())
        self.assertIn('Test-IW7TicketCanFit', err)
        self.assertNotIn('(Assert-IW7QueueTurn)', err)

    def test_mention_is_not_a_definition(self):
        self.assertNotEqual(run(SCRIPT, str(self.core('mention.ps1', MENTION))).returncode, 0)

    def test_new_core_is_accepted(self):
        path = self.core('new.ps1', NEW)
        r = run(SCRIPT, str(path))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(Path(r.stdout.strip()), path.resolve())

    def test_environment_variables(self):
        path = self.core('new.ps1', NEW)
        r = run(SCRIPT, env_extra={'IW7_RESOURCE_SCHEDULER': str(path)})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(Path(r.stdout.strip()), path.resolve())
        components = self.tmp / 'components'
        (components / 'ops').mkdir(parents=True)
        (components / 'ops' / 'Resource-Scheduler.Core.ps1').write_text(OLD, encoding='utf-8')
        copy = self.tmp / 'tree' / 'tools-source' / 'iwzmap'
        copy.mkdir(parents=True)
        shutil.copy(SCRIPT, copy / 'scheduler.ps1')
        r = run(copy / 'scheduler.ps1', env_extra={'IWZ_COMPONENTS': str(components)})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('IWZ_COMPONENTS', r.stderr)

    def test_no_default_checkout(self):
        copy = self.tmp / 'tree' / 'tools-source' / 'iwzmap'
        copy.mkdir(parents=True)
        shutil.copy(SCRIPT, copy / 'scheduler.ps1')
        r = run(copy / 'scheduler.ps1')
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('No resource scheduler core named', ' '.join(r.stderr.split()))

    def test_prepared_workspace(self):
        copy = self.tmp / 'ws' / 'tools-source' / 'iwzmap'
        copy.mkdir(parents=True)
        shutil.copy(SCRIPT, copy / 'scheduler.ps1')
        (self.tmp / 'ws' / 'source-workspace.json').write_text('{}', encoding='utf-8')
        (self.tmp / 'ws' / 'ops').mkdir()
        core = self.tmp / 'ws' / 'ops' / 'Resource-Scheduler.Core.ps1'
        core.write_text(NEW, encoding='utf-8')
        r = run(copy / 'scheduler.ps1', env_extra={'IWZ_COMPONENTS': str(self.tmp / 'absent')})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(Path(r.stdout.strip()), core.resolve())

    @unittest.skipUnless((ROOT / 'source-workspace.json').exists(), 'only inside a composed workspace')
    def test_pinned_core_of_this_workspace_is_accepted(self):
        r = run(SCRIPT)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(Path(r.stdout.strip()), (ROOT / 'ops' / 'Resource-Scheduler.Core.ps1').resolve())

    def test_every_caller_goes_through_the_guard(self):
        loaders = []
        for path in IWZMAP.rglob('*.ps1'):
            text = path.read_text(encoding='utf-8', errors='replace')
            # a load that skips the guard: the old machine.ps1 lookup, the variable read directly, a bare dot-source
            if path.name not in ('scheduler.ps1', 'machine.ps1') and re.search(
                    r'machine\.ps1"\s*Components|IW7_RESOURCE_SCHEDULER|IWZ_COMPONENTS|^\s*\.\s+\$Scheduler\b', text, re.M):
                loaders.append(path.relative_to(IWZMAP).as_posix())
        self.assertEqual(loaders, [], 'load the core through scheduler.ps1')
        for name in ('zt.ps1', 'build-zt.ps1', 'darkness/build-g-dark.ps1'):
            self.assertIn('scheduler.ps1', (IWZMAP / name).read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
