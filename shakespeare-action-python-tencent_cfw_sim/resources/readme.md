# 腾讯云防火墙 CFW（模拟）

> 版本：v1.0.0
> 类型：腾讯云安全产品离线模拟器
> 说明：本应用由雾帜智能提供，仅用于 SOAR 演示、培训和 PoC，不是腾讯云官方连接器。

## 应用简介

离线模拟腾讯云防火墙的 VPC 间访问控制、策略同步、TTL 回滚和审计能力。应用不连接腾讯云，不需要 SecretId、SecretKey 或其他密钥。未配置 asset 资源时会使用内置 SQLite 和样例数据直接运行。

## 可选配置

- `database_path`：SQLite 状态库路径，默认 `/tmp/tencent_cfw_sim.db`
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
| `list_vpc_firewalls` | query | `{"firewall_id":"cfw-vpc-fw-prod-01"}` | 查询 VPC 间防火墙及策略同步状态 |
| `list_vpc_access_rules` | query | `{"source":"10.10.8.23","destination":"10.10.9.15"}` | 查询 VPC 间访问控制规则 |
| `create_vpc_block_rule` | write | `{"source":"10.10.8.23","destination":"10.10.9.15","protocol":"TCP","port":"3306","reason":"Web 主机异常访问数据库","ttl_minutes":120,"alert_id":"soc-alert-20260724-0003","trace_id":"demo-trace-lateral-0003"}` | 创建 VPC 间拒绝访问规则 |
| `delete_vpc_access_rule` | write | `{"policy_id":"cfw-rule-demo-0001","source":"10.10.8.23","destination":"10.10.9.15","trace_id":"demo-trace-lateral-0003"}` | 删除或回滚 VPC 间访问控制规则 |
| `expire_due_policies` | write | `{"as_of":"2100-01-01T00:00:00+08:00","trigger_source":"scheduled","trace_id":"demo-trace-ttl-cfw"}` | 扫描并回滚已到期 CFW 规则 |
| `query_operation_history` | query | `{"trace_id":"demo-trace-web-0001","limit":20}` | 查询产品模拟操作审计记录 |

## 内置样例数据

| ID | 类型 | 名称 | IP | 负责人 | 状态 | 等级 | 摘要 |
|---|---|---|---|---|---|---|---|
| `cfw-vpc-fw-prod-01` | cfw_vpc_firewall | 生产 VPC 间防火墙 | - | cloud-sec | running | medium | 保护生产 Web VPC 与数据 VPC 之间的东西向访问 |
| `cfw-rule-demo-0001` | cfw_vpc_block_rule | 阻断 Web 主机访问核心数据库管理端口 | 10.10.8.23 | soar-demo | active | high | VPC 间高优先级拒绝规则，限制异常东西向访问 |

## 安全约束

- app 只模拟产品能力；白名单、置信度阈值、人工审批和多产品选择应由 SOAR 剧本负责。
- 写动作统一记录操作者、触发来源、trace_id、策略 ID、TTL 和执行结果。
- `simulated_api_status` 和 `simulated_auth_status` 可用于演示 API 不可用、权限不足、失败重试和人工补偿分支。
