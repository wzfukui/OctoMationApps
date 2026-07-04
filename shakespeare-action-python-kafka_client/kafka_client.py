# -*- coding: utf-8 -*-
import json
import time


def _response(code=200, msg="", data=None, status_code=200, summary_msg=""):
    return {
        "code": code,
        "msg": msg,
        "data": data or {},
        "summary": {
            "statusCode": status_code,
            "msg": summary_msg or msg
        }
    }


def _int_value(value, default):
    try:
        if value is None or value == "":
            return default
        return int(value)
    except Exception:
        return default


def _float_value(value, default):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def _bool_value(value, default=False):
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("1", "true", "yes", "y", "on")


def _normalise_bootstrap_servers(value):
    if isinstance(value, list):
        servers = [str(item).strip() for item in value if str(item).strip()]
    else:
        servers = [item.strip() for item in str(value or "").split(",") if item.strip()]
    if not servers:
        raise ValueError("bootstrap_servers is required")
    return servers


def _parse_headers(headers):
    if not headers:
        return []
    if isinstance(headers, dict):
        return [(str(key), _to_bytes(value)) for key, value in headers.items()]
    if isinstance(headers, list):
        parsed = []
        for item in headers:
            if isinstance(item, dict):
                key = item.get("key")
                value = item.get("value")
                if key:
                    parsed.append((str(key), _to_bytes(value)))
        return parsed

    text = str(headers).strip()
    if not text:
        return []
    try:
        payload = json.loads(text)
        return _parse_headers(payload)
    except Exception:
        parsed = []
        for part in text.split(","):
            if "=" not in part:
                continue
            key, value = part.split("=", 1)
            key = key.strip()
            if key:
                parsed.append((key, _to_bytes(value.strip())))
        return parsed


def _to_bytes(value, encoding="utf-8"):
    if value is None:
        return None
    if isinstance(value, bytes):
        return value
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False).encode(encoding)
    return str(value).encode(encoding)


def _decode_bytes(value, encoding="utf-8"):
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        return value.decode(encoding)
    except Exception:
        return repr(value)


def _load_kafka():
    try:
        from kafka import KafkaAdminClient, KafkaConsumer, KafkaProducer, TopicPartition
    except Exception as error:
        raise RuntimeError("kafka-python is required. Install it with: pip install kafka-python") from error
    return KafkaAdminClient, KafkaConsumer, KafkaProducer, TopicPartition


def _load_admin_models():
    try:
        from kafka.admin import ConfigResource, ConfigResourceType, NewPartitions, NewTopic
    except Exception as error:
        raise RuntimeError("kafka-python admin models are required") from error
    return ConfigResource, ConfigResourceType, NewPartitions, NewTopic


def _require_confirm(params):
    confirm = str((params or {}).get("confirm") or "").strip().lower()
    if confirm != "yes":
        raise ValueError("confirm=yes is required for this management action")


def _parse_key_value_configs(value):
    if not value:
        return {}
    if isinstance(value, dict):
        return {str(key): str(item) for key, item in value.items()}
    text = str(value).strip()
    if not text:
        return {}
    try:
        payload = json.loads(text)
        if isinstance(payload, dict):
            return {str(key): str(item) for key, item in payload.items()}
    except Exception:
        pass

    configs = {}
    for part in text.split(","):
        if "=" not in part:
            continue
        key, item = part.split("=", 1)
        key = key.strip()
        if key:
            configs[key] = item.strip()
    return configs


def _json_safe(value):
    if isinstance(value, bytes):
        return _decode_bytes(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(_json_safe(key)): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "_asdict"):
        return _json_safe(value._asdict())
    if hasattr(value, "__dict__"):
        return _json_safe(value.__dict__)
    return str(value)


def _normalise_group_name(item):
    if isinstance(item, (list, tuple)) and item:
        return str(item[0])
    if hasattr(item, "group"):
        return str(item.group)
    return str(item)


