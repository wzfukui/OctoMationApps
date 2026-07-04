# splunk_query

`splunk_query` 是用于 HoneyGuide SOAR / OctoMation 的 Splunk 只读查询客户端，面向 SIEM 告警轮询场景。

## 配置

- `splunk_web_url`: Splunk Web 地址，例如 `http://192.168.44.28:8000`
- `splunk_api_url`: Splunk REST API 地址，例如 `https://192.168.44.28:8089`。为空时会根据 `splunk_web_url` 自动推导。
- `connection_mode`: 连接模式，默认 `auto`
  - `auto`: 优先使用 `https://host:8089` REST API，连接失败后回退到 Splunk Web proxy。
  - `rest_api`: 只使用 Splunk REST API。
  - `web_proxy`: 只使用 Splunk Web 的 `/en-US/splunkd/__raw` 代理。
- `username`: Splunk 用户名
- `password`: Splunk 密码
- `verify_ssl`: 是否校验 SSL 证书，演示环境可关闭
- `timeout`: 请求超时时间

不要在源码或剧本正文里硬编码 Splunk 密码，应通过应用配置资产保存。

## REST API 与 splunklib 说明

Splunk Python SDK 的包名是 `splunk-sdk`，代码中导入模块名是 `splunklib`。本地开发环境可以使用：

```bash
python3 -m pip install splunk-sdk
```

本 app 当前使用 Splunk 官方 REST API 直接查询，原因是 OctoMation 应用包导入后不一定允许现场环境临时安装 Python 依赖。直接调用 REST API 可以减少部署依赖，并且 `/services/search/jobs/export`、`/services/search/jobs`、`/services/server/info` 这类接口是 Splunk 官方搜索接口。

如果客户只开放 Splunk Web `8000` 端口，`connection_mode=auto` 会在 `8089` 连接失败后，自动登录 Splunk Web，并通过 `/en-US/splunkd/__raw` 代理执行查询。这个模式适合演示和内网临时验证；生产环境仍建议显式开放或代理 Splunk REST API 管理端口。

## Splunk 10.x Free 授权说明

在 Splunk 10.x Free 授权环境下，`8089` 管理/REST API 端口可能不会开放。这是 Splunk Free 授权场景下的限制，不是 `splunk_query` app 的连接故障。

如果使用 Splunk 10.x Free 授权做演示，请按下面方式配置：

```text
splunk_web_url    = http://<splunk-host>:8000
splunk_api_url    = 留空
connection_mode   = auto 或 web_proxy
username          = Splunk Web 登录用户
password          = Splunk Web 登录密码
verify_ssl        = false
timeout           = 20
```

此时 app 会通过 Splunk Web 的 `/en-US/splunkd/__raw` 代理路径执行查询，不依赖 `8089` 端口。

正式商业授权或生产环境中，如果 `8089` 可用，仍建议使用：

```text
splunk_api_url    = https://<splunk-host>:8089
connection_mode   = rest_api 或 auto
```

如果客户现场要求全部走 SDK，也可以把 `splunklib` 作为 vendor 目录打包进 app，或者在运行环境安装 `splunk-sdk` 后改为 SDK 实现。SDK 本质上也是 Splunk REST API 的 Python 封装，优势是连接、Job、结果解析更标准；劣势是需要额外依赖和版本管理。

生产建议：

- 演示和轻量轮询：当前 REST 版本足够。
- 大规模结果集、复杂异步 Job 管理、Splunk Cloud 兼容性验证：建议切换到 `splunklib` 或增加 SDK fallback。
- 无论 REST 还是 SDK，都应显式传入 `earliest_time` 和 `latest_time`，避免 REST 搜索默认跑全量历史数据。

## 动作

### health_check

检查 Splunk REST API 是否可访问。

### run_search

执行任意 SPL 查询，支持 `earliest_time`、`latest_time` 和 `max_count`。

示例：

```text
search sourcetype=fortigate
```

时间窗口：

```text
earliest_time=-5m
latest_time=now
```

### poll_alerts

用于 SOAR 轮询告警。

- `base_search`: 基础告警查询，例如 `search sourcetype=fortigate`
- `last_poll_time`: 上次轮询水位时间；有值时优先作为本次 `earliest_time`
- `earliest_time`: 默认 `-5m`
- `latest_time`: 默认 `now`
- `alert_time_field`: 默认 `_time`
- `next_poll_time`: 返回结果中的建议下次轮询水位

## 演示建议

Splunk Web 地址可配置为客户可见的 Web 控制台地址。Splunk REST API 默认常见地址是 `https://host:8089`，如果现场环境不同，请显式填写 `splunk_api_url`。

## 测试

本 app 包含两个测试文件：

- `test_splunk_query.py`: 本地单元测试，不访问真实 Splunk。
- `splunk_query_live_test.py`: 真实 Splunk 查询测试，通过环境变量传入连接信息和密码。

示例：

```bash
SPLUNK_QUERY_LIVE=1 \
SPLUNK_WEB_URL=http://192.168.44.28:8000 \
SPLUNK_USERNAME=admin \
SPLUNK_PASSWORD='***' \
python3 splunk_query_live_test.py
```
