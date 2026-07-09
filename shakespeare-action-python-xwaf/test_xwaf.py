# -*- coding: utf-8 -*-
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from xwaf import health_check, query_attack_events, query_protected_sites, block_ip, unblock_ip, add_url_rule, query_operation_history


ACTION_CASES = [
    [
        "health_check",
        {}
    ],
    [
        "query_attack_events",
        {
            "source_ip": "203.0.113.77"
        }
    ],
    [
        "query_protected_sites",
        {
            "site": "checkout.example.com"
        }
    ],
    [
        "block_ip",
        {
            "ip": "203.0.113.77",
            "reason": "SQL 注入攻击"
        }
    ],
    [
        "unblock_ip",
        {
            "ip": "203.0.113.77"
        }
    ],
    [
        "add_url_rule",
        {
            "url": "/admin/debug",
            "rule": "禁止调试路径访问"
        }
    ],
    [
        "query_operation_history",
        {}
    ]
]


class TestXwaf(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.assets = {
            "database_path": os.path.join(self.tmpdir.name, "xwaf.db"),
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
