# -*- coding: utf-8 -*-
import hashlib
import json
import os
import random
import sqlite3
import time
import uuid
from datetime import datetime


APP_NAME = 'xiam'
PRODUCT_NAME = 'XIAM 身份与访问管理'
APP_DESCRIPTION = '离线模拟 AD/LDAP/IAM 身份系统，支持用户查询、登录记录、禁用、启用和重置密码'
DEFAULT_RECORDS = json.loads('[\n  {\n    "id": "user-alice",\n    "type": "user",\n    "name": "alice",\n    "owner": "电商业务部",\n    "user": "alice",\n    "status": "enabled",\n    "severity": "medium",\n    "summary": "支付系统负责人，最近发生异地登录",\n    "metadata": {\n      "email": "alice@example.com",\n      "mfa": true,\n      "last_login_ip": "203.0.113.77"\n    }\n  },\n  {\n    "id": "user-carol",\n    "type": "user",\n    "name": "carol",\n    "owner": "财务部",\n    "user": "carol",\n    "status": "enabled",\n    "severity": "medium",\n    "summary": "财务用户，收到钓鱼邮件",\n    "metadata": {\n      "email": "carol@example.com",\n      "mfa": false,\n      "last_login_ip": "10.20.4.77"\n    }\n  }\n]')
ACTION_DEFINITIONS = json.loads('[\n  {\n    "action": "health_check",\n    "description": "健康检查",\n    "classify": "query",\n    "operation": "health",\n    "parameters": {},\n    "filter_keys": [],\n    "result_status": null,\n    "allow_create": false,\n    "sample": {}\n  },\n  {\n    "action": "query_user",\n    "description": "查询用户信息",\n    "classify": "query",\n    "operation": "query",\n    "parameters": {\n      "username": {\n        "data_type": "string",\n        "description": "用户名",\n        "required": true,\n        "order": 0\n      }\n    },\n    "filter_keys": [\n      "name",\n      "user",\n      "username"\n    ],\n    "result_status": null,\n    "allow_create": false,\n    "sample": {\n      "username": "alice"\n    }\n  },\n  {\n    "action": "query_user_logins",\n    "description": "查询用户登录记录",\n    "classify": "query",\n    "operation": "query",\n    "parameters": {\n      "username": {\n        "data_type": "string",\n        "description": "用户名",\n        "required": true,\n        "order": 0\n      }\n    },\n    "filter_keys": [\n      "name",\n      "user",\n      "username"\n    ],\n    "result_status": null,\n    "allow_create": false,\n    "sample": {\n      "username": "alice"\n    }\n  },\n  {\n    "action": "disable_user",\n    "description": "禁用用户",\n    "classify": "write",\n    "operation": "write",\n    "parameters": {\n      "username": {\n        "data_type": "string",\n        "description": "用户名",\n        "required": true,\n        "order": 0\n      },\n      "reason": {\n        "data_type": "string",\n        "description": "禁用原因",\n        "required": false,\n        "order": 1,\n        "default_value": "安全事件处置"\n      }\n    },\n    "filter_keys": [\n      "name",\n      "user",\n      "username"\n    ],\n    "result_status": "disabled",\n    "allow_create": false,\n    "sample": {\n      "username": "alice",\n      "reason": "疑似账号失陷"\n    }\n  },\n  {\n    "action": "enable_user",\n    "description": "启用用户",\n    "classify": "write",\n    "operation": "write",\n    "parameters": {\n      "username": {\n        "data_type": "string",\n        "description": "用户名",\n        "required": true,\n        "order": 0\n      }\n    },\n    "filter_keys": [\n      "name",\n      "user",\n      "username"\n    ],\n    "result_status": "enabled",\n    "allow_create": false,\n    "sample": {\n      "username": "alice"\n    }\n  },\n  {\n    "action": "reset_password",\n    "description": "重置用户密码",\n    "classify": "write",\n    "operation": "write",\n    "parameters": {\n      "username": {\n        "data_type": "string",\n        "description": "用户名",\n        "required": true,\n        "order": 0\n      },\n      "reason": {\n        "data_type": "string",\n        "description": "重置原因",\n        "required": false,\n        "order": 1,\n        "default_value": "账号风险处置"\n      }\n    },\n    "filter_keys": [\n      "name",\n      "user",\n      "username"\n    ],\n    "result_status": "password_reset",\n    "allow_create": false,\n    "sample": {\n      "username": "alice",\n      "reason": "账号疑似泄露"\n    }\n  },\n  {\n    "action": "query_operation_history",\n    "description": "查询模拟操作历史",\n    "classify": "query",\n    "operation": "query",\n    "parameters": {\n      "target": {\n        "data_type": "string",\n        "description": "目标对象，可填写 IP、主机名、用户、工单号等",\n        "required": false,\n        "order": 0\n      },\n      "limit": {\n        "data_type": "integer",\n        "description": "返回结果数量限制",\n        "required": false,\n        "order": 1,\n        "default_value": 50\n      }\n    },\n    "filter_keys": [\n      "target"\n    ],\n    "result_status": null,\n    "allow_create": false,\n    "sample": {}\n  }\n]')


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _response(code=200, msg="", data=None, summary=None):
    return {
        "code": code,
        "msg": msg,
        "data": data or {},
        "summary": summary or {"statusCode": str(code), "msg": msg or "success"},
    }


