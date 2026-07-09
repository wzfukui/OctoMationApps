# XScanner 漏洞扫描器

> 版本: v1.0.0
> 供应商: 雾帜智能
> 类型: 离线模拟产品

## 应用简介

离线模拟漏洞扫描器，支持目标管理、扫描任务、漏洞结果和报告生成。本应用不连接任何外部系统，所有动作均基于本地 SQLite 状态库和内置样例数据执行，适合开箱即用的 SOAR 剧本演示、培训和 PoC。

## 配置参数

- `database_path`: SQLite 模拟状态库路径，默认 `/tmp/xscanner.db`
- `scenario_profile`: 模拟场景名称，默认 `default`
- `scenario_seed`: 模拟数据种子，默认 `x-series-default`
- `delay_min_seconds`: 写入/处置动作最小模拟延迟秒数，默认 `1`
- `delay_max_seconds`: 写入/处置动作最大模拟延迟秒数，默认 `3`

## 动作列表

| 动作 | 类型 | 示例参数 | 说明 |
|---|---|---|---|
| `health_check` | query | - | 健康检查 |
| `add_scan_target` | write | `{"target":"10.10.8.23","owner":"alice"}` | 新增扫描目标 |
| `start_scan` | write | `{"target":"10.10.8.23","profile":"full"}` | 启动扫描任务 |
| `query_scan_status` | query | `{"target":"10.10.8.23"}` | 查询扫描状态 |
| `query_vulnerabilities` | query | `{"severity":"critical"}` | 查询漏洞结果 |
| `generate_report` | write | `{"target":"10.10.8.23","format":"html"}` | 生成扫描报告 |
| `query_operation_history` | query | - | 查询模拟操作历史 |

## 内置样例索引

以下值可以直接用于动作参数测试，不需要连接外部系统。

- 负责人账号: `alice`
- IP: `10.10.8.23`
- 指标: `CVE-2026-10001`

## 内置样例数据

| ID | 名称 | IP/指标 | 负责人 | 用户/账号 | 状态 | 等级 | 关键信息 | 摘要 |
|---|---|---|---|---|---|---|---|---|
| `scan-target-10-10-8-23` | prod-web-01 | 10.10.8.23 | alice | - | ready | critical | 服务=Example Portal；CVSS=9.8；port=443 | 发现远程命令执行高危漏洞 |

## 返回结构

所有动作统一返回 `code`、`msg`、`data`、`summary`。查询类动作返回 `records`、`record`、`total_count` 和 `statistics`；写入、通知、创建、更新和删除类动作返回 `operation`、`records` 和 `affected_count`；健康检查返回 `system_info`，其中包含 `sample_values` 和 `sample_records` 便于发现可用样例值。

## 适用剧本

- 安全告警查询、研判和上下文补全
- 恶意 IP、账号、主机、邮件、文件的模拟处置
- 工单、通知和审计留痕演示
- 无真实安全设备或 SaaS 服务时的产品体验与编排训练
