# -*- coding: utf-8 -*-
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from xldap import health_check, query_user, query_group, query_user_groups, create_user, disable_user, enable_user, reset_password, add_user_to_group, query_operation_history


ACTION_CASES = [
    [
        "health_check",
        {}
    ],
    [
        "query_user",
        {
            "username": "alice"
        }
    ],
    [
        "query_group",
        {
            "group_name": "vpn-users"
        }
    ],
    [
        "query_user_groups",
        {
            "username": "alice"
        }
    ],
    [
        "create_user",
        {
            "username": "dave",
            "display_name": "Dave",
            "department": "安全运营"
        }
    ],
    [
        "disable_user",
        {
            "username": "alice",
            "reason": "账号风险处置"
        }
    ],
    [
        "enable_user",
        {
            "username": "alice"
        }
    ],
    [
        "reset_password",
        {
            "username": "alice",
            "reason": "疑似凭证泄露"
        }
    ],
    [
        "add_user_to_group",
        {
            "username": "alice",
            "group_name": "vpn-users"
        }
    ],
    [
        "query_operation_history",
        {}
    ]
]


class TestXldap(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.assets = {
            "database_path": os.path.join(self.tmpdir.name, "xldap.db"),
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
