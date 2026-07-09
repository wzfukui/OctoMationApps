# -*- coding: utf-8 -*-
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from xjumpserver import health_check, query_login_records, query_target_access, query_online_sessions, query_command_audit, terminate_session, query_operation_history


ACTION_CASES = [
    [
        "health_check",
        {}
    ],
    [
        "query_login_records",
        {
            "username": "alice",
            "target_ip": "10.10.8.23"
        }
    ],
    [
        "query_target_access",
        {
            "username": "carol",
            "target_ip": "10.20.4.77"
        }
    ],
    [
        "query_online_sessions",
        {
            "username": "carol"
        }
    ],
    [
        "query_command_audit",
        {
            "session_id": "sess-jms-0001"
        }
    ],
    [
        "terminate_session",
        {
            "session_id": "sess-jms-0002",
            "reason": "可疑远程访问"
        }
    ],
    [
        "query_operation_history",
        {}
    ]
]


class TestXjumpserver(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.assets = {
            "database_path": os.path.join(self.tmpdir.name, "xjumpserver.db"),
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
