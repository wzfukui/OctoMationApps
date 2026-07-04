import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
import re
from hg_special import  get_mysql_params_from_sdk, get_mysql_params_for_app_from_env

class ActiveListManager:
    _prefix = '_al_'
    _list_name_pattern = re.compile(r'^[a-zA-Z0-9_\-]+$')
    _identifier_pattern = re.compile(r'^[a-zA-Z0-9_]+$')

    def __init__(self, hg_client=None):
        self.db_connection = None
        self.hg_client = hg_client
        self.msg = "ActiveListManager:\n"

    def _validate_list_name(self, table_name):
        if table_name is None or table_name == "":
            raise ValueError("活动列表名称不能为空")
        if not self._list_name_pattern.match(table_name):
            raise ValueError("活动列表名称不符合要求：字母、数字、下划线、中划线的组合")
        max_name_length = 64 - len(self._prefix)
        if len(f"{self._prefix}{table_name}") > 64:
            raise ValueError(f"活动列表名称过长，最长支持{max_name_length}个字符")

    def _quote_identifier(self, identifier):
        if identifier is None or not self._identifier_pattern.match(identifier):
            raise ValueError(f"非法数据库标识符：{identifier}")
        return f"`{identifier}`"

    def _table_identifier(self, table_name):
        self._validate_list_name(table_name)
        return f"`{self._prefix}{table_name}`"

    def _resolve_time_window(self, end_time=None, time_delta="30m"):
        if end_time is None:
            end_time = datetime.now()
        elif isinstance(end_time, str):
            end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")

        if not time_delta or len(time_delta) < 2:
            raise ValueError("Invalid time_delta format. Use 'm' for minutes, 'h' for hours, 'd' for days.")

        delta_amount = int(time_delta[:-1])
        delta_unit = time_delta[-1]
        if delta_unit == 'm':
            delta = timedelta(minutes=delta_amount)
        elif delta_unit == 'h':
            delta = timedelta(hours=delta_amount)
        elif delta_unit == 'd':
            delta = timedelta(days=delta_amount)
        else:
            raise ValueError("Invalid time_delta format. Use 'm' for minutes, 'h' for hours, 'd' for days.")

        return end_time - delta, end_time

    def _ensure_active_list_indexes(self, cursor, table_name, key_col="`_key`", value_col="`_value`"):
        index_definitions = {
            "idx_al_key": f"CREATE INDEX `idx_al_key` ON {{table_name}} ({key_col}(255));",
            "idx_al_value": f"CREATE INDEX `idx_al_value` ON {{table_name}} ({value_col}(255));",
            "idx_al_create_time": "CREATE INDEX `idx_al_create_time` ON {table_name} (`create_time`);",
            "idx_al_update_time": "CREATE INDEX `idx_al_update_time` ON {table_name} (`update_time`);",
            "idx_al_key_create_time": f"CREATE INDEX `idx_al_key_create_time` ON {{table_name}} ({key_col}(255), `create_time`);",
            "idx_al_value_create_time": f"CREATE INDEX `idx_al_value_create_time` ON {{table_name}} ({value_col}(255), `create_time`);",
            "idx_al_key_value_create_time": f"CREATE INDEX `idx_al_key_value_create_time` ON {{table_name}} ({key_col}(255), {value_col}(255), `create_time`);",
        }
        cursor.execute(f"SHOW INDEX FROM {table_name};")
        existing_indexes = {row[2] for row in cursor.fetchall()}
        for index_name, create_sql in index_definitions.items():
            if index_name not in existing_indexes:
                cursor.execute(create_sql.format(table_name=table_name))
    
    # 数据库连接
    def get_db_connection(self):
        db_conn = None
        # 获取数据库连接信息
        # mysql_params = get_mysql_params_from_env()
        # mysql_params = get_mysql_params_for_app_from_env()
        mysql_params = get_mysql_params_from_sdk(self.hg_client)
        # self.msg += str(mysql_params) + "\n"
        db_host = mysql_params['host']
        db_name = mysql_params['database']
        db_username = mysql_params['username']
        db_password = mysql_params['password']
        db_port = mysql_params['port']
        db_ssl = mysql_params['ssl']
        # self.msg += str(mysql_params) + "\n"
        try:
            connection = mysql.connector.connect(
                host=db_host,
                database=db_name,
                user=db_username,
                password=db_password,
                port=db_port,
                ssl_disabled=not db_ssl
            )
            db_conn = connection
        except Error as e:
            self.msg += f"get_db_connection() Error: {e}\n"
        return db_conn

    # 初始化活动列表表
    def initialize_active_list_table(self, table_name, key_name="_key", value_name="_value", remark_name="_remark"):
        ret = False
        conn = None
        cursor = None
        try:
            table_name = self._table_identifier(table_name)
            key_col = self._quote_identifier(key_name)
            value_col = self._quote_identifier(value_name)
            remark_col = self._quote_identifier(remark_name)
            conn = self.get_db_connection()
            if not conn:
                self.msg +="Failed to connect to database\n"
                return ret
            cursor = conn.cursor()
            
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                {key_col} VARCHAR(512) NOT NULL,
                {value_col} TEXT,
                {remark_col} TEXT,
                _ext_01 TEXT,
                _ext_02 TEXT,
                _ext_03 TEXT,
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                expire_time DATETIME DEFAULT NULL,
                KEY `idx_al_key` ({key_col}(255)),
                KEY `idx_al_value` ({value_col}(255)),
                KEY `idx_al_create_time` (`create_time`),
                KEY `idx_al_update_time` (`update_time`),
                KEY `idx_al_key_create_time` ({key_col}(255), `create_time`),
                KEY `idx_al_value_create_time` ({value_col}(255), `create_time`),
                KEY `idx_al_key_value_create_time` ({key_col}(255), {value_col}(255), `create_time`)
            );
            """
            cursor.execute(create_table_query)
            self._ensure_active_list_indexes(cursor, table_name, key_col=key_col, value_col=value_col)
            conn.commit()
            ret = True
        except (Error, ValueError) as e:
            self.msg += f"initialize_active_list_table() Error: {e}\n"
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        return ret

    # 添加记录到列表
    def add_record_to_active_list(self, table_name, item_key=None, item_value=None, item_remark="", replace_if_exists=False):
        ret = False
        conn = None
        cursor = None
        try:
            table_name = self._table_identifier(table_name)
            conn = self.get_db_connection()
            if not conn:
                self.msg +="Failed to connect to database\n"
                return ret
            cursor = conn.cursor()
            if replace_if_exists:
                # 先查询数据库，看是否有相同的key存在
                select_query = f"SELECT COUNT(*) FROM {table_name} WHERE _key = %s;"
                cursor.execute(select_query, (item_key,))
                result = cursor.fetchone()
                if result and result[0] > 0:
                    # 存在相同的key，则更新
                    self.msg += f"存在相同的key，更新\n"
                    update_query = f"""
                    UPDATE {table_name} SET _value = %s, _remark = %s, update_time = CURRENT_TIMESTAMP
                    WHERE _key = %s;
                    """
                    cursor.execute(update_query, (item_value, item_remark, item_key))
                    conn.commit()
                else:
                    # 不存在相同的key，则插入
                    self.msg += f"不存在相同的key，插入.\n"
                    insert_query = f"""
                    INSERT INTO {table_name} (_key, _value, _remark, create_time, update_time)
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
                    """
                    cursor.execute(insert_query, (item_key, item_value, item_remark))
                    conn.commit()
            else:
                # 直接插入数据
                insert_query = f"""
                INSERT INTO {table_name} (_key, _value, _remark, create_time, update_time)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
                """
                cursor.execute(insert_query, (item_key, item_value, item_remark))
                conn.commit()
            ret = True
        # except mysql.connector.IntegrityError as err:
        #     # Catch duplicate entry error
        #     if err.errno == mysql.connector.errorcode.ER_DUP_ENTRY:
        except (Error, ValueError) as e:
            self.msg += f"add_record_to_active_list() Error: {e}\n"
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        return ret

    # 在时间窗口内计数
    def count_records_within_time_window(self, table_name, item_key, end_time=None, time_delta="30m"):
        xcount = None
        conn = None
        cursor = None
        try:
            table_name = self._table_identifier(table_name)
            start_time, end_time = self._resolve_time_window(end_time, time_delta)
            conn = self.get_db_connection()
            if not conn:
                self.msg += f"DB connection error.\n"
                return xcount
            cursor = conn.cursor()
            if item_key == "*" or item_key == "":
                count_query = f"""
                SELECT COUNT(*) FROM {table_name}
                WHERE create_time BETWEEN %s AND %s;
                """
                cursor.execute(count_query, (start_time, end_time))
            else:
                count_query = f"""
                SELECT COUNT(*) FROM {table_name}
                WHERE _key = %s AND create_time BETWEEN %s AND %s;
                """
                cursor.execute(count_query, (item_key, start_time, end_time))
            count = cursor.fetchone()[0]
            xcount = count
        except Exception as e:
            self.msg += f"count_records_within_time_window() Error: {e}\n"
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        return xcount

    # 列举出所有活动列表
    def list_all_active_lists(self):
        """
        列举出所有活动列表，以_al_开头的表名
        :return: 列表名称组成的list
        """
        lists = None
        conn = None
        cursor = None
        try:
            conn = self.get_db_connection()
            if not conn:
                self.msg +="Failed to connect to database\n"
                return lists
            cursor = conn.cursor()
            count_query = f"""SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND table_name LIKE '{self._prefix}%';
            """
            cursor.execute(count_query)
            result = cursor.fetchall()
            lists = [table_name.replace(self._prefix, "",1) for table_name, in result]
        except Exception as e:
            self.msg += f"list_all_active_lists() Error: {e}\n"
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        return lists

    # 从列表中移除项
    def remove_record_from_active_list(self, table_name, item_key):
        ret = False
        conn = None
        cursor = None
        try:
            table_name = self._table_identifier(table_name)
            conn = self.get_db_connection()
            if not conn:
                return ret
            cursor = conn.cursor()
            
            delete_query = f"DELETE FROM {table_name} WHERE _key = %s;"
            cursor.execute(delete_query, (item_key,))
            conn.commit()
            ret = True
        except (Error, ValueError) as e:
            self.msg += f"remove_record_from_active_list() Error: {e}\n"
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        return ret
    
    # 从列表中移除项
    def clear_active_list(self, table_name):
        ret = False
        conn = None
        cursor = None
        try:
            table_name = self._table_identifier(table_name)
            conn = self.get_db_connection()
            if not conn:
                self.msg +="Failed to connect to database\n"
                return ret
            cursor = conn.cursor()
            truncate_command = f"TRUNCATE TABLE {table_name};"
            cursor.execute(truncate_command)
            conn.commit()
            ret = True
        except (Error, ValueError) as e:
            self.msg += f"clear_active_list() Error: {e}\n"
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        return ret
    
    # 删除活动列表
    def delete_active_list(self, table_name):
        ret = False
        conn = None
        cursor = None
        try:
            table_name = self._table_identifier(table_name)
            conn = self.get_db_connection()
            if not conn:
                self.msg +="Failed to connect to database\n"
                return ret
            cursor = conn.cursor()
            drop_command = f"DROP TABLE IF EXISTS {table_name};"
            cursor.execute(drop_command)
            conn.commit()
            ret = True
        except (Error, ValueError) as e:
            self.msg += f"delete_active_list() Error: {e}\n"
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        return ret

    # 按照创建时间的天、小时、分钟统计活动列表中的元素数量
    def count_records_by_time_unit(self, table_name, time_unit="day", unit_amount=None):
        ret = None
        conn = None
        cursor = None
        try:    
            table_name = self._table_identifier(table_name)
            conn = self.get_db_connection()
            if not conn:
                self.msg +="Failed to connect to database\n"
                return ret
            cursor = conn.cursor()
            if unit_amount is not None:
                unit_amount = int(unit_amount)
            if time_unit.lower() == "day":
                # 按天统计N天以内的元素记录，根据create_time字段分组
                if unit_amount is None:
                    unit_amount = 7
                count_query = f"""
                SELECT DATE(create_time) AS XTIME, COUNT(*) AS XCOUNT FROM {table_name}
                WHERE create_time >= DATE_SUB(NOW(), INTERVAL {unit_amount} DAY)
                GROUP BY XTIME; 
                """
            elif time_unit.lower() == "hour":
                # 按小时统计N小时以内的元素记录，对格式化之后的create_time字段XTIME进行分组，XTIME格式：MMDD_HH
                # MySQL语句中对create_time先做format，然后再进行分组
                if unit_amount is None:
                    unit_amount = 24
                count_query = f"""
                SELECT DATE_FORMAT(create_time, '%m%d_%H') AS XTIME, COUNT(*) AS XCOUNT FROM {table_name}
                WHERE create_time >= DATE_SUB(NOW(), INTERVAL {unit_amount} HOUR)
                GROUP BY XTIME;
                """
            elif time_unit.lower() == "minute":
                # 按分钟统计N分钟以内的元素记录，对格式化之后的create_time字段XTIME进行分组，XTIME格式：MMDD_HHMM
                # MySQL语句中对create_time先做format，然后再进行分组
                if unit_amount is None:
                    unit_amount = 60
                count_query = f"""
                SELECT DATE_FORMAT(create_time, '%m%d_%H%i') AS XTIME, COUNT(*) AS XCOUNT FROM {table_name}
                WHERE create_time >= DATE_SUB(NOW(), INTERVAL {unit_amount} MINUTE)
                GROUP BY XTIME;
                """
            else:
                self.msg += f"Invalid time_unit format. Use 'day', 'hour', or'minute'.\n"
                return ret
            cursor.execute(count_query)
            result = cursor.fetchall()
            ret = result
        except (Error, ValueError) as e:
            self.msg += f"count_records_by_time_unit() Error: {e}\n"
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        return ret

    def get_records_time_trend(self, table_name, item_key="",time_unit="day", unit_amount=None):
        """
        获取指定key的活动列表中的时间趋势数据，天/时/分
        """
        ret = None
        conn = None
        cursor = None
        try:    
            table_name = self._table_identifier(table_name)
            conn = self.get_db_connection()
            if not conn:
                self.msg +="Failed to connect to database\n"
                return ret
            cursor = conn.cursor()
            params = []
            select_query = f"SELECT DATE(create_time) AS XTIME, COUNT(*) AS XCOUNT FROM {table_name} WHERE "
            
            if item_key:
                select_query += "_key = %s AND "
                params.append(item_key)
    
            if time_unit.lower() == "day":
                # 按天统计N天以内的元素记录，根据create_time字段分组
                if unit_amount is None:
                    unit_amount = 7
                select_query += f"create_time >= DATE_SUB(NOW(), INTERVAL {unit_amount} DAY) GROUP BY XTIME; "
            elif time_unit.lower() == "hour":
                # 按小时统计N小时以内的元素记录，对格式化之后的create_time字段XTIME进行分组，XTIME格式：MMDD_HH
                # MySQL语句中对create_time先做format，然后再进行分组
                if unit_amount is None:
                    unit_amount = 24
                select_query += f"create_time >= DATE_SUB(NOW(), INTERVAL {unit_amount} HOUR) GROUP BY XTIME;"
            elif time_unit.lower() == "minute":
                # 按分钟统计N分钟以内的元素记录，对格式化之后的create_time字段XTIME进行分组，XTIME格式：MMDD_HHMM
                # MySQL语句中对create_time先做format，然后再进行分组
                if unit_amount is None:
                    unit_amount = 60
                select_query += f"create_time >= DATE_SUB(NOW(), INTERVAL {unit_amount} MINUTE) GROUP BY XTIME;"
            else:
                self.msg += f"Invalid time_unit format. Use 'day', 'hour', or'minute'.\n"
                return ret
            cursor.execute(select_query, tuple(params))
            result = cursor.fetchall()
            ret = result
        except (Error, ValueError) as e:
            self.msg += f"get_records_time_trend() Error: {e}\n"
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        return ret

    def check_record_exists_in_active_list(
        self,
        table_name,
        item_key=None,
        item_value=None,
        match_mode="key",
        end_time=None,
        time_delta=None
    ):
        """
        判断活动列表中是否存在指定记录。

        match_mode:
        - key: 按_key判断
        - value: 按_value判断
        - key_value: 同时按_key和_value判断
        """
        ret = None
        conn = None
        cursor = None
        try:
            table_name = self._table_identifier(table_name)
            where_clauses = []
            query_params = []
            if match_mode == "key":
                if item_key is None or item_key == "":
                    raise ValueError("item_key不能为空")
                where_clauses.append("_key = %s")
                query_params.append(item_key)
            elif match_mode == "value":
                if item_value is None or item_value == "":
                    raise ValueError("item_value不能为空")
                where_clauses.append("_value = %s")
                query_params.append(item_value)
            elif match_mode == "key_value":
                if item_key is None or item_key == "" or item_value is None or item_value == "":
                    raise ValueError("item_key和item_value不能为空")
                where_clauses.append("_key = %s")
                query_params.append(item_key)
                where_clauses.append("_value = %s")
                query_params.append(item_value)
            else:
                raise ValueError("match_mode仅支持key、value、key_value")

            if time_delta:
                start_time, end_time = self._resolve_time_window(end_time, time_delta)
                where_clauses.append("create_time BETWEEN %s AND %s")
                query_params.extend([start_time, end_time])

            conn = self.get_db_connection()
            if not conn:
                self.msg += "Failed to connect to database\n"
                return ret
            cursor = conn.cursor()
            where_sql = " AND ".join(where_clauses)
            count_query = f"SELECT COUNT(*) FROM {table_name} WHERE {where_sql};"
            cursor.execute(count_query, tuple(query_params))
            record_count = cursor.fetchone()[0]
            ret = {
                "record_exists": record_count > 0,
                "record_count": record_count
            }
        except Exception as e:
            self.msg += f"check_record_exists_in_active_list() Error: {e}\n"
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        return ret

    # 快速查看活动列表，返回最新10条记录
    def quick_view_active_list(self, table_name, item_key="*"):
        ret = None
        conn = None
        cursor = None
        try:
            table_name = self._table_identifier(table_name)
            conn = self.get_db_connection()
            if not conn:
                self.msg +="Failed to connect to database\n"
                return ret
            cursor = conn.cursor()
            if item_key == "" or item_key == "*":
                quick_view_query = f"SELECT _key, _value, _remark, create_time, update_time FROM {table_name} ORDER BY create_time DESC LIMIT 10;"
                cursor.execute(quick_view_query)
            else:
                quick_view_query = f"SELECT _key, _value, _remark, create_time, update_time FROM {table_name} WHERE _key = %s ORDER BY create_time DESC LIMIT 10;"
                cursor.execute(quick_view_query, (item_key,))
            result = cursor.fetchall()
            ret = result
        except (Error, ValueError) as e:
            self.msg += f"quick_view_active_list() Error: {e}\n"
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        return ret

if __name__ == '__main__':
    import time
    alm = ActiveListManager()
    print(alm.get_db_connection())
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    alm.initialize_active_list_table("test_activelist")
    alm.add_record_to_active_list("test_activelist", "key1", "value1-1", "remark1-1")
    alm.add_record_to_active_list("test_activelist", "key1", "value1-2", "remark1-2")
    alm.add_record_to_active_list("test_activelist", "key2", "value2", "remark2")
    alm.add_record_to_active_list("test_activelist", "key3", "value3", "remark3")
    alm.add_record_to_active_list("test_activelist", "key3", "value3", "remark3",True)
    print(alm.count_records_within_time_window("test_activelist", "key1"))
    print(alm.count_records_within_time_window("test_activelist", "key2"))
    print(alm.count_records_within_time_window("test_activelist", "key3"))
    alm.remove_record_from_active_list("test_activelist", "key2")
    print(alm.count_records_within_time_window("test_activelist", "key2", current_time, "30m"))
    print(alm.count_records_within_time_window("test_activelist", "key1", current_time))
    print(alm.count_records_within_time_window("test_activelist", "key4"))
    print(alm.list_all_active_lists())
    try:
        alm.is_key_in_active_list("key1", "test_activelist")
    except mysql.connector.Error as e:
        print(e)
