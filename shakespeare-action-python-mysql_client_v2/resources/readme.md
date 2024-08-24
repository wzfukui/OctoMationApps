# MySQL客户端工具2.0
## 基本信息
- 名称：MySQL客户端工具2.0(兼容TDSQL)
- 版本：v2.1.0
- 语言：Python 3.6+
- 开发者：[wzfukui](https://github.com/wzfukui)
- 发布日期：2024-07-28
- 更新日期：2024-08-24

### 依赖

- **mysql-connector-python**
  - 安装命令：`pip install mysql-connector-python`

## 功能

MySQL客户端工具2.0主要功能如下：

- 执行给定的MySQL语句
- 根据给定的字段名和数值，将数据插入数据库表中（INSERT、INSERT IGNORE、REPLACE）
- 根据给定的字段名和数值，更新数据库表中的数据（UPDATE）
- 数据库健康性检查（HEALTH CHECK）

## 数据库资源配置信息

#markdown生成表格，格式如下：字段名、类型、默认值，是否必填，说明

| 字段名 | 类型 | 默认值 | 是否必填 | 说明 |
| host | string | 127.0.0.1 | 是 | MySQL数据库地址 |
| port | int | 3306 | 是 | MySQL数据库端口 |
| database | string |  | 是 | MySQL数据库名称 | 
| user | string | root | 是 | MySQL数据库用户名 |
| password | string |  | 是 | MySQL数据库密码 |
| charset | string | utf8mb4 | 否 | MySQL数据库字符集 |

## 应用动作及数据示例

### EXECUTE

输入SQL语句，执行SQL语句，返回执行结果。

```json
{
  "msg": "",
  "code": 200,
  "data": {
    "err_msg": "",
    "err_code": 0,
    "column_names": [
      "_key",
      "_value"
    ],
    "rows": [
      [
        "7.7.7.7",
        "7.7.7.7-New"
      ],
      [
        "7.7.7.7",
        "7.7.7.7-New"
      ],
      [
        "8.8.8.8",
        "8.8.8.8"
      ],
      [
        "11.11.11.11",
        "11.11.11.11"
      ],
      [
        "1.2.3.99",
        "xxoo"
      ]
    ],
    "row_count": 5
  }
}
```


### INSERT/REPLACE

输入数据库表名、字段名、数值，将数据插入数据库表中，默认提供最多6个字段的支持。

```json
{
  "msg": "",
  "code": 200,
  "data": {
    "err_msg": "",
    "success": true,
    "err_code": 0,
    "row_count": 1
  }
}
```

### UPDATE

输入数据库表名、字段名、数值、条件，根据条件更新数据库表中的数据。

```json
{
  "msg": "",
  "code": 200,
  "data": {
    "err_msg": "",
    "success": true,
    "err_code": 0,
    "row_count": 2
  }
}
```

## HEALTH CHECK

检查数据库连接是否正常。

```json
{
  "msg": "",
  "code": 200,
  "summary": {
    "msg": "OK",
    "statusCode": 200
  },
  "data": {
    "err_msg": "",
    "err_code": 0
  }
}
```

## 单元测试

修改文件中MySQL数据库配置信息，然后执行命令：

```bash
python3 test_mysql_client_v2.py
```

## 更新记录
- 2024-07-28 v1.0 发布
  - 完成基本功能: 执行MySQL语句、插入数据、更新数据、数据库健康性检查
  - 增加单元测试
- 2024-08-24 v2.1.0 验证TDSQL支持，移除SQL语句末尾的分号