def _db_path(assets):
    assets = assets or {}
    return assets.get("database_path") or f"/tmp/{APP_NAME}.db"


def _connect(assets):
    path = _db_path(assets)
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    _init_db(conn)
    return conn


def _init_db(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id TEXT PRIMARY KEY,
            record_type TEXT,
            name TEXT,
            ip TEXT,
            owner TEXT,
            user TEXT,
            status TEXT,
            severity TEXT,
            indicator TEXT,
            summary TEXT,
            metadata TEXT,
            created_time TEXT,
            updated_time TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS operation_logs (
            id TEXT PRIMARY KEY,
            action TEXT NOT NULL,
            target TEXT,
            status TEXT,
            reason TEXT,
            affected_count INTEGER DEFAULT 0,
            latency_seconds REAL DEFAULT 0,
            details TEXT,
            timestamp TEXT NOT NULL
        )
    """)
    cursor.execute("SELECT COUNT(*) AS cnt FROM records")
    if cursor.fetchone()["cnt"] == 0:
        for record in DEFAULT_RECORDS:
            _insert_record(conn, record, commit=False)
    conn.commit()


def _insert_record(conn, record, commit=True):
    cursor = conn.cursor()
    record = dict(record)
    metadata = record.get("metadata") or {}
    now = _now()
    cursor.execute(
        """
        INSERT OR REPLACE INTO records (
            id, record_type, name, ip, owner, user, status, severity,
            indicator, summary, metadata, created_time, updated_time
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            record.get("id") or f"{APP_NAME}-{uuid.uuid4().hex[:10]}",
            record.get("type", "simulated"),
            record.get("name", ""),
            record.get("ip", ""),
            record.get("owner", ""),
            record.get("user", ""),
            record.get("status", "active"),
            record.get("severity", "medium"),
            record.get("indicator", ""),
            record.get("summary", ""),
            json.dumps(metadata, ensure_ascii=False),
            record.get("created_time", now),
            record.get("updated_time", now),
        ),
    )
    if commit:
        conn.commit()


def _compact_display_value(value):
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return ",".join(str(item) for item in value)
    if isinstance(value, dict):
        parts = []
        for key, item in value.items():
            if item not in ("", None, [], {}):
                parts.append(f"{key}={_compact_display_value(item)}")
        return ",".join(parts)
    return str(value)


def _metadata_key_info(metadata):
    metadata = metadata or {}
    key_labels = {
        "department": "部门",
        "business": "业务",
        "tags": "标签",
        "relations": "关联",
        "groups": "用户组",
        "email": "邮箱",
        "target_ip": "目标IP",
        "source_ip": "来源IP",
        "access_protocol": "协议",
        "auth_method": "认证",
        "login_method": "方式",
        "session_id": "会话",
        "mac": "MAC",
        "vlan": "VLAN",
        "site": "站点",
        "url": "URL",
        "sender": "发件人",
        "recipient": "收件人",
        "last_login_ip": "最近登录IP",
        "last_login_time": "最近登录",
        "region": "区域",
        "security_group": "安全组",
        "instance_type": "规格",
        "service": "服务",
        "cvss": "CVSS",
        "confidence": "置信度",
        "family": "家族",
        "score": "评分",
        "behaviors": "行为",
        "assignee": "处理人",
        "mfa": "MFA",
        "client": "客户端",
        "command": "命令",
        "risk": "风险",
        "dn": "DN",
        "members": "成员",
    }
    preferred = list(key_labels)
    parts = []
    for key in preferred + [key for key in metadata if key not in preferred]:
        if key in ("last_params",):
            continue
        value = metadata.get(key)
        if value in ("", None, [], {}):
            continue
        label = key_labels.get(key, key)
        parts.append(f"{label}={_compact_display_value(value)}")
        if len(parts) >= 6:
            break
    return "；".join(parts)


