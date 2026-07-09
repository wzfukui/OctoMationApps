# XTicket 工单系统

> 版本: v1.0.0
> 供应商: 雾帜智能
> 类型: 离线模拟产品

## 应用简介

离线模拟工单系统，支持创建、分派、评论、流转和历史查询。本应用不连接任何外部系统，所有动作均基于本地 SQLite 状态库和内置样例数据执行，适合开箱即用的 SOAR 剧本演示、培训和 PoC。

## 配置参数

- `database_path`: SQLite 模拟状态库路径，默认 `/tmp/xticket.db`
- `scenario_profile`: 模拟场景名称，默认 `default`
- `scenario_seed`: 模拟数据种子，默认 `x-series-default`
- `delay_min_seconds`: 写入/处置动作最小模拟延迟秒数，默认 `1`
- `delay_max_seconds`: 写入/处置动作最大模拟延迟秒数，默认 `3`

## 动作列表

| 动作 | 类型 | 示例参数 | 说明 |
|---|---|---|---|
| `health_check` | query | - | 健康检查 |
| `create_ticket` | write | `{"title":"恶意 IP 自动封堵确认","severity":"high","description":"SOAR 剧本已完成封堵，请复核"}` | 创建工单 |
| `query_ticket` | query | `{"ticket_id":"TCK-20260709-0001"}` | 查询工单 |
| `update_ticket_status` | write | `{"ticket_id":"TCK-20260709-0001","status":"in_progress","reason":"已分派安全运营"}` | 更新工单状态 |
| `add_ticket_comment` | write | `{"ticket_id":"TCK-20260709-0001","comment":"已通知资产负责人"}` | 追加工单评论 |
| `assign_ticket` | write | `{"ticket_id":"TCK-20260709-0001","assignee":"secops"}` | 分派工单 |
| `query_ticket_history` | query | `{"ticket_id":"TCK-20260709-0001"}` | 查询工单历史 |

## 内置样例索引

以下值可以直接用于动作参数测试，不需要连接外部系统。

- 负责人账号: `secops`
- 用户/账号: `alice`
- IP: `10.10.8.23`

## 内置样例数据

| ID | 名称 | IP/指标 | 负责人 | 用户/账号 | 状态 | 等级 | 关键信息 | 摘要 |
|---|---|---|---|---|---|---|---|---|
| `TCK-20260709-0001` | prod-web-01 恶意外联处置 | 10.10.8.23 | secops | alice | open | high | 处理人=secops；comments=剧本已封禁恶意 IP | 自动化剧本创建，待业务负责人确认 |

## 返回结构

所有动作统一返回 `code`、`msg`、`data`、`summary`。查询类动作返回 `records`、`record`、`total_count` 和 `statistics`；写入、通知、创建、更新和删除类动作返回 `operation`、`records` 和 `affected_count`；健康检查返回 `system_info`，其中包含 `sample_values` 和 `sample_records` 便于发现可用样例值。

## 适用剧本

- 安全告警查询、研判和上下文补全
- 恶意 IP、账号、主机、邮件、文件的模拟处置
- 工单、通知和审计留痕演示
- 无真实安全设备或 SaaS 服务时的产品体验与编排训练
