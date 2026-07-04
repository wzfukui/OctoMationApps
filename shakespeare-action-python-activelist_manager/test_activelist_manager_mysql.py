import random
import sys
import types
import unittest

import mysql.connector


class FakeDbConfig:
    def getHost(self, domain="app"):
        return "127.0.0.1"

    def getPort(self, domain="app"):
        return 3306

    def getUsername(self, domain="app"):
        return "octomation_test"

    def appPassword(self):
        return "octomation_test"


class FakeHoneyGuide:
    def __init__(self, context_info=None):
        self.dbConfig = FakeDbConfig()


action_sdk_pkg = types.ModuleType("action_sdk_for_cache")
action_cache_sdk = types.ModuleType("action_sdk_for_cache.action_cache_sdk")
action_cache_sdk.HoneyGuide = FakeHoneyGuide
sys.modules.setdefault("action_sdk_for_cache", action_sdk_pkg)
sys.modules.setdefault("action_sdk_for_cache.action_cache_sdk", action_cache_sdk)

import core_activelist
from core_activelist import ActiveListManager
from activelist_manager import (
    add_record_to_active_list,
    check_record_exists_in_active_list,
    delete_active_list,
    initialize_active_list_table,
    quick_view_active_list,
)


TEST_DB_PARAMS = {
    "host": "127.0.0.1",
    "port": 3306,
    "database": "octomation_activelist_test",
    "username": "octomation_test",
    "password": "octomation_test",
    "ssl": False,
}


def fake_mysql_params_from_sdk(hg_client=None):
    return TEST_DB_PARAMS.copy()


core_activelist.get_mysql_params_from_sdk = fake_mysql_params_from_sdk


