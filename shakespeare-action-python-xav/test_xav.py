# -*- coding: utf-8 -*-
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from xav import health_check, query_endpoint, query_threat_events, start_scan, quarantine_file, remove_threat, query_operation_history


ACTION_CASES = [
    [
        "health_check",
        {}
    ],
    [
        "query_endpoint",
        {
            "ip": "10.20.4.77"
        }
    ],
    [
        "query_threat_events",
        {
            "severity": "high"
        }
    ],
    [
        "start_scan",
        {
            "ip": "10.20.4.77",
            "scan_type": "full"
        }
    ],
    [
        "quarantine_file",
        {
            "file_hash": "44d88612fea8a8f36de82e1278abb02f",
            "reason": "命中木马规则"
        }
    ],
    [
        "remove_threat",
        {
            "threat_id": "threat-1001"
        }
    ],
    [
        "query_operation_history",
        {}
    ]
]


class TestXav(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.assets = {
            "database_path": os.path.join(self.tmpdir.name, "xav.db"),
            "delay_min_seconds": 0,
            "delay_max_seconds": 0,
            "scenario_profile": "unit-test",
        }
        self.context = {}

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_health_check(self):
        ret = health_check({}, self.assets, self.context)
        self.assertEqual(ret["code"], 200)
        self.assertEqual(ret["summary"]["statusCode"], "200")
        self.assertGreaterEqual(ret["data"]["system_info"]["record_count"], 1)

    def test_all_actions_return_success(self):
        for action_name, params in ACTION_CASES:
            with self.subTest(action=action_name):
                func = globals()[action_name]
                ret = func(params, self.assets, self.context)
                self.assertEqual(ret["code"], 200)
                self.assertIn("data", ret)



if __name__ == "__main__":
    unittest.main()
