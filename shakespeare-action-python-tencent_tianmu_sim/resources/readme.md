# 腾讯天幕 NIPS（模拟）

> 版本：v1.0.0
> 类型：腾讯云安全产品离线模拟器
> 说明：本应用由雾帜智能提供，仅用于 SOAR 演示、培训和 PoC，不是腾讯云官方连接器。

## 应用简介

离线模拟腾讯天幕旁路阻断、解封、策略查询、TTL 到期和审计能力。应用不连接腾讯云，不需要 SecretId、SecretKey 或其他密钥。未配置 asset 资源时会使用内置 SQLite 和样例数据直接运行。

## 可选配置

- `database_path`：SQLite 状态库路径，默认 `/tmp/tencent_tianmu_sim.db`
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
| `list_block_policies` | query | `{"ip":"203.0.113.77"}` | 查询旁路阻断策略 |
| `block_ip` | write | `{"ip":"198.51.100.66","reason":"反弹 Shell 外联 C2","ttl_minutes":120,"scope":"global","direction":"bidirectional","alert_id":"soc-alert-20260724-0002","trace_id":"demo-trace-reverse-shell-0002"}` | 创建天幕旁路 IP 阻断策略 |
| `unblock_ip` | write | `{"policy_id":"tm-pol-demo-0001","ip":"203.0.113.77","reason":"人工复核后解除","trace_id":"demo-trace-web-0001"}` | 解除天幕旁路 IP 阻断 |
| `expire_due_policies` | write | `{"as_of":"2100-01-01T00:00:00+08:00","trigger_source":"scheduled","trace_id":"demo-trace-ttl-tianmu"}` | 扫描并自动释放已到期策略 |
| `query_operation_history` | query | `{"trace_id":"demo-trace-web-0001","limit":20}` | 查询产品模拟操作审计记录 |

## 内置样例数据

| ID | 类型 | 名称 | IP | 负责人 | 状态 | 等级 | 摘要 |
|---|---|---|---|---|---|---|---|
| `tm-pol-demo-0001` | tianmu_block_policy | SQL 注入攻击源旁路阻断 | 203.0.113.77 | soar-demo | active | high | 由 SOC 高危 Web 攻击告警触发的 4 层旁路阻断策略 |
| `tm-pol-demo-0002` | tianmu_block_policy | 历史恶意扫描源阻断 | 192.0.2.44 | soar-demo | released | medium | TTL 到期后已自动解封的历史策略 |

## 安全约束

- app 只模拟产品能力；白名单、置信度阈值、人工审批和多产品选择应由 SOAR 剧本负责。
- 写动作统一记录操作者、触发来源、trace_id、策略 ID、TTL 和执行结果。
- `simulated_api_status` 和 `simulated_auth_status` 可用于演示 API 不可用、权限不足、失败重试和人工补偿分支。