class TestActiveListManagerMysql(unittest.TestCase):
    table_name = "perf_10000"
    sql_table_name = f"_al_{table_name}"

    @classmethod
    def setUpClass(cls):
        cls.admin_conn = mysql.connector.connect(
            host=TEST_DB_PARAMS["host"],
            port=TEST_DB_PARAMS["port"],
            database=TEST_DB_PARAMS["database"],
            user=TEST_DB_PARAMS["username"],
            password=TEST_DB_PARAMS["password"],
        )
        cls.admin_conn.autocommit = True

    @classmethod
    def tearDownClass(cls):
        cls.admin_conn.close()

    def setUp(self):
        delete_active_list({"activelist_name": self.table_name}, {}, {})
        result = initialize_active_list_table({"activelist_name": self.table_name}, {}, {})
        self.assertEqual(result["data"]["err_code"], 0, result)

    def tearDown(self):
        delete_active_list({"activelist_name": self.table_name}, {}, {})

    def _bulk_seed_ip_records(self, total_count=10000):
        random.seed(20260704)
        rows = []
        for i in range(total_count):
            source_ip = f"10.{(i // 65536) % 256}.{(i // 256) % 256}.{i % 256}"
            destination_ip = f"172.16.{random.randint(0, 255)}.{random.randint(1, 254)}"
            rows.append((source_ip, destination_ip, f"seed-{i}"))

        cursor = self.admin_conn.cursor()
        try:
            cursor.executemany(
                f"""
                INSERT INTO `{self.sql_table_name}` (_key, _value, _remark, create_time, update_time)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                rows,
            )
        finally:
            cursor.close()
        return rows

    def _show_index_names(self):
        cursor = self.admin_conn.cursor()
        try:
            cursor.execute(f"SHOW INDEX FROM `{self.sql_table_name}`")
            return {row[2] for row in cursor.fetchall()}
        finally:
            cursor.close()

    def _explain_key_for_query(self, sql, params):
        cursor = self.admin_conn.cursor(dictionary=True)
        try:
            cursor.execute(f"EXPLAIN {sql}", params)
            row = cursor.fetchone()
            return row.get("key") or row.get("key".upper()) or row.get("Key") or row.get("EXPLAIN")
        finally:
            cursor.close()

    def test_initialize_creates_query_indexes(self):
        indexes = self._show_index_names()
        self.assertIn("idx_al_key", indexes)
        self.assertIn("idx_al_value", indexes)
        self.assertIn("idx_al_key_create_time", indexes)
        self.assertIn("idx_al_value_create_time", indexes)
        self.assertIn("idx_al_key_value_create_time", indexes)

    def test_check_record_exists_by_key_value_and_key_value_pair_with_10000_ip_records(self):
        rows = self._bulk_seed_ip_records()
        target_key, target_value, _ = rows[5432]

        by_key = check_record_exists_in_active_list(
            {"activelist_name": self.table_name, "match_mode": "key", "item_key": target_key},
            {},
            {},
        )
        self.assertTrue(by_key["data"]["record_exists"])
        self.assertEqual(by_key["data"]["record_count"], 1)

        by_value = check_record_exists_in_active_list(
            {"activelist_name": self.table_name, "match_mode": "value", "item_value": target_value},
            {},
            {},
        )
        self.assertTrue(by_value["data"]["record_exists"])
        self.assertGreaterEqual(by_value["data"]["record_count"], 1)

        by_pair = check_record_exists_in_active_list(
            {
                "activelist_name": self.table_name,
                "match_mode": "key_value",
                "item_key": target_key,
                "item_value": target_value,
            },
            {},
            {},
        )
        self.assertTrue(by_pair["data"]["record_exists"])
        self.assertEqual(by_pair["data"]["record_count"], 1)

        missing_pair = check_record_exists_in_active_list(
            {
                "activelist_name": self.table_name,
                "match_mode": "key_value",
                "item_key": target_key,
                "item_value": "172.31.255.254",
            },
            {},
            {},
        )
        self.assertFalse(missing_pair["data"]["record_exists"])
        self.assertEqual(missing_pair["data"]["record_count"], 0)

    def test_check_record_exists_can_use_time_window_and_indexes(self):
        rows = self._bulk_seed_ip_records()
        target_key, target_value, _ = rows[2222]

        result = check_record_exists_in_active_list(
            {
                "activelist_name": self.table_name,
                "match_mode": "key_value",
                "item_key": target_key,
                "item_value": target_value,
                "time_delta_minute": 60,
            },
            {},
            {},
        )
        self.assertTrue(result["data"]["record_exists"])

        used_key = self._explain_key_for_query(
            f"""
            SELECT COUNT(*) FROM `{self.sql_table_name}`
            WHERE _key = %s AND _value = %s
            AND create_time BETWEEN DATE_SUB(NOW(), INTERVAL 60 MINUTE) AND NOW()
            """,
            (target_key, target_value),
        )
        self.assertIsNotNone(used_key)
        self.assertIn("Index", used_key)

    def test_sql_injection_like_key_does_not_match_or_break_table(self):
        self._bulk_seed_ip_records()
        injected_key = "10.0.0.1' OR '1'='1"

        exists_result = check_record_exists_in_active_list(
            {"activelist_name": self.table_name, "match_mode": "key", "item_key": injected_key},
            {},
            {},
        )
        self.assertFalse(exists_result["data"]["record_exists"])
        self.assertEqual(exists_result["data"]["record_count"], 0)

        quick_view_result = quick_view_active_list(
            {"activelist_name": self.table_name, "item_key": injected_key},
            {},
            {},
        )
        self.assertEqual(quick_view_result["data"]["total_count"], 0)

    def test_repeated_queries_do_not_leak_mysql_connections(self):
        rows = self._bulk_seed_ip_records()
        target_key, _, _ = rows[1]
        cursor = self.admin_conn.cursor()
        try:
            cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
            before = int(cursor.fetchone()[1])
            for _ in range(50):
                result = check_record_exists_in_active_list(
                    {"activelist_name": self.table_name, "match_mode": "key", "item_key": target_key},
                    {},
                    {},
                )
                self.assertTrue(result["data"]["record_exists"])
            cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
            after = int(cursor.fetchone()[1])
        finally:
            cursor.close()

        self.assertLessEqual(after, before + 2)

    def test_add_record_replace_still_updates_existing_key(self):
        first = add_record_to_active_list(
            {
                "activelist_name": self.table_name,
                "item_key": "192.0.2.10",
                "item_value": "198.51.100.10",
                "replace_if_exists": True,
            },
            {},
            {},
        )
        self.assertEqual(first["data"]["err_code"], 0)

        second = add_record_to_active_list(
            {
                "activelist_name": self.table_name,
                "item_key": "192.0.2.10",
                "item_value": "203.0.113.10",
                "replace_if_exists": True,
            },
            {},
            {},
        )
        self.assertEqual(second["data"]["err_code"], 0)

        old_value = check_record_exists_in_active_list(
            {
                "activelist_name": self.table_name,
                "match_mode": "key_value",
                "item_key": "192.0.2.10",
                "item_value": "198.51.100.10",
            },
            {},
            {},
        )
        new_value = check_record_exists_in_active_list(
            {
                "activelist_name": self.table_name,
                "match_mode": "key_value",
                "item_key": "192.0.2.10",
                "item_value": "203.0.113.10",
            },
            {},
            {},
        )
        self.assertFalse(old_value["data"]["record_exists"])
        self.assertTrue(new_value["data"]["record_exists"])


if __name__ == "__main__":
    unittest.main()
