# -*- coding: utf-8 -*-
import mysql.connector
from action_sdk_for_cache.action_cache_sdk import HoneyGuide

def execute_sql(params, assets, context_info):
    """执行SQL语句"""
    # MySQL数据库主机名
    host = assets.get('host', '127.0.0.1')
    # MySQL数据库端口
    port = int(assets.get('port', 3306))
    # MySQL数据库库名
    database = assets.get('database', "test")
    # MySQL数据库用户名
    username = assets.get('username', "root")
    # MySQL数据库密码
    password = assets.get('password', "")
    # MySQL数据库字符集
    charset = assets.get('charset', "utf8mb4")

    # SQL语句
    sql = params.get("sql", "")

    json_ret = {"code": 200, "msg": "","data": {"err_code": 0, "err_msg": "", "row_count": 0, "rows": [], "column_names": []}}

    hg_client = HoneyGuide(context_info=context_info)
    hg_client.actionLog.info(f"执行SQL语句：{sql}")

    if not sql:
        json_ret["data"]['err_code'] = 400
        json_ret["data"]['err_msg'] = "SQL语句不能为空"
        return json_ret
    
    try:
        # 连接数据库
        conn = mysql.connector.connect(
            host=host,
            port=port,
            database=database,
            user=username,
            password=password,
            charset=charset
        )
        # 创建游标
        cursor = conn.cursor()
        # 执行SQL语句
        cursor.execute(sql)
        if sql.split()[0].upper() in( "SELECT", "SHOW", "DESC", "EXPLAIN" ):
            # 获取查询结果
            rows = cursor.fetchall()
            column_names = [i[0] for i in cursor.description]
            json_ret["data"]["rows"] = rows
            json_ret["data"]["column_names"] = column_names
        else:
            conn.commit()
            # json_ret["msg"] = cursor.description
        # 获取查询结果行数
        row_count = cursor.rowcount
        json_ret["data"]["row_count"] = row_count
        
        # 关闭游标
        cursor.close()
        # 关闭数据库连接
        conn.close()
        # 设置返回值
        
        
    except Exception as e:
        json_ret["data"]['err_code'] = 500
        json_ret["data"]['err_msg'] = f"执行SQL语句:{sql},失败：{e}"

    return json_ret 

def insert_data_with_columns(params, assets, context_info):
    """根据给定的列名和值，插入数据"""
    json_ret = {"code": 200, "msg": "","data": {"err_code": 0, "err_msg": "", "row_count": 0, "success": True}}
    
    # MySQL数据库主机名
    host = assets.get('host', '127.0.0.1')
    # MySQL数据库端口
    port = int(assets.get('port', 3306))
    # MySQL数据库库名
    database = assets.get('database', "test")
    # MySQL数据库用户名
    username = assets.get('username', "root")
    # MySQL数据库密码
    password = assets.get('password', "")
    # MySQL数据库字符集
    charset = assets.get('charset', "utf8mb4")

    enable_insert_ignore = params.get("enable_insert_ignore", False)
    # 表名
    table_name = params.get("table_name", "")    
    # 列名
    column_names_with_comma = params.get("column_names_with_comma", "").split(",")

    if not table_name or len(column_names_with_comma) == 0:
        json_ret["data"]["err_code"] = 400
        json_ret["data"]["err_msg"] = "表名或列名不能为空"
        return json_ret

    # 根据colums_with_comma获取values，并做计数，如果values数量不多等于columns数量，则返回错误
    for i in range(len(column_names_with_comma)):
        value_variable_name = f"value_for_column_{i+1}"
        globals()[value_variable_name] = params.get(value_variable_name, "")
        if globals()[value_variable_name] == "NULL":
            globals()[value_variable_name] = None
        if globals()[value_variable_name] == "":
            json_ret["data"]["err_code"] = 400
            json_ret["data"]["err_msg"] = "参数错误，values数量不等于columns数量，请重新检查！"
            return json_ret

    
    if enable_insert_ignore:
        sql = f"INSERT IGNORE INTO {table_name} ({','.join(column_names_with_comma)}) VALUES ("
    else:
        sql = f"INSERT INTO {table_name} ({','.join(column_names_with_comma)}) VALUES ("

    # 组装values数组
    placeholders = []
    values = []
    for i in range(len(column_names_with_comma)):
        placeholders.append("%s")
        values.append(globals()[f"value_for_column_{i+1}"])
    
    sql += ",".join(placeholders) + ")"
    values = tuple(values)
    try:
        # 连接数据库
        conn = mysql.connector.connect(
            host=host,
            port=port, 
            database=database,
            user=username,
            password=password,
            charset=charset
        )
        # 创建游标
        cursor = conn.cursor()
        # 执行SQL语句
        cursor.execute(sql, values)
        # 获取查询结果行数
        row_count = cursor.rowcount
        # 关闭游标
        cursor.close()
        # 提交事务
        conn.commit()
        # 关闭数据库连接
        conn.close()
        # 设置返回值
        json_ret["data"]["row_count"] = row_count
    except Exception as e:
        json_ret["data"]['err_code'] = 500
        json_ret["data"]['err_msg'] = f"执行SQL语句:{sql},失败：{e}"
        json_ret["data"]['success'] = False
    return json_ret



