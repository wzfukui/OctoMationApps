# 腾讯云容器安全 TCSS（模拟）

> 版本：v1.0.0
> 类型：腾讯云安全产品离线模拟器
> 说明：本应用由雾帜智能提供，仅用于 SOAR 演示、培训和 PoC，不是腾讯云官方连接器。

## 应用简介

离线模拟腾讯云容器安全的集群、运行时告警、异常进程、恶意外联和健康状态。应用不连接腾讯云，不需要 SecretId、SecretKey 或其他密钥。未配置 asset 资源时会使用内置 SQLite 和样例数据直接运行。

## 可选配置

- `database_path`：SQLite 状态库路径，默认 `/tmp/tencent_tcss_sim.db`
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
| `query_clusters` | query | `{"cluster_id":"cls-prod-checkout"}` | 查询容器集群与传感器状态 |
| `query_runtime_alerts` | query | `{"cluster_id":"cls-prod-checkout","severity":"high"}` | 查询容器运行时安全告警 |
| `query_runtime_processes` | query | `{"cluster_id":"cls-prod-checkout","process_name":"xmrig"}` | 查询容器异常进程线索 |
| `query_malicious_connections` | query | `{"cluster_id":"cls-prod-checkout","external_ip":"198.51.100.66"}` | 查询容器恶意外联线索 |
| `update_alert_status` | write | `{"alert_id":"tcss-alert-20260724-0001","status":"processing","comment":"已阻断矿池外联 IP","trace_id":"demo-trace-container-0005"}` | 更新容器安全告警状态 |
| `query_operation_history` | query | `{"trace_id":"demo-trace-web-0001","limit":20}` | 查询产品模拟操作审计记录 |

## 内置样例数据

| ID | 类型 | 名称 | IP | 负责人 | 状态 | 等级 | 摘要 |
|---|---|---|---|---|---|---|---|
| `cls-prod-checkout` | tcss_cluster | prod-checkout-tke | 10.30.0.10 | platform-team | protected | medium | 统一收银台生产 TKE 集群，运行时防护已启用 |
| `tcss-alert-20260724-0001` | tcss_alert | 容器异常外联 | 198.51.100.66 | platform-team | new | high | checkout-api Pod 连接已知矿池地址 |
| `tcss-process-20260724-0001` | tcss_process | xmrig | 10.30.2.17 | platform-team | running | high | 容器中发现矿池进程 xmrig |

## 安全约束

- app 只模拟产品能力；白名单、置信度阈值、人工审批和多产品选择应由 SOAR 剧本负责。
- 写动作统一记录操作者、触发来源、trace_id、策略 ID、TTL 和执行结果。
- `simulated_api_status` 和 `simulated_auth_status` 可用于演示 API 不可用、权限不足、失败重试和人工补偿分支。
