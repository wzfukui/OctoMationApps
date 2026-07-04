# kafka_client 应用文档

Kafka 客户端，支持连接检查、发送消息、读取消息、简单读取消息 Value 和统计 Topic 条目。

当前版本：`1.1.0`

## 依赖

运行环境需要安装 Python 依赖：

```bash
pip install kafka-python==2.0.1
```

如果 HoneyGuide SOAR 执行环境未内置该依赖，动作会返回明确错误：

```text
kafka-python is required. Install it with: pip install kafka-python
```

## 默认连接

| 配置 | 默认值 |
| --- | --- |
| bootstrap_servers | `192.168.22.251:9092` |
| security_protocol | `PLAINTEXT` |
| kafka-python | `2.0.1` |

多个 bootstrap server 使用英文逗号分隔。Topic 不属于资产级配置，需要在每个动作参数中填写，方便同一个 Kafka 资产在不同剧本节点里操作不同 Topic。

## 动作分类

平台动作类型只使用：

| 类型 | 动作 |
| --- | --- |
| query | `health_check`, `list_topics`, `describe_topic`, `count_messages`, `read_messages`, `simple_read_message`, `list_consumer_groups`, `describe_consumer_group`, `consumer_lag` |
| write | `send_message`, `create_topic`, `delete_topic`, `clear_topic`, `create_partitions`, `alter_topic_config` |
| notify | 当前未使用 |

## 查询动作

### health_check

检查 Kafka 连接，并返回可见 Topic 列表。

### list_topics

列出 Topic。默认不包含 `__consumer_offsets` 等内部 Topic。

### describe_topic

查看 Topic 分区、副本、leader、ISR 等元数据。

### count_messages

统计 Topic 当前可读条目数。

统计方式：按分区读取 beginning offset 和 end offset，并计算差值。

### read_messages

读取 Topic 消息。

| 参数 | 说明 |
| --- | --- |
| topic | Topic 名称 |
| max_messages | 最多读取条数 |
| read_from | `latest` 从分区尾部回看 N 条；`earliest` 从起始位置读取 |
| timeout_ms | 读取超时时间 |

说明：`latest` 模式会按每个分区尾部回看，最终按时间和 offset 排序后截断到 `max_messages`。

### simple_read_message

读取一条 Kafka 消息，并且只返回消息的 `value` 字符串。

适合剧本里只需要消费消息正文，不需要 partition、offset、timestamp、key、headers 等元数据的场景。

| 参数 | 说明 |
| --- | --- |
| topic | Topic 名称 |
| read_from | `latest` 读取最新一条；`earliest` 读取最早一条 |
| timeout_ms | 读取超时时间 |

返回示例：

```json
{
    "code": 200,
    "msg": "Kafka message value read",
    "data": "{\"event_type\": \"kafka_client_live_test\", \"source\": \"honeyguide\"}"
}
```

### list_consumer_groups

列出 Consumer Group。

### describe_consumer_group

查看 Consumer Group 状态和成员信息。

### consumer_lag

按 Consumer Group 统计已提交 offset 与 Topic end offset 的差值。

## 写入动作

### send_message

向指定 Topic 发送消息。

常用参数：

| 参数 | 说明 |
| --- | --- |
| topic | Topic 名称，必填；每次动作执行时从动作参数读取 |
| message | 消息内容，字符串或 JSON 文本 |
| key | 消息 Key，可为空 |
| headers | 支持 JSON、`key=value,key2=value2` 或空 |
| partition | 指定分区，可为空 |
| timestamp_ms | 指定消息时间戳，可为空 |

## 管理动作

管理动作均为 `write` 类型，并且都需要传入：

```text
confirm = yes
```

没有确认字段时动作会直接失败，不会连接 Kafka 执行操作。

### create_topic

创建 Topic，支持分区数、副本因子和 Topic 配置。

### delete_topic

删除 Topic。

### clear_topic

清空 Topic。

注意：`kafka-python 2.0.1` 不支持 `delete_records` Admin API，因此当前服务器版本下该动作会返回“不支持”，不会执行任何变通清理。

### create_partitions

增加 Topic 分区。Kafka 只能增加分区，不能减少分区。

### alter_topic_config

修改 Topic 配置，例如：

```text
retention.ms=60000
```

## 测试 Topic

```text
zensoc-alerts
```
