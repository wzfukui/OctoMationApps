# -*- coding: utf-8 -*-
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from xscanner import health_check, add_scan_target, start_scan, query_scan_status, query_vulnerabilities, generate_report, query_operation_history


ACTION_CASES = [
    [
        "health_check",
        {}
    ],
    [
        "add_scan_target",
        {
            "target": "10.10.8.23",
            "owner": "alice"
        }
    ],
    [
        "start_scan",
        {
            "target": "10.10.8.23",
            "profile": "full"
        }
    ],
    [
        "query_scan_status",
        {
            "target": "10.10.8.23"
        }
    ],
    [
        "query_vulnerabilities",
        {
            "severity": "critical"
        }
    ],
    [
        "generate_report",
        {
            "target": "10.10.8.23",
            "format": "html"
        }
    ],
    [
        "query_operation_history",
        {}
    ]
]


class TestXscanner(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.assets = {
            "database_path": os.path.join(self.tmpdir.name, "xscanner.db"),
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