def replace_data_with_columns(params, assets, context_info):
    """根据给定的列名和值，replace数据"""
    json_ret = {"code": 200, "msg": "","data": {"err_code": 0, "err_msg": "", "row_count": 0, "success": True}}
    
    # MySQL数据库主机名
    host = assets.get('host', '127.0.0.1')
    # MySQL数据库端口
    port = int(assets.get('port', 3306))
    # MySQL数据库库名
    database = assets.get('database', "test")
    # MySQL数据库用户名
    username = assets.get('username', "root")
    # MySQL数据库密码
    password = assets.get('password', "")
    # MySQL数据库字符集
    charset = assets.get('charset', "utf8mb4")

    table_name = params.get("table_name", "")    
    # 列名
    column_names_with_comma = params.get("column_names_with_comma", "").split(",")

    if not table_name or len(column_names_with_comma) == 0:
        json_ret["data"]["err_code"] = 400
        json_ret["data"]["err_msg"] = "表名或列名不能为空"
        return json_ret

    # 根据colums_with_comma获取values，并做计数，如果values数量不多等于columns数量，则返回错误
    for i in range(len(column_names_with_comma)):
        value_variable_name = f"value_for_column_{i+1}"
        globals()[value_variable_name] = params.get(value_variable_name, "")
        if globals()[value_variable_name] == "NULL":
            globals()[value_variable_name] = None
        if globals()[value_variable_name] == "":
            json_ret["data"]["err_code"] = 400
            json_ret["data"]["err_msg"] = "参数错误，values数量不等于columns数量，请重新检查！"
            return json_ret

    
    sql = f"REPLACE INTO {table_name} ({','.join(column_names_with_comma)}) VALUES ("

    # 组装values数组
    placeholders = []
    values = []
    for i in range(len(column_names_with_comma)):
        placeholders.append("%s")
        values.append(globals()[f"value_for_column_{i+1}"])
    
    sql += ",".join(placeholders) + ")"
    values = tuple(values)
    try:
        # 连接数据库
        conn = mysql.connector.connect(
            host=host,
            port=port, 
            database=database,
            user=username,
            password=password,
            charset=charset
        )
        # 创建游标
        cursor = conn.cursor()
        # 执行SQL语句
        cursor.execute(sql, values)
        # 获取查询结果行数
        row_count = cursor.rowcount
        # 关闭游标
        cursor.close()
        # 提交事务
        conn.commit()
        # 关闭数据库连接
        conn.close()
        # 设置返回值
        json_ret["data"]["row_count"] = row_count
    except Exception as e:
        json_ret["data"]['err_code'] = 500
        json_ret["data"]['err_msg'] = f"执行SQL语句:{sql},失败：{e}"
        json_ret["data"]['success'] = False
    return json_ret