def _record_from_row(row):
    metadata = {}
    if row["metadata"]:
        try:
            metadata = json.loads(row["metadata"])
        except Exception:
            metadata = {"raw": row["metadata"]}
    record = {
        "id": row["id"],
        "type": row["record_type"],
        "name": row["name"],
        "ip": row["ip"],
        "owner": row["owner"],
        "user": row["user"],
        "status": row["status"],
        "severity": row["severity"],
        "indicator": row["indicator"],
        "summary": row["summary"],
        "metadata": metadata,
        "created_time": row["created_time"],
        "updated_time": row["updated_time"],
    }
    record["key_info"] = _metadata_key_info(metadata)
    return record


def _all_records(conn):
    rows = conn.execute("SELECT * FROM records ORDER BY updated_time DESC, id ASC").fetchall()
    return [_record_from_row(row) for row in rows]


def _value_by_path(record, path):
    current = record
    for part in path.split("."):
        if part in ("asset_id", "host_id", "ticket_id", "message_id", "notification_id", "instance_id", "sample_id", "threat_id", "alert_id"):
            part = "id"
        elif part == "username":
            part = "user"
        elif part in ("group_name", "site", "interface", "channel_name"):
            part = "name"
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return ""
    return current


def _flatten(value):
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return " ".join(_flatten(item) for item in value)
    if isinstance(value, dict):
        return " ".join(f"{k} {_flatten(v)}" for k, v in value.items())
    return str(value)


def _matches(record, params, filter_keys):
    params = params or {}
    active_filters = {}
    for key in filter_keys or []:
        param_key = key.split(".")[-1]
        param_aliases = {
            "id": [
                "asset_id", "host_id", "ticket_id", "message_id", "notification_id",
                "instance_id", "sample_id", "threat_id", "alert_id", "session_id",
            ],
            "name": ["username", "group_name", "site", "interface", "channel_name", "target", "domain", "title", "asset_name"],
            "type": ["asset_type", "indicator_type"],
            "ip": ["ip", "source_ip", "target_ip"],
            "user": ["username", "recipient", "assignee"],
            "owner": ["username", "owner", "assignee"],
            "session_id": ["session_id"],
            "target_ip": ["target_ip"],
            "sender": ["sender"],
            "recipient": ["recipient"],
            "region": ["region"],
            "security_group": ["security_group_id"],
            "indicator": ["indicator", "file_hash", "url", "domain", "cve_id"],
            "url": ["url"],
            "mac": ["mac"],
        }
        candidates = [param_key, key] + param_aliases.get(param_key, [])
        raw = None
        matched_candidate = None
        for candidate in candidates:
            if candidate in params:
                raw = params.get(candidate)
                matched_candidate = candidate
                break
        if raw is not None and str(raw).strip() != "":
            item = active_filters.setdefault(
                matched_candidate,
                {"expected": str(raw).strip().lower(), "paths": []},
            )
            item["paths"].append(key)
    if not active_filters:
        query = str(params.get("query", "")).strip().lower()
        if not query:
            return True
        if "=" in query:
            query_key, query_value = [part.strip() for part in query.split("=", 1)]
            if query_key and query_value:
                return query_value.lower() in _flatten(_value_by_path(record, query_key)).lower()
        return query in _flatten(record).lower()
    for item in active_filters.values():
        expected = item["expected"]
        if not any(expected in _flatten(_value_by_path(record, path)).lower() for path in item["paths"]):
            return False
    return True


def _apply_param_defaults(params, action_def):
    values = dict(params or {})
    for name, meta in (action_def.get("parameters") or {}).items():
        if name not in values and "default_value" in meta:
            values[name] = meta["default_value"]
    return values


def _limit(params, default=50):
    try:
        return max(1, min(int(params.get("limit", default)), 500))
    except Exception:
        return default


