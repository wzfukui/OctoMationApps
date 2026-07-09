# -*- coding: utf-8 -*-
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from xvpn import health_check, query_login_status, query_online_users, create_vpn_account, disable_vpn_account, enable_vpn_account, kick_vpn_user, query_vpn_history


ACTION_CASES = [
    [
        "health_check",
        {}
    ],
    [
        "query_login_status",
        {
            "username": "alice"
        }
    ],
    [
        "query_online_users",
        {
            "username": "alice"
        }
    ],
    [
        "create_vpn_account",
        {
            "username": "dave",
            "display_name": "Dave",
            "department": "安全运营"
        }
    ],
    [
        "disable_vpn_account",
        {
            "username": "alice",
            "reason": "疑似账号失陷"
        }
    ],
    [
        "enable_vpn_account",
        {
            "username": "alice"
        }
    ],
    [
        "kick_vpn_user",
        {
            "username": "alice",
            "reason": "异常公网 IP 登录"
        }
    ],
    [
        "query_vpn_history",
        {
            "username": "alice"
        }
    ]
]


class TestXvpn(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.assets = {
            "database_path": os.path.join(self.tmpdir.name, "xvpn.db"),
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