def update_data_with_columns(params, assets, context_info):
    """根据给定的列名和值，update数据"""
    json_ret = {"code": 200, "msg": "","data": {"err_code": 0, "err_msg": "", "row_count": 0, "success": True}}
    
    # MySQL数据库主机名
    host = assets.get('host', '127.0.0.1')
    # MySQL数据库端口
    port = int(assets.get('port', 3306))
    # MySQL数据库库名
    database = assets.get('database', "test")
    # MySQL数据库用户名
    username = assets.get('username', "root")
    # MySQL数据库密码
    password = assets.get('password', "")
    # MySQL数据库字符集
    charset = assets.get('charset', "utf8mb4")

    table_name = params.get("table_name", "")    
    # 列名
    column_names_with_comma = params.get("column_names_with_comma", "").split(",")

    if not table_name or len(column_names_with_comma) == 0:
        json_ret["data"]["err_code"] = 400
        json_ret["data"]["err_msg"] = "表名或列名不能为空"
        return json_ret

    # 根据colums_with_comma获取values，并做计数，如果values数量不多等于columns数量，则返回错误
    for i in range(len(column_names_with_comma)):
        value_variable_name = f"value_for_column_{i+1}"
        globals()[value_variable_name] = params.get(value_variable_name, "")
        if globals()[value_variable_name] == "NULL":
            globals()[value_variable_name] = None
        if globals()[value_variable_name] == "":
            json_ret["data"]["err_code"] = 400
            json_ret["data"]["err_msg"] = "参数错误，values数量不等于columns数量，请重新检查！"
            return json_ret

    where_condition = params.get("where_condition", "")
    if not where_condition:
        json_ret["data"]["err_code"] = 400
        json_ret["data"]["err_msg"] = "where_condition不能为空"
        return json_ret
    
    values = []
    sql = f"UPDATE {table_name} SET "
    for i in range(len(column_names_with_comma)):
        sql += f"{column_names_with_comma[i]} = %s, "
        values.append(globals()[f"value_for_column_{i+1}"])
    sql = sql[:-2] # 去掉最后一个逗号
    if where_condition:
        sql += f" WHERE {where_condition}"
    values = tuple(values)
    try:
        # 连接数据库
        conn = mysql.connector.connect(
            host=host,
            port=port, 
            database=database,
            user=username,
            password=password,
            charset=charset
        )
        # 创建游标
        cursor = conn.cursor()
        # 执行SQL语句
        cursor.execute(sql, values)
        # 获取查询结果行数
        row_count = cursor.rowcount
        # 关闭游标
        cursor.close()
        # 提交事务
        conn.commit()
        # 关闭数据库连接
        conn.close()
        # 设置返回值
        json_ret["data"]["row_count"] = row_count
    except Exception as e:
        json_ret["data"]['err_code'] = 500
        json_ret["data"]['err_msg'] = f"执行SQL语句:{sql},失败：{e}"
        json_ret["data"]['success'] = False
    return json_ret

def health_check(params, assets, context_info):
    """执行SQL查询"""

    # MySQL数据库主机名
    host = assets.get('host', '127.0.0.1')
    # MySQL数据库端口
    port = int(assets.get('port', 3306))
    # MySQL数据库库名
    database = assets.get('database', "test")
    # MySQL数据库用户名
    username = assets.get('username', "root")
    # MySQL数据库密码
    password = assets.get('password', "")
    # MySQL数据库字符集
    charset = assets.get('charset', "utf8mb4")


    # 返回值
    json_ret = {"code": 200, "msg": "","data": {"err_code": 0, "err_msg": ""}, "summary":{"statusCode":200, "msg": "OK"}}

    '''添加函数实现
    
    '''
   
    sql = "SELECT 1"
    try:
        # 连接数据库
        conn = mysql.connector.connect(
            host=host,
            port=port,
            database=database,
            user=username,
            password=password,
            charset=charset
        )
        # 创建游标
        cursor = conn.cursor()
        # 执行SQL语句
        cursor.execute(sql)
        cursor.fetchall()
        cursor.close()
        # 关闭数据库连接
        conn.close()
    except Exception as e:
        json_ret["data"]['err_code'] = 500
        json_ret["data"]['err_msg'] = f"执行SQL语句:{sql},失败：{e}"
        json_ret["summary"]['statusCode'] = 500
        json_ret["summary"]['msg'] = f"执行SQL语句:{sql},失败：{e}"

    return json_ret 