class KafkaClient:
    def __init__(self, assets):
        assets = assets or {}
        self.bootstrap_servers = _normalise_bootstrap_servers(
            assets.get("bootstrap_servers") or assets.get("bootstrap") or "192.168.22.251:9092"
        )
        self.client_id = (assets.get("client_id") or "honeyguide-kafka-client").strip()
        self.timeout_ms = _int_value(assets.get("timeout_ms"), 10000)
        self.encoding = assets.get("encoding") or "utf-8"
        self.security_protocol = (assets.get("security_protocol") or "PLAINTEXT").strip()
        self.sasl_mechanism = (assets.get("sasl_mechanism") or "").strip()
        self.sasl_username = assets.get("sasl_username") or ""
        self.sasl_password = assets.get("sasl_password") or ""

    def common_kwargs(self):
        kwargs = {
            "bootstrap_servers": self.bootstrap_servers,
            "client_id": self.client_id,
            "request_timeout_ms": self.timeout_ms,
            "security_protocol": self.security_protocol
        }
        if self.sasl_mechanism:
            kwargs["sasl_mechanism"] = self.sasl_mechanism
        if self.sasl_username:
            kwargs["sasl_plain_username"] = self.sasl_username
        if self.sasl_password:
            kwargs["sasl_plain_password"] = self.sasl_password
        return kwargs

    def consumer_kwargs(self, consumer_timeout_ms=1000):
        kwargs = self.common_kwargs()
        kwargs["consumer_timeout_ms"] = consumer_timeout_ms
        kwargs["enable_auto_commit"] = False
        return kwargs

    def health_check(self):
        KafkaAdminClient, _, _, _ = _load_kafka()
        started_at = time.time()
        admin = KafkaAdminClient(**self.common_kwargs())
        try:
            topics = sorted(admin.list_topics())
            data = {
                "status": "ok",
                "bootstrap_servers": self.bootstrap_servers,
                "topic_count": len(topics),
                "topics": topics[:50],
                "elapsed_ms": int((time.time() - started_at) * 1000)
            }
            return _response(code=200, msg="Kafka connected", data=data, status_code=200, summary_msg="连接成功")
        finally:
            admin.close()

    def list_topics(self, include_internal=False):
        KafkaAdminClient, _, _, _ = _load_kafka()
        admin = KafkaAdminClient(**self.common_kwargs())
        try:
            topics = sorted(admin.list_topics())
            if not include_internal:
                topics = [topic for topic in topics if not topic.startswith("__")]
            return {
                "bootstrap_servers": self.bootstrap_servers,
                "count": len(topics),
                "topics": topics
            }
        finally:
            admin.close()

    def describe_topic(self, topic):
        KafkaAdminClient, _, _, _ = _load_kafka()
        topic = (topic or "").strip()
        if not topic:
            raise ValueError("topic is required")
        admin = KafkaAdminClient(**self.common_kwargs())
        try:
            descriptions = admin.describe_topics([topic])
            return {
                "topic": topic,
                "description": _json_safe(descriptions[0] if descriptions else {})
            }
        finally:
            admin.close()

    def send_message(self, topic, message, key="", headers=None, partition=None, timestamp_ms=None):
        _, _, KafkaProducer, _ = _load_kafka()
        from kafka.serializer import Serializer

        class BytesSerializer(Serializer):
            def __init__(self, encoding):
                self.encoding = encoding

            def serialize(self, topic, *args):
                data = args[-1] if args else None
                return _to_bytes(data, self.encoding)

        topic = (topic or "").strip()
        if not topic:
            raise ValueError("topic is required")
        if message is None:
            message = ""

        producer = KafkaProducer(
            **self.common_kwargs(),
            key_serializer=BytesSerializer(self.encoding),
            value_serializer=BytesSerializer(self.encoding)
        )
        try:
            future = producer.send(
                topic,
                key=key if key != "" else None,
                value=message,
                headers=_parse_headers(headers),
                partition=partition if partition is not None and partition != "" else None,
                timestamp_ms=timestamp_ms if timestamp_ms is not None and timestamp_ms != "" else None
            )
            metadata = future.get(timeout=max(1, self.timeout_ms / 1000.0))
            producer.flush(timeout=max(1, self.timeout_ms / 1000.0))
            data = {
                "topic": metadata.topic,
                "partition": metadata.partition,
                "offset": metadata.offset,
                "timestamp_ms": timestamp_ms or "",
                "sent": True
            }
            return _response(code=200, msg="Kafka message sent", data=data, status_code=200, summary_msg="发送成功")
        finally:
            producer.close()

    def get_offsets(self, topic):
        _, KafkaConsumer, _, TopicPartition = _load_kafka()
        topic = (topic or "").strip()
        if not topic:
            raise ValueError("topic is required")

        consumer = KafkaConsumer(**self.consumer_kwargs(consumer_timeout_ms=1000))
        try:
            partitions = consumer.partitions_for_topic(topic)
            if partitions is None:
                raise ValueError("topic not found: %s" % topic)
            topic_partitions = [TopicPartition(topic, partition) for partition in sorted(partitions)]
            consumer.assign(topic_partitions)
            beginning = consumer.beginning_offsets(topic_partitions)
            end = consumer.end_offsets(topic_partitions)
            details = []
            total = 0
            for tp in topic_partitions:
                first_offset = beginning.get(tp, 0)
                last_offset = end.get(tp, 0)
                count = max(0, last_offset - first_offset)
                total += count
                details.append({
                    "topic": tp.topic,
                    "partition": tp.partition,
                    "beginning_offset": first_offset,
                    "end_offset": last_offset,
                    "count": count
                })
            return {
                "topic": topic,
                "partition_count": len(topic_partitions),
                "count": total,
                "partitions": details
            }
        finally:
            consumer.close()

    def list_consumer_groups(self):
        KafkaAdminClient, _, _, _ = _load_kafka()
        admin = KafkaAdminClient(**self.common_kwargs())
        try:
            groups = admin.list_consumer_groups()
            records = []
            for item in groups:
                if isinstance(item, (list, tuple)):
                    records.append({
                        "group_id": item[0] if len(item) > 0 else "",
                        "protocol_type": item[1] if len(item) > 1 else ""
                    })
                else:
                    records.append({"group_id": _normalise_group_name(item), "protocol_type": ""})
            records.sort(key=lambda item: item.get("group_id", ""))
            return {"count": len(records), "consumer_groups": records}
        finally:
            admin.close()

    def describe_consumer_group(self, group_id):
        KafkaAdminClient, _, _, _ = _load_kafka()
        group_id = (group_id or "").strip()
        if not group_id:
            raise ValueError("group_id is required")
        admin = KafkaAdminClient(**self.common_kwargs())
        try:
            descriptions = admin.describe_consumer_groups([group_id])
            return {
                "group_id": group_id,
                "description": _json_safe(descriptions[0] if descriptions else {})
            }
        finally:
            admin.close()

    def consumer_lag(self, group_id, topic=""):
        KafkaAdminClient, KafkaConsumer, _, TopicPartition = _load_kafka()
        group_id = (group_id or "").strip()
        topic = (topic or "").strip()
        if not group_id:
            raise ValueError("group_id is required")

        admin = KafkaAdminClient(**self.common_kwargs())
        consumer = KafkaConsumer(**self.consumer_kwargs(consumer_timeout_ms=1000))
        try:
            committed = admin.list_consumer_group_offsets(group_id)
            topic_partitions = sorted(committed.keys(), key=lambda item: (item.topic, item.partition))
            if topic:
                topic_partitions = [tp for tp in topic_partitions if tp.topic == topic]
            if not topic_partitions:
                return {"group_id": group_id, "topic": topic, "count": 0, "total_lag": 0, "partitions": []}

            consumer.assign(topic_partitions)
            end_offsets = consumer.end_offsets(topic_partitions)
            rows = []
            total_lag = 0
            for tp in topic_partitions:
                committed_item = committed.get(tp)
                committed_offset = getattr(committed_item, "offset", None)
                end_offset = end_offsets.get(tp, 0)
                if committed_offset is None or committed_offset < 0:
                    lag = None
                else:
                    lag = max(0, end_offset - committed_offset)
                    total_lag += lag
                rows.append({
                    "topic": tp.topic,
                    "partition": tp.partition,
                    "committed_offset": committed_offset,
                    "end_offset": end_offset,
                    "lag": lag
                })
            return {
                "group_id": group_id,
                "topic": topic,
                "count": len(rows),
                "total_lag": total_lag,
                "partitions": rows
            }
        finally:
            consumer.close()
            admin.close()

    def read_messages(self, topic, max_messages=10, read_from="latest", timeout_ms=None, include_headers=True):
        _, KafkaConsumer, _, TopicPartition = _load_kafka()
        topic = (topic or "").strip()
        if not topic:
            raise ValueError("topic is required")
        max_messages = _int_value(max_messages, 10)
        if max_messages < 1:
            max_messages = 1
        read_from = (read_from or "latest").strip().lower()
        timeout_ms = _int_value(timeout_ms, self.timeout_ms)

        consumer = KafkaConsumer(**self.consumer_kwargs(consumer_timeout_ms=max(1000, timeout_ms)))
        try:
            partitions = consumer.partitions_for_topic(topic)
            if partitions is None:
                raise ValueError("topic not found: %s" % topic)
            topic_partitions = [TopicPartition(topic, partition) for partition in sorted(partitions)]
            consumer.assign(topic_partitions)

            if read_from == "earliest":
                consumer.seek_to_beginning(*topic_partitions)
            else:
                end_offsets = consumer.end_offsets(topic_partitions)
                for tp in topic_partitions:
                    consumer.seek(tp, max(0, end_offsets.get(tp, 0) - max_messages))

            started_at = time.time()
            records = []
            while len(records) < max_messages:
                batch = consumer.poll(timeout_ms=500, max_records=max_messages)
                for _, messages in batch.items():
                    for message in messages:
                        records.append(_serialise_message(message, self.encoding, include_headers))
                        if len(records) >= max_messages:
                            break
                    if len(records) >= max_messages:
                        break
                if int((time.time() - started_at) * 1000) >= timeout_ms:
                    break

            records.sort(key=lambda item: (item.get("timestamp") or 0, item.get("partition"), item.get("offset")))
            if read_from != "earliest" and len(records) > max_messages:
                records = records[-max_messages:]
            return {
                "topic": topic,
                "read_from": read_from,
                "count": len(records),
                "messages": records,
                "elapsed_ms": int((time.time() - started_at) * 1000)
            }
        finally:
            consumer.close()

    def create_topic(self, topic, partitions=1, replication_factor=1, topic_configs=None):
        KafkaAdminClient, _, _, _ = _load_kafka()
        _, _, _, NewTopic = _load_admin_models()
        topic = (topic or "").strip()
        if not topic:
            raise ValueError("topic is required")
        new_topic = NewTopic(
            name=topic,
            num_partitions=_int_value(partitions, 1),
            replication_factor=_int_value(replication_factor, 1),
            topic_configs=_parse_key_value_configs(topic_configs)
        )
        admin = KafkaAdminClient(**self.common_kwargs())
        try:
            result = admin.create_topics([new_topic], timeout_ms=self.timeout_ms)
            return {"topic": topic, "created": True, "result": _json_safe(result)}
        finally:
            admin.close()

    def delete_topic(self, topic):
        KafkaAdminClient, _, _, _ = _load_kafka()
        topic = (topic or "").strip()
        if not topic:
            raise ValueError("topic is required")
        admin = KafkaAdminClient(**self.common_kwargs())
        try:
            result = admin.delete_topics([topic], timeout_ms=self.timeout_ms)
            return {"topic": topic, "deleted": True, "result": _json_safe(result)}
        finally:
            admin.close()

    def create_partitions(self, topic, total_count):
        KafkaAdminClient, _, _, _ = _load_kafka()
        _, _, NewPartitions, _ = _load_admin_models()
        topic = (topic or "").strip()
        if not topic:
            raise ValueError("topic is required")
        total_count = _int_value(total_count, 0)
        if total_count < 1:
            raise ValueError("total_count must be greater than 0")
        admin = KafkaAdminClient(**self.common_kwargs())
        try:
            result = admin.create_partitions({topic: NewPartitions(total_count)}, timeout_ms=self.timeout_ms)
            return {"topic": topic, "total_count": total_count, "updated": True, "result": _json_safe(result)}
        finally:
            admin.close()

    def alter_topic_config(self, topic, topic_configs):
        KafkaAdminClient, _, _, _ = _load_kafka()
        ConfigResource, ConfigResourceType, _, _ = _load_admin_models()
        topic = (topic or "").strip()
        configs = _parse_key_value_configs(topic_configs)
        if not topic:
            raise ValueError("topic is required")
        if not configs:
            raise ValueError("topic_configs is required")
        admin = KafkaAdminClient(**self.common_kwargs())
        try:
            resource = ConfigResource(ConfigResourceType.TOPIC, topic, configs=configs)
            result = admin.alter_configs([resource])
            return {"topic": topic, "configs": configs, "updated": True, "result": _json_safe(result)}
        finally:
            admin.close()

    def clear_topic(self, topic):
        KafkaAdminClient, KafkaConsumer, _, TopicPartition = _load_kafka()
        topic = (topic or "").strip()
        if not topic:
            raise ValueError("topic is required")
        if not hasattr(KafkaAdminClient, "delete_records"):
            raise NotImplementedError("clear_topic requires kafka-python delete_records support; kafka-python 2.0.1 does not provide it")

        admin = KafkaAdminClient(**self.common_kwargs())
        consumer = KafkaConsumer(**self.consumer_kwargs(consumer_timeout_ms=1000))
        try:
            partitions = consumer.partitions_for_topic(topic)
            if partitions is None:
                raise ValueError("topic not found: %s" % topic)
            topic_partitions = [TopicPartition(topic, partition) for partition in sorted(partitions)]
            consumer.assign(topic_partitions)
            end_offsets = consumer.end_offsets(topic_partitions)
            records_to_delete = {tp: end_offsets.get(tp, 0) for tp in topic_partitions}
            result = admin.delete_records(records_to_delete, timeout_ms=self.timeout_ms)
            return {
                "topic": topic,
                "cleared": True,
                "deleted_to_offsets": [
                    {"topic": tp.topic, "partition": tp.partition, "offset": offset}
                    for tp, offset in records_to_delete.items()
                ],
                "result": _json_safe(result)
            }
        finally:
            consumer.close()
            admin.close()


