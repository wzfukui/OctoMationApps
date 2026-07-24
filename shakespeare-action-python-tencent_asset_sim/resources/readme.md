# 腾讯云资产中心（模拟）

> 版本：v1.0.0
> 类型：腾讯云安全产品离线模拟器
> 说明：本应用由雾帜智能提供，仅用于 SOAR 演示、培训和 PoC，不是腾讯云官方连接器。

## 应用简介

离线模拟腾讯云主机、业务系统、负责人、VPC 和互联网暴露面资产上下文。应用不连接腾讯云，不需要 SecretId、SecretKey 或其他密钥。未配置 asset 资源时会使用内置 SQLite 和样例数据直接运行。

## 可选配置

- `database_path`：SQLite 状态库路径，默认 `/tmp/tencent_asset_sim.db`
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
| `list_assets` | query | `{"owner":"alice","limit":20}` | 查询云资产列表 |
| `query_asset_by_ip` | query | `{"ip":"10.10.8.23"}` | 根据 IP 查询主机、业务、负责人和暴露面 |
| `query_asset_by_id` | query | `{"asset_id":"asset-cvm-prod-web-01"}` | 根据资产 ID 查询资产上下文 |
| `query_assets_by_owner` | query | `{"owner":"alice"}` | 根据负责人账号查询名下资产 |
| `list_exposed_assets` | query | `{"exposure":"internet"}` | 查询互联网暴露资产 |
| `query_business_context` | query | `{"business_id":"biz-checkout"}` | 查询业务系统关联资产与负责人 |
| `create_asset` | write | `{"asset_id":"asset-cvm-demo-01","asset_name":"demo-api-01","ip":"10.40.8.21","asset_type":"cvm","owner":"secops","business_id":"biz-demo","business_name":"演示业务","exposure":"private","trace_id":"demo-trace-asset-crud"}` | 新增模拟云资产 |
| `update_asset` | write | `{"asset_id":"asset-cvm-prod-web-01","owner":"alice","exposure":"internet","status":"online","trace_id":"demo-trace-asset-update"}` | 更新模拟云资产信息 |
| `delete_asset` | write | `{"asset_id":"asset-cvm-demo-01","reason":"演示资产下线","trace_id":"demo-trace-asset-crud"}` | 删除模拟云资产 |
| `query_operation_history` | query | `{"trace_id":"demo-trace-web-0001","limit":20}` | 查询产品模拟操作审计记录 |

## 内置样例数据

| ID | 类型 | 名称 | IP | 负责人 | 状态 | 等级 | 摘要 |
|---|---|---|---|---|---|---|---|
| `asset-cvm-prod-web-01` | cloud_asset | prod-web-01 | 10.10.8.23 | alice | online | critical | 统一收银台公网 Web 主机，关联 WAF 域名并暴露 80/443 |
| `asset-cvm-order-db-01` | cloud_asset | order-db-01 | 10.10.9.15 | bob | online | critical | 订单核心数据库，仅允许业务 VPC 按白名单访问 |
| `asset-clb-checkout-01` | cloud_asset | checkout-clb-01 | 10.10.8.10 | alice | online | high | 统一收银台公网负载均衡，前置腾讯云 WAF |
| `asset-tke-prod-checkout` | cloud_asset | prod-checkout-tke | 10.30.0.10 | platform-team | online | high | 统一收银台生产 TKE 集群，启用容器安全运行时防护 |

## 安全约束

- app 只模拟产品能力；白名单、置信度阈值、人工审批和多产品选择应由 SOAR 剧本负责。
- 写动作统一记录操作者、触发来源、trace_id、策略 ID、TTL 和执行结果。
- `simulated_api_status` 和 `simulated_auth_status` 可用于演示 API 不可用、权限不足、失败重试和人工补偿分支。
