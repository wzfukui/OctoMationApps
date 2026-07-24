# -*- coding: utf-8 -*-
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from tencent_asset_sim import health_check, list_assets, query_asset_by_ip, query_asset_by_id, query_assets_by_owner, list_exposed_assets, query_business_context, create_asset, update_asset, delete_asset, query_operation_history


ACTION_CASES = [
    [
        "health_check",
        {}
    ],
    [
        "list_assets",
        {
            "owner": "alice",
            "limit": 20
        }
    ],
    [
        "query_asset_by_ip",
        {
            "ip": "10.10.8.23"
        }
    ],
    [
        "query_asset_by_id",
        {
            "asset_id": "asset-cvm-prod-web-01"
        }
    ],
    [
        "query_assets_by_owner",
        {
            "owner": "alice"
        }
    ],
    [
        "list_exposed_assets",
        {
            "exposure": "internet"
        }
    ],
    [
        "query_business_context",
        {
            "business_id": "biz-checkout"
        }
    ],
    [
        "create_asset",
        {
            "asset_id": "asset-cvm-demo-01",
            "asset_name": "demo-api-01",
            "ip": "10.40.8.21",
            "asset_type": "cvm",
            "owner": "secops",
            "business_id": "biz-demo",
            "business_name": "演示业务",
            "exposure": "private",
            "trace_id": "demo-trace-asset-crud"
        }
    ],
    [
        "update_asset",
        {
            "asset_id": "asset-cvm-prod-web-01",
            "owner": "alice",
            "exposure": "internet",
            "status": "online",
            "trace_id": "demo-trace-asset-update"
        }
    ],
    [
        "delete_asset",
        {
            "asset_id": "asset-cvm-demo-01",
            "reason": "演示资产下线",
            "trace_id": "demo-trace-asset-crud"
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


class TestTencentAssetSim(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.assets = {
            "database_path": os.path.join(self.tempdir.name, "tencent_asset_sim.db"),
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
        result = query_asset_by_ip({}, self.assets, {})
        self.assertEqual(result["code"], 400)
        self.assertTrue(result["data"]["missing_parameters"])



if __name__ == "__main__":
    unittest.main()
