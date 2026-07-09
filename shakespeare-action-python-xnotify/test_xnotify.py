# -*- coding: utf-8 -*-
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from xnotify import health_check, send_message, send_email, send_sms, query_notification_history, query_delivery_status, register_channel


ACTION_CASES = [
    [
        "health_check",
        {}
    ],
    [
        "send_message",
        {
            "recipient": "alice",
            "message": "X 系列剧本已完成封堵",
            "severity": "info"
        }
    ],
    [
        "send_email",
        {
            "recipient": "secops@example.com",
            "subject": "安全事件通知",
            "message": "请复核自动处置结果"
        }
    ],
    [
        "send_sms",
        {
            "recipient": "13800000000",
            "message": "安全事件已自动处置"
        }
    ],
    [
        "query_notification_history",
        {
            "recipient": "alice"
        }
    ],
    [
        "query_delivery_status",
        {
            "notification_id": "notice-20260709-0001"
        }
    ],
    [
        "register_channel",
        {
            "channel_name": "secops-webhook",
            "channel_type": "webhook"
        }
    ]
]


class TestXnotify(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.assets = {
            "database_path": os.path.join(self.tmpdir.name, "xnotify.db"),
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
