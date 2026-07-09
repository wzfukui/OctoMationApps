# -*- coding: utf-8 -*-
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from xmail import health_check, parse_email, query_mail_events, quarantine_message, release_message, block_sender, query_operation_history


ACTION_CASES = [
    [
        "health_check",
        {}
    ],
    [
        "parse_email",
        {
            "message_id": "mail-20260709-0007"
        }
    ],
    [
        "query_mail_events",
        {
            "recipient": "carol@example.com"
        }
    ],
    [
        "quarantine_message",
        {
            "message_id": "mail-20260709-0007",
            "reason": "钓鱼链接"
        }
    ],
    [
        "release_message",
        {
            "message_id": "mail-20260709-0007"
        }
    ],
    [
        "block_sender",
        {
            "sender": "invoice@malicious.example",
            "reason": "钓鱼邮件源"
        }
    ],
    [
        "query_operation_history",
        {}
    ]
]


class TestXmail(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.assets = {
            "database_path": os.path.join(self.tmpdir.name, "xmail.db"),
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
