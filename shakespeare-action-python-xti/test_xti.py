# -*- coding: utf-8 -*-
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from xti import health_check, query_ip_reputation, query_domain_reputation, query_url_reputation, query_file_reputation, query_cve_intel, submit_indicator


ACTION_CASES = [
    [
        "health_check",
        {}
    ],
    [
        "query_ip_reputation",
        {
            "ip": "203.0.113.77"
        }
    ],
    [
        "query_domain_reputation",
        {
            "domain": "malicious.example"
        }
    ],
    [
        "query_url_reputation",
        {
            "url": "https://malicious.example/login"
        }
    ],
    [
        "query_file_reputation",
        {
            "file_hash": "44d88612fea8a8f36de82e1278abb02f"
        }
    ],
    [
        "query_cve_intel",
        {
            "cve_id": "CVE-2026-10001"
        }
    ],
    [
        "submit_indicator",
        {
            "indicator": "198.51.100.88",
            "indicator_type": "ip",
            "severity": "medium"
        }
    ]
]


class TestXti(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.assets = {
            "database_path": os.path.join(self.tmpdir.name, "xti.db"),
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
