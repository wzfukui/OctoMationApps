# -*- coding: utf-8 -*-
import json
import os
import random
import sqlite3
import time
import uuid
from datetime import datetime, timedelta, timezone


APP_NAME = 'tencent_cfw_sim'
PRODUCT_NAME = '腾讯云防火墙 CFW（模拟）'
APP_DESCRIPTION = '离线模拟腾讯云防火墙的 VPC 间访问控制、策略同步、TTL 回滚和审计能力'
APP_VERSION = '1.0.0'
DEFAULT_RECORDS = json.loads('[{"id": "cfw-vpc-fw-prod-01", "kind": "cfw_vpc_firewall", "name": "生产 VPC 间防火墙", "ip": "", "owner": "cloud-sec", "status": "running", "severity": "medium", "summary": "保护生产 Web VPC 与数据 VPC 之间的东西向访问", "data": {"firewall_id": "cfw-vpc-fw-prod-01", "source_vpc_id": "vpc-web-prod", "destination_vpc_id": "vpc-data-prod", "region": "ap-guangzhou", "sync_status": "synced"}}, {"id": "cfw-rule-demo-0001", "kind": "cfw_vpc_block_rule", "name": "阻断 Web 主机访问核心数据库管理端口", "ip": "10.10.8.23", "owner": "soar-demo", "status": "active", "severity": "high", "summary": "VPC 间高优先级拒绝规则，限制异常东西向访问", "data": {"policy_id": "cfw-rule-demo-0001", "trace_id": "demo-trace-lateral-0003", "operator": "soar-demo", "trigger_source": "soc_alert", "source": "10.10.8.23", "destination": "10.10.9.15", "source_vpc_id": "vpc-web-prod", "destination_vpc_id": "vpc-data-prod", "protocol": "TCP", "port": "3306", "direction": "east_west", "action": "deny", "priority": 10, "ttl_minutes": 120, "expires_at": "2099-07-24T12:12:03+08:00", "alert_id": "soc-alert-20260724-0003"}}]')
ACTION_DEFINITIONS = json.loads('[{"action": "health_check", "description": "检查模拟 API、鉴权和组件状态", "operation": "health", "classify": "query", "parameters": {}, "sample": {}, "record_kinds": [], "filter_map": {}, "target_params": []}, {"action": "list_vpc_firewalls", "description": "查询 VPC 间防火墙及策略同步状态", "operation": "query", "classify": "query", "parameters": {"firewall_id": {"data_type": "string", "description": "VPC 间防火墙 ID", "required": false, "order": 0}, "region": {"data_type": "string", "description": "地域", "required": false, "order": 1}, "status": {"data_type": "string", "description": "状态", "required": false, "order": 2}}, "sample": {"firewall_id": "cfw-vpc-fw-prod-01"}, "record_kinds": ["cfw_vpc_firewall"], "filter_map": {"firewall_id": ["id", "firewall_id"], "region": ["region"], "status": ["status"]}, "target_params": []}, {"action": "list_vpc_access_rules", "description": "查询 VPC 间访问控制规则", "operation": "query", "classify": "query", "parameters": {"policy_id": {"data_type": "string", "description": "策略 ID", "required": false, "order": 0}, "source": {"data_type": "string", "description": "源 IP/CIDR", "required": false, "order": 1}, "destination": {"data_type": "string", "description": "目的 IP/CIDR", "required": false, "order": 2}, "status": {"data_type": "string", "description": "策略状态", "required": false, "order": 3}, "trace_id": {"data_type": "string", "description": "SOAR trace_id", "required": false, "order": 4}, "limit": {"data_type": "integer", "description": "返回数量", "required": false, "order": 5, "default_value": 50}}, "sample": {"source": "10.10.8.23", "destination": "10.10.9.15"}, "record_kinds": ["cfw_vpc_block_rule"], "filter_map": {"policy_id": ["id", "policy_id"], "source": ["source", "ip"], "destination": ["destination"], "status": ["status"], "trace_id": ["trace_id"]}, "target_params": []}, {"action": "create_vpc_block_rule", "description": "创建 VPC 间拒绝访问规则", "operation": "create_policy", "classify": "write", "parameters": {"source": {"data_type": "string", "description": "源 IP/CIDR", "required": true, "order": 0}, "destination": {"data_type": "string", "description": "目的 IP/CIDR", "required": true, "order": 1}, "source_vpc_id": {"data_type": "string", "description": "源 VPC ID", "required": false, "order": 2, "default_value": "vpc-web-prod"}, "destination_vpc_id": {"data_type": "string", "description": "目的 VPC ID", "required": false, "order": 3, "default_value": "vpc-data-prod"}, "protocol": {"data_type": "string", "description": "协议", "required": false, "order": 4, "default_value": "TCP"}, "port": {"data_type": "string", "description": "目的端口", "required": false, "order": 5, "default_value": "ALL"}, "direction": {"data_type": "string", "description": "访问方向", "required": false, "order": 6, "default_value": "east_west"}, "reason": {"data_type": "string", "description": "阻断原因", "required": false, "order": 7, "default_value": "SOAR 横向访问处置"}, "ttl_minutes": {"data_type": "integer", "description": "策略时长（分钟），0 表示永久", "required": false, "order": 8, "default_value": 120}, "alert_id": {"data_type": "string", "description": "关联 SOC 告警 ID", "required": false, "order": 9}, "trace_id": {"data_type": "string", "description": "SOAR 链路追踪 ID", "required": false, "order": 20, "default_value": "demo-trace-web-0001"}, "operator": {"data_type": "string", "description": "操作者账号", "required": false, "order": 21, "default_value": "soar-demo"}, "trigger_source": {"data_type": "string", "description": "触发来源，例如 soc_alert、manual、scheduled", "required": false, "order": 22, "default_value": "soc_alert"}, "approval_id": {"data_type": "string", "description": "审批单 ID；需要审批时由剧本传入", "required": false, "order": 23}}, "sample": {"source": "10.10.8.23", "destination": "10.10.9.15", "protocol": "TCP", "port": "3306", "reason": "Web 主机异常访问数据库", "ttl_minutes": 120, "alert_id": "soc-alert-20260724-0003", "trace_id": "demo-trace-lateral-0003"}, "record_kinds": [], "filter_map": {}, "target_params": ["source", "destination", "protocol", "port"], "result_status": "active", "policy_kind": "cfw_vpc_block_rule", "policy_prefix": "cfw-rule"}, {"action": "delete_vpc_access_rule", "description": "删除或回滚 VPC 间访问控制规则", "operation": "release_policy", "classify": "write", "parameters": {"policy_id": {"data_type": "string", "description": "策略 ID", "required": false, "order": 0}, "source": {"data_type": "string", "description": "源 IP/CIDR", "required": false, "order": 1}, "destination": {"data_type": "string", "description": "目的 IP/CIDR", "required": false, "order": 2}, "reason": {"data_type": "string", "description": "回滚原因", "required": false, "order": 3, "default_value": "TTL 到期或人工复核"}, "trace_id": {"data_type": "string", "description": "SOAR 链路追踪 ID", "required": false, "order": 10, "default_value": "demo-trace-web-0001"}, "operator": {"data_type": "string", "description": "操作者账号", "required": false, "order": 11, "default_value": "soar-demo"}, "trigger_source": {"data_type": "string", "description": "触发来源，例如 soc_alert、manual、scheduled", "required": false, "order": 12, "default_value": "soc_alert"}, "approval_id": {"data_type": "string", "description": "审批单 ID；需要审批时由剧本传入", "required": false, "order": 13}}, "sample": {"policy_id": "cfw-rule-demo-0001", "source": "10.10.8.23", "destination": "10.10.9.15", "trace_id": "demo-trace-lateral-0003"}, "record_kinds": [], "filter_map": {}, "target_params": ["policy_id", "source", "destination"], "result_status": "released", "policy_kind": "cfw_vpc_block_rule"}, {"action": "expire_due_policies", "description": "扫描并回滚已到期 CFW 规则", "operation": "expire_policies", "classify": "write", "parameters": {"as_of": {"data_type": "string", "description": "到期判断时间，ISO 8601；默认当前时间", "required": false, "order": 0}, "trace_id": {"data_type": "string", "description": "SOAR 链路追踪 ID", "required": false, "order": 10, "default_value": "demo-trace-web-0001"}, "operator": {"data_type": "string", "description": "操作者账号", "required": false, "order": 11, "default_value": "soar-demo"}, "trigger_source": {"data_type": "string", "description": "触发来源，例如 soc_alert、manual、scheduled", "required": false, "order": 12, "default_value": "soc_alert"}, "approval_id": {"data_type": "string", "description": "审批单 ID；需要审批时由剧本传入", "required": false, "order": 13}}, "sample": {"as_of": "2100-01-01T00:00:00+08:00", "trigger_source": "scheduled", "trace_id": "demo-trace-ttl-cfw"}, "record_kinds": [], "filter_map": {}, "target_params": [], "result_status": "expired", "policy_kind": "cfw_vpc_block_rule"}, {"action": "query_operation_history", "description": "查询产品模拟操作审计记录", "operation": "history", "classify": "query", "parameters": {"trace_id": {"data_type": "string", "description": "按 trace_id 过滤", "required": false, "order": 0}, "target": {"data_type": "string", "description": "按目标 IP、资产或策略 ID 过滤", "required": false, "order": 1}, "limit": {"data_type": "integer", "description": "返回数量", "required": false, "order": 2, "default_value": 50}}, "sample": {"trace_id": "demo-trace-web-0001", "limit": 20}, "record_kinds": [], "filter_map": {}, "target_params": []}]')
HEALTH_COMPONENTS = json.loads('["CFW API 网关", "VPC 间防火墙", "访问控制策略同步", "日志审计"]')
TZ = timezone(timedelta(hours=8))


