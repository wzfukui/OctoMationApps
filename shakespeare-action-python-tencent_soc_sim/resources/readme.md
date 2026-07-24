# 腾讯云 SOC（模拟）

> 版本：v1.0.0
> 类型：腾讯云安全产品离线模拟器
> 说明：本应用由雾帜智能提供，仅用于 SOAR 演示、培训和 PoC，不是腾讯云官方连接器。

## 应用简介

离线模拟腾讯云 SOC 的告警汇聚、事件分级、链路健康和处置回写能力。应用不连接腾讯云，不需要 SecretId、SecretKey 或其他密钥。未配置 asset 资源时会使用内置 SQLite 和样例数据直接运行。

## 可选配置

- `database_path`：SQLite 状态库路径，默认 `/tmp/tencent_soc_sim.db`
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
| `query_ingestion_health` | query | - | 查询 Syslog/Kafka 告警外发链路和最近告警时间 |
| `fetch_high_risk_alerts` | query | `{"severity":"critical","status":"new","limit":20}` | 拉取待处置的高危告警 |
| `query_alert_detail` | query | `{"alert_id":"soc-alert-20260724-0001"}` | 根据告警 ID 查询完整处置上下文 |
| `emit_demo_alert` | write | `{"alert_name":"手动演示 Web 攻击告警","src_ip":"203.0.113.77","dst_ip":"10.10.8.23","asset_id":"asset-cvm-prod-web-01","owner":"alice","severity":"high","confidence":95,"trace_id":"demo-trace-manual-0004"}` | 生成一条手动演示告警 |
| `update_alert_status` | write | `{"alert_id":"soc-alert-20260724-0001","status":"investigating","comment":"SOAR 已完成上下文增强","trace_id":"demo-trace-web-0001"}` | 更新 SOC 告警状态 |
| `writeback_disposition` | write | `{"alert_id":"soc-alert-20260724-0001","status":"closed","disposition":"confirmed_malicious","policy_ids":"tm-pol-demo-0001,waf-pol-demo-0001","trace_id":"demo-trace-web-0001"}` | 回写跨产品处置结果和策略 ID |
| `query_operation_history` | query | `{"trace_id":"demo-trace-web-0001","limit":20}` | 查询产品模拟操作审计记录 |

## 内置样例数据

| ID | 类型 | 名称 | IP | 负责人 | 状态 | 等级 | 摘要 |
|---|---|---|---|---|---|---|---|
| `soc-alert-20260724-0001` | soc_alert | 支付站点 SQL 注入攻击 | 203.0.113.77 | alice | new | critical | WAF 检测到高置信 SQL 注入，建议联动天幕与 WAF 封禁来源 IP |
| `soc-alert-20260724-0002` | soc_alert | 主机反弹 Shell 与矿池外联 | 10.10.8.23 | alice | new | critical | 主机安全检测到异常 bash 进程连接外部 C2，建议 CFW/天幕双向阻断 |
| `soc-alert-20260724-0003` | soc_alert | VPC 内横向访问核心数据库 | 10.10.8.23 | alice | investigating | high | Web 主机异常访问核心数据库管理端口，建议使用 CFW 限制东西向流量 |

## 安全约束

- app 只模拟产品能力；白名单、置信度阈值、人工审批和多产品选择应由 SOAR 剧本负责。
- 写动作统一记录操作者、触发来源、trace_id、策略 ID、TTL 和执行结果。
- `simulated_api_status` 和 `simulated_auth_status` 可用于演示 API 不可用、权限不足、失败重试和人工补偿分支。
