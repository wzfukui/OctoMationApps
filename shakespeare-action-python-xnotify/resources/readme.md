# XNotify 通知系统

> 版本: v1.0.0
> 供应商: 雾帜智能
> 类型: 离线模拟产品

## 应用简介

离线模拟通知服务，支持企业微信、邮件、短信式通知与投递状态查询。本应用不连接任何外部系统，所有动作均基于本地 SQLite 状态库和内置样例数据执行，适合开箱即用的 SOAR 剧本演示、培训和 PoC。

## 配置参数

- `database_path`: SQLite 模拟状态库路径，默认 `/tmp/xnotify.db`
- `scenario_profile`: 模拟场景名称，默认 `default`
- `scenario_seed`: 模拟数据种子，默认 `x-series-default`
- `delay_min_seconds`: 写入/处置动作最小模拟延迟秒数，默认 `1`
- `delay_max_seconds`: 写入/处置动作最大模拟延迟秒数，默认 `3`

## 动作列表

| 动作 | 类型 | 示例参数 | 说明 |
|---|---|---|---|
| `health_check` | query | - | 健康检查 |
| `send_message` | notify | `{"recipient":"alice","message":"X 系列剧本已完成封堵","severity":"info"}` | 发送企业微信式消息 |
| `send_email` | notify | `{"recipient":"secops@example.com","subject":"安全事件通知","message":"请复核自动处置结果"}` | 发送邮件式通知 |
| `send_sms` | notify | `{"recipient":"13800000000","message":"安全事件已自动处置"}` | 发送短信式通知 |
| `query_notification_history` | query | `{"recipient":"alice"}` | 查询通知历史 |
| `query_delivery_status` | query | `{"notification_id":"notice-20260709-0001"}` | 查询投递状态 |
| `register_channel` | write | `{"channel_name":"secops-webhook","channel_type":"webhook"}` | 注册通知通道 |

## 内置样例索引

以下值可以直接用于动作参数测试，不需要连接外部系统。

- 负责人账号: `secops`
- 用户/账号: `alice`

## 内置样例数据

| ID | 名称 | IP/指标 | 负责人 | 用户/账号 | 状态 | 等级 | 关键信息 | 摘要 |
|---|---|---|---|---|---|---|---|---|
| `notice-20260709-0001` | 安全事件通知 | - | secops | alice | delivered | medium | 收件人=alice；channel=wecom；message=prod-web-01 已完成恶意 IP 封堵 | 已向业务负责人发送封堵确认通知 |

## 返回结构

所有动作统一返回 `code`、`msg`、`data`、`summary`。查询类动作返回 `records`、`record`、`total_count` 和 `statistics`；写入、通知、创建、更新和删除类动作返回 `operation`、`records` 和 `affected_count`；健康检查返回 `system_info`，其中包含 `sample_values` 和 `sample_records` 便于发现可用样例值。

## 适用剧本

- 安全告警查询、研判和上下文补全
- 恶意 IP、账号、主机、邮件、文件的模拟处置
- 工单、通知和审计留痕演示
- 无真实安全设备或 SaaS 服务时的产品体验与编排训练