def _now_dt():
    return datetime.now(TZ)


def _now():
    return _now_dt().isoformat(timespec="seconds")


def _response(code=200, msg="", data=None):
    message = msg or ("success" if code == 200 else "failed")
    return {
        "code": code,
        "msg": msg,
        "data": data or {},
        "summary": {"statusCode": str(code), "msg": message},
    }


def _db_path(assets):
    return (assets or {}).get("database_path") or f"/tmp/{APP_NAME}.db"


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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            name TEXT,
            ip TEXT,
            owner TEXT,
            status TEXT,
            severity TEXT,
            summary TEXT,
            data TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS operations (
            operation_id TEXT PRIMARY KEY,
            action TEXT NOT NULL,
            target TEXT,
            policy_id TEXT,
            status TEXT,
            operator TEXT,
            trigger_source TEXT,
            trace_id TEXT,
            reason TEXT,
            ttl_minutes INTEGER,
            expires_at TEXT,
            details TEXT,
            timestamp TEXT NOT NULL
        )
    """)
    count = conn.execute("SELECT COUNT(*) AS count FROM records").fetchone()["count"]
    if count == 0:
        for record in DEFAULT_RECORDS:
            _insert_record(conn, record, commit=False)
    conn.commit()


def _insert_record(conn, record, commit=True):
    now = _now()
    value = dict(record)
    conn.execute(
        """
        INSERT OR REPLACE INTO records (
            id, kind, name, ip, owner, status, severity, summary,
            data, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            value.get("id") or f"{APP_NAME}-{uuid.uuid4().hex[:12]}",
            value.get("kind") or "simulated_record",
            value.get("name") or "",
            value.get("ip") or "",
            value.get("owner") or "",
            value.get("status") or "active",
            value.get("severity") or "medium",
            value.get("summary") or "",
            json.dumps(value.get("data") or {}, ensure_ascii=False),
            value.get("created_at") or now,
            value.get("updated_at") or now,
        ),
    )
    if commit:
        conn.commit()


