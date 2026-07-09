# -*- coding: utf-8 -*-
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from xiam import health_check, query_user, query_user_logins, disable_user, enable_user, reset_password, query_operation_history


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
        "query_user_logins",
        {
            "username": "alice"
        }
    ],
    [
        "disable_user",
        {
            "username": "alice",
            "reason": "疑似账号失陷"
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
            "reason": "账号疑似泄露"
        }
    ],
    [
        "query_operation_history",
        {}
    ]
]


class TestXiam(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.assets = {
            "database_path": os.path.join(self.tmpdir.name, "xiam.db"),
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
