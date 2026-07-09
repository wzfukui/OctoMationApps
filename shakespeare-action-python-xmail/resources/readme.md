# XMail 邮件安全

> 版本: v1.0.0
> 供应商: 雾帜智能
> 类型: 离线模拟产品

## 应用简介

离线模拟邮件安全网关，支持邮件解析、事件查询、隔离、释放和发件人阻断。本应用不连接任何外部系统，所有动作均基于本地 SQLite 状态库和内置样例数据执行，适合开箱即用的 SOAR 剧本演示、培训和 PoC。

## 配置参数

- `database_path`: SQLite 模拟状态库路径，默认 `/tmp/xmail.db`
- `scenario_profile`: 模拟场景名称，默认 `default`
- `scenario_seed`: 模拟数据种子，默认 `x-series-default`
- `delay_min_seconds`: 写入/处置动作最小模拟延迟秒数，默认 `1`
- `delay_max_seconds`: 写入/处置动作最大模拟延迟秒数，默认 `3`

## 动作列表

| 动作 | 类型 | 示例参数 | 说明 |
|---|---|---|---|
| `health_check` | query | - | 健康检查 |
| `parse_email` | query | `{"message_id":"mail-20260709-0007"}` | 解析邮件内容 |
| `query_mail_events` | query | `{"recipient":"carol@example.com"}` | 查询邮件安全事件 |
| `quarantine_message` | write | `{"message_id":"mail-20260709-0007","reason":"钓鱼链接"}` | 隔离邮件 |
| `release_message` | write | `{"message_id":"mail-20260709-0007"}` | 释放邮件 |
| `block_sender` | write | `{"sender":"invoice@malicious.example","reason":"钓鱼邮件源"}` | 阻断发件人 |
| `query_operation_history` | query | - | 查询模拟操作历史 |

## 内置样例索引

以下值可以直接用于动作参数测试，不需要连接外部系统。

- 负责人账号: `mailops`
- 用户/账号: `carol`
- 指标: `malicious.example`

## 内置样例数据

| ID | 名称 | IP/指标 | 负责人 | 用户/账号 | 状态 | 等级 | 关键信息 | 摘要 |
|---|---|---|---|---|---|---|---|---|
| `mail-20260709-0007` | 发票确认通知 | malicious.example | mailops | carol | delivered | high | URL=https://malicious.example/login；发件人=invoice@malicious.example；收件人=carol@example.com | 疑似钓鱼邮件投递给财务用户 |

## 返回结构

所有动作统一返回 `code`、`msg`、`data`、`summary`。查询类动作返回 `records`、`record`、`total_count` 和 `statistics`；写入、通知、创建、更新和删除类动作返回 `operation`、`records` 和 `affected_count`；健康检查返回 `system_info`，其中包含 `sample_values` 和 `sample_records` 便于发现可用样例值。

## 适用剧本

- 安全告警查询、研判和上下文补全
- 恶意 IP、账号、主机、邮件、文件的模拟处置
- 工单、通知和审计留痕演示
- 无真实安全设备或 SaaS 服务时的产品体验与编排训练