def _parse_json(value):
    if not value:
        return {}
    try:
        return json.loads(value)
    except Exception:
        return {"raw": value}


def _compact(value):
    if value in (None, "", [], {}):
        return ""
    if isinstance(value, list):
        return ",".join(str(item) for item in value)
    if isinstance(value, dict):
        return ",".join(
            f"{key}={_compact(item)}"
            for key, item in value.items()
            if item not in (None, "", [], {})
        )
    return str(value)


def _record_from_row(row):
    details = _parse_json(row["data"])
    record = {
        "id": row["id"],
        "type": row["kind"],
        "kind": row["kind"],
        "name": row["name"],
        "ip": row["ip"],
        "owner": row["owner"],
        "status": row["status"],
        "severity": row["severity"],
        "summary": row["summary"],
        "details": details,
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
    for key, value in details.items():
        if key not in record:
            record[key] = value
    preferred = [
        "asset_id", "host_id", "cluster_id", "business_id", "business_name",
        "src_ip", "dst_ip", "external_ip", "domain", "owner_account",
        "confidence", "trace_id", "policy_id", "expires_at",
    ]
    record["key_info"] = "；".join(
        f"{key}={_compact(record.get(key))}"
        for key in preferred
        if record.get(key) not in (None, "", [], {})
    )
    return record


def _all_records(conn):
    rows = conn.execute(
        "SELECT * FROM records ORDER BY updated_at DESC, id ASC"
    ).fetchall()
    return [_record_from_row(row) for row in rows]


def _definition(action_name):
    return next(
        (item for item in ACTION_DEFINITIONS if item["action"] == action_name),
        None,
    )


def _apply_defaults(params, action_def):
    values = dict(params or {})
    for name, metadata in (action_def.get("parameters") or {}).items():
        if name not in values and "default_value" in metadata:
            values[name] = metadata["default_value"]
    return values


def _validate_required(params, action_def):
    missing = []
    for name, metadata in (action_def.get("parameters") or {}).items():
        if metadata.get("required") and params.get(name) in (None, ""):
            missing.append(name)
    if missing:
        return _response(
            400,
            f"缺少必填参数: {', '.join(missing)}",
            {"result": "参数校验失败", "missing_parameters": missing},
        )
    return None


def _value(record, path):
    current = record
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _matches(record, params, action_def):
    kinds = action_def.get("record_kinds") or []
    if kinds and record.get("kind") not in kinds:
        return False
    for parameter_name, paths in (action_def.get("filter_map") or {}).items():
        expected = params.get(parameter_name)
        if expected in (None, ""):
            continue
        expected_text = str(expected).strip().lower()
        values = [_value(record, path) for path in paths]
        if not any(expected_text in _compact(value).lower() for value in values):
            return False
    return True


def _limit(params, default=50):
    try:
        return max(1, min(int(params.get("limit", default)), 500))
    except Exception:
        return default


def _query(conn, params, action_def):
    matches = [
        record
        for record in _all_records(conn)
        if _matches(record, params, action_def)
    ]
    selected = matches[:_limit(params)]
    return _response(
        data={
            "result": f"查询完成，共 {len(matches)} 条匹配记录",
            "records": selected,
            "record": selected[0] if selected else {},
            "total_count": len(matches),
            "query": params,
        }
    )


def _safe_float(value, default):
    try:
        return float(value)
    except Exception:
        return default


def _simulate_latency(assets):
    assets = assets or {}
    low = max(0.0, _safe_float(assets.get("delay_min_seconds"), 1.0))
    high = max(low, _safe_float(assets.get("delay_max_seconds"), 3.0))
    delay = round(random.uniform(low, high), 2)
    if delay:
        time.sleep(delay)
    return delay


def _availability_error(assets):
    assets = assets or {}
    api_status = str(assets.get("simulated_api_status") or "healthy").lower()
    auth_status = str(assets.get("simulated_auth_status") or "authorized").lower()
    if auth_status not in ("authorized", "ok", "healthy"):
        return _response(
            403,
            "模拟鉴权失败",
            {
                "result": "permission_denied",
                "api_status": api_status,
                "auth_status": auth_status,
            },
        )
    if api_status in ("unavailable", "down", "offline"):
        return _response(
            503,
            "模拟 API 不可用",
            {
                "result": "service_unavailable",
                "api_status": api_status,
                "auth_status": auth_status,
            },
        )
    return None


def _health(assets):
    assets = assets or {}
    api_status = str(assets.get("simulated_api_status") or "healthy").lower()
    auth_status = str(assets.get("simulated_auth_status") or "authorized").lower()
    link_status = str(assets.get("simulated_link_status") or "healthy").lower()
    code = 200
    message = "健康检查成功"
    if auth_status not in ("authorized", "ok", "healthy"):
        code = 403
        message = "模拟鉴权失败"
    elif api_status in ("unavailable", "down", "offline"):
        code = 503
        message = "模拟 API 不可用"
    try:
        conn = _connect(assets)
        records = _all_records(conn)
        policy_count = len(
            [record for record in records if "policy" in record.get("kind", "") or "rule" in record.get("kind", "")]
        )
        conn.close()
        components = []
        for name in HEALTH_COMPONENTS:
            component_status = "healthy"
            if "鉴权" in name:
                component_status = auth_status
            elif "链路" in name or "Kafka" in name or "Syslog" in name:
                component_status = link_status
            elif api_status != "healthy":
                component_status = api_status
            components.append(
                {
                    "name": name,
                    "status": component_status,
                    "latency_ms": random.randint(8, 65),
                }
            )
        system_info = {
            "product": PRODUCT_NAME,
            "version": APP_VERSION,
            "status": "running" if code == 200 else "abnormal",
            "api_status": api_status,
            "auth_status": auth_status,
            "link_status": link_status,
            "database_path": _db_path(assets),
            "record_count": len(records),
            "policy_count": policy_count,
            "scenario_profile": assets.get("scenario_profile") or "default",
            "last_alert_time": max(
                [
                    record.get("occurred_at")
                    for record in records
                    if record.get("occurred_at")
                ]
                or [""]
            ),
            "components": components,
            "sample_values": {
                "record_ids": [record["id"] for record in records[:10]],
                "ips": sorted({record["ip"] for record in records if record.get("ip")})[:10],
                "owners": sorted({record["owner"] for record in records if record.get("owner")})[:10],
                "trace_ids": sorted(
                    {record.get("trace_id") for record in records if record.get("trace_id")}
                )[:10],
            },
            "sample_records": records[:5],
        }
        return _response(
            code,
            "" if code == 200 else message,
            {"msg": message, "system_info": system_info},
        )
    except Exception as exc:
        return _response(
            500,
            str(exc),
            {"msg": f"健康检查失败: {exc}", "system_info": {}},
        )


def _parse_time(value):
    if not value:
        return None
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=TZ)
        return parsed
    except Exception:
        return None