def _serialise_message(message, encoding="utf-8", include_headers=True):
    item = {
        "topic": message.topic,
        "partition": message.partition,
        "offset": message.offset,
        "timestamp": message.timestamp,
        "timestamp_type": message.timestamp_type,
        "key": _decode_bytes(message.key, encoding),
        "value": _decode_bytes(message.value, encoding)
    }
    if include_headers:
        item["headers"] = [
            {"key": key, "value": _decode_bytes(value, encoding)}
            for key, value in (message.headers or [])
        ]
    return item


def health_check(params, assets, context_info=None):
    try:
        client = KafkaClient(assets)
        return client.health_check()
    except Exception as error:
        return _response(
            code=500,
            msg=str(error),
            data={"status": "failed"},
            status_code=500,
            summary_msg="连接异常"
        )


def send_message(params, assets, context_info=None):
    try:
        params = params or {}
        client = KafkaClient(assets)
        return client.send_message(
            topic=params.get("topic", ""),
            message=params.get("message", ""),
            key=params.get("key", ""),
            headers=params.get("headers", ""),
            partition=params.get("partition", None),
            timestamp_ms=params.get("timestamp_ms", None)
        )
    except Exception as error:
        return _response(code=500, msg=str(error), data={"sent": False}, status_code=500, summary_msg="发送异常")


