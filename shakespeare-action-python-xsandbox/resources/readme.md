# XSandbox 文件沙箱

> 版本: v1.0.0
> 供应商: 雾帜智能
> 类型: 离线模拟产品

## 应用简介

离线模拟沙箱分析平台，支持文件/URL 提交、分析报告和行为轨迹查询。本应用不连接任何外部系统，所有动作均基于本地 SQLite 状态库和内置样例数据执行，适合开箱即用的 SOAR 剧本演示、培训和 PoC。

## 配置参数

- `database_path`: SQLite 模拟状态库路径，默认 `/tmp/xsandbox.db`
- `scenario_profile`: 模拟场景名称，默认 `default`
- `scenario_seed`: 模拟数据种子，默认 `x-series-default`
- `delay_min_seconds`: 写入/处置动作最小模拟延迟秒数，默认 `1`
- `delay_max_seconds`: 写入/处置动作最大模拟延迟秒数，默认 `3`

## 动作列表

| 动作 | 类型 | 示例参数 | 说明 |
|---|---|---|---|
| `health_check` | query | - | 健康检查 |
| `submit_file` | write | `{"file_hash":"44d88612fea8a8f36de82e1278abb02f","file_name":"invoice.exe"}` | 提交文件样本 |
| `submit_url` | write | `{"url":"https://malicious.example/login"}` | 提交 URL 样本 |
| `query_analysis_report` | query | `{"sample_id":"44d88612fea8a8f36de82e1278abb02f"}` | 查询分析报告 |
| `query_behavior_trace` | query | `{"sample_id":"44d88612fea8a8f36de82e1278abb02f"}` | 查询行为轨迹 |
| `query_operation_history` | query | - | 查询模拟操作历史 |

## 内置样例索引

以下值可以直接用于动作参数测试，不需要连接外部系统。

- 指标: `44d88612fea8a8f36de82e1278abb02f`

## 内置样例数据

| ID | 名称 | IP/指标 | 负责人 | 用户/账号 | 状态 | 等级 | 关键信息 | 摘要 |
|---|---|---|---|---|---|---|---|---|
| `sandbox-44d8` | invoice.exe | 44d88612fea8a8f36de82e1278abb02f | - | - | completed | high | 评分=92；行为=persistence,network_c2,process_injection | 沙箱检测到持久化、下载器和 C2 连接行为 |

## 返回结构

所有动作统一返回 `code`、`msg`、`data`、`summary`。查询类动作返回 `records`、`record`、`total_count` 和 `statistics`；写入、通知、创建、更新和删除类动作返回 `operation`、`records` 和 `affected_count`；健康检查返回 `system_info`，其中包含 `sample_values` 和 `sample_records` 便于发现可用样例值。

## 适用剧本

- 安全告警查询、研判和上下文补全
- 恶意 IP、账号、主机、邮件、文件的模拟处置
- 工单、通知和审计留痕演示
- 无真实安全设备或 SaaS 服务时的产品体验与编排训练
