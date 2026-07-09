# XCloud 云平台

> 版本: v1.0.0
> 供应商: 雾帜智能
> 类型: 离线模拟产品

## 应用简介

离线模拟云资产和安全组处置能力，支持云资产、安全组、封禁和快照。本应用不连接任何外部系统，所有动作均基于本地 SQLite 状态库和内置样例数据执行，适合开箱即用的 SOAR 剧本演示、培训和 PoC。

## 配置参数

- `database_path`: SQLite 模拟状态库路径，默认 `/tmp/xcloud.db`
- `scenario_profile`: 模拟场景名称，默认 `default`
- `scenario_seed`: 模拟数据种子，默认 `x-series-default`
- `delay_min_seconds`: 写入/处置动作最小模拟延迟秒数，默认 `1`
- `delay_max_seconds`: 写入/处置动作最大模拟延迟秒数，默认 `3`

## 动作列表

| 动作 | 类型 | 示例参数 | 说明 |
|---|---|---|---|
| `health_check` | query | - | 健康检查 |
| `query_cloud_assets` | query | `{"ip":"10.10.8.23"}` | 查询云资产 |
| `query_security_groups` | query | `{"security_group_id":"sg-dmz-web"}` | 查询安全组 |
| `block_ip_in_security_group` | write | `{"security_group_id":"sg-dmz-web","ip":"203.0.113.77","reason":"攻击源封禁"}` | 在安全组中封禁 IP |
| `unblock_ip_in_security_group` | write | `{"security_group_id":"sg-dmz-web","ip":"203.0.113.77"}` | 从安全组中解除 IP 封禁 |
| `create_snapshot` | write | `{"instance_id":"ecs-prod-web-01","reason":"应急取证"}` | 创建云主机快照 |
| `query_operation_history` | query | - | 查询模拟操作历史 |

## 内置样例索引

以下值可以直接用于动作参数测试，不需要连接外部系统。

- 负责人账号: `alice`
- IP: `10.10.8.23`

## 内置样例数据

| ID | 名称 | IP/指标 | 负责人 | 用户/账号 | 状态 | 等级 | 关键信息 | 摘要 |
|---|---|---|---|---|---|---|---|---|
| `ecs-prod-web-01` | prod-web-01 | 10.10.8.23 | alice | - | running | high | 区域=cn-example-1；安全组=sg-dmz-web；规格=c8.large | 云上 Web 服务器，绑定 sg-dmz-web |
| `sg-dmz-web` | sg-dmz-web | - | - | - | active | medium | rules=tcp/80,tcp/443 | DMZ Web 安全组，允许 80/443 |

## 返回结构

所有动作统一返回 `code`、`msg`、`data`、`summary`。查询类动作返回 `records`、`record`、`total_count` 和 `statistics`；写入、通知、创建、更新和删除类动作返回 `operation`、`records` 和 `affected_count`；健康检查返回 `system_info`，其中包含 `sample_values` 和 `sample_records` 便于发现可用样例值。

## 适用剧本

- 安全告警查询、研判和上下文补全
- 恶意 IP、账号、主机、邮件、文件的模拟处置
- 工单、通知和审计留痕演示
- 无真实安全设备或 SaaS 服务时的产品体验与编排训练
