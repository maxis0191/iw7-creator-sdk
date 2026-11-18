"""Stage cache of the map chain: keys follow inputs, entries are stored and restored whole."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import stage_cache as sc  # noqa: E402


class StageCacheTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.environ['IW7_BUILD_CACHE'] = os.path.join(self.tmp, 'cache')
        self.src = os.path.join(self.tmp, 'src')
        os.makedirs(self.src)
        for n, t in (('world.bin', 'w1'), ('entities.txt', 'e1'), ('lighting.txt', 'l1')):
            with open(os.path.join(self.src, n), 'w') as f:
                f.write(t)

    def tearDown(self):
        os.environ.pop('IW7_BUILD_CACHE', None)

    def write(self, name, text):
        with open(os.path.join(self.src, name), 'w') as f:
            f.write(text)

    def bake_key(self):
        return sc.make_key([os.path.join(self.src, 'world.bin'), os.path.join(self.src, 'lighting.txt')], [], ['rays=256'])

    def test_bake_key_ignores_entities_but_not_the_world(self):
        k = self.bake_key()
        self.write('entities.txt', 'e2')
        self.assertEqual(k, self.bake_key(), 'an entity change must not bake again')
        self.write('world.bin', 'w2')
        self.assertNotEqual(k, self.bake_key(), 'a world change must bake again')

    def test_compile_key_follows_every_file_and_the_skip_list(self):
        k = sc.make_key([], [(self.src, {'noise.log'})], [])
        self.write('noise.log', 'x')
        self.assertEqual(k, sc.make_key([], [(self.src, {'noise.log'})], []))
        self.write('entities.txt', 'e9')
        self.assertNotEqual(k, sc.make_key([], [(self.src, {'noise.log'})], []))

    def test_store_restore_replaces_destination_and_misses_are_false(self):
        key = self.bake_key()
        self.assertFalse(sc.restore('bake', key, os.path.join(self.tmp, 'out')))
        sc.save('bake', key, self.src, {'note': 'n'})
        out = os.path.join(self.tmp, 'out')
        os.makedirs(out)
        with open(os.path.join(out, 'stale.txt'), 'w') as f:
            f.write('old')
        self.assertTrue(sc.restore('bake', key, out))
        self.assertTrue(os.path.isfile(os.path.join(out, 'world.bin')))
        self.assertFalse(os.path.exists(os.path.join(out, 'stale.txt')), 'the destination is replaced, not merged')

    def test_prune_keeps_the_most_recently_used(self):
        for i, key in enumerate(('a' * 64, 'b' * 64)):
            sc.save('bake', key, self.src, {})
            stamp = os.path.join(sc.stage_dir('bake', key), 'used.stamp')
            with open(stamp, 'w') as f:
                f.write('x')
            os.utime(stamp, (1000 + i * 100000, 1000 + i * 100000))
        size = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(sc.stage_dir('bake', 'b' * 64)) for f in fs)
        sc.prune('bake', (size + 10) / (1 << 30))
        self.assertTrue(os.path.isdir(sc.stage_dir('bake', 'b' * 64)))
        self.assertFalse(os.path.isdir(sc.stage_dir('bake', 'a' * 64)))


if __name__ == '__main__':
    unittest.main()