def _simulate_latency(assets):
    assets = assets or {}
    min_delay = float(assets.get("delay_min_seconds", 1))
    max_delay = float(assets.get("delay_max_seconds", 3))
    if min_delay < 0:
        min_delay = 0
    if max_delay < min_delay:
        max_delay = min_delay
    delay = round(random.uniform(min_delay, max_delay), 2)
    if delay > 0:
        time.sleep(delay)
    return delay


def _log_operation(conn, action_name, target, status, reason, affected_count, latency_seconds, details):
    operation_id = f"op-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
    conn.execute(
        """
        INSERT INTO operation_logs (
            id, action, target, status, reason, affected_count,
            latency_seconds, details, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            operation_id,
            action_name,
            target,
            status,
            reason,
            affected_count,
            latency_seconds,
            json.dumps(details or {}, ensure_ascii=False),
            _now(),
        ),
    )
    conn.commit()
    return operation_id


def _operation_history(conn, params, action_def):
    target = str(params.get("target") or params.get("ticket_id") or params.get("recipient") or "").strip()
    limit = _limit(params)
    if target:
        rows = conn.execute(
            "SELECT * FROM operation_logs WHERE target LIKE ? ORDER BY timestamp DESC LIMIT ?",
            (f"%{target}%", limit),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM operation_logs ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
    records = []
    for row in rows:
        details = {}
        if row["details"]:
            try:
                details = json.loads(row["details"])
            except Exception:
                details = {"raw": row["details"]}
        records.append({
            "operation_id": row["id"],
            "action": row["action"],
            "target": row["target"],
            "status": row["status"],
            "reason": row["reason"],
            "affected_count": row["affected_count"],
            "latency_seconds": row["latency_seconds"],
            "timestamp": row["timestamp"],
            "details": details,
        })
    return _response(data={
        "result": f"查询到 {len(records)} 条操作历史",
        "records": records,
        "history_records": records,
        "total_count": len(records),
    })


def _summary(records):
    by_status = {}
    by_severity = {}
    by_type = {}
    by_owner = {}
    by_user = {}
    for record in records:
        by_status[record["status"]] = by_status.get(record["status"], 0) + 1
        by_severity[record["severity"]] = by_severity.get(record["severity"], 0) + 1
        by_type[record["type"]] = by_type.get(record["type"], 0) + 1
        if record.get("owner"):
            by_owner[record["owner"]] = by_owner.get(record["owner"], 0) + 1
        if record.get("user"):
            by_user[record["user"]] = by_user.get(record["user"], 0) + 1
    return {"status": by_status, "severity": by_severity, "type": by_type, "owner": by_owner, "user": by_user}


def _health_check(params, assets, context_info):
    try:
        conn = _connect(assets)
        records = _all_records(conn)
        sample_values = {
            "record_ids": sorted({record["id"] for record in records if record.get("id")})[:10],
            "owners": sorted({record["owner"] for record in records if record.get("owner")})[:10],
            "users": sorted({record["user"] for record in records if record.get("user")})[:10],
            "ips": sorted({record["ip"] for record in records if record.get("ip")})[:10],
            "indicators": sorted({record["indicator"] for record in records if record.get("indicator")})[:10],
        }
        system_info = {
            "product": PRODUCT_NAME,
            "version": "1.0.0",
            "status": "running",
            "database_path": _db_path(assets),
            "record_count": len(records),
            "scenario_profile": (assets or {}).get("scenario_profile", "default"),
            "sample_values": sample_values,
            "sample_records": records[:5],
            "components": [
                {"name": "模拟数据引擎", "status": "running", "latency_ms": random.randint(8, 55)},
                {"name": "SQLite 状态库", "status": "connected", "path": _db_path(assets)},
                {"name": "动作执行器", "status": "ready", "queue_depth": random.randint(0, 5)},
            ],
        }
        conn.close()
        return _response(
            data={"msg": f"{PRODUCT_NAME} 运行正常", "system_info": system_info},
            summary={"statusCode": "200", "msg": "健康检查成功"},
        )
    except Exception as exc:
        return _response(
            code=500,
            msg=str(exc),
            data={"msg": f"健康检查失败: {exc}", "system_info": {}},
            summary={"statusCode": "500", "msg": "健康检查失败"},
        )


def _target_from_params(params):
    for key in (
        "ip", "host_id", "asset_id", "ticket_id", "message_id", "notification_id",
        "asset_name", "username", "target", "indicator", "file_hash", "url", "domain",
        "security_group_id", "instance_id", "sample_id", "interface", "recipient",
        "sender", "alert_id", "threat_id", "cve_id", "session_id", "group_name",
        "account_name", "target_ip",
    ):
        value = params.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return APP_NAME


def _synthetic_record(action_name, params, status):
    target = _target_from_params(params)
    digest = hashlib.sha1(f"{action_name}:{target}".encode("utf-8")).hexdigest()[:10]
    metadata = dict(params or {})
    record_id = params.get("asset_id") or params.get("id") or f"{APP_NAME}-{digest}"
    record_type = params.get("asset_type") or params.get("indicator_type") or action_name
    if action_name == "create_asset" and not params.get("asset_id"):
        record_id = f"asset-{digest}"
    record = {
        "id": record_id,
        "type": record_type,
        "name": (
            params.get("asset_name") or params.get("name") or params.get("title") or
            params.get("display_name") or params.get("file_name") or
            params.get("channel_name") or target
        ),
        "ip": params.get("ip") or params.get("target_ip") or params.get("target", ""),
        "owner": params.get("owner") or params.get("assignee") or params.get("recipient") or params.get("username", ""),
        "user": params.get("user") or params.get("username") or params.get("recipient") or params.get("owner", ""),
        "status": status or "active",
        "severity": params.get("severity", "medium"),
        "indicator": params.get("indicator") or params.get("file_hash") or params.get("url") or "",
        "summary": params.get("summary") or params.get("description") or params.get("message") or f"由 {action_name} 生成的模拟记录",
        "metadata": metadata,
    }
    record["key_info"] = _metadata_key_info(metadata)
    return record


def _query(conn, params, action_def):
    records = _all_records(conn)
    matches = [record for record in records if _matches(record, params, action_def.get("filter_keys", []))]
    if not matches and action_def.get("allow_create"):
        created = _synthetic_record(action_def["action"], params, action_def.get("result_status") or "simulated")
        _insert_record(conn, created)
        records = _all_records(conn)
        matches = [record for record in records if record["id"] == created["id"]]
    limit = _limit(params, 50)
    selected = matches[:limit]
    data = {
        "result": f"查询完成，共 {len(matches)} 条匹配记录",
        "records": selected,
        "record": selected[0] if selected else {},
        "total_count": len(matches),
        "query": params,
        "statistics": _summary(matches),
    }
    return _response(data=data)


def _write(conn, action_name, params, assets, action_def):
    latency = _simulate_latency(assets)
    records = _all_records(conn)
    matches = [record for record in records if _matches(record, params, action_def.get("filter_keys", []))]
    if not matches and action_def.get("allow_create"):
        created = _synthetic_record(action_name, params, action_def.get("result_status") or "active")
        _insert_record(conn, created)
        matches = [created]
    new_status = params.get("status") or action_def.get("result_status") or "processed"
    now = _now()
    for record in matches:
        metadata = record.get("metadata") or {}
        if params.get("tag"):
            tags = metadata.get("tags") or []
            if not isinstance(tags, list):
                tags = [str(tags)]
            tag = str(params.get("tag")).strip()
            if tag and tag not in tags:
                tags.append(tag)
            metadata["tags"] = tags
            if params.get("value") is not None:
                tag_values = metadata.get("tag_values") or {}
                tag_values[tag] = params.get("value")
                metadata["tag_values"] = tag_values
        metadata["last_action"] = action_name
        metadata["last_params"] = params
        conn.execute(
            "UPDATE records SET status = ?, metadata = ?, updated_time = ? WHERE id = ?",
            (new_status, json.dumps(metadata, ensure_ascii=False), now, record["id"]),
        )
    conn.commit()
    updated_records = _all_records(conn)
    updated_matches = [record for record in updated_records if record["id"] in [item["id"] for item in matches]]
    target = _target_from_params(params)
    operation_id = _log_operation(
        conn,
        action_name,
        target,
        new_status,
        params.get("reason") or params.get("comment") or params.get("message") or "",
        len(updated_matches),
        latency,
        {"params": params, "action": action_name},
    )
    operation = {
        "operation_id": operation_id,
        "action": action_name,
        "target": target,
        "status": new_status,
        "affected_count": len(updated_matches),
        "latency_seconds": latency,
        "timestamp": now,
    }
    return _response(data={
        "result": f"{action_name} 模拟执行完成，影响 {len(updated_matches)} 条记录",
        "operation": operation,
        "records": updated_matches,
        "affected_count": len(updated_matches),
    })


def _non_empty_param(params, key, current=None):
    value = params.get(key)
    if value is None:
        return current
    if isinstance(value, str) and value.strip() == "":
        return current
    return value


def _coerce_metadata_param(value):
    if value is None:
        return None
    if isinstance(value, (dict, list, tuple, set, bool, int, float)):
        return value
    text = str(value).strip()
    if "," in text:
        return [item.strip() for item in text.split(",") if item.strip()]
    return value


def _apply_metadata_params(metadata, params):
    metadata = dict(metadata or {})
    metadata_param_keys = [
        "department", "business", "tags", "relations", "groups", "email",
        "target_ip", "source_ip", "access_protocol", "auth_method",
        "login_method", "session_id", "mac", "vlan", "site", "url",
        "sender", "recipient", "last_login_ip", "last_login_time", "region",
        "security_group", "instance_type", "service", "cvss", "confidence",
        "family", "score", "behaviors", "assignee", "mfa", "client",
        "command", "risk", "dn", "members",
    ]
    for key in metadata_param_keys:
        if key in params and params.get(key) not in (None, ""):
            metadata[key] = _coerce_metadata_param(params.get(key))
    if params.get("tag"):
        tags = metadata.get("tags") or []
        if not isinstance(tags, list):
            tags = [str(tags)]
        tag = str(params.get("tag")).strip()
        if tag and tag not in tags:
            tags.append(tag)
        metadata["tags"] = tags
        if params.get("value") is not None:
            tag_values = metadata.get("tag_values") or {}
            tag_values[tag] = params.get("value")
            metadata["tag_values"] = tag_values
    return metadata


def _update(conn, action_name, params, assets, action_def):
    latency = _simulate_latency(assets)
    records = _all_records(conn)
    matches = [record for record in records if _matches(record, params, action_def.get("filter_keys", []))]
    now = _now()
    for record in matches:
        metadata = _apply_metadata_params(record.get("metadata") or {}, params)
        metadata["last_action"] = action_name
        metadata["last_params"] = params
        conn.execute(
            """
            UPDATE records
            SET record_type = ?, name = ?, ip = ?, owner = ?, user = ?,
                status = ?, severity = ?, indicator = ?, summary = ?,
                metadata = ?, updated_time = ?
            WHERE id = ?
            """,
            (
                _non_empty_param(params, "asset_type", _non_empty_param(params, "type", record["type"])),
                _non_empty_param(params, "asset_name", _non_empty_param(params, "name", record["name"])),
                _non_empty_param(params, "ip", record["ip"]),
                _non_empty_param(params, "owner", record["owner"]),
                _non_empty_param(params, "user", record["user"]),
                _non_empty_param(params, "status", record["status"]),
                _non_empty_param(params, "severity", record["severity"]),
                _non_empty_param(params, "indicator", record["indicator"]),
                _non_empty_param(params, "summary", record["summary"]),
                json.dumps(metadata, ensure_ascii=False),
                now,
                record["id"],
            ),
        )
    conn.commit()
    updated_records = _all_records(conn)
    updated_matches = [record for record in updated_records if record["id"] in [item["id"] for item in matches]]
    target = _target_from_params(params)
    operation_id = _log_operation(
        conn,
        action_name,
        target,
        action_def.get("result_status") or params.get("status") or "updated",
        params.get("reason") or params.get("comment") or "",
        len(updated_matches),
        latency,
        {"params": params, "action": action_name},
    )
    operation = {
        "operation_id": operation_id,
        "action": action_name,
        "target": target,
        "status": action_def.get("result_status") or params.get("status") or "updated",
        "affected_count": len(updated_matches),
        "latency_seconds": latency,
        "timestamp": now,
    }
    return _response(data={
        "result": f"{action_name} 更新完成，影响 {len(updated_matches)} 条记录",
        "operation": operation,
        "records": updated_matches,
        "affected_count": len(updated_matches),
    })


def _delete(conn, action_name, params, assets, action_def):
    latency = _simulate_latency(assets)
    records = _all_records(conn)
    matches = [record for record in records if _matches(record, params, action_def.get("filter_keys", []))]
    ids = [record["id"] for record in matches]
    if ids:
        conn.executemany("DELETE FROM records WHERE id = ?", [(item,) for item in ids])
    conn.commit()
    target = _target_from_params(params)
    operation_id = _log_operation(
        conn,
        action_name,
        target,
        action_def.get("result_status") or "deleted",
        params.get("reason") or params.get("comment") or "",
        len(matches),
        latency,
        {"params": params, "action": action_name, "deleted_ids": ids},
    )
    operation = {
        "operation_id": operation_id,
        "action": action_name,
        "target": target,
        "status": action_def.get("result_status") or "deleted",
        "affected_count": len(matches),
        "latency_seconds": latency,
        "timestamp": _now(),
    }
    return _response(data={
        "result": f"{action_name} 删除完成，影响 {len(matches)} 条记录",
        "operation": operation,
        "records": matches,
        "deleted_records": matches,
        "affected_count": len(matches),
    })


def _create(conn, action_name, params, assets, action_def):
    latency = _simulate_latency(assets)
    status = action_def.get("result_status") or params.get("status") or "created"
    record = _synthetic_record(action_name, params, status)
    if action_name == "create_ticket":
        record["id"] = f"TCK-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
        record["type"] = "security_ticket"
    if action_name == "create_asset":
        record["type"] = params.get("asset_type") or "asset"
        record["metadata"] = _apply_metadata_params(record.get("metadata") or {}, params)
        record["key_info"] = _metadata_key_info(record["metadata"])
    _insert_record(conn, record)
    target = record["id"]
    operation_id = _log_operation(conn, action_name, target, status, params.get("reason", ""), 1, latency, {"params": params})
    operation = {
        "operation_id": operation_id,
        "action": action_name,
        "target": target,
        "status": status,
        "affected_count": 1,
        "latency_seconds": latency,
        "timestamp": _now(),
    }
    return _response(data={
        "result": f"{action_name} 创建模拟记录成功",
        "operation": operation,
        "record": record,
        "records": [record],
        "created_id": record["id"],
    })


def _execute(action_name, params, assets, context_info):
    params = params or {}
    assets = assets or {}
    action_def = next((item for item in ACTION_DEFINITIONS if item["action"] == action_name), None)
    if not action_def:
        return _response(code=404, msg=f"未知动作: {action_name}", data={"result": "动作不存在"})
    params = _apply_param_defaults(params, action_def)
    operation = action_def.get("operation", "query")
    if operation == "health":
        return _health_check(params, assets, context_info)
    try:
        conn = _connect(assets)
        if operation == "history":
            result = _operation_history(conn, params, action_def)
        elif operation == "summary":
            records = _all_records(conn)
            result = _response(data={
                "result": "统计摘要生成成功",
                "statistics": _summary(records),
                "records": records[:_limit(params, 20)],
                "total_count": len(records),
            })
        elif operation in ("write",):
            result = _write(conn, action_name, params, assets, action_def)
        elif operation == "update":
            result = _update(conn, action_name, params, assets, action_def)
        elif operation == "delete":
            result = _delete(conn, action_name, params, assets, action_def)
        elif operation in ("create", "notify"):
            result = _create(conn, action_name, params, assets, action_def)
        else:
            result = _query(conn, params, action_def)
        conn.close()
        return result
    except Exception as exc:
        return _response(code=500, msg=str(exc), data={"result": f"{action_name} 执行失败: {exc}"})


def health_check(params, assets, context_info):
    """健康检查"""
    return _execute('health_check', params, assets, context_info)


def query_user(params, assets, context_info):
    """查询用户信息"""
    return _execute('query_user', params, assets, context_info)


def query_user_logins(params, assets, context_info):
    """查询用户登录记录"""
    return _execute('query_user_logins', params, assets, context_info)


def disable_user(params, assets, context_info):
    """禁用用户"""
    return _execute('disable_user', params, assets, context_info)


def enable_user(params, assets, context_info):
    """启用用户"""
    return _execute('enable_user', params, assets, context_info)


def reset_password(params, assets, context_info):
    """重置用户密码"""
    return _execute('reset_password', params, assets, context_info)


def query_operation_history(params, assets, context_info):
    """查询模拟操作历史"""
    return _execute('query_operation_history', params, assets, context_info)
