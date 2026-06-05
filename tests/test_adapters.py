import json
import unittest
from unittest.mock import patch

from sv_terminal_worker.adapters.linear.graphql_client import LinearGraphQLClient
from sv_terminal_worker.adapters.linear.webhook_normalizer import normalize_linear_comment_marker, verify_linear_signature
from sv_terminal_worker.adapters.n8n.event_queue import N8nEventQueue


class AdapterTests(unittest.TestCase):
    def test_linear_graphql_request_body(self):
        captured = {}

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return b'{"data":{"ok":true}}'

        def fake_urlopen(request, timeout):
            captured["body"] = json.loads(request.data.decode("utf-8"))
            captured["auth"] = request.headers["Authorization"]
            captured["timeout"] = timeout
            return FakeResponse()

        with patch("urllib.request.urlopen", fake_urlopen):
            data = LinearGraphQLClient("lin_api_key").execute("query Test { ok }", {"x": 1})

        self.assertEqual(data, {"ok": True})
        self.assertEqual(captured["body"]["variables"], {"x": 1})
        self.assertEqual(captured["auth"], "lin_api_key")

    def test_n8n_poll_maps_events(self):
        class FakeQueue(N8nEventQueue):
            def _request(self, method, path, data=None):
                self.last = (method, path, data)
                return {
                    "data": [
                        {
                            "event_id": "evt_1",
                            "type": "linear_marker_detected",
                            "status": "queued",
                            "linear_issue_identifier": "BAA-1234",
                            "source": "linear",
                            "dedupe_key": "key",
                            "payload_json": {"action_id": "act_1"},
                        }
                    ]
                }

        queue = FakeQueue("https://n8n.example/api/v1", "api", "table_1")
        events = queue.poll_queued(limit=1)

        self.assertEqual(events[0].event_id, "evt_1")
        self.assertEqual(events[0].linear_issue_identifier, "BAA-1234")
        self.assertEqual(queue.last[1], "/data-tables/table_1/rows?limit=1")

    def test_n8n_status_update_uses_datatable_update_endpoint(self):
        class FakeQueue(N8nEventQueue):
            def _request(self, method, path, data=None):
                self.last = (method, path, data)
                return {}

        queue = FakeQueue("https://n8n.example/api/v1", "api", "table_1")
        queue.mark_processed("evt_1", "ok")

        method, path, data = queue.last
        self.assertEqual(method, "PATCH")
        self.assertEqual(path, "/data-tables/table_1/rows/update")
        self.assertEqual(data["filter"]["filters"][0]["value"], "evt_1")
        self.assertEqual(data["data"]["status"], "processed")

    def test_linear_webhook_normalizer_builds_queue_row(self):
        payload = {
            "type": "Comment",
            "webhookTimestamp": 1780000000,
            "data": {
                "id": "comment_1",
                "body": "[SV_APPROVAL action_id=act_1 decision=approved target=proposal:v1 by=hirotea]",
                "issue": {"id": "issue_1", "identifier": "BAA-1234"},
                "user": {"id": "user_1"},
            },
        }

        row = normalize_linear_comment_marker(payload)

        self.assertIsNotNone(row)
        self.assertEqual(row.dedupe_key, "linear:BAA-1234:act_1")
        self.assertEqual(row.payload_json["target"], "proposal:v1")

    def test_linear_signature_verification(self):
        import hashlib
        import hmac

        raw = b'{"ok":true}'
        signature = hmac.new(b"secret", raw, hashlib.sha256).hexdigest()

        self.assertTrue(verify_linear_signature(raw, signature, "secret"))
        self.assertFalse(verify_linear_signature(raw, signature, "wrong"))


if __name__ == "__main__":
    unittest.main()
