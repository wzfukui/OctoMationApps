#coding=utf-8
# 使用unitest测试mysql_client_v2.py
import unittest
from unittest import TestCase
from mysql_client_v2 import execute_sql, insert_data_with_columns, replace_data_with_columns, update_data_with_columns,health_check

class TestMySQLClient(unittest.TestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        self.assets = {
            "host": "192.168.22.251",
            "port": 3306,
            "username": "hg_soar_app",
            "password": "_RIGHT_PASSWORD_",
            "database": "honeyguide_application"
        }
        self.context_info = None
    
    # @unittest.order(1)
    def test_1_health_check(self):
        result = health_check({}, self.assets, None)
        self.assertEqual(result['summary']['statusCode'], 200)
        assets = {
            "host": "192.168.22.251",
            "port": 3306,
            "username": "hg_soar_app",
            "password": "_WRONG_PASSWORD_",
            "database": "honeyguide_application"
        }
        result = health_check({}, assets, None)
        self.assertEqual(result['summary']['statusCode'], 500)


    # @unittest.order(2)
    def test_2_execute_sql(self):
        params = {
            "sql": "DROP TABLE IF EXISTS _mysql_client_v2_test"
        }
        result = execute_sql(params, self.assets, None)
        self.assertEqual(result['data']['err_code'], 0)

        params = {
            "sql": "CREATE TABLE IF NOT EXISTS _mysql_client_v2_test (id INT PRIMARY KEY, name VARCHAR(255), age INT)"
        }
        result = execute_sql(params, self.assets, None)
        self.assertEqual(result['data']['err_code'], 0)

    # @unittest.order(3)
    def test_3_insert_data_with_columns(self):
        params = {
            "sql": "TRUNCATE TABLE _mysql_client_v2_test"
        }
        result = execute_sql(params, self.assets, None)
        self.assertEqual(result['data']['err_code'], 0)


        params = {
            "table_name": "_mysql_client_v2_test",
            "column_names_with_comma": "id,name,age",
            "value_for_column_1": "1",
            "value_for_column_2": "Chris",
            "value_for_column_3": "25"
        }
        # 插入记录
        result = insert_data_with_columns(params, self.assets, None)
        print(result)
        self.assertEqual(result['data']['err_code'], 0)
        self.assertEqual(result['data']['row_count'], 1)

        # 插入重复记录
        result = insert_data_with_columns(params, self.assets, None)
        print(result)
        self.assertEqual(result['data']['err_code'], 500)

        # 插入记录，忽略重复
        params["enable_insert_ignore"] = True
        result = insert_data_with_columns(params, self.assets, None)
        print(result)
        self.assertEqual(result['data']['err_code'], 0)

    # @unittest.order(4)
    def test_4_replace_data_with_columns(self):
        params = {
            "table_name": "_mysql_client_v2_test",
            "column_names_with_comma": "id,name,age",
            "value_for_column_1": "2",
            "value_for_column_2": "Zeander",
            "value_for_column_3": "35"
        }
        result = replace_data_with_columns(params, self.assets, None)
        print(result)
        self.assertEqual(result['data']['err_code'], 0)
        self.assertEqual(result['data']['row_count'], 1)

    # @unittest.order(5)
    def test_5_update_data_with_columns(self):
        params = {
            "table_name": "_mysql_client_v2_test",
            "where_condition": "id=2",
            "column_names_with_comma": "name,age",
            "value_for_column_1": "wzfukui",
            "value_for_column_2": "40"
        }
        result = update_data_with_columns(params, self.assets, None)
        print(result)
        self.assertEqual(result['data']['err_code'], 0)
        self.assertEqual(result['data']['row_count'], 1)

    # @unittest.order(9)
    def test_9_clean_up(self):
        params = {
            "sql": "DROP TABLE IF EXISTS _mysql_client_v2_test"
        }
        result = execute_sql(params, self.assets, None)
        self.assertEqual(result['data']['err_code'], 0)

if __name__ == '__main__':
    # unittest.main()
    suite = unittest.TestSuite()
    suite.addTest(TestMySQLClient('test_1_health_check'))
    suite.addTest(TestMySQLClient('test_2_execute_sql'))
    suite.addTest(TestMySQLClient('test_3_insert_data_with_columns'))
    suite.addTest(TestMySQLClient('test_4_replace_data_with_columns'))
    suite.addTest(TestMySQLClient('test_5_update_data_with_columns'))
    suite.addTest(TestMySQLClient('test_9_clean_up'))

    runner = unittest.TextTestRunner()
    runner.run(suite)