# 腾讯云安全产品模拟器与 Demo 剧本设计

## 目标

本系列用于在没有真实腾讯云、TCE、安全设备或 API 凭据时，开箱演示 SOAR 的告警归一化、资产增强、人工审批、跨产品处置、TTL 回滚、失败补偿和审计闭环。

所有 app 均为离线模拟器，由雾帜智能提供，不是腾讯云官方连接器。app 使用内置样例数据和本地 SQLite 持久化状态，不要求配置 asset 资源；配置项仅用于覆盖默认数据库、模拟延迟和健康状态。

## 设计边界

- app 负责模拟产品 API、产品状态、策略状态和操作审计。
- 剧本负责白名单、置信度阈值、核心资产判断、人工审批、产品选择、重试、补偿和通知。
- SOC 是告警入口和处置结果回写点，不替代 SOAR 的编排判断。
- 资产中心是业务、负责人、暴露面和关键资产上下文来源。
- HIDS/TCSS 第一期只提供检测、进程、连接和告警状态，不默认提供主机隔离、进程查杀或容器隔离。
- 天幕、CFW 和 WAF 是网络侧写动作产品，写动作必须带上 `trace_id`、`operator`、`trigger_source`，并返回 `policy_id`。

## 产品矩阵

| App | 产品定位 | 主要查询动作 | 主要写动作 |
|---|---|---|---|
| `tencent_soc_sim` | 告警汇聚、分级和回写 | 链路健康、高危告警、告警详情 | 生成演示告警、更新状态、回写处置 |
| `tencent_asset_sim` | 主机、业务、负责人和暴露面 | 按 IP/ID/负责人/业务查询、暴露面查询 | 资产增删改 |
| `tencent_tianmu_sim` | 4 层旁路 IP 阻断 | 策略查询、API 健康 | IP 阻断、解封、TTL 到期扫描 |
| `tencent_cfw_sim` | VPC 间或东西向访问控制 | VPC 防火墙、访问规则查询 | 创建/删除 VPC 拒绝规则、TTL 到期扫描 |
| `tencent_waf_sim` | Web 攻击检测和来源 IP 封禁 | 域名、攻击事件、IP 策略查询 | 域名维度封禁/解封、TTL 到期扫描 |
| `tencent_hids_sim` | 主机告警与调查线索 | 主机、告警、进程、外联 | 更新告警状态 |
| `tencent_tcss_sim` | 容器运行时告警与调查线索 | 集群、告警、异常进程、恶意外联 | 更新告警状态 |

## 统一字段契约

告警和调查动作优先返回以下顶层字段，剧本不需要再从不稳定的嵌套 JSON 中反复取值：

| 字段 | 含义 |
|---|---|
| `alert_id` | 产品告警 ID |
| `src_ip` / `dst_ip` | 网络会话源和目的 IP |
| `host_ip` / `external_ip` | 受害主机和外部攻击/C2 IP |
| `asset_id` / `host_id` / `cluster_id` | 资产关联标识 |
| `business_id` / `owner` | 业务系统和负责人 |
| `severity` / `confidence` | 告警等级和置信度 |
| `direction` | `inbound`、`outbound` 或 `east_west` |
| `trace_id` | 一次 SOAR 处置链路的全局追踪 ID |

策略写动作统一返回：

- `policy_id`
- `status`
- `expires_at`
- `operator`
- `trigger_source`
- `trace_id`
- `operation.operation_id`

## 剧本 1：高危告警驱动的攻击源 IP 处置闭环

推荐主线使用内置告警 `soc-alert-20260724-0001`。

1. `tencent_soc_sim.fetch_high_risk_alerts` 拉取 `critical + new` 告警。
2. `tencent_soc_sim.query_alert_detail` 获取 `src_ip`、`dst_ip`、`asset_id`、`confidence` 和 `trace_id`。
3. `tencent_asset_sim.query_asset_by_id` 补充业务、负责人、是否关键资产和暴露面。
4. 剧本执行白名单检查。白名单命中立即停止写动作并回写 SOC。
5. `confidence < 90`、核心资产或管理网段进入人工审批。
6. Web 攻击调用 `tencent_waf_sim.block_source_ip`；需要全局 4 层阻断时同时调用 `tencent_tianmu_sim.block_ip`。
7. 收集两个动作返回的 `policy_id`，调用 `tencent_soc_sim.writeback_disposition`。
8. 定时剧本调用 WAF/天幕的 `expire_due_policies`，解封失败进入重试和人工工单。

