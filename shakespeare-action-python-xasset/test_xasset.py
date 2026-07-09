# -*- coding: utf-8 -*-
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from xasset import health_check, list_assets, query_asset_by_ip, query_assets_by_owner, query_asset_relations, query_inventory_summary, update_asset_tag, create_asset, update_asset, delete_asset


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
        "query_assets_by_owner",
        {
            "owner": "alice"
        }
    ],
    [
        "query_asset_relations",
        {
            "asset_id": "asset-web-01"
        }
    ],
    [
        "query_inventory_summary",
        {}
    ],
    [
        "update_asset_tag",
        {
            "asset_id": "asset-web-01",
            "tag": "incident",
            "value": "IR-2026-0001"
        }
    ],
    [
        "create_asset",
        {
            "asset_id": "asset-demo-01",
            "asset_name": "demo-server-01",
            "ip": "10.30.6.10",
            "asset_type": "server",
            "owner": "secops",
            "status": "online"
        }
    ],
    [
        "update_asset",
        {
            "asset_id": "asset-web-01",
            "owner": "alice",
            "status": "maintenance"
        }
    ],
    [
        "delete_asset",
        {
            "asset_id": "asset-lb-01",
            "reason": "资产下线"
        }
    ]
]


class TestXasset(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.assets = {
            "database_path": os.path.join(self.tmpdir.name, "xasset.db"),
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


    def test_owner_query_returns_owner_context(self):
        ret = query_assets_by_owner({"owner": "carol"}, self.assets, self.context)
        self.assertEqual(ret["code"], 200)
        self.assertEqual(ret["data"]["total_count"], 1)
        record = ret["data"]["records"][0]
        self.assertEqual(record["owner"], "carol")
        self.assertIn("财务部", record["key_info"])

    def test_asset_crud_roundtrip(self):
        created = create_asset({
            "asset_id": "asset-unit-01",
            "asset_name": "unit-server-01",
            "ip": "10.99.1.10",
            "asset_type": "server",
            "owner": "secops",
            "status": "online",
            "summary": "单元测试新增资产"
        }, self.assets, self.context)
        self.assertEqual(created["code"], 200)
        self.assertEqual(created["data"]["created_id"], "asset-unit-01")

        queried = query_asset_by_ip({"ip": "10.99.1.10"}, self.assets, self.context)
        self.assertEqual(queried["data"]["total_count"], 1)
        self.assertEqual(queried["data"]["records"][0]["owner"], "secops")

        updated = update_asset({
            "asset_id": "asset-unit-01",
            "owner": "alice",
            "status": "maintenance",
            "severity": "low"
        }, self.assets, self.context)
        self.assertEqual(updated["code"], 200)
        self.assertEqual(updated["data"]["affected_count"], 1)
        self.assertEqual(updated["data"]["records"][0]["owner"], "alice")
        self.assertEqual(updated["data"]["records"][0]["status"], "maintenance")

        deleted = delete_asset({"asset_id": "asset-unit-01", "reason": "unit cleanup"}, self.assets, self.context)
        self.assertEqual(deleted["code"], 200)
        self.assertEqual(deleted["data"]["affected_count"], 1)

        missing = query_asset_by_ip({"ip": "10.99.1.10"}, self.assets, self.context)
        self.assertEqual(missing["data"]["total_count"], 0)


if __name__ == "__main__":
    unittest.main()
