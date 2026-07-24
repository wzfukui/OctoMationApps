# 腾讯云 WAF（模拟）

> 版本：v1.0.0
> 类型：腾讯云安全产品离线模拟器
> 说明：本应用由雾帜智能提供，仅用于 SOAR 演示、培训和 PoC，不是腾讯云官方连接器。

## 应用简介

离线模拟腾讯云 WAF 的域名防护、攻击事件、IP 黑名单、解封和 TTL 审计能力。应用不连接腾讯云，不需要 SecretId、SecretKey 或其他密钥。未配置 asset 资源时会使用内置 SQLite 和样例数据直接运行。

## 可选配置

- `database_path`：SQLite 状态库路径，默认 `/tmp/tencent_waf_sim.db`
- `scenario_profile`：场景名称，默认 `default`
- `delay_min_seconds` / `delay_max_seconds`：写动作模拟延迟，默认 1-3 秒
- `simulated_api_status`：`healthy`、`degraded`、`unavailable`
- `simulated_auth_status`：`authorized`、`forbidden`
- `simulated_link_status`：`healthy`、`delayed`、`down`

## 联动字段契约

告警和调查动作优先返回 `alert_id`、`src_ip`、`dst_ip`、`host_ip`、`external_ip`、`asset_id`、`host_id`、`business_id`、`owner`、`severity`、`confidence`、`trace_id`。策略写动作返回 `policy_id`、`status`、`expires_at`、`operator`、`trigger_source`、`trace_id` 和 `operation`。

## 动作列表

| 动作 | 类型 | 示例参数 | 说明 |
|---|---|---|---|
| `health_check` | query | - | 检查模拟 API、鉴权和组件状态 |
| `list_protected_domains` | query | `{"domain":"checkout.example.com"}` | 查询 WAF 受保护域名 |
| `query_attack_events` | query | `{"source_ip":"203.0.113.77","domain":"checkout.example.com"}` | 查询 Web 攻击事件 |
| `list_ip_block_policies` | query | `{"ip":"203.0.113.77","domain":"checkout.example.com"}` | 查询 WAF IP 黑名单策略 |
| `block_source_ip` | write | `{"ip":"203.0.113.77","domain":"checkout.example.com","reason":"SQL 注入攻击","ttl_minutes":60,"alert_id":"soc-alert-20260724-0001","trace_id":"demo-trace-web-0001"}` | 在指定 WAF 域名上封禁攻击源 IP |
| `unblock_source_ip` | write | `{"policy_id":"waf-pol-demo-0001","ip":"203.0.113.77","domain":"checkout.example.com","trace_id":"demo-trace-web-0001"}` | 解除 WAF 攻击源 IP 封禁 |
| `expire_due_policies` | write | `{"as_of":"2100-01-01T00:00:00+08:00","trigger_source":"scheduled","trace_id":"demo-trace-ttl-waf"}` | 扫描并解除已到期 WAF IP 策略 |
| `query_operation_history` | query | `{"trace_id":"demo-trace-web-0001","limit":20}` | 查询产品模拟操作审计记录 |

## 内置样例数据

| ID | 类型 | 名称 | IP | 负责人 | 状态 | 等级 | 摘要 |
|---|---|---|---|---|---|---|---|
| `waf-domain-checkout` | waf_domain | checkout.example.com | 10.10.8.23 | alice | protected | medium | 统一收银台公网域名，启用 SQLi、XSS 和 RCE 防护 |
| `waf-event-20260724-0001` | waf_attack_event | SQL 注入攻击 | 203.0.113.77 | alice | blocked | critical | 攻击者请求 /pay?id=1 OR 1=1，命中 SQL 注入规则 |
| `waf-pol-demo-0001` | waf_ip_block_policy | 支付站点攻击源 IP 黑名单 | 203.0.113.77 | soar-demo | active | high | 针对 checkout.example.com 的攻击源 IP 封禁策略 |

## 安全约束

- app 只模拟产品能力；白名单、置信度阈值、人工审批和多产品选择应由 SOAR 剧本负责。
- 写动作统一记录操作者、触发来源、trace_id、策略 ID、TTL 和执行结果。
- `simulated_api_status` 和 `simulated_auth_status` 可用于演示 API 不可用、权限不足、失败重试和人工补偿分支。