def list_topics(params, assets, context_info=None):
    try:
        params = params or {}
        client = KafkaClient(assets)
        data = client.list_topics(include_internal=_bool_value(params.get("include_internal"), False))
        return _response(code=200, msg="Kafka topics listed", data=data, status_code=200, summary_msg="查询成功")
    except Exception as error:
        return _response(code=500, msg=str(error), data={"topics": [], "count": 0}, status_code=500, summary_msg="查询异常")


def describe_topic(params, assets, context_info=None):
    try:
        params = params or {}
        client = KafkaClient(assets)
        data = client.describe_topic(params.get("topic", ""))
        return _response(code=200, msg="Kafka topic described", data=data, status_code=200, summary_msg="查询成功")
    except Exception as error:
        return _response(code=500, msg=str(error), data={}, status_code=500, summary_msg="查询异常")


def read_messages(params, assets, context_info=None):
    try:
        params = params or {}
        client = KafkaClient(assets)
        data = client.read_messages(
            topic=params.get("topic", ""),
            max_messages=_int_value(params.get("max_messages"), 10),
            read_from=params.get("read_from", "latest"),
            timeout_ms=_int_value(params.get("timeout_ms"), client.timeout_ms),
            include_headers=_bool_value(params.get("include_headers"), True)
        )
        return _response(code=200, msg="Kafka messages read", data=data, status_code=200, summary_msg="读取成功")
    except Exception as error:
        return _response(code=500, msg=str(error), data={"messages": [], "count": 0}, status_code=500, summary_msg="读取异常")


