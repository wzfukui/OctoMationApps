# XTI 威胁情报

> 版本: v1.0.0
> 供应商: 雾帜智能
> 类型: 离线模拟产品

## 应用简介

离线模拟威胁情报平台，支持 IP、域名、URL、文件 Hash、CVE 查询。本应用不连接任何外部系统，所有动作均基于本地 SQLite 状态库和内置样例数据执行，适合开箱即用的 SOAR 剧本演示、培训和 PoC。

## 配置参数

- `database_path`: SQLite 模拟状态库路径，默认 `/tmp/xti.db`
- `scenario_profile`: 模拟场景名称，默认 `default`
- `scenario_seed`: 模拟数据种子，默认 `x-series-default`
- `delay_min_seconds`: 写入/处置动作最小模拟延迟秒数，默认 `1`
- `delay_max_seconds`: 写入/处置动作最大模拟延迟秒数，默认 `3`

## 动作列表

| 动作 | 类型 | 示例参数 | 说明 |
|---|---|---|---|
| `health_check` | query | - | 健康检查 |
| `query_ip_reputation` | query | `{"ip":"203.0.113.77"}` | 查询 IP 信誉 |
| `query_domain_reputation` | query | `{"domain":"malicious.example"}` | 查询域名信誉 |
| `query_url_reputation` | query | `{"url":"https://malicious.example/login"}` | 查询 URL 信誉 |
| `query_file_reputation` | query | `{"file_hash":"44d88612fea8a8f36de82e1278abb02f"}` | 查询文件 Hash 信誉 |
| `query_cve_intel` | query | `{"cve_id":"CVE-2026-10001"}` | 查询漏洞情报 |
| `submit_indicator` | write | `{"indicator":"198.51.100.88","indicator_type":"ip","severity":"medium"}` | 提交自定义情报指标 |

## 内置样例索引

以下值可以直接用于动作参数测试，不需要连接外部系统。

- IP: `203.0.113.77`
- 指标: `203.0.113.77`, `44d88612fea8a8f36de82e1278abb02f`, `CVE-2026-10001`

## 内置样例数据

| ID | 名称 | IP/指标 | 负责人 | 用户/账号 | 状态 | 等级 | 关键信息 | 摘要 |
|---|---|---|---|---|---|---|---|---|
| `ioc-ip-203-0-113-77` | 203.0.113.77 | 203.0.113.77 | - | - | malicious | high | 置信度=92；labels=scanner,bruteforce；asn=AS64500 | 近期参与 Web 攻击和凭证爆破 |
| `ioc-hash-44d8` | invoice.exe | 44d88612fea8a8f36de82e1278abb02f | - | - | malicious | high | 置信度=95；家族=Agent.X | 宏木马投递的二阶段载荷 |
| `cve-2026-10001` | CVE-2026-10001 | CVE-2026-10001 | - | - | exploited | critical | CVSS=9.8；product=Example Portal | 样例远程命令执行漏洞，已出现利用 |

## 返回结构

所有动作统一返回 `code`、`msg`、`data`、`summary`。查询类动作返回 `records`、`record`、`total_count` 和 `statistics`；写入、通知、创建、更新和删除类动作返回 `operation`、`records` 和 `affected_count`；健康检查返回 `system_info`，其中包含 `sample_values` 和 `sample_records` 便于发现可用样例值。

## 适用剧本

- 安全告警查询、研判和上下文补全
- 恶意 IP、账号、主机、邮件、文件的模拟处置
- 工单、通知和审计留痕演示
- 无真实安全设备或 SaaS 服务时的产品体验与编排训练
