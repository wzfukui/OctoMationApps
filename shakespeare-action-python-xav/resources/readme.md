# XAV 防病毒软件

> 版本: v1.0.0
> 供应商: 雾帜智能
> 类型: 离线模拟产品

## 应用简介

离线模拟防病毒与 EDR 轻量处置能力，支持扫描、隔离文件和清除威胁。本应用不连接任何外部系统，所有动作均基于本地 SQLite 状态库和内置样例数据执行，适合开箱即用的 SOAR 剧本演示、培训和 PoC。

## 配置参数

- `database_path`: SQLite 模拟状态库路径，默认 `/tmp/xav.db`
- `scenario_profile`: 模拟场景名称，默认 `default`
- `scenario_seed`: 模拟数据种子，默认 `x-series-default`
- `delay_min_seconds`: 写入/处置动作最小模拟延迟秒数，默认 `1`
- `delay_max_seconds`: 写入/处置动作最大模拟延迟秒数，默认 `3`

## 动作列表

| 动作 | 类型 | 示例参数 | 说明 |
|---|---|---|---|
| `health_check` | query | - | 健康检查 |
| `query_endpoint` | query | `{"ip":"10.20.4.77"}` | 查询终端防护状态 |
| `query_threat_events` | query | `{"severity":"high"}` | 查询病毒威胁事件 |
| `start_scan` | write | `{"ip":"10.20.4.77","scan_type":"full"}` | 发起终端扫描任务 |
| `quarantine_file` | write | `{"file_hash":"44d88612fea8a8f36de82e1278abb02f","reason":"命中木马规则"}` | 隔离恶意文件 |
| `remove_threat` | write | `{"threat_id":"threat-1001"}` | 清除威胁 |
| `query_operation_history` | query | - | 查询模拟操作历史 |

## 内置样例索引

以下值可以直接用于动作参数测试，不需要连接外部系统。

- 负责人账号: `alice`, `carol`
- 用户/账号: `carol`
- IP: `10.10.8.23`, `10.20.4.77`
- 指标: `44d88612fea8a8f36de82e1278abb02f`

## 内置样例数据

| ID | 名称 | IP/指标 | 负责人 | 用户/账号 | 状态 | 等级 | 关键信息 | 摘要 |
|---|---|---|---|---|---|---|---|---|
| `threat-1001` | Trojan.Agent.X | 10.20.4.77 | carol | carol | active | high | file_path=C:/Users/carol/AppData/Local/Temp/invoice.exe；engine=XAV Engine | 财务终端发现可疑宏木马 |
| `endpoint-prod-web-01` | prod-web-01 | 10.10.8.23 | alice | - | protected | medium | agent_version=4.6.2；signature=20260709.1 | Linux 服务器安装了 XAV Agent |

## 返回结构

所有动作统一返回 `code`、`msg`、`data`、`summary`。查询类动作返回 `records`、`record`、`total_count` 和 `statistics`；写入、通知、创建、更新和删除类动作返回 `operation`、`records` 和 `affected_count`；健康检查返回 `system_info`，其中包含 `sample_values` 和 `sample_records` 便于发现可用样例值。

## 适用剧本

- 安全告警查询、研判和上下文补全
- 恶意 IP、账号、主机、邮件、文件的模拟处置
- 工单、通知和审计留痕演示
- 无真实安全设备或 SaaS 服务时的产品体验与编排训练
