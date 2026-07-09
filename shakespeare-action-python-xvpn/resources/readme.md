# XVPN 远程接入

> 版本: v1.0.0
> 供应商: 雾帜智能
> 类型: 离线模拟产品

## 应用简介

离线模拟 VPN 远程接入系统，支持登录状态、账号创建、账号禁用和踢人下线。本应用不连接任何外部系统，所有动作均基于本地 SQLite 状态库和内置样例数据执行，适合开箱即用的 SOAR 剧本演示、培训和 PoC。

## 配置参数

- `database_path`: SQLite 模拟状态库路径，默认 `/tmp/xvpn.db`
- `scenario_profile`: 模拟场景名称，默认 `default`
- `scenario_seed`: 模拟数据种子，默认 `x-series-default`
- `delay_min_seconds`: 写入/处置动作最小模拟延迟秒数，默认 `1`
- `delay_max_seconds`: 写入/处置动作最大模拟延迟秒数，默认 `3`

## 动作列表

| 动作 | 类型 | 示例参数 | 说明 |
|---|---|---|---|
| `health_check` | query | - | 健康检查 |
| `query_login_status` | query | `{"username":"alice"}` | 查询 VPN 用户登录状态 |
| `query_online_users` | query | `{"username":"alice"}` | 查询 VPN 在线用户 |
| `create_vpn_account` | write | `{"username":"dave","display_name":"Dave","department":"安全运营"}` | 创建 VPN 账号 |
| `disable_vpn_account` | write | `{"username":"alice","reason":"疑似账号失陷"}` | 禁用 VPN 账号 |
| `enable_vpn_account` | write | `{"username":"alice"}` | 启用 VPN 账号 |
| `kick_vpn_user` | write | `{"username":"alice","reason":"异常公网 IP 登录"}` | 踢 VPN 用户下线 |
| `query_vpn_history` | query | `{"username":"alice"}` | 查询 VPN 登录历史 |

## 内置样例索引

以下值可以直接用于动作参数测试，不需要连接外部系统。

- 负责人账号: `alice`, `电商业务部`, `财务部`
- 用户/账号: `alice`, `carol`
- IP: `10.60.8.11`

## 内置样例数据

| ID | 名称 | IP/指标 | 负责人 | 用户/账号 | 状态 | 等级 | 关键信息 | 摘要 |
|---|---|---|---|---|---|---|---|---|
| `vpn-user-alice` | alice | - | 电商业务部 | alice | enabled | medium | 用户组=vpn-users；最近登录IP=203.0.113.77；最近登录=2026-07-09 09:18:24；MFA=True | alice VPN 账号已启用，最近从异常公网 IP 登录 |
| `vpn-session-alice-001` | alice active vpn session | 10.60.8.11 | alice | alice | online | high | 来源IP=203.0.113.77；会话=vpn-sess-0001；客户端=macOS；login_time=2026-07-09 10:02:15 | alice 当前 VPN 在线，会话源 IP 命中威胁情报 |
| `vpn-user-carol` | carol | - | 财务部 | carol | enabled | medium | 用户组=vpn-users；最近登录IP=198.51.100.23；MFA=False | carol VPN 账号已启用 |

## 返回结构

所有动作统一返回 `code`、`msg`、`data`、`summary`。查询类动作返回 `records`、`record`、`total_count` 和 `statistics`；写入、通知、创建、更新和删除类动作返回 `operation`、`records` 和 `affected_count`；健康检查返回 `system_info`，其中包含 `sample_values` 和 `sample_records` 便于发现可用样例值。

## 适用剧本

- 安全告警查询、研判和上下文补全
- 恶意 IP、账号、主机、邮件、文件的模拟处置
- 工单、通知和审计留痕演示
- 无真实安全设备或 SaaS 服务时的产品体验与编排训练
