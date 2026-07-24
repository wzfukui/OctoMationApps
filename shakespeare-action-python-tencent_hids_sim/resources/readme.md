# 腾讯云主机安全 HIDS/CWP（模拟）

> 版本：v1.0.0
> 类型：腾讯云安全产品离线模拟器
> 说明：本应用由雾帜智能提供，仅用于 SOAR 演示、培训和 PoC，不是腾讯云官方连接器。

## 应用简介

离线模拟腾讯云主机安全的主机、告警、进程、外联线索和告警处置状态。应用不连接腾讯云，不需要 SecretId、SecretKey 或其他密钥。未配置 asset 资源时会使用内置 SQLite 和样例数据直接运行。

## 可选配置

- `database_path`：SQLite 状态库路径，默认 `/tmp/tencent_hids_sim.db`
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
| `query_host` | query | `{"host_id":"ins-prod-web-01"}` | 查询主机安全资产详情 |
| `query_host_alerts` | query | `{"host_id":"ins-prod-web-01","severity":"critical"}` | 查询主机安全告警 |
| `query_processes` | query | `{"host_id":"ins-prod-web-01","process_name":"bash"}` | 查询主机进程线索 |
| `query_outbound_connections` | query | `{"host_id":"ins-prod-web-01","external_ip":"198.51.100.66"}` | 查询主机外联线索 |
| `update_alert_status` | write | `{"alert_id":"hids-alert-20260724-0001","status":"processing","comment":"已对外联 C2 下发 CFW 与天幕策略","trace_id":"demo-trace-reverse-shell-0002"}` | 更新主机安全告警状态 |
| `query_operation_history` | query | `{"trace_id":"demo-trace-web-0001","limit":20}` | 查询产品模拟操作审计记录 |

## 内置样例数据

| ID | 类型 | 名称 | IP | 负责人 | 状态 | 等级 | 摘要 |
|---|---|---|---|---|---|---|---|
| `ins-prod-web-01` | hids_host | prod-web-01 | 10.10.8.23 | alice | protected | high | 统一收银台 Web 主机，主机安全 Agent 在线 |
| `hids-alert-20260724-0001` | hids_alert | 反弹 Shell | 10.10.8.23 | alice | new | critical | www-data 启动交互式 bash 并连接外部 C2 |
| `hids-process-18422` | hids_process | bash | 10.10.8.23 | alice | running | critical | 可疑 bash 进程，由 nginx worker 派生 |
| `hids-conn-20260724-0001` | hids_connection | 异常 C2 外联 | 198.51.100.66 | alice | established | critical | 主机 10.10.8.23:49822 连接 198.51.100.66:4444 |

## 安全约束

- app 只模拟产品能力；白名单、置信度阈值、人工审批和多产品选择应由 SOAR 剧本负责。
- 写动作统一记录操作者、触发来源、trace_id、策略 ID、TTL 和执行结果。
- `simulated_api_status` 和 `simulated_auth_status` 可用于演示 API 不可用、权限不足、失败重试和人工补偿分支。