手工演示时可先调用 `tencent_soc_sim.emit_demo_alert`。真实 syslog/Kafka 入站属于触发器或消息接入能力，不应硬编码在动作 app 中；离线 demo 使用拉取动作来复现同一编排入口。

## 剧本 2：主机挖矿与反弹 Shell 联动响应

推荐主线使用主机安全告警 `hids-alert-20260724-0001`，对应 SOC 告警 `soc-alert-20260724-0002`。

1. `tencent_hids_sim.query_host_alerts` 获取主机高危告警。
2. `tencent_hids_sim.query_processes` 获取 `bash` 进程、父进程和命令行。
3. `tencent_hids_sim.query_outbound_connections` 获取外联 IP `198.51.100.66`。
4. `tencent_asset_sim.query_asset_by_id` 获取业务、负责人和关键资产标记。
5. 明确区分受害主机 `10.10.8.23` 与外联 C2 `198.51.100.66`。
6. `tencent_tianmu_sim.block_ip` 阻断外部 C2；存在 VPC 间横向访问时调用 `tencent_cfw_sim.create_vpc_block_rule`。
7. 若入口来自 Web 攻击，再调用 `tencent_waf_sim.block_source_ip`，不能把受害主机 IP 当作攻击源封禁。
8. `tencent_hids_sim.update_alert_status` 和 `tencent_soc_sim.writeback_disposition` 回写处置结果。
9. 定时复查同一 `host_id` 是否继续出现异常外联，持续命中时升级人工响应。

## 剧本 3：云安全产品健康巡检与策略校验

1. 每 30 分钟依次调用 7 个 app 的 `health_check`。
2. SOC 额外调用 `query_ingestion_health`，检查 Syslog/Kafka 链路和最近告警时间。
3. 天幕、CFW、WAF 查询有效策略，检查重复策略、已到期未释放策略和策略状态。
4. HIDS/TCSS 检查云 API、Agent/传感器和告警检索组件状态。
5. 通过 asset 配置将 `simulated_api_status` 设为 `unavailable`，可演示 API 503、失败重试和工单分支。
6. 将 `simulated_auth_status` 设为 `forbidden`，可演示权限不足与 API 不可用的差异化处理。
7. 巡检默认只读。`expire_due_policies` 等补偿写动作应在审批后或明确配置后执行。

## 内置贯通数据

| 对象 | 样例值 |
|---|---|
| Web 攻击源 | `203.0.113.77` |
| 反弹 Shell / 矿池 C2 | `198.51.100.66` |
| 受害 Web 主机 | `10.10.8.23` / `ins-prod-web-01` |
| 核心数据库 | `10.10.9.15` / `asset-cvm-order-db-01` |
| WAF 域名 | `checkout.example.com` |
| 业务系统 | `biz-checkout` / 统一收银台 |
| 负责人 | `alice` |
| Web 攻击 trace | `demo-trace-web-0001` |
| 反弹 Shell trace | `demo-trace-reverse-shell-0002` |
| 横向访问 trace | `demo-trace-lateral-0003` |

## 后续扩展建议

第二阶段可增加威胁情报、白名单台账、审批、工单和通知 app，但这些应保持供应商无关，以便腾讯云系列和 X 系列共同复用。真实腾讯云连接器可以沿用当前动作名称和输出契约，将模拟运行时替换为腾讯云 API SDK，而不需要重画剧本。

## 产品能力参考

- [腾讯天幕 NIPS 产品说明](https://cloud.tencent.com/product/nips)
- [腾讯云防火墙 API 概览](https://cloud.tencent.com/document/product/1132/49080)
- [腾讯云 WAF API 概览](https://cloud.tencent.com/document/product/627/53618)
- [腾讯云主机安全告警设置](https://cloud.tencent.com/document/product/296/112185)
- [腾讯云容器安全 API 文档](https://cloud.tencent.com/document/product/1285/65412)
- [腾讯云 SOC 常见问题](https://cloud.tencent.com/document/product/1011/31162)
