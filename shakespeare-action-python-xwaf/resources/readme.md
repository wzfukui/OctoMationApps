# XWAF Web应用防火墙

> 版本: v1.0.0
> 供应商: 雾帜智能
> 类型: 离线模拟产品

## 应用简介

离线模拟 WAF 攻击检测、站点防护、IP 封禁和 URL 规则能力。本应用不连接任何外部系统，所有动作均基于本地 SQLite 状态库和内置样例数据执行，适合开箱即用的 SOAR 剧本演示、培训和 PoC。

## 配置参数

- `database_path`: SQLite 模拟状态库路径，默认 `/tmp/xwaf.db`
- `scenario_profile`: 模拟场景名称，默认 `default`
- `scenario_seed`: 模拟数据种子，默认 `x-series-default`
- `delay_min_seconds`: 写入/处置动作最小模拟延迟秒数，默认 `1`
- `delay_max_seconds`: 写入/处置动作最大模拟延迟秒数，默认 `3`

## 动作列表

| 动作 | 类型 | 示例参数 | 说明 |
|---|---|---|---|
| `health_check` | query | - | 健康检查 |
| `query_attack_events` | query | `{"source_ip":"203.0.113.77"}` | 查询 Web 攻击事件 |
| `query_protected_sites` | query | `{"site":"checkout.example.com"}` | 查询受保护站点 |
| `block_ip` | write | `{"ip":"203.0.113.77","reason":"SQL 注入攻击"}` | 在 WAF 中封禁源 IP |
| `unblock_ip` | write | `{"ip":"203.0.113.77"}` | 解除 WAF IP 封禁 |
| `add_url_rule` | write | `{"url":"/admin/debug","rule":"禁止调试路径访问"}` | 新增 URL 防护规则 |
| `query_operation_history` | query | - | 查询模拟操作历史 |

## 内置样例索引

以下值可以直接用于动作参数测试，不需要连接外部系统。

- 负责人账号: `alice`
- IP: `10.10.8.23`, `203.0.113.77`
- 指标: `203.0.113.77`

## 内置样例数据

| ID | 名称 | IP/指标 | 负责人 | 用户/账号 | 状态 | 等级 | 关键信息 | 摘要 |
|---|---|---|---|---|---|---|---|---|
| `waf-event-9001` | checkout SQL injection | 203.0.113.77 | - | - | detected | high | 站点=checkout.example.com；URL=/pay?id=1%20or%201=1；action=blocked | 支付站点命中 SQL 注入攻击规则 |
| `waf-site-01` | checkout.example.com | 10.10.8.23 | alice | - | protected | medium | policy=strict；qps=1280 | 核心支付站点，启用 SQLi/XSS/RCE 防护 |

## 返回结构

所有动作统一返回 `code`、`msg`、`data`、`summary`。查询类动作返回 `records`、`record`、`total_count` 和 `statistics`；写入、通知、创建、更新和删除类动作返回 `operation`、`records` 和 `affected_count`；健康检查返回 `system_info`，其中包含 `sample_values` 和 `sample_records` 便于发现可用样例值。

## 适用剧本

- 安全告警查询、研判和上下文补全
- 恶意 IP、账号、主机、邮件、文件的模拟处置
- 工单、通知和审计留痕演示
- 无真实安全设备或 SaaS 服务时的产品体验与编排训练
