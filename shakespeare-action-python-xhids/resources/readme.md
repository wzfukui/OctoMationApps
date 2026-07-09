# XHIDS 主机安全

> 版本: v1.0.0
> 供应商: 雾帜智能
> 类型: 离线模拟产品

## 应用简介

离线模拟 HIDS 主机安全平台，提供主机、进程、端口、告警与隔离动作。本应用不连接任何外部系统，所有动作均基于本地 SQLite 状态库和内置样例数据执行，适合开箱即用的 SOAR 剧本演示、培训和 PoC。

## 配置参数

- `database_path`: SQLite 模拟状态库路径，默认 `/tmp/xhids.db`
- `scenario_profile`: 模拟场景名称，默认 `default`
- `scenario_seed`: 模拟数据种子，默认 `x-series-default`
- `delay_min_seconds`: 写入/处置动作最小模拟延迟秒数，默认 `1`
- `delay_max_seconds`: 写入/处置动作最大模拟延迟秒数，默认 `3`

## 动作列表

| 动作 | 类型 | 示例参数 | 说明 |
|---|---|---|---|
| `health_check` | query | - | 健康检查 |
| `query_host_by_ip` | query | `{"ip":"10.10.8.23"}` | 根据 IP 查询主机信息 |
| `query_host_processes` | query | `{"host_id":"host-prod-web-01"}` | 查询主机进程信息 |
| `query_host_ports` | query | `{"host_id":"host-prod-web-01"}` | 查询主机端口信息 |
| `query_security_events` | query | `{"severity":"high"}` | 查询主机安全事件 |
| `isolate_host` | write | `{"host_id":"host-prod-web-01","reason":"检测到反弹 shell"}` | 隔离主机 |
| `release_host` | write | `{"host_id":"host-prod-web-01","reason":"人工确认恢复"}` | 解除主机隔离 |
| `query_operation_history` | query | - | 查询模拟操作历史 |

## 内置样例索引

以下值可以直接用于动作参数测试，不需要连接外部系统。

- 负责人账号: `alice`, `carol`
- 用户/账号: `carol`, `www-data`
- IP: `10.10.8.23`, `10.20.4.77`

## 内置样例数据

| ID | 名称 | IP/指标 | 负责人 | 用户/账号 | 状态 | 等级 | 关键信息 | 摘要 |
|---|---|---|---|---|---|---|---|---|
| `host-prod-web-01` | prod-web-01 | 10.10.8.23 | alice | www-data | monitored | high | processes=nginx,python3 /tmp/.x/update.py,sshd；ports=22,80,443,8443；events=abnormal_login,reverse_shell | 检测到异常登录和反弹 shell 行为 |
| `host-fin-laptop-07` | fin-laptop-07 | 10.20.4.77 | carol | carol | monitored | medium | processes=winword.exe,powershell.exe；ports=135,445；events=suspicious_child_process | 可疑 Office 子进程启动 PowerShell |

## 返回结构

所有动作统一返回 `code`、`msg`、`data`、`summary`。查询类动作返回 `records`、`record`、`total_count` 和 `statistics`；写入、通知、创建、更新和删除类动作返回 `operation`、`records` 和 `affected_count`；健康检查返回 `system_info`，其中包含 `sample_values` 和 `sample_records` 便于发现可用样例值。

## 适用剧本

- 安全告警查询、研判和上下文补全
- 恶意 IP、账号、主机、邮件、文件的模拟处置
- 工单、通知和审计留痕演示
- 无真实安全设备或 SaaS 服务时的产品体验与编排训练
