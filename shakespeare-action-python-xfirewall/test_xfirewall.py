# -*- coding: utf-8 -*-
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from xfirewall import (
    block_ip,
    health_check,
    query_block_history,
    query_blocked_ips,
    query_firewall_status,
    unblock_ip,
)


class TestXFirewall(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.assets = {
            "firewall_url": "https://xfirewall.local",
            "admin_token": "unit-test-token",
            "database_path": os.path.join(self.tmpdir.name, "xfirewall.db"),
            "delay_min_seconds": 0,
            "delay_max_seconds": 0,
        }
        self.context = {}

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_health_and_status(self):
        health = health_check({}, self.assets, self.context)
        self.assertEqual(health["code"], 200)
        self.assertEqual(health["summary"]["statusCode"], "200")

        status = query_firewall_status({}, self.assets, self.context)
        self.assertEqual(status["code"], 200)
        self.assertEqual(status["data"]["status"], "running")

    def test_block_query_history_and_unblock(self):
        params = {"ip": "203.0.113.77", "reason": "单元测试封禁"}
        blocked = block_ip(params, self.assets, self.context)
        self.assertEqual(blocked["code"], 200)
        self.assertIn("rule_id", blocked["data"])

        current = query_blocked_ips({"limit": 10}, self.assets, self.context)
        self.assertEqual(current["code"], 200)
        self.assertEqual(current["data"]["total_count"], 1)

        history = query_block_history({"ip": "203.0.113.77"}, self.assets, self.context)
        self.assertEqual(history["code"], 200)
        self.assertGreaterEqual(history["data"]["total_count"], 1)

        released = unblock_ip({"ip": "203.0.113.77"}, self.assets, self.context)
        self.assertEqual(released["code"], 200)
        self.assertEqual(released["data"]["unblocked_count"], 1)


if __name__ == "__main__":
    unittest.main()
