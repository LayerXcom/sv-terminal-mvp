import unittest

from sv_terminal_worker.markers import find_markers, is_proposal_approval, parse_marker


class MarkerTests(unittest.TestCase):
    def test_parse_marker(self):
        marker = parse_marker("[SV_APPROVAL action_id=act_1 decision=approved target=proposal:v1 by=hirotea]")

        self.assertEqual(marker.kind, "SV_APPROVAL")
        self.assertEqual(marker.get("action_id"), "act_1")
        self.assertEqual(marker.get("decision"), "approved")
        self.assertEqual(marker.get("target"), "proposal:v1")

    def test_detect_proposal_approval(self):
        marker = parse_marker("[SV_APPROVAL action_id=act_1 decision=approved target=proposal:v1 by=hirotea]")

        self.assertTrue(is_proposal_approval(marker))

    def test_find_markers(self):
        markers = find_markers(
            """
            text
            [SV_EVENT id=evt_1 type=test status=done source=worker]
            [SV_APPROVAL action_id=act_1 decision=approved target=proposal:v1 by=hirotea]
            """
        )

        self.assertEqual(len(markers), 2)


if __name__ == "__main__":
    unittest.main()
