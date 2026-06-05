import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class CliTests(unittest.TestCase):
    def test_poll_once_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "sv_terminal_worker.cli",
                    "poll",
                    "--once",
                    "--event-source",
                    "fixture",
                    "--issue-source",
                    "fixture",
                    "--run-dir",
                    tmp,
                ],
                check=True,
                text=True,
                capture_output=True,
            )

            payload = json.loads(proc.stdout)
            self.assertEqual(payload[0]["status"], "context_built")

    def test_run_action_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "sv_terminal_worker.cli",
                    "run-action",
                    "--issue",
                    "BAA-1234",
                    "--action-id",
                    "act_20260605_001",
                    "--issue-source",
                    "fixture",
                    "--run-dir",
                    tmp,
                ],
                check=True,
                text=True,
                capture_output=True,
            )

            payload = json.loads(proc.stdout)
            self.assertEqual(payload["status"], "context_built")
            self.assertTrue(Path(payload["context_path"]).exists())


if __name__ == "__main__":
    unittest.main()
