# -*- coding: utf-8 -*-
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from xticket import health_check, create_ticket, query_ticket, update_ticket_status, add_ticket_comment, assign_ticket, query_ticket_history


ACTION_CASES = [
    [
        "health_check",
        {}
    ],
    [
        "create_ticket",
        {
            "title": "恶意 IP 自动封堵确认",
            "severity": "high",
            "description": "SOAR 剧本已完成封堵，请复核"
        }
    ],
    [
        "query_ticket",
        {
            "ticket_id": "TCK-20260709-0001"
        }
    ],
    [
        "update_ticket_status",
        {
            "ticket_id": "TCK-20260709-0001",
            "status": "in_progress",
            "reason": "已分派安全运营"
        }
    ],
    [
        "add_ticket_comment",
        {
            "ticket_id": "TCK-20260709-0001",
            "comment": "已通知资产负责人"
        }
    ],
    [
        "assign_ticket",
        {
            "ticket_id": "TCK-20260709-0001",
            "assignee": "secops"
        }
    ],
    [
        "query_ticket_history",
        {
            "ticket_id": "TCK-20260709-0001"
        }
    ]
]


class TestXticket(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.assets = {
            "database_path": os.path.join(self.tmpdir.name, "xticket.db"),
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