def simple_read_message(params, assets, context_info=None):
    try:
        params = params or {}
        client = KafkaClient(assets)
        data = client.read_messages(
            topic=params.get("topic", ""),
            max_messages=1,
            read_from=params.get("read_from", "latest"),
            timeout_ms=_int_value(params.get("timeout_ms"), client.timeout_ms),
            include_headers=False
        )
        messages = data.get("messages") or []
        value = messages[0].get("value", "") if messages else ""
        return _response(code=200, msg="Kafka message value read", data=value, status_code=200, summary_msg="读取成功")
    except Exception as error:
        return _response(code=500, msg=str(error), data="", status_code=500, summary_msg="读取异常")


def count_messages(params, assets, context_info=None):
    try:
        params = params or {}
        client = KafkaClient(assets)
        data = client.get_offsets(params.get("topic", ""))
        return _response(code=200, msg="Kafka topic counted", data=data, status_code=200, summary_msg="统计成功")
    except Exception as error:
        return _response(code=500, msg=str(error), data={"count": 0}, status_code=500, summary_msg="统计异常")


def list_consumer_groups(params, assets, context_info=None):
    try:
        client = KafkaClient(assets)
        data = client.list_consumer_groups()
        return _response(code=200, msg="Kafka consumer groups listed", data=data, status_code=200, summary_msg="查询成功")
    except Exception as error:
        return _response(code=500, msg=str(error), data={"consumer_groups": [], "count": 0}, status_code=500, summary_msg="查询异常")