def _target(params, action_def):
    values = []
    for name in action_def.get("target_params") or []:
        value = params.get(name)
        if value not in (None, ""):
            values.append(str(value))
    if values:
        return " -> ".join(values)
    for name in ("policy_id", "alert_id", "asset_id", "host_id", "ip", "target"):
        if params.get(name) not in (None, ""):
            return str(params[name])
    return APP_NAME


def _log_operation(
    conn,
    action_name,
    params,
    action_def,
    *,
    status,
    policy_id="",
    expires_at="",
    details=None,
):
    operation_id = f"op-{datetime.now(TZ).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
    conn.execute(
        """
        INSERT INTO operations (
            operation_id, action, target, policy_id, status, operator,
            trigger_source, trace_id, reason, ttl_minutes, expires_at,
            details, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            operation_id,
            action_name,
            _target(params, action_def),
            policy_id,
            status,
            params.get("operator") or "soar-demo",
            params.get("trigger_source") or "manual",
            params.get("trace_id") or "",
            params.get("reason") or params.get("comment") or "",
            int(params.get("ttl_minutes") or 0),
            expires_at,
            json.dumps(details or {}, ensure_ascii=False),
            _now(),
        ),
    )
    conn.commit()
    return {
        "operation_id": operation_id,
        "action": action_name,
        "target": _target(params, action_def),
        "policy_id": policy_id,
        "status": status,
        "operator": params.get("operator") or "soar-demo",
        "trigger_source": params.get("trigger_source") or "manual",
        "trace_id": params.get("trace_id") or "",
        "reason": params.get("reason") or params.get("comment") or "",
        "ttl_minutes": int(params.get("ttl_minutes") or 0),
        "expires_at": expires_at,
        "timestamp": _now(),
    }


def _policy_duplicate(records, params, action_def):
    target_fields = action_def.get("target_params") or []
    for record in records:
        if record.get("kind") != action_def.get("policy_kind"):
            continue
        if record.get("status") not in ("active", "enabled"):
            continue
        if all(
            _compact(record.get(name)).lower() == _compact(params.get(name)).lower()
            for name in target_fields
        ):
            return record
    return None


def _create_policy(conn, action_name, params, assets, action_def):
    existing = _policy_duplicate(_all_records(conn), params, action_def)
    if existing:
        operation = _log_operation(
            conn,
            action_name,
            params,
            action_def,
            status="duplicate",
            policy_id=existing["id"],
            expires_at=existing.get("expires_at") or "",
            details={"duplicate": True},
        )
        return _response(
            data={
                "result": "目标已存在有效策略，返回现有策略",
                "policy": existing,
                "policy_id": existing["id"],
                "operation": operation,
                "duplicate": True,
                "affected_count": 0,
            }
        )
    latency = _simulate_latency(assets)
    ttl_minutes = max(0, int(params.get("ttl_minutes") or 0))
    expires_at = ""
    if ttl_minutes:
        expires_at = (_now_dt() + timedelta(minutes=ttl_minutes)).isoformat(timespec="seconds")
    prefix = action_def.get("policy_prefix") or "policy"
    policy_id = f"{prefix}-{datetime.now(TZ).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
    details = dict(params)
    details.update(
        {
            "policy_id": policy_id,
            "product": PRODUCT_NAME,
            "target": _target(params, action_def),
            "expires_at": expires_at,
            "created_at": _now(),
            "latency_seconds": latency,
        }
    )
    ip = params.get("ip") or params.get("source") or ""
    record = {
        "id": policy_id,
        "kind": action_def.get("policy_kind") or "block_policy",
        "name": params.get("policy_name") or action_def["description"],
        "ip": ip,
        "owner": params.get("operator") or "soar-demo",
        "status": action_def.get("result_status") or "active",
        "severity": params.get("severity") or "high",
        "summary": params.get("reason") or action_def["description"],
        "data": details,
    }
    _insert_record(conn, record)
    policy = next(item for item in _all_records(conn) if item["id"] == policy_id)
    operation = _log_operation(
        conn,
        action_name,
        params,
        action_def,
        status=policy["status"],
        policy_id=policy_id,
        expires_at=expires_at,
        details={"latency_seconds": latency},
    )
    return _response(
        data={
            "result": "模拟策略创建成功",
            "policy": policy,
            "policy_id": policy_id,
            "expires_at": expires_at,
            "operation": operation,
            "duplicate": False,
            "affected_count": 1,
        }
    )


def _policy_matches(record, params, action_def):
    if record.get("kind") != action_def.get("policy_kind"):
        return False
    if params.get("policy_id") and record.get("id") != params.get("policy_id"):
        return False
    compared = False
    for name in action_def.get("target_params") or []:
        if name == "policy_id" or params.get(name) in (None, ""):
            continue
        compared = True
        if _compact(record.get(name)).lower() != _compact(params.get(name)).lower():
            return False
    return bool(params.get("policy_id") or compared)


def _release_policy(conn, action_name, params, assets, action_def):
    latency = _simulate_latency(assets)
    matches = [
        record
        for record in _all_records(conn)
        if _policy_matches(record, params, action_def)
    ]
    if not matches:
        return _response(
            404,
            "未找到匹配策略",
            {"result": "policy_not_found", "affected_count": 0},
        )
    now = _now()
    affected = 0
    for record in matches:
        details = dict(record.get("details") or {})
        details.update(
            {
                "released_at": now,
                "release_reason": params.get("reason") or "",
                "release_operator": params.get("operator") or "soar-demo",
            }
        )
        if record["status"] not in ("released", "expired", "deleted"):
            affected += 1
        conn.execute(
            "UPDATE records SET status = ?, data = ?, updated_at = ? WHERE id = ?",
            (
                action_def.get("result_status") or "released",
                json.dumps(details, ensure_ascii=False),
                now,
                record["id"],
            ),
        )
    conn.commit()
    policies = [
        record for record in _all_records(conn) if record["id"] in {item["id"] for item in matches}
    ]
    operation = _log_operation(
        conn,
        action_name,
        params,
        action_def,
        status=action_def.get("result_status") or "released",
        policy_id=policies[0]["id"],
        details={"latency_seconds": latency, "affected_count": affected},
    )
    return _response(
        data={
            "result": f"模拟策略解除完成，影响 {affected} 条策略",
            "policies": policies,
            "policy": policies[0],
            "policy_id": policies[0]["id"],
            "operation": operation,
            "affected_count": affected,
        }
    )


def _expire_policies(conn, action_name, params, assets, action_def):
    latency = _simulate_latency(assets)
    as_of = _parse_time(params.get("as_of")) or _now_dt()
    due = []
    for record in _all_records(conn):
        if record.get("kind") != action_def.get("policy_kind"):
            continue
        if record.get("status") not in ("active", "enabled"):
            continue
        expires_at = _parse_time(record.get("expires_at"))
        if expires_at and expires_at <= as_of:
            due.append(record)
    now = _now()
    for record in due:
        details = dict(record.get("details") or {})
        details.update(
            {
                "expired_at": now,
                "expiry_scan_time": as_of.isoformat(timespec="seconds"),
            }
        )
        conn.execute(
            "UPDATE records SET status = ?, data = ?, updated_at = ? WHERE id = ?",
            (
                action_def.get("result_status") or "expired",
                json.dumps(details, ensure_ascii=False),
                now,
                record["id"],
            ),
        )
    conn.commit()
    policies = [
        record for record in _all_records(conn) if record["id"] in {item["id"] for item in due}
    ]
    operation = _log_operation(
        conn,
        action_name,
        params,
        action_def,
        status="completed",
        details={
            "latency_seconds": latency,
            "affected_count": len(policies),
            "as_of": as_of.isoformat(timespec="seconds"),
        },
    )
    return _response(
        data={
            "result": f"TTL 扫描完成，共处理 {len(policies)} 条到期策略",
            "policies": policies,
            "records": policies,
            "operation": operation,
            "affected_count": len(policies),
        }
    )


def _update_record(conn, action_name, params, assets, action_def):
    latency = _simulate_latency(assets)
    matches = [
        record
        for record in _all_records(conn)
        if _matches(record, params, action_def)
    ]
    if not matches:
        return _response(
            404,
            "未找到匹配记录",
            {"result": "record_not_found", "affected_count": 0},
        )
    now = _now()
    reserved = {
        "alert_id", "asset_id", "host_id", "cluster_id", "status", "severity",
        "owner", "asset_name", "summary",
    }
    for record in matches:
        details = dict(record.get("details") or {})
        details.update(
            {
                key: value
                for key, value in params.items()
                if value not in (None, "") and key not in reserved
            }
        )
        conn.execute(
            """
            UPDATE records
            SET name = ?, owner = ?, status = ?, severity = ?, summary = ?,
                data = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                params.get("asset_name") or record["name"],
                params.get("owner") or record["owner"],
                params.get("status") or action_def.get("result_status") or record["status"],
                params.get("severity") or record["severity"],
                params.get("summary") or record["summary"],
                json.dumps(details, ensure_ascii=False),
                now,
                record["id"],
            ),
        )
    conn.commit()
    records = [
        record for record in _all_records(conn) if record["id"] in {item["id"] for item in matches}
    ]
    operation = _log_operation(
        conn,
        action_name,
        params,
        action_def,
        status=records[0]["status"],
        details={"latency_seconds": latency, "affected_count": len(records)},
    )
    return _response(
        data={
            "result": f"模拟记录更新完成，影响 {len(records)} 条记录",
            "records": records,
            "record": records[0],
            "operation": operation,
            "affected_count": len(records),
        }
    )


