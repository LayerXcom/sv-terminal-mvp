import json
import unittest
from unittest.mock import patch

from sv_terminal_worker.adapters.linear.graphql_client import LinearGraphQLClient
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
                    "events": [
                        {
                            "event_id": "evt_1",
                            "type": "linear_marker_detected",
                            "linear_issue_identifier": "BAA-1234",
                            "source": "linear",
                            "dedupe_key": "key",
                            "payload_json": {"action_id": "act_1"},
                        }
                    ]
                }

        queue = FakeQueue("https://n8n.example", "api")
        events = queue.poll_queued(limit=1)

        self.assertEqual(events[0].event_id, "evt_1")
        self.assertEqual(events[0].linear_issue_identifier, "BAA-1234")


if __name__ == "__main__":
    unittest.main()
