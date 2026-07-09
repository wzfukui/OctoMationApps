# -*- coding: utf-8 -*-
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from xsandbox import health_check, submit_file, submit_url, query_analysis_report, query_behavior_trace, query_operation_history


ACTION_CASES = [
    [
        "health_check",
        {}
    ],
    [
        "submit_file",
        {
            "file_hash": "44d88612fea8a8f36de82e1278abb02f",
            "file_name": "invoice.exe"
        }
    ],
    [
        "submit_url",
        {
            "url": "https://malicious.example/login"
        }
    ],
    [
        "query_analysis_report",
        {
            "sample_id": "44d88612fea8a8f36de82e1278abb02f"
        }
    ],
    [
        "query_behavior_trace",
        {
            "sample_id": "44d88612fea8a8f36de82e1278abb02f"
        }
    ],
    [
        "query_operation_history",
        {}
    ]
]


class TestXsandbox(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.assets = {
            "database_path": os.path.join(self.tmpdir.name, "xsandbox.db"),
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