def _new_record_id(params, action_def):
    id_param = action_def.get("id_param")
    if id_param and params.get(id_param):
        return str(params[id_param])
    prefix = action_def.get("create_kind") or APP_NAME
    return f"{prefix}-{datetime.now(TZ).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"


def _create_record(conn, action_name, params, assets, action_def):
    latency = _simulate_latency(assets)
    record_id = _new_record_id(params, action_def)
    name = (
        params.get("asset_name")
        or params.get("alert_name")
        or params.get("name")
        or action_def["description"]
    )
    ip = params.get("ip") or params.get("src_ip") or ""
    details = dict(params)
    details[action_def.get("id_param") or "record_id"] = record_id
    details["created_by_action"] = action_name
    record = {
        "id": record_id,
        "kind": action_def.get("create_kind") or "simulated_record",
        "name": name,
        "ip": ip,
        "owner": params.get("owner") or params.get("operator") or "soar-demo",
        "status": action_def.get("result_status") or params.get("status") or "active",
        "severity": params.get("severity") or "medium",
        "summary": params.get("summary") or action_def["description"],
        "data": details,
    }
    _insert_record(conn, record)
    created = next(item for item in _all_records(conn) if item["id"] == record_id)
    operation = _log_operation(
        conn,
        action_name,
        params,
        action_def,
        status=created["status"],
        details={"latency_seconds": latency, "created_id": record_id},
    )
    return _response(
        data={
            "result": "模拟记录创建成功",
            "record": created,
            "records": [created],
            "created_id": record_id,
            "operation": operation,
            "affected_count": 1,
        }
    )


