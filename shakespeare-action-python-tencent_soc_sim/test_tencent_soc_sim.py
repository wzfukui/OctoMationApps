# -*- coding: utf-8 -*-
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from tencent_soc_sim import health_check, query_ingestion_health, fetch_high_risk_alerts, query_alert_detail, emit_demo_alert, update_alert_status, writeback_disposition, query_operation_history


ACTION_CASES = [
    [
        "health_check",
        {}
    ],
    [
        "query_ingestion_health",
        {}
    ],
    [
        "fetch_high_risk_alerts",
        {
            "severity": "critical",
            "status": "new",
            "limit": 20
        }
    ],
    [
        "query_alert_detail",
        {
            "alert_id": "soc-alert-20260724-0001"
        }
    ],
    [
        "emit_demo_alert",
        {
            "alert_name": "手动演示 Web 攻击告警",
            "src_ip": "203.0.113.77",
            "dst_ip": "10.10.8.23",
            "asset_id": "asset-cvm-prod-web-01",
            "owner": "alice",
            "severity": "high",
            "confidence": 95,
            "trace_id": "demo-trace-manual-0004"
        }
    ],
    [
        "update_alert_status",
        {
            "alert_id": "soc-alert-20260724-0001",
            "status": "investigating",
            "comment": "SOAR 已完成上下文增强",
            "trace_id": "demo-trace-web-0001"
        }
    ],
    [
        "writeback_disposition",
        {
            "alert_id": "soc-alert-20260724-0001",
            "status": "closed",
            "disposition": "confirmed_malicious",
            "policy_ids": "tm-pol-demo-0001,waf-pol-demo-0001",
            "trace_id": "demo-trace-web-0001"
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


class TestTencentSocSim(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.assets = {
            "database_path": os.path.join(self.tempdir.name, "tencent_soc_sim.db"),
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
        result = query_alert_detail({}, self.assets, {})
        self.assertEqual(result["code"], 400)
        self.assertTrue(result["data"]["missing_parameters"])



if __name__ == "__main__":
    unittest.main()
