from pathlib import Path
import tempfile
import unittest

from sv_terminal_worker.adapters.local.file_run_store import FileRunStore
from sv_terminal_worker.adapters.local.fixture_event_queue import FixtureEventQueue
from sv_terminal_worker.adapters.local.fixture_issue_repository import FixtureIssueRepository
from sv_terminal_worker.application.run_worker import WorkerConfig, poll_loop, run_action


ISSUE_FIXTURE = Path("fixtures/issues/approved_rule_change.json")
EVENT_FIXTURE = Path("fixtures/events/approved_proposal_event.json")


class WorkerUsecaseTests(unittest.TestCase):
    def test_run_action_builds_context_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            issues = FixtureIssueRepository(ISSUE_FIXTURE)
            runs = FileRunStore(Path(tmp))

            result = run_action("BAA-1234", "act_20260605_001", issues, runs)
            duplicate = run_action("BAA-1234", "act_20260605_001", issues, runs)

            self.assertEqual(result.status, "context_built")
            self.assertTrue(Path(result.context_path).exists())
            self.assertEqual(duplicate.status, "skipped")
            self.assertEqual(len(issues.writes), 1)

    def test_poll_loop_processes_fixture_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            queue = FixtureEventQueue(EVENT_FIXTURE)
            issues = FixtureIssueRepository(ISSUE_FIXTURE)
            runs = FileRunStore(Path(tmp))

            results = poll_loop(queue, issues, runs, WorkerConfig(once=True))

            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].status, "context_built")
            self.assertIn("evt_20260605_approved_proposal", queue.statuses)
            self.assertTrue(queue.statuses["evt_20260605_approved_proposal"].startswith("processed:"))


if __name__ == "__main__":
    unittest.main()