def _delete_record(conn, action_name, params, assets, action_def):
    latency = _simulate_latency(assets)
    matches = [
        record
        for record in _all_records(conn)
        if _matches(record, params, action_def)
    ]
    if not matches:
        return _response(
            404,
            "未找到匹配记录",
            {"result": "record_not_found", "affected_count": 0},
        )
    ids = [record["id"] for record in matches]
    conn.executemany("DELETE FROM records WHERE id = ?", [(item,) for item in ids])
    conn.commit()
    operation = _log_operation(
        conn,
        action_name,
        params,
        action_def,
        status="deleted",
        details={"latency_seconds": latency, "deleted_ids": ids},
    )
    return _response(
        data={
            "result": f"模拟记录删除完成，影响 {len(matches)} 条记录",
            "deleted_records": matches,
            "records": matches,
            "operation": operation,
            "affected_count": len(matches),
        }
    )


def _operation_history(conn, params):
    clauses = []
    values = []
    if params.get("trace_id"):
        clauses.append("trace_id = ?")
        values.append(str(params["trace_id"]))
    if params.get("target"):
        clauses.append("(target LIKE ? OR policy_id LIKE ?)")
        value = f"%{params['target']}%"
        values.extend([value, value])
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    values.append(_limit(params))
    rows = conn.execute(
        f"SELECT * FROM operations {where} ORDER BY timestamp DESC LIMIT ?",
        values,
    ).fetchall()
    records = []
    for row in rows:
        record = dict(row)
        record["details"] = _parse_json(record.get("details"))
        records.append(record)
    return _response(
        data={
            "result": f"查询到 {len(records)} 条操作审计记录",
            "records": records,
            "history_records": records,
            "total_count": len(records),
        }
    )