def describe_consumer_group(params, assets, context_info=None):
    try:
        params = params or {}
        client = KafkaClient(assets)
        data = client.describe_consumer_group(params.get("group_id", ""))
        return _response(code=200, msg="Kafka consumer group described", data=data, status_code=200, summary_msg="查询成功")
    except Exception as error:
        return _response(code=500, msg=str(error), data={}, status_code=500, summary_msg="查询异常")


def consumer_lag(params, assets, context_info=None):
    try:
        params = params or {}
        client = KafkaClient(assets)
        data = client.consumer_lag(params.get("group_id", ""), params.get("topic", ""))
        return _response(code=200, msg="Kafka consumer lag calculated", data=data, status_code=200, summary_msg="查询成功")
    except Exception as error:
        return _response(code=500, msg=str(error), data={"total_lag": 0, "partitions": []}, status_code=500, summary_msg="查询异常")


def create_topic(params, assets, context_info=None):
    try:
        params = params or {}
        _require_confirm(params)
        client = KafkaClient(assets)
        data = client.create_topic(
            topic=params.get("topic", ""),
            partitions=_int_value(params.get("partitions"), 1),
            replication_factor=_int_value(params.get("replication_factor"), 1),
            topic_configs=params.get("topic_configs", "")
        )
        return _response(code=200, msg="Kafka topic created", data=data, status_code=200, summary_msg="创建成功")
    except Exception as error:
        return _response(code=500, msg=str(error), data={"created": False}, status_code=500, summary_msg="创建异常")


def delete_topic(params, assets, context_info=None):
    try:
        params = params or {}
        _require_confirm(params)
        client = KafkaClient(assets)
        data = client.delete_topic(params.get("topic", ""))
        return _response(code=200, msg="Kafka topic deleted", data=data, status_code=200, summary_msg="删除成功")
    except Exception as error:
        return _response(code=500, msg=str(error), data={"deleted": False}, status_code=500, summary_msg="删除异常")


def clear_topic(params, assets, context_info=None):
    try:
        params = params or {}
        _require_confirm(params)
        client = KafkaClient(assets)
        data = client.clear_topic(params.get("topic", ""))
        return _response(code=200, msg="Kafka topic cleared", data=data, status_code=200, summary_msg="清空成功")
    except NotImplementedError as error:
        return _response(code=500, msg=str(error), data={"cleared": False}, status_code=501, summary_msg="当前版本不支持")
    except Exception as error:
        return _response(code=500, msg=str(error), data={"cleared": False}, status_code=500, summary_msg="清空异常")


def create_partitions(params, assets, context_info=None):
    try:
        params = params or {}
        _require_confirm(params)
        client = KafkaClient(assets)
        data = client.create_partitions(params.get("topic", ""), _int_value(params.get("total_count"), 0))
        return _response(code=200, msg="Kafka topic partitions updated", data=data, status_code=200, summary_msg="更新成功")
    except Exception as error:
        return _response(code=500, msg=str(error), data={"updated": False}, status_code=500, summary_msg="更新异常")


def alter_topic_config(params, assets, context_info=None):
    try:
        params = params or {}
        _require_confirm(params)
        client = KafkaClient(assets)
        data = client.alter_topic_config(params.get("topic", ""), params.get("topic_configs", ""))
        return _response(code=200, msg="Kafka topic config updated", data=data, status_code=200, summary_msg="更新成功")
    except Exception as error:
        return _response(code=500, msg=str(error), data={"updated": False}, status_code=500, summary_msg="更新异常")
