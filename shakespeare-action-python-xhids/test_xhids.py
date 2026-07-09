# -*- coding: utf-8 -*-
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from xhids import health_check, query_host_by_ip, query_host_processes, query_host_ports, query_security_events, isolate_host, release_host, query_operation_history


ACTION_CASES = [
    [
        "health_check",
        {}
    ],
    [
        "query_host_by_ip",
        {
            "ip": "10.10.8.23"
        }
    ],
    [
        "query_host_processes",
        {
            "host_id": "host-prod-web-01"
        }
    ],
    [
        "query_host_ports",
        {
            "host_id": "host-prod-web-01"
        }
    ],
    [
        "query_security_events",
        {
            "severity": "high"
        }
    ],
    [
        "isolate_host",
        {
            "host_id": "host-prod-web-01",
            "reason": "检测到反弹 shell"
        }
    ],
    [
        "release_host",
        {
            "host_id": "host-prod-web-01",
            "reason": "人工确认恢复"
        }
    ],
    [
        "query_operation_history",
        {}
    ]
]


class TestXhids(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.assets = {
            "database_path": os.path.join(self.tmpdir.name, "xhids.db"),
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
