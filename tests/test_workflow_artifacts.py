import json
from pathlib import Path
import unittest


class WorkflowArtifactTests(unittest.TestCase):
    def test_n8n_workflow_is_sanitized_and_targets_data_table(self):
        path = Path("workflows/n8n/linear-comment-marker-to-event-queue.json")
        workflow = json.loads(path.read_text())

        self.assertNotIn("credentials", workflow)

        raw = json.dumps(workflow)
        self.assertNotIn("api_key", raw.lower())
        self.assertNotIn("secret_", raw.lower())
        self.assertNotIn("LINEAR_WEBHOOK_SECRET", raw)
        self.assertIn("REPLACE_WITH_SV_TERMINAL_EVENTS_TABLE_ID", raw)
        self.assertIn("Issue Comment", raw)

        node_types = {node["type"] for node in workflow["nodes"]}
        self.assertIn("n8n-nodes-base.linearTrigger", node_types)
        self.assertIn("n8n-nodes-base.code", node_types)
        self.assertIn("n8n-nodes-base.dataTable", node_types)
        self.assertNotIn("n8n-nodes-base.webhook", node_types)
        self.assertNotIn("n8n-nodes-base.respondToWebhook", node_types)

        trigger = next(node for node in workflow["nodes"] if node["type"] == "n8n-nodes-base.linearTrigger")
        self.assertEqual(trigger["parameters"]["resources"], ["comment"])
        self.assertNotIn("credentials", trigger)

        data_table = next(node for node in workflow["nodes"] if node["type"] == "n8n-nodes-base.dataTable")
        columns = data_table["parameters"]["columns"]
        self.assertEqual(columns["matchingColumns"], ["dedupe_key"])
        self.assertEqual(columns["value"]["dedupe_key"], "={{ $json.row.dedupe_key }}")
        self.assertEqual(columns["value"]["event_id"], "={{ $json.row.event_id }}")


if __name__ == "__main__":
    unittest.main()
