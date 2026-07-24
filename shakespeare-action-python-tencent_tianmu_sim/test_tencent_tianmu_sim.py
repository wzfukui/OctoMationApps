# -*- coding: utf-8 -*-
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from tencent_tianmu_sim import health_check, list_block_policies, block_ip, unblock_ip, expire_due_policies, query_operation_history


ACTION_CASES = [
    [
        "health_check",
        {}
    ],
    [
        "list_block_policies",
        {
            "ip": "203.0.113.77"
        }
    ],
    [
        "block_ip",
        {
            "ip": "198.51.100.66",
            "reason": "反弹 Shell 外联 C2",
            "ttl_minutes": 120,
            "scope": "global",
            "direction": "bidirectional",
            "alert_id": "soc-alert-20260724-0002",
            "trace_id": "demo-trace-reverse-shell-0002"
        }
    ],
    [
        "unblock_ip",
        {
            "policy_id": "tm-pol-demo-0001",
            "ip": "203.0.113.77",
            "reason": "人工复核后解除",
            "trace_id": "demo-trace-web-0001"
        }
    ],
    [
        "expire_due_policies",
        {
            "as_of": "2100-01-01T00:00:00+08:00",
            "trigger_source": "scheduled",
            "trace_id": "demo-trace-ttl-tianmu"
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


class TestTencentTianmuSim(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.assets = {
            "database_path": os.path.join(self.tempdir.name, "tencent_tianmu_sim.db"),
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
        result = block_ip({}, self.assets, {})
        self.assertEqual(result["code"], 400)
        self.assertTrue(result["data"]["missing_parameters"])


    def test_policy_action_returns_audit_contract(self):
        result = block_ip({'ip': '198.51.100.66', 'reason': '反弹 Shell 外联 C2', 'ttl_minutes': 120, 'scope': 'global', 'direction': 'bidirectional', 'alert_id': 'soc-alert-20260724-0002', 'trace_id': 'demo-trace-reverse-shell-0002'}, self.assets, {})
        self.assertEqual(result["code"], 200)
        self.assertTrue(result["data"]["policy_id"])
        self.assertEqual(
            result["data"]["operation"]["trace_id"],
            'demo-trace-reverse-shell-0002',
        )
        self.assertIn("expires_at", result["data"]["policy"])


if __name__ == "__main__":
    unittest.main()
