# XJumpServer 堡垒机

> 版本: v1.0.0
> 供应商: 雾帜智能
> 类型: 离线模拟产品

## 应用简介

离线模拟堡垒机访问审计，返回员工通过堡垒机访问目标设备的方式、协议、会话和命令记录。本应用不连接任何外部系统，所有动作均基于本地 SQLite 状态库和内置样例数据执行，适合开箱即用的 SOAR 剧本演示、培训和 PoC。

## 配置参数

- `database_path`: SQLite 模拟状态库路径，默认 `/tmp/xjumpserver.db`
- `scenario_profile`: 模拟场景名称，默认 `default`
- `scenario_seed`: 模拟数据种子，默认 `x-series-default`
- `delay_min_seconds`: 写入/处置动作最小模拟延迟秒数，默认 `1`
- `delay_max_seconds`: 写入/处置动作最大模拟延迟秒数，默认 `3`

## 动作列表

| 动作 | 类型 | 示例参数 | 说明 |
|---|---|---|---|
| `health_check` | query | - | 健康检查 |
| `query_login_records` | query | `{"username":"alice","target_ip":"10.10.8.23"}` | 查询堡垒机登录记录 |
| `query_target_access` | query | `{"username":"carol","target_ip":"10.20.4.77"}` | 查询员工访问目标设备的方式 |
| `query_online_sessions` | query | `{"username":"carol"}` | 查询当前在线堡垒机会话 |
| `query_command_audit` | query | `{"session_id":"sess-jms-0001"}` | 查询堡垒机命令审计 |
| `terminate_session` | write | `{"session_id":"sess-jms-0002","reason":"可疑远程访问"}` | 终止堡垒机会话 |
| `query_operation_history` | query | - | 查询模拟操作历史 |

## 内置样例索引

以下值可以直接用于动作参数测试，不需要连接外部系统。

- 负责人账号: `alice`, `carol`
- 用户/账号: `alice`, `carol`
- IP: `10.10.8.23`, `10.20.4.77`

## 内置样例数据

| ID | 名称 | IP/指标 | 负责人 | 用户/账号 | 状态 | 等级 | 关键信息 | 摘要 |
|---|---|---|---|---|---|---|---|---|
| `jms-login-20260709-0001` | alice -> prod-web-01 | 10.10.8.23 | alice | alice | finished | medium | 目标IP=10.10.8.23；来源IP=10.30.1.25；协议=ssh；认证=ssh_key；方式=web_terminal；会话=sess-jms-0001 | alice 通过堡垒机使用 SSH 密钥登录 prod-web-01 |
| `jms-login-20260709-0002` | carol -> fin-laptop-07 | 10.20.4.77 | carol | carol | online | high | 目标IP=10.20.4.77；来源IP=10.30.1.88；协议=rdp；认证=password；方式=native_client；会话=sess-jms-0002 | carol 通过堡垒机使用 RDP 账号密码访问财务终端 |
| `jms-command-20260709-0100` | prod-web-01 command audit | 10.10.8.23 | alice | alice | recorded | medium | 会话=sess-jms-0001；命令=sudo systemctl restart nginx；风险=normal | 堡垒机会话命令审计记录 |

## 返回结构

所有动作统一返回 `code`、`msg`、`data`、`summary`。查询类动作返回 `records`、`record`、`total_count` 和 `statistics`；写入、通知、创建、更新和删除类动作返回 `operation`、`records` 和 `affected_count`；健康检查返回 `system_info`，其中包含 `sample_values` 和 `sample_records` 便于发现可用样例值。

## 适用剧本

- 安全告警查询、研判和上下文补全
- 恶意 IP、账号、主机、邮件、文件的模拟处置
- 工单、通知和审计留痕演示
- 无真实安全设备或 SaaS 服务时的产品体验与编排训练
