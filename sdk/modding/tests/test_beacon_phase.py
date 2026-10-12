import io
import sys
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from beacon_tool_phase import copy_bounded, command


class BoundedPhaseTests(unittest.TestCase):
    def test_exact_boundary_and_overflow(self):
        for length in (0, 31, 32, 33, 8192):
            with self.subTest(length=length):
                output = io.BytesIO()
                exceeded = threading.Event()
                count = copy_bounded(io.BytesIO(b"x" * length), output, exceeded, 32)
                self.assertEqual(count, min(length, 32))
                self.assertEqual(len(output.getvalue()), min(length, 32))
                self.assertEqual(exceeded.is_set(), length > 32)

    def test_pipe_or_disk_failure_is_not_success(self):
        class Broken:
            def write(self, block):
                raise OSError("disk fixture")
        exceeded = threading.Event()
        copy_bounded(io.BytesIO(b"data"), Broken(), exceeded, 32)
        self.assertTrue(exceeded.is_set())

    def test_arguments_use_new_zone_and_no_shell(self):
        for phase, verb in (("build", "-buildzone"), ("verify", "-verifyzone"), ("dump", "-dumpzone")):
            self.assertEqual(command(phase, "tool.exe", "work", "dump"),
                             ["tool.exe", "-headless", "-unbuffered-io", "-strict-content-sources", verb, "sdk_beacon"])
        self.assertEqual(command("read", "reader.exe", "work", "original dump"),
                         ["reader.exe", "--verify-existing", "original dump"])


if __name__ == "__main__":
    unittest.main()