def _execute(action_name, params, assets, context_info):
    action_def = _definition(action_name)
    if not action_def:
        return _response(404, f"未知动作: {action_name}", {"result": "action_not_found"})
    params = _apply_defaults(params, action_def)
    invalid = _validate_required(params, action_def)
    if invalid:
        return invalid
    operation = action_def.get("operation") or "query"
    if operation == "health":
        return _health(assets)
    unavailable = _availability_error(assets)
    if unavailable:
        return unavailable
    conn = None
    try:
        conn = _connect(assets)
        if operation == "query":
            return _query(conn, params, action_def)
        if operation == "create_policy":
            return _create_policy(conn, action_name, params, assets, action_def)
        if operation == "release_policy":
            return _release_policy(conn, action_name, params, assets, action_def)
        if operation == "expire_policies":
            return _expire_policies(conn, action_name, params, assets, action_def)
        if operation == "update_record":
            return _update_record(conn, action_name, params, assets, action_def)
        if operation == "create_record":
            return _create_record(conn, action_name, params, assets, action_def)
        if operation == "delete_record":
            return _delete_record(conn, action_name, params, assets, action_def)
        if operation == "history":
            return _operation_history(conn, params)
        return _response(500, f"未实现的操作类型: {operation}", {"result": "operation_not_supported"})
    except Exception as exc:
        return _response(500, str(exc), {"result": f"{action_name} 执行失败: {exc}"})
    finally:
        if conn is not None:
            conn.close()


def health_check(params, assets, context_info):
    """检查模拟 API、鉴权和组件状态"""
    return _execute('health_check', params, assets, context_info)


def list_vpc_firewalls(params, assets, context_info):
    """查询 VPC 间防火墙及策略同步状态"""
    return _execute('list_vpc_firewalls', params, assets, context_info)


def list_vpc_access_rules(params, assets, context_info):
    """查询 VPC 间访问控制规则"""
    return _execute('list_vpc_access_rules', params, assets, context_info)


def create_vpc_block_rule(params, assets, context_info):
    """创建 VPC 间拒绝访问规则"""
    return _execute('create_vpc_block_rule', params, assets, context_info)


def delete_vpc_access_rule(params, assets, context_info):
    """删除或回滚 VPC 间访问控制规则"""
    return _execute('delete_vpc_access_rule', params, assets, context_info)


def expire_due_policies(params, assets, context_info):
    """扫描并回滚已到期 CFW 规则"""
    return _execute('expire_due_policies', params, assets, context_info)


def query_operation_history(params, assets, context_info):
    """查询产品模拟操作审计记录"""
    return _execute('query_operation_history', params, assets, context_info)
