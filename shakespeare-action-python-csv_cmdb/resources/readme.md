# APP文档帮助文档

## 一、APP介绍

描述：csv_cmdb - 基于 CSV 台账文件的轻量 CMDB 查询应用，适用于演示或小规模资产台账联动。支持在 HoneyGuide 后台资产配置中上传 CSV 文件，然后在剧本中根据 IP 查询负责人信息，或根据负责人 AD 账号查询名下资产。

| 内容 | 详细描述 |
| ---- | ------ |
| app版本 | 1.0.0 |
| 发布时间 | 2026-06-25 00:00:00 |
| 应用连接方式 | 上传 CSV 文件 |
| 作者 | 雾帜智能 |

## 二、配置说明

### 系统配置

| 参数名 | 参数描述 | 参数类型 | 是否必填 | 默认值 |
|--------|----------|----------|----------|--------|
| cmdb_csv_file | CMDB 台账 CSV 文件对象 | outside_file | 是 | |

HoneyGuide 前端会在文件控件上传 CSV 后传入文件路径，应用会按该路径读取 CSV。

### 推荐 CSV 表头

```csv
ip,hostname,owner_name,mobile,email,department,ad_account,wechat_work_id,asset_type,location,status
```

字段说明：

| 字段名 | 说明 |
|--------|------|
| ip | 资产 IP 地址 |
| hostname | 主机名 |
| owner_name | 负责人姓名 |
| mobile | 负责人电话 |
| email | 负责人邮箱 |
| department | 负责人部门 |
| ad_account | 负责人 AD 账号 |
| wechat_work_id | 企业微信 ID |
| asset_type | 资产类型 |
| location | 资产位置 |
| status | 资产状态 |

应用也兼容部分常见别名，例如 `ip_address`、`owner`、`phone`、`mail`、`owner_id` 等。

## 三、APP动作清单

### health_check（检查 CMDB CSV 文件是否可读取）

#### 入参

无。

#### 出参

| 参数名 | 参数描述 | 参数类型 | 备注 |
|--------|----------|----------|------|
| action_result.data.status | 状态 | string | ok/error |
| action_result.data.msg | 健康检查消息 | string | |
| action_result.data.csv_file | CSV 文件路径 | string | |
| action_result.data.asset_count | 资产数量 | integer | |

### query_owner_by_ip（根据 IP 查询资产负责人信息）

#### 入参

| 参数名 | 参数描述 | 参数类型 | 是否必填 | 默认值 |
|--------|----------|----------|----------|--------|
| ip | 资产 IP 地址 | string | 是 | |

#### 出参

| 参数名 | 参数描述 | 参数类型 | 备注 |
|--------|----------|----------|------|
| action_result.data.matched | 是否匹配到资产 | boolean | |
| action_result.data.owner_id | 负责人 ID | string | |
| action_result.data.owner_name | 负责人姓名 | string | |
| action_result.data.ad_account | 负责人 AD 账号 | string | |
| action_result.data.email | 负责人邮箱 | string | |
| action_result.data.mobile | 负责人电话 | string | |
| action_result.data.department | 负责人部门 | string | |
| action_result.data.wechat_work_id | 企业微信 ID | string | |
| action_result.data.owner | 负责人信息对象 | jsonObject | |
| action_result.data.asset | 匹配到的资产完整记录 | jsonObject | |

### query_assets_by_ad_id（根据负责人 AD 账号查询名下资产）

#### 入参

| 参数名 | 参数描述 | 参数类型 | 是否必填 | 默认值 |
|--------|----------|----------|----------|--------|
| ad_account | 负责人 AD 账号 | string | 是 | |

#### 出参

| 参数名 | 参数描述 | 参数类型 | 备注 |
|--------|----------|----------|------|
| action_result.data.matched | 是否匹配到资产 | boolean | |
| action_result.data.count | 资产数量 | integer | |
| action_result.data.assets.* | 资产列表循环输出 | jsonObject | |
| action_result.data.assets | 资产列表 | jsonArray | |
| action_result.data.owner | 负责人信息对象 | jsonObject | |

## 四、使用建议

在钓鱼邮件或终端阻断剧本中，可以先从告警中提取终端 IP，再调用 `query_owner_by_ip` 得到 `email`、`mobile`、`ad_account`，后续串联邮件通知、短信/企微通知、AD 账号隔离等动作。

## 五、测试说明

应用内置匿名化测试文件 `testdata/cmdb_sample_anonymized.csv` 和单元测试 `test_csv_cmdb.py`，用于验证健康检查、按 IP 查询负责人、按 AD 账号查询资产等能力。测试数据使用保留地址段和示例邮箱域名，不包含真实用户信息。
