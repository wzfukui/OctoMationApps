# -*- coding: utf-8 -*-
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from xcloud import health_check, query_cloud_assets, query_security_groups, block_ip_in_security_group, unblock_ip_in_security_group, create_snapshot, query_operation_history


ACTION_CASES = [
    [
        "health_check",
        {}
    ],
    [
        "query_cloud_assets",
        {
            "ip": "10.10.8.23"
        }
    ],
    [
        "query_security_groups",
        {
            "security_group_id": "sg-dmz-web"
        }
    ],
    [
        "block_ip_in_security_group",
        {
            "security_group_id": "sg-dmz-web",
            "ip": "203.0.113.77",
            "reason": "攻击源封禁"
        }
    ],
    [
        "unblock_ip_in_security_group",
        {
            "security_group_id": "sg-dmz-web",
            "ip": "203.0.113.77"
        }
    ],
    [
        "create_snapshot",
        {
            "instance_id": "ecs-prod-web-01",
            "reason": "应急取证"
        }
    ],
    [
        "query_operation_history",
        {}
    ]
]


class TestXcloud(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.assets = {
            "database_path": os.path.join(self.tmpdir.name, "xcloud.db"),
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
