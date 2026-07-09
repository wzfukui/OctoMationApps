# -*- coding: utf-8 -*-
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from xsiem import health_check, search_events, query_alert_detail, aggregate_events, update_alert_status, query_case_timeline, query_operation_history


ACTION_CASES = [
    [
        "health_check",
        {}
    ],
    [
        "search_events",
        {
            "query": "severity=high"
        }
    ],
    [
        "query_alert_detail",
        {
            "alert_id": "alert-20260709-001"
        }
    ],
    [
        "aggregate_events",
        {
            "window_minutes": 60
        }
    ],
    [
        "update_alert_status",
        {
            "alert_id": "alert-20260709-001",
            "status": "in_progress",
            "reason": "已触发自动封堵"
        }
    ],
    [
        "query_case_timeline",
        {
            "alert_id": "alert-20260709-001"
        }
    ],
    [
        "query_operation_history",
        {}
    ]
]


class TestXsiem(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.assets = {
            "database_path": os.path.join(self.tmpdir.name, "xsiem.db"),
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
