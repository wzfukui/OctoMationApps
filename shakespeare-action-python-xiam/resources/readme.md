# XIAM 身份与访问管理

> 版本: v1.0.0
> 供应商: 雾帜智能
> 类型: 离线模拟产品

## 应用简介

离线模拟 AD/LDAP/IAM 身份系统，支持用户查询、登录记录、禁用、启用和重置密码。本应用不连接任何外部系统，所有动作均基于本地 SQLite 状态库和内置样例数据执行，适合开箱即用的 SOAR 剧本演示、培训和 PoC。

## 配置参数

- `database_path`: SQLite 模拟状态库路径，默认 `/tmp/xiam.db`
- `scenario_profile`: 模拟场景名称，默认 `default`
- `scenario_seed`: 模拟数据种子，默认 `x-series-default`
- `delay_min_seconds`: 写入/处置动作最小模拟延迟秒数，默认 `1`
- `delay_max_seconds`: 写入/处置动作最大模拟延迟秒数，默认 `3`

## 动作列表

| 动作 | 类型 | 示例参数 | 说明 |
|---|---|---|---|
| `health_check` | query | - | 健康检查 |
| `query_user` | query | `{"username":"alice"}` | 查询用户信息 |
| `query_user_logins` | query | `{"username":"alice"}` | 查询用户登录记录 |
| `disable_user` | write | `{"username":"alice","reason":"疑似账号失陷"}` | 禁用用户 |
| `enable_user` | write | `{"username":"alice"}` | 启用用户 |
| `reset_password` | write | `{"username":"alice","reason":"账号疑似泄露"}` | 重置用户密码 |
| `query_operation_history` | query | - | 查询模拟操作历史 |

## 内置样例索引

以下值可以直接用于动作参数测试，不需要连接外部系统。

- 负责人账号: `电商业务部`, `财务部`
- 用户/账号: `alice`, `carol`

## 内置样例数据

| ID | 名称 | IP/指标 | 负责人 | 用户/账号 | 状态 | 等级 | 关键信息 | 摘要 |
|---|---|---|---|---|---|---|---|---|
| `user-alice` | alice | - | 电商业务部 | alice | enabled | medium | 邮箱=alice@example.com；最近登录IP=203.0.113.77；MFA=True | 支付系统负责人，最近发生异地登录 |
| `user-carol` | carol | - | 财务部 | carol | enabled | medium | 邮箱=carol@example.com；最近登录IP=10.20.4.77；MFA=False | 财务用户，收到钓鱼邮件 |

## 返回结构

所有动作统一返回 `code`、`msg`、`data`、`summary`。查询类动作返回 `records`、`record`、`total_count` 和 `statistics`；写入、通知、创建、更新和删除类动作返回 `operation`、`records` 和 `affected_count`；健康检查返回 `system_info`，其中包含 `sample_values` 和 `sample_records` 便于发现可用样例值。

## 适用剧本

- 安全告警查询、研判和上下文补全
- 恶意 IP、账号、主机、邮件、文件的模拟处置
- 工单、通知和审计留痕演示
- 无真实安全设备或 SaaS 服务时的产品体验与编排训练
