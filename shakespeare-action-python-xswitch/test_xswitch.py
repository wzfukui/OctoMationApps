# -*- coding: utf-8 -*-
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from xswitch import health_check, query_mac_table, query_arp_table, query_interface_status, disable_port, enable_port, query_operation_history


ACTION_CASES = [
    [
        "health_check",
        {}
    ],
    [
        "query_mac_table",
        {
            "mac": "00:16:3e:7a:4b:11"
        }
    ],
    [
        "query_arp_table",
        {
            "ip": "10.20.4.77"
        }
    ],
    [
        "query_interface_status",
        {
            "interface": "GE1/0/12"
        }
    ],
    [
        "disable_port",
        {
            "interface": "GE1/0/12",
            "reason": "终端隔离"
        }
    ],
    [
        "enable_port",
        {
            "interface": "GE1/0/12"
        }
    ],
    [
        "query_operation_history",
        {}
    ]
]


class TestXswitch(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.assets = {
            "database_path": os.path.join(self.tmpdir.name, "xswitch.db"),
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
