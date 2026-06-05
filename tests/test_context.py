from pathlib import Path
import tempfile
import unittest

from sv_terminal_worker.agent_input import render_agent_input
from sv_terminal_worker.context import build_context_packet, detect_approved_proposal, load_issue_fixture, write_run_files


FIXTURE = Path("fixtures/issues/approved_rule_change.json")


class ContextTests(unittest.TestCase):
    def test_build_context_from_fixture(self):
        issue_data = load_issue_fixture(FIXTURE)
        action = detect_approved_proposal(issue_data)

        self.assertIsNotNone(action)
        context = build_context_packet(issue_data, action)

        self.assertEqual(context["issue"]["identifier"], "BAA-1234")
        self.assertEqual(context["approval"]["action_id"], "act_20260605_001")
        self.assertEqual(context["proposal"]["target"], "proposal:v1")
        self.assertTrue(context["sources"]["synced_slack_thread"]["available"])

    def test_write_run_files_and_render_agent_input(self):
        issue_data = load_issue_fixture(FIXTURE)
        action = detect_approved_proposal(issue_data)
        context = build_context_packet(issue_data, action)

        with tempfile.TemporaryDirectory() as tmp:
            paths = write_run_files(Path(tmp), context)
            self.assertTrue(paths["context"].exists())
            self.assertTrue(paths["state"].exists())

        agent_input = render_agent_input(context)
        self.assertIn("References BAA-1234", agent_input)
        self.assertIn("Do not use closing magic words.", agent_input)


if __name__ == "__main__":
    unittest.main()
