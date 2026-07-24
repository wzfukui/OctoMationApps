# -*- coding: utf-8 -*-
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from tencent_tcss_sim import health_check, query_clusters, query_runtime_alerts, query_runtime_processes, query_malicious_connections, update_alert_status, query_operation_history


ACTION_CASES = [
    [
        "health_check",
        {}
    ],
    [
        "query_clusters",
        {
            "cluster_id": "cls-prod-checkout"
        }
    ],
    [
        "query_runtime_alerts",
        {
            "cluster_id": "cls-prod-checkout",
            "severity": "high"
        }
    ],
    [
        "query_runtime_processes",
        {
            "cluster_id": "cls-prod-checkout",
            "process_name": "xmrig"
        }
    ],
    [
        "query_malicious_connections",
        {
            "cluster_id": "cls-prod-checkout",
            "external_ip": "198.51.100.66"
        }
    ],
    [
        "update_alert_status",
        {
            "alert_id": "tcss-alert-20260724-0001",
            "status": "processing",
            "comment": "已阻断矿池外联 IP",
            "trace_id": "demo-trace-container-0005"
        }
    ],
    [
        "query_operation_history",
        {
            "trace_id": "demo-trace-web-0001",
            "limit": 20
        }
    ]
]


class TestTencentTcssSim(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.assets = {
            "database_path": os.path.join(self.tempdir.name, "tencent_tcss_sim.db"),
            "delay_min_seconds": 0,
            "delay_max_seconds": 0,
        }

    def tearDown(self):
        self.tempdir.cleanup()

    def test_health_and_none_assets_compatibility(self):
        self.assertEqual(health_check({}, self.assets, {})["code"], 200)
        self.assertEqual(health_check({}, None, {})["code"], 200)

    def test_all_actions_execute(self):
        for action_name, params in ACTION_CASES:
            with self.subTest(action=action_name):
                result = globals()[action_name](params, self.assets, {})
                self.assertEqual(result["code"], 200, result)
                self.assertIn("data", result)

    def test_simulated_api_failure_is_distinguishable(self):
        unavailable = dict(self.assets)
        unavailable["simulated_api_status"] = "unavailable"
        result = health_check({}, unavailable, {})
        self.assertEqual(result["code"], 503)
        self.assertEqual(result["data"]["system_info"]["api_status"], "unavailable")


    def test_required_parameter_validation(self):
        result = query_runtime_processes({}, self.assets, {})
        self.assertEqual(result["code"], 400)
        self.assertTrue(result["data"]["missing_parameters"])



if __name__ == "__main__":
    unittest.main()
