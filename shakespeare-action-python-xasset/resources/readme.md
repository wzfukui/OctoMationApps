# XAsset 资产管理

> 版本: v1.0.0
> 供应商: 雾帜智能
> 类型: 离线模拟产品

## 应用简介

离线模拟资产与负责人 CMDB，提供资产归属、标签和关联查询能力。本应用不连接任何外部系统，所有动作均基于本地 SQLite 状态库和内置样例数据执行，适合开箱即用的 SOAR 剧本演示、培训和 PoC。

## 配置参数

- `database_path`: SQLite 模拟状态库路径，默认 `/tmp/xasset.db`
- `scenario_profile`: 模拟场景名称，默认 `default`
- `scenario_seed`: 模拟数据种子，默认 `x-series-default`
- `delay_min_seconds`: 写入/处置动作最小模拟延迟秒数，默认 `1`
- `delay_max_seconds`: 写入/处置动作最大模拟延迟秒数，默认 `3`

## 动作列表

| 动作 | 类型 | 示例参数 | 说明 |
|---|---|---|---|
| `health_check` | query | - | 健康检查 |
| `list_assets` | query | `{"owner":"alice","limit":20}` | 查询资产列表 |
| `query_asset_by_ip` | query | `{"ip":"10.10.8.23"}` | 根据 IP 查询资产负责人信息 |
| `query_assets_by_owner` | query | `{"owner":"alice"}` | 根据负责人账号查询名下资产 |
| `query_asset_relations` | query | `{"asset_id":"asset-web-01"}` | 查询资产关联关系 |
| `query_inventory_summary` | query | - | 查询资产统计摘要 |
| `update_asset_tag` | write | `{"asset_id":"asset-web-01","tag":"incident","value":"IR-2026-0001"}` | 更新资产标签 |
| `create_asset` | write | `{"asset_id":"asset-demo-01","asset_name":"demo-server-01","ip":"10.30.6.10","asset_type":"server","owner":"secops","status":"online"}` | 新增资产 |
| `update_asset` | write | `{"asset_id":"asset-web-01","owner":"alice","status":"maintenance"}` | 更新资产信息 |
| `delete_asset` | write | `{"asset_id":"asset-lb-01","reason":"资产下线"}` | 删除资产 |

## 内置样例索引

以下值可以直接用于动作参数测试，不需要连接外部系统。

- 负责人账号: `alice`, `bob`, `carol`
- 用户/账号: `alice`, `bob`, `carol`
- IP: `10.10.8.10`, `10.10.8.23`, `10.10.9.15`, `10.20.4.77`

## 内置样例数据

| ID | 名称 | IP/指标 | 负责人 | 用户/账号 | 状态 | 等级 | 关键信息 | 摘要 |
|---|---|---|---|---|---|---|---|---|
| `asset-web-01` | prod-web-01 | 10.10.8.23 | alice | alice | online | high | 部门=电商业务部；业务=checkout；标签=internet,linux,critical；关联=asset-db-01,asset-lb-01 | 互联网业务 Web 服务器，近期命中 WAF 攻击与 HIDS 异常登录 |
| `asset-db-01` | mysql-core-01 | 10.10.9.15 | bob | bob | online | medium | 部门=平台工程；业务=order；标签=mysql,pci | 核心订单数据库，禁止直接暴露互联网访问 |
| `asset-lb-01` | prod-lb-01 | 10.10.8.10 | alice | alice | online | low | 部门=电商业务部；业务=checkout；标签=internet,lb；关联=asset-web-01 | 互联网业务入口负载均衡，关联 prod-web-01 |
| `asset-laptop-07` | fin-laptop-07 | 10.20.4.77 | carol | carol | online | medium | 部门=财务部；业务=finance；标签=windows,office | 财务终端，曾收到钓鱼邮件 |

## 返回结构

所有动作统一返回 `code`、`msg`、`data`、`summary`。查询类动作返回 `records`、`record`、`total_count` 和 `statistics`；写入、通知、创建、更新和删除类动作返回 `operation`、`records` 和 `affected_count`；健康检查返回 `system_info`，其中包含 `sample_values` 和 `sample_records` 便于发现可用样例值。

## 适用剧本

- 安全告警查询、研判和上下文补全
- 恶意 IP、账号、主机、邮件、文件的模拟处置
- 工单、通知和审计留痕演示
- 无真实安全设备或 SaaS 服务时的产品体验与编排训练
