# -*- coding: utf-8 -*-
"""Generate self-contained X-series simulated Shakespeare apps.

The generated apps intentionally avoid external APIs. Each app uses SQLite
state, deterministic seed data, action templates, tests, and compact SVG logos.
"""

from __future__ import annotations

import json
import os
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUPPLIER = "雾帜智能"


def p(name, description, data_type="string", required=True, default=None, order=0):
    if isinstance(data_type, bool):
        legacy_required = data_type
        legacy_default = required
        legacy_order = default if default is not None else order
        data_type = "string"
        required = legacy_required
        default = legacy_default
        order = legacy_order
    item = {
        "data_type": data_type,
        "description": description,
        "required": required,
        "order": order,
    }
    if default is not None:
        item["default_value"] = default
    return name, item


def action(
    name,
    description,
    classify="query",
    operation="query",
    params=None,
    filter_keys=None,
    result_status=None,
    allow_create=False,
    sample=None,
):
    return {
        "action": name,
        "description": description,
        "classify": classify,
        "operation": operation,
        "parameters": dict(params or []),
        "filter_keys": filter_keys or [],
        "result_status": result_status,
        "allow_create": allow_create,
        "sample": sample or {},
    }


COMMON_HISTORY_ACTION = action(
    "query_operation_history",
    "查询模拟操作历史",
    params=[
        p("target", "目标对象，可填写 IP、主机名、用户、工单号等", required=False, order=0),
        p("limit", "返回结果数量限制", "integer", required=False, default=50, order=1),
    ],
    filter_keys=["target"],
)


def health_action():
    return action("health_check", "健康检查", operation="health")


APP_SPECS = [
    {
        "name": "xasset",
        "dir": "shakespeare-action-python-xasset",
        "module": "xasset",
        "product_name": "XAsset 资产管理",
        "description": "离线模拟资产与负责人 CMDB，提供资产归属、标签和关联查询能力",
        "category": "IT系统",
        "letter": "A",
        "colors": ("#0f766e", "#14b8a6"),
        "records": [
            {
                "id": "asset-web-01",
                "type": "server",
                "name": "prod-web-01",
                "ip": "10.10.8.23",
                "owner": "alice",
                "user": "alice",
                "status": "online",
                "severity": "high",
                "summary": "互联网业务 Web 服务器，近期命中 WAF 攻击与 HIDS 异常登录",
                "metadata": {
                    "department": "电商业务部",
                    "business": "checkout",
                    "tags": ["internet", "linux", "critical"],
                    "relations": ["asset-db-01", "asset-lb-01"],
                },
            },
            {
                "id": "asset-db-01",
                "type": "database",
                "name": "mysql-core-01",
                "ip": "10.10.9.15",
                "owner": "bob",
                "user": "bob",
                "status": "online",
                "severity": "medium",
                "summary": "核心订单数据库，禁止直接暴露互联网访问",
                "metadata": {"department": "平台工程", "business": "order", "tags": ["mysql", "pci"]},
            },
            {
                "id": "asset-lb-01",
                "type": "load_balancer",
                "name": "prod-lb-01",
                "ip": "10.10.8.10",
                "owner": "alice",
                "user": "alice",
                "status": "online",
                "severity": "low",
                "summary": "互联网业务入口负载均衡，关联 prod-web-01",
                "metadata": {
                    "department": "电商业务部",
                    "business": "checkout",
                    "tags": ["internet", "lb"],
                    "relations": ["asset-web-01"],
                },
            },
            {
                "id": "asset-laptop-07",
                "type": "endpoint",
                "name": "fin-laptop-07",
                "ip": "10.20.4.77",
                "owner": "carol",
                "user": "carol",
                "status": "online",
                "severity": "medium",
                "summary": "财务终端，曾收到钓鱼邮件",
                "metadata": {"department": "财务部", "business": "finance", "tags": ["windows", "office"]},
            },
        ],
        "actions": [
            health_action(),
            action(
                "list_assets",
                "查询资产列表",
                params=[
                    p("owner", "负责人账号，可选；内置样例包括 alice、bob、carol", required=False, order=0),
                    p("status", "资产状态，可选", required=False, order=1),
                    p("limit", "返回数量", "integer", False, 50, 2),
                ],
                filter_keys=["owner", "status"],
                sample={"owner": "alice", "limit": 20},
            ),
            action(
                "query_asset_by_ip",
                "根据 IP 查询资产负责人信息",
                params=[p("ip", "资产 IP 地址", order=0)],
                filter_keys=["ip"],
                sample={"ip": "10.10.8.23"},
            ),
            action(
                "query_assets_by_owner",
                "根据负责人账号查询名下资产",
                params=[
                    p("owner", "负责人账号；内置样例包括 alice、bob、carol", default="alice", order=0),
                    p("limit", "返回数量", "integer", False, 20, 1),
                ],
                filter_keys=["owner"],
                sample={"owner": "alice"},
            ),
            action(
                "query_asset_relations",
                "查询资产关联关系",
                params=[p("asset_id", "资产 ID", order=0)],
                filter_keys=["id", "asset_id"],
                sample={"asset_id": "asset-web-01"},
            ),
            action(
                "query_inventory_summary",
                "查询资产统计摘要",
                operation="summary",
                params=[],
            ),
            action(
                "update_asset_tag",
                "更新资产标签",
                "write",
                "write",
                params=[p("asset_id", "资产 ID", order=0), p("tag", "标签名", order=1), p("value", "标签值", order=2)],
                filter_keys=["id", "asset_id"],
                result_status="tagged",
                sample={"asset_id": "asset-web-01", "tag": "incident", "value": "IR-2026-0001"},
            ),
            action(
                "create_asset",
                "新增资产",
                "write",
                "create",
                params=[
                    p("asset_id", "资产 ID，不填则自动生成", required=False, order=0),
                    p("asset_name", "资产名称", order=1),
                    p("ip", "资产 IP 地址", required=False, order=2),
                    p("asset_type", "资产类型", required=False, default="server", order=3),
                    p("owner", "负责人账号", required=False, default="secops", order=4),
                    p("status", "资产状态", required=False, default="online", order=5),
                    p("severity", "资产等级", required=False, default="medium", order=6),
                    p("summary", "资产说明", required=False, default="手工新增模拟资产", order=7),
                ],
                sample={
                    "asset_id": "asset-demo-01",
                    "asset_name": "demo-server-01",
                    "ip": "10.30.6.10",
                    "asset_type": "server",
                    "owner": "secops",
                    "status": "online",
                },
            ),
            action(
                "update_asset",
                "更新资产信息",
                "write",
                "update",
                params=[
                    p("asset_id", "资产 ID", order=0),
                    p("asset_name", "资产名称", required=False, order=1),
                    p("ip", "资产 IP 地址", required=False, order=2),
                    p("asset_type", "资产类型", required=False, order=3),
                    p("owner", "负责人账号", required=False, order=4),
                    p("status", "资产状态", required=False, order=5),
                    p("severity", "资产等级", required=False, order=6),
                    p("summary", "资产说明", required=False, order=7),
                ],
                filter_keys=["id", "asset_id"],
                sample={"asset_id": "asset-web-01", "owner": "alice", "status": "maintenance"},
            ),
            action(
                "delete_asset",
                "删除资产",
                "write",
                "delete",
                params=[
                    p("asset_id", "资产 ID", order=0),
                    p("reason", "删除原因", required=False, default="资产下线", order=1),
                ],
                filter_keys=["id", "asset_id"],
                result_status="deleted",
                sample={"asset_id": "asset-lb-01", "reason": "资产下线"},
            ),
        ],
    },
    {
        "name": "xhids",
        "dir": "shakespeare-action-python-xhids",
        "module": "xhids",
        "product_name": "XHIDS 主机安全",
        "description": "离线模拟 HIDS 主机安全平台，提供主机、进程、端口、告警与隔离动作",
        "category": "安全产品",
        "letter": "H",
        "colors": ("#7c2d12", "#f97316"),
        "records": [
            {
                "id": "host-prod-web-01",
                "type": "linux_host",
                "name": "prod-web-01",
                "ip": "10.10.8.23",
                "owner": "alice",
                "user": "www-data",
                "status": "monitored",
                "severity": "high",
                "summary": "检测到异常登录和反弹 shell 行为",
                "metadata": {
                    "processes": ["nginx", "python3 /tmp/.x/update.py", "sshd"],
                    "ports": [22, 80, 443, 8443],
                    "events": ["abnormal_login", "reverse_shell"],
                },
            },
            {
                "id": "host-fin-laptop-07",
                "type": "windows_host",
                "name": "fin-laptop-07",
                "ip": "10.20.4.77",
                "owner": "carol",
                "user": "carol",
                "status": "monitored",
                "severity": "medium",
                "summary": "可疑 Office 子进程启动 PowerShell",
                "metadata": {"processes": ["winword.exe", "powershell.exe"], "ports": [135, 445], "events": ["suspicious_child_process"]},
            },
        ],
        "actions": [
            health_action(),
            action("query_host_by_ip", "根据 IP 查询主机信息", params=[p("ip", "主机 IP", order=0)], filter_keys=["ip"], sample={"ip": "10.10.8.23"}),
            action("query_host_processes", "查询主机进程信息", params=[p("host_id", "主机 ID", order=0)], filter_keys=["id", "host_id"], sample={"host_id": "host-prod-web-01"}),
            action("query_host_ports", "查询主机端口信息", params=[p("host_id", "主机 ID", order=0)], filter_keys=["id", "host_id"], sample={"host_id": "host-prod-web-01"}),
            action("query_security_events", "查询主机安全事件", params=[p("severity", "事件等级", required=False, order=0), p("limit", "返回数量", "integer", False, 20, 1)], filter_keys=["severity"], sample={"severity": "high"}),
            action("isolate_host", "隔离主机", "write", "write", params=[p("host_id", "主机 ID", order=0), p("reason", "隔离原因", required=False, default="安全事件处置", order=1)], filter_keys=["id", "host_id"], result_status="isolated", sample={"host_id": "host-prod-web-01", "reason": "检测到反弹 shell"}),
            action("release_host", "解除主机隔离", "write", "write", params=[p("host_id", "主机 ID", order=0), p("reason", "解除原因", required=False, default="处置完成", order=1)], filter_keys=["id", "host_id"], result_status="monitored", sample={"host_id": "host-prod-web-01", "reason": "人工确认恢复"}),
            COMMON_HISTORY_ACTION,
        ],
    },
    {
        "name": "xav",
        "dir": "shakespeare-action-python-xav",
        "module": "xav",
        "product_name": "XAV 防病毒软件",
        "description": "离线模拟防病毒与 EDR 轻量处置能力，支持扫描、隔离文件和清除威胁",
        "category": "安全产品",
        "letter": "V",
        "colors": ("#991b1b", "#ef4444"),
        "records": [
            {
                "id": "threat-1001",
                "type": "malware",
                "name": "Trojan.Agent.X",
                "ip": "10.20.4.77",
                "owner": "carol",
                "user": "carol",
                "status": "active",
                "severity": "high",
                "indicator": "44d88612fea8a8f36de82e1278abb02f",
                "summary": "财务终端发现可疑宏木马",
                "metadata": {"file_path": "C:/Users/carol/AppData/Local/Temp/invoice.exe", "engine": "XAV Engine"},
            },
            {
                "id": "endpoint-prod-web-01",
                "type": "endpoint",
                "name": "prod-web-01",
                "ip": "10.10.8.23",
                "owner": "alice",
                "status": "protected",
                "severity": "medium",
                "summary": "Linux 服务器安装了 XAV Agent",
                "metadata": {"agent_version": "4.6.2", "signature": "20260709.1"},
            },
        ],
        "actions": [
            health_action(),
            action("query_endpoint", "查询终端防护状态", params=[p("ip", "终端 IP", order=0)], filter_keys=["ip"], sample={"ip": "10.20.4.77"}),
            action("query_threat_events", "查询病毒威胁事件", params=[p("severity", "威胁等级", required=False, order=0)], filter_keys=["severity"], sample={"severity": "high"}),
            action("start_scan", "发起终端扫描任务", "write", "write", params=[p("ip", "终端 IP", order=0), p("scan_type", "扫描类型", required=False, default="quick", order=1)], filter_keys=["ip"], result_status="scanning", allow_create=True, sample={"ip": "10.20.4.77", "scan_type": "full"}),
            action("quarantine_file", "隔离恶意文件", "write", "write", params=[p("file_hash", "文件 Hash", order=0), p("reason", "隔离原因", required=False, default="命中病毒库", order=1)], filter_keys=["indicator", "file_hash"], result_status="quarantined", sample={"file_hash": "44d88612fea8a8f36de82e1278abb02f", "reason": "命中木马规则"}),
            action("remove_threat", "清除威胁", "write", "write", params=[p("threat_id", "威胁 ID", order=0)], filter_keys=["id", "threat_id"], result_status="removed", sample={"threat_id": "threat-1001"}),
            COMMON_HISTORY_ACTION,
        ],
    },
    {
        "name": "xwaf",
        "dir": "shakespeare-action-python-xwaf",
        "module": "xwaf",
        "product_name": "XWAF Web应用防火墙",
        "description": "离线模拟 WAF 攻击检测、站点防护、IP 封禁和 URL 规则能力",
        "category": "安全产品",
        "letter": "W",
        "colors": ("#1d4ed8", "#60a5fa"),
        "records": [
            {
                "id": "waf-event-9001",
                "type": "sql_injection",
                "name": "checkout SQL injection",
                "ip": "203.0.113.77",
                "status": "detected",
                "severity": "high",
                "indicator": "203.0.113.77",
                "summary": "支付站点命中 SQL 注入攻击规则",
                "metadata": {"site": "checkout.example.com", "url": "/pay?id=1%20or%201=1", "action": "blocked"},
            },
            {
                "id": "waf-site-01",
                "type": "protected_site",
                "name": "checkout.example.com",
                "ip": "10.10.8.23",
                "owner": "alice",
                "status": "protected",
                "severity": "medium",
                "summary": "核心支付站点，启用 SQLi/XSS/RCE 防护",
                "metadata": {"policy": "strict", "qps": 1280},
            },
        ],
        "actions": [
            health_action(),
            action("query_attack_events", "查询 Web 攻击事件", params=[p("source_ip", "攻击源 IP", required=False, order=0), p("severity", "攻击等级", required=False, order=1)], filter_keys=["ip", "source_ip", "severity"], sample={"source_ip": "203.0.113.77"}),
            action("query_protected_sites", "查询受保护站点", params=[p("site", "站点域名", required=False, order=0)], filter_keys=["name", "site"], sample={"site": "checkout.example.com"}),
            action("block_ip", "在 WAF 中封禁源 IP", "write", "write", params=[p("ip", "源 IP", order=0), p("reason", "封禁原因", False, "攻击源阻断", 1)], filter_keys=["ip"], result_status="blocked", allow_create=True, sample={"ip": "203.0.113.77", "reason": "SQL 注入攻击"}),
            action("unblock_ip", "解除 WAF IP 封禁", "write", "write", params=[p("ip", "源 IP", order=0)], filter_keys=["ip"], result_status="released", sample={"ip": "203.0.113.77"}),
            action("add_url_rule", "新增 URL 防护规则", "write", "write", params=[p("url", "URL 路径", order=0), p("rule", "规则名称", False, "custom-block", 1)], filter_keys=["metadata.url", "url"], result_status="rule_added", allow_create=True, sample={"url": "/admin/debug", "rule": "禁止调试路径访问"}),
            COMMON_HISTORY_ACTION,
        ],
    },
    {
        "name": "xswitch",
        "dir": "shakespeare-action-python-xswitch",
        "module": "xswitch",
        "product_name": "XSwitch 交换机",
        "description": "离线模拟交换机 MAC、ARP、接口状态和端口阻断/恢复能力",
        "category": "网络设备",
        "letter": "S",
        "colors": ("#365314", "#84cc16"),
        "records": [
            {
                "id": "sw-core-01-ge1-0-12",
                "type": "switch_port",
                "name": "GE1/0/12",
                "ip": "10.20.4.77",
                "owner": "carol",
                "status": "up",
                "severity": "medium",
                "summary": "财务终端接入端口",
                "metadata": {"switch": "sw-core-01", "mac": "00:16:3e:7a:4b:11", "vlan": "finance"},
            },
            {
                "id": "sw-core-01-ge1-0-24",
                "type": "switch_port",
                "name": "GE1/0/24",
                "ip": "10.10.8.23",
                "owner": "alice",
                "status": "up",
                "severity": "low",
                "summary": "Web 服务器接入端口",
                "metadata": {"switch": "sw-core-01", "mac": "00:16:3e:12:8a:23", "vlan": "dmz"},
            },
        ],
        "actions": [
            health_action(),
            action("query_mac_table", "查询 MAC 地址表", params=[p("mac", "MAC 地址", required=False, order=0)], filter_keys=["metadata.mac", "mac"], sample={"mac": "00:16:3e:7a:4b:11"}),
            action("query_arp_table", "查询 ARP 表", params=[p("ip", "IP 地址", required=False, order=0)], filter_keys=["ip"], sample={"ip": "10.20.4.77"}),
            action("query_interface_status", "查询接口状态", params=[p("interface", "接口名称", order=0)], filter_keys=["name", "interface"], sample={"interface": "GE1/0/12"}),
            action("disable_port", "关闭交换机端口", "write", "write", params=[p("interface", "接口名称", order=0), p("reason", "关闭原因", False, "安全处置", 1)], filter_keys=["name", "interface"], result_status="down", sample={"interface": "GE1/0/12", "reason": "终端隔离"}),
            action("enable_port", "恢复交换机端口", "write", "write", params=[p("interface", "接口名称", order=0)], filter_keys=["name", "interface"], result_status="up", sample={"interface": "GE1/0/12"}),
            COMMON_HISTORY_ACTION,
        ],
    },
    {
        "name": "xti",
        "dir": "shakespeare-action-python-xti",
        "module": "xti",
        "product_name": "XTI 威胁情报",
        "description": "离线模拟威胁情报平台，支持 IP、域名、URL、文件 Hash、CVE 查询",
        "category": "安全产品",
        "letter": "T",
        "colors": ("#581c87", "#a855f7"),
        "records": [
            {
                "id": "ioc-ip-203-0-113-77",
                "type": "ip",
                "name": "203.0.113.77",
                "ip": "203.0.113.77",
                "status": "malicious",
                "severity": "high",
                "indicator": "203.0.113.77",
                "summary": "近期参与 Web 攻击和凭证爆破",
                "metadata": {"labels": ["scanner", "bruteforce"], "confidence": 92, "asn": "AS64500"},
            },
            {
                "id": "ioc-hash-44d8",
                "type": "file",
                "name": "invoice.exe",
                "status": "malicious",
                "severity": "high",
                "indicator": "44d88612fea8a8f36de82e1278abb02f",
                "summary": "宏木马投递的二阶段载荷",
                "metadata": {"family": "Agent.X", "confidence": 95},
            },
            {
                "id": "cve-2026-10001",
                "type": "cve",
                "name": "CVE-2026-10001",
                "status": "exploited",
                "severity": "critical",
                "indicator": "CVE-2026-10001",
                "summary": "样例远程命令执行漏洞，已出现利用",
                "metadata": {"cvss": 9.8, "product": "Example Portal"},
            },
        ],
        "actions": [
            health_action(),
            action("query_ip_reputation", "查询 IP 信誉", params=[p("ip", "IP 地址", order=0)], filter_keys=["ip", "indicator"], sample={"ip": "203.0.113.77"}),
            action("query_domain_reputation", "查询域名信誉", params=[p("domain", "域名", order=0)], filter_keys=["name", "indicator", "domain"], allow_create=True, sample={"domain": "malicious.example"}),
            action("query_url_reputation", "查询 URL 信誉", params=[p("url", "URL", order=0)], filter_keys=["metadata.url", "indicator", "url"], allow_create=True, sample={"url": "https://malicious.example/login"}),
            action("query_file_reputation", "查询文件 Hash 信誉", params=[p("file_hash", "文件 Hash", order=0)], filter_keys=["indicator", "file_hash"], sample={"file_hash": "44d88612fea8a8f36de82e1278abb02f"}),
            action("query_cve_intel", "查询漏洞情报", params=[p("cve_id", "CVE 编号", order=0)], filter_keys=["indicator", "name", "cve_id"], sample={"cve_id": "CVE-2026-10001"}),
            action("submit_indicator", "提交自定义情报指标", "write", "create", params=[p("indicator", "情报指标", order=0), p("indicator_type", "指标类型", False, "ip", 1), p("severity", "风险等级", False, "medium", 2)], result_status="submitted", sample={"indicator": "198.51.100.88", "indicator_type": "ip", "severity": "medium"}),
        ],
    },
    {
        "name": "xsiem",
        "dir": "shakespeare-action-python-xsiem",
        "module": "xsiem",
        "product_name": "XSIEM 日志与告警平台",
        "description": "离线模拟 SIEM 日志搜索、告警详情、事件聚合和告警状态流转",
        "category": "安全产品",
        "letter": "L",
        "colors": ("#0f172a", "#38bdf8"),
        "records": [
            {
                "id": "alert-20260709-001",
                "type": "alert",
                "name": "Web 服务器异常登录后发起外联",
                "ip": "10.10.8.23",
                "owner": "alice",
                "status": "open",
                "severity": "high",
                "indicator": "203.0.113.77",
                "summary": "prod-web-01 登录异常后访问高风险 IP",
                "metadata": {"source": "hids", "rule": "abnormal_login_then_c2", "events": 7},
            },
            {
                "id": "alert-20260709-002",
                "type": "alert",
                "name": "财务终端执行可疑 PowerShell",
                "ip": "10.20.4.77",
                "owner": "carol",
                "status": "open",
                "severity": "medium",
                "indicator": "44d88612fea8a8f36de82e1278abb02f",
                "summary": "Office 子进程启动 PowerShell 并下载文件",
                "metadata": {"source": "edr", "events": 4},
            },
        ],
        "actions": [
            health_action(),
            action("search_events", "搜索日志事件", params=[p("query", "搜索语句", required=False, default="severity=high", order=0), p("limit", "返回数量", "integer", False, 20, 1)], filter_keys=["summary", "name", "metadata.rule", "severity"], sample={"query": "severity=high"}),
            action("query_alert_detail", "查询告警详情", params=[p("alert_id", "告警 ID", order=0)], filter_keys=["id", "alert_id"], sample={"alert_id": "alert-20260709-001"}),
            action("aggregate_events", "聚合事件统计", operation="summary", params=[p("window_minutes", "聚合窗口分钟", "integer", False, 60, 0)], sample={"window_minutes": 60}),
            action("update_alert_status", "更新告警状态", "write", "write", params=[p("alert_id", "告警 ID", order=0), p("status", "目标状态", False, "closed", 1), p("reason", "处理说明", False, "剧本自动处置", 2)], filter_keys=["id", "alert_id"], result_status="closed", sample={"alert_id": "alert-20260709-001", "status": "in_progress", "reason": "已触发自动封堵"}),
            action("query_case_timeline", "查询事件时间线", params=[p("alert_id", "告警 ID", order=0)], filter_keys=["id", "alert_id"], sample={"alert_id": "alert-20260709-001"}),
            COMMON_HISTORY_ACTION,
        ],
    },
    {
        "name": "xticket",
        "dir": "shakespeare-action-python-xticket",
        "module": "xticket",
        "product_name": "XTicket 工单系统",
        "description": "离线模拟工单系统，支持创建、分派、评论、流转和历史查询",
        "category": "IT系统",
        "letter": "K",
        "colors": ("#854d0e", "#facc15"),
        "records": [
            {
                "id": "TCK-20260709-0001",
                "type": "security_ticket",
                "name": "prod-web-01 恶意外联处置",
                "ip": "10.10.8.23",
                "owner": "secops",
                "user": "alice",
                "status": "open",
                "severity": "high",
                "summary": "自动化剧本创建，待业务负责人确认",
                "metadata": {"assignee": "secops", "comments": ["剧本已封禁恶意 IP"]},
            }
        ],
        "actions": [
            health_action(),
            action("create_ticket", "创建工单", "write", "create", params=[p("title", "工单标题", order=0), p("severity", "严重等级", False, "medium", 1), p("description", "工单描述", False, "", 2)], result_status="open", sample={"title": "恶意 IP 自动封堵确认", "severity": "high", "description": "SOAR 剧本已完成封堵，请复核"}),
            action("query_ticket", "查询工单", params=[p("ticket_id", "工单 ID", order=0)], filter_keys=["id", "ticket_id"], sample={"ticket_id": "TCK-20260709-0001"}),
            action("update_ticket_status", "更新工单状态", "write", "write", params=[p("ticket_id", "工单 ID", order=0), p("status", "目标状态", False, "closed", 1), p("reason", "处理说明", False, "处置完成", 2)], filter_keys=["id", "ticket_id"], result_status="closed", sample={"ticket_id": "TCK-20260709-0001", "status": "in_progress", "reason": "已分派安全运营"}),
            action("add_ticket_comment", "追加工单评论", "write", "write", params=[p("ticket_id", "工单 ID", order=0), p("comment", "评论内容", order=1)], filter_keys=["id", "ticket_id"], result_status="commented", sample={"ticket_id": "TCK-20260709-0001", "comment": "已通知资产负责人"}),
            action("assign_ticket", "分派工单", "write", "write", params=[p("ticket_id", "工单 ID", order=0), p("assignee", "处理人", order=1)], filter_keys=["id", "ticket_id"], result_status="assigned", sample={"ticket_id": "TCK-20260709-0001", "assignee": "secops"}),
            action("query_ticket_history", "查询工单历史", operation="history", params=[p("ticket_id", "工单 ID", required=False, order=0), p("limit", "返回数量", "integer", False, 50, 1)], filter_keys=["ticket_id"], sample={"ticket_id": "TCK-20260709-0001"}),
        ],
    },
    {
        "name": "xnotify",
        "dir": "shakespeare-action-python-xnotify",
        "module": "xnotify",
        "product_name": "XNotify 通知系统",
        "description": "离线模拟通知服务，支持企业微信、邮件、短信式通知与投递状态查询",
        "category": "SaaS服务",
        "letter": "N",
        "colors": ("#155e75", "#22d3ee"),
        "records": [
            {
                "id": "notice-20260709-0001",
                "type": "wecom",
                "name": "安全事件通知",
                "owner": "secops",
                "user": "alice",
                "status": "delivered",
                "severity": "medium",
                "summary": "已向业务负责人发送封堵确认通知",
                "metadata": {"recipient": "alice", "channel": "wecom", "message": "prod-web-01 已完成恶意 IP 封堵"},
            }
        ],
        "actions": [
            health_action(),
            action("send_message", "发送企业微信式消息", "notify", "notify", params=[p("recipient", "接收人", order=0), p("message", "消息内容", order=1), p("severity", "消息等级", False, "info", 2)], result_status="delivered", sample={"recipient": "alice", "message": "X 系列剧本已完成封堵", "severity": "info"}),
            action("send_email", "发送邮件式通知", "notify", "notify", params=[p("recipient", "邮箱", order=0), p("subject", "邮件主题", order=1), p("message", "邮件内容", order=2)], result_status="delivered", sample={"recipient": "secops@example.com", "subject": "安全事件通知", "message": "请复核自动处置结果"}),
            action("send_sms", "发送短信式通知", "notify", "notify", params=[p("recipient", "手机号", order=0), p("message", "短信内容", order=1)], result_status="delivered", sample={"recipient": "13800000000", "message": "安全事件已自动处置"}),
            action("query_notification_history", "查询通知历史", operation="history", params=[p("recipient", "接收人", required=False, order=0), p("limit", "返回数量", "integer", False, 50, 1)], filter_keys=["recipient"], sample={"recipient": "alice"}),
            action("query_delivery_status", "查询投递状态", params=[p("notification_id", "通知 ID", order=0)], filter_keys=["id", "notification_id"], sample={"notification_id": "notice-20260709-0001"}),
            action("register_channel", "注册通知通道", "write", "create", params=[p("channel_name", "通道名称", order=0), p("channel_type", "通道类型", False, "webhook", 1)], result_status="registered", sample={"channel_name": "secops-webhook", "channel_type": "webhook"}),
        ],
    },
    {
        "name": "xscanner",
        "dir": "shakespeare-action-python-xscanner",
        "module": "xscanner",
        "product_name": "XScanner 漏洞扫描器",
        "description": "离线模拟漏洞扫描器，支持目标管理、扫描任务、漏洞结果和报告生成",
        "category": "安全产品",
        "letter": "R",
        "colors": ("#be123c", "#fb7185"),
        "records": [
            {
                "id": "scan-target-10-10-8-23",
                "type": "scan_target",
                "name": "prod-web-01",
                "ip": "10.10.8.23",
                "owner": "alice",
                "status": "ready",
                "severity": "critical",
                "indicator": "CVE-2026-10001",
                "summary": "发现远程命令执行高危漏洞",
                "metadata": {"port": 443, "service": "Example Portal", "cvss": 9.8},
            }
        ],
        "actions": [
            health_action(),
            action("add_scan_target", "新增扫描目标", "write", "create", params=[p("target", "扫描目标 IP/域名", order=0), p("owner", "负责人", False, "secops", 1)], result_status="ready", sample={"target": "10.10.8.23", "owner": "alice"}),
            action("start_scan", "启动扫描任务", "write", "write", params=[p("target", "扫描目标", order=0), p("profile", "扫描模板", False, "full", 1)], filter_keys=["ip", "name", "target"], result_status="scanning", allow_create=True, sample={"target": "10.10.8.23", "profile": "full"}),
            action("query_scan_status", "查询扫描状态", params=[p("target", "扫描目标", order=0)], filter_keys=["ip", "name", "target"], sample={"target": "10.10.8.23"}),
            action("query_vulnerabilities", "查询漏洞结果", params=[p("severity", "漏洞等级", required=False, order=0)], filter_keys=["severity"], sample={"severity": "critical"}),
            action("generate_report", "生成扫描报告", "write", "write", params=[p("target", "扫描目标", order=0), p("format", "报告格式", False, "pdf", 1)], filter_keys=["ip", "name", "target"], result_status="reported", sample={"target": "10.10.8.23", "format": "html"}),
            COMMON_HISTORY_ACTION,
        ],
    },
    {
        "name": "xmail",
        "dir": "shakespeare-action-python-xmail",
        "module": "xmail",
        "product_name": "XMail 邮件安全",
        "description": "离线模拟邮件安全网关，支持邮件解析、事件查询、隔离、释放和发件人阻断",
        "category": "安全产品",
        "letter": "M",
        "colors": ("#4338ca", "#818cf8"),
        "records": [
            {
                "id": "mail-20260709-0007",
                "type": "phishing_mail",
                "name": "发票确认通知",
                "owner": "mailops",
                "user": "carol",
                "status": "delivered",
                "severity": "high",
                "indicator": "malicious.example",
                "summary": "疑似钓鱼邮件投递给财务用户",
                "metadata": {"sender": "invoice@malicious.example", "recipient": "carol@example.com", "url": "https://malicious.example/login"},
            }
        ],
        "actions": [
            health_action(),
            action("parse_email", "解析邮件内容", params=[p("message_id", "邮件 ID", order=0)], filter_keys=["id", "message_id"], sample={"message_id": "mail-20260709-0007"}),
            action("query_mail_events", "查询邮件安全事件", params=[p("recipient", "收件人", required=False, order=0), p("severity", "风险等级", required=False, order=1)], filter_keys=["metadata.recipient", "user", "severity"], sample={"recipient": "carol@example.com"}),
            action("quarantine_message", "隔离邮件", "write", "write", params=[p("message_id", "邮件 ID", order=0), p("reason", "隔离原因", False, "疑似钓鱼", 1)], filter_keys=["id", "message_id"], result_status="quarantined", sample={"message_id": "mail-20260709-0007", "reason": "钓鱼链接"}),
            action("release_message", "释放邮件", "write", "write", params=[p("message_id", "邮件 ID", order=0)], filter_keys=["id", "message_id"], result_status="released", sample={"message_id": "mail-20260709-0007"}),
            action("block_sender", "阻断发件人", "write", "write", params=[p("sender", "发件人地址", order=0), p("reason", "阻断原因", False, "恶意发件人", 1)], filter_keys=["metadata.sender", "sender"], result_status="sender_blocked", sample={"sender": "invoice@malicious.example", "reason": "钓鱼邮件源"}),
            COMMON_HISTORY_ACTION,
        ],
    },
    {
        "name": "xiam",
        "dir": "shakespeare-action-python-xiam",
        "module": "xiam",
        "product_name": "XIAM 身份与访问管理",
        "description": "离线模拟 AD/LDAP/IAM 身份系统，支持用户查询、登录记录、禁用、启用和重置密码",
        "category": "IT系统",
        "letter": "I",
        "colors": ("#0e7490", "#67e8f9"),
        "records": [
            {
                "id": "user-alice",
                "type": "user",
                "name": "alice",
                "owner": "电商业务部",
                "user": "alice",
                "status": "enabled",
                "severity": "medium",
                "summary": "支付系统负责人，最近发生异地登录",
                "metadata": {"email": "alice@example.com", "mfa": True, "last_login_ip": "203.0.113.77"},
            },
            {
                "id": "user-carol",
                "type": "user",
                "name": "carol",
                "owner": "财务部",
                "user": "carol",
                "status": "enabled",
                "severity": "medium",
                "summary": "财务用户，收到钓鱼邮件",
                "metadata": {"email": "carol@example.com", "mfa": False, "last_login_ip": "10.20.4.77"},
            },
        ],
        "actions": [
            health_action(),
            action("query_user", "查询用户信息", params=[p("username", "用户名", order=0)], filter_keys=["name", "user", "username"], sample={"username": "alice"}),
            action("query_user_logins", "查询用户登录记录", params=[p("username", "用户名", order=0)], filter_keys=["name", "user", "username"], sample={"username": "alice"}),
            action("disable_user", "禁用用户", "write", "write", params=[p("username", "用户名", order=0), p("reason", "禁用原因", False, "安全事件处置", 1)], filter_keys=["name", "user", "username"], result_status="disabled", sample={"username": "alice", "reason": "疑似账号失陷"}),
            action("enable_user", "启用用户", "write", "write", params=[p("username", "用户名", order=0)], filter_keys=["name", "user", "username"], result_status="enabled", sample={"username": "alice"}),
            action("reset_password", "重置用户密码", "write", "write", params=[p("username", "用户名", order=0), p("reason", "重置原因", False, "账号风险处置", 1)], filter_keys=["name", "user", "username"], result_status="password_reset", sample={"username": "alice", "reason": "账号疑似泄露"}),
            COMMON_HISTORY_ACTION,
        ],
    },
    {
        "name": "xldap",
        "dir": "shakespeare-action-python-xldap",
        "module": "xldap",
        "product_name": "XLDAP 目录服务",
        "description": "离线模拟 LDAP/AD 目录服务，支持用户、组织、用户组和账号状态管理",
        "category": "IT系统",
        "letter": "D",
        "colors": ("#164e63", "#06b6d4"),
        "records": [
            {
                "id": "ldap-user-alice",
                "type": "ldap_user",
                "name": "alice",
                "owner": "电商业务部",
                "user": "alice",
                "status": "enabled",
                "severity": "medium",
                "summary": "支付系统负责人，属于 app-admins 与 vpn-users 组",
                "metadata": {
                    "dn": "uid=alice,ou=People,dc=example,dc=com",
                    "email": "alice@example.com",
                    "groups": ["app-admins", "vpn-users"],
                    "department": "电商业务部",
                    "last_bind_time": "2026-07-09 09:42:31",
                },
            },
            {
                "id": "ldap-user-carol",
                "type": "ldap_user",
                "name": "carol",
                "owner": "财务部",
                "user": "carol",
                "status": "enabled",
                "severity": "medium",
                "summary": "财务用户，属于 finance 与 vpn-users 组",
                "metadata": {
                    "dn": "uid=carol,ou=People,dc=example,dc=com",
                    "email": "carol@example.com",
                    "groups": ["finance", "vpn-users"],
                    "department": "财务部",
                    "last_bind_time": "2026-07-09 10:17:22",
                },
            },
            {
                "id": "ldap-group-vpn-users",
                "type": "ldap_group",
                "name": "vpn-users",
                "owner": "IT 运维",
                "status": "active",
                "severity": "low",
                "summary": "允许远程 VPN 接入的用户组",
                "metadata": {"dn": "cn=vpn-users,ou=Groups,dc=example,dc=com", "members": ["alice", "carol"]},
            },
        ],
        "actions": [
            health_action(),
            action("query_user", "查询 LDAP 用户信息", params=[p("username", "用户名", order=0)], filter_keys=["name", "user", "username"], sample={"username": "alice"}),
            action("query_group", "查询 LDAP 用户组信息", params=[p("group_name", "用户组名称", order=0)], filter_keys=["name", "group_name"], sample={"group_name": "vpn-users"}),
            action("query_user_groups", "查询用户所属组", params=[p("username", "用户名", order=0)], filter_keys=["name", "user", "username"], sample={"username": "alice"}),
            action("create_user", "创建 LDAP 用户", "write", "create", params=[p("username", "用户名", order=0), p("display_name", "显示名", False, "", 1), p("department", "部门", False, "未分配", 2)], result_status="enabled", sample={"username": "dave", "display_name": "Dave", "department": "安全运营"}),
            action("disable_user", "禁用 LDAP 用户", "write", "write", params=[p("username", "用户名", order=0), p("reason", "禁用原因", False, "安全事件处置", 1)], filter_keys=["name", "user", "username"], result_status="disabled", sample={"username": "alice", "reason": "账号风险处置"}),
            action("enable_user", "启用 LDAP 用户", "write", "write", params=[p("username", "用户名", order=0)], filter_keys=["name", "user", "username"], result_status="enabled", sample={"username": "alice"}),
            action("reset_password", "重置 LDAP 用户密码", "write", "write", params=[p("username", "用户名", order=0), p("reason", "重置原因", False, "账号风险处置", 1)], filter_keys=["name", "user", "username"], result_status="password_reset", sample={"username": "alice", "reason": "疑似凭证泄露"}),
            action("add_user_to_group", "将用户加入用户组", "write", "write", params=[p("username", "用户名", order=0), p("group_name", "用户组名称", order=1)], filter_keys=["name", "user", "username"], result_status="group_updated", sample={"username": "alice", "group_name": "vpn-users"}),
            COMMON_HISTORY_ACTION,
        ],
    },
    {
        "name": "xjumpserver",
        "dir": "shakespeare-action-python-xjumpserver",
        "module": "xjumpserver",
        "product_name": "XJumpServer 堡垒机",
        "description": "离线模拟堡垒机访问审计，返回员工通过堡垒机访问目标设备的方式、协议、会话和命令记录",
        "category": "安全产品",
        "letter": "J",
        "colors": ("#312e81", "#6366f1"),
        "records": [
            {
                "id": "jms-login-20260709-0001",
                "type": "bastion_login",
                "name": "alice -> prod-web-01",
                "ip": "10.10.8.23",
                "owner": "alice",
                "user": "alice",
                "status": "finished",
                "severity": "medium",
                "summary": "alice 通过堡垒机使用 SSH 密钥登录 prod-web-01",
                "metadata": {
                    "target_asset": "prod-web-01",
                    "target_ip": "10.10.8.23",
                    "source_ip": "10.30.1.25",
                    "access_protocol": "ssh",
                    "auth_method": "ssh_key",
                    "login_method": "web_terminal",
                    "session_id": "sess-jms-0001",
                    "start_time": "2026-07-09 09:21:03",
                    "end_time": "2026-07-09 09:47:18",
                },
            },
            {
                "id": "jms-login-20260709-0002",
                "type": "bastion_login",
                "name": "carol -> fin-laptop-07",
                "ip": "10.20.4.77",
                "owner": "carol",
                "user": "carol",
                "status": "online",
                "severity": "high",
                "summary": "carol 通过堡垒机使用 RDP 账号密码访问财务终端",
                "metadata": {
                    "target_asset": "fin-laptop-07",
                    "target_ip": "10.20.4.77",
                    "source_ip": "10.30.1.88",
                    "access_protocol": "rdp",
                    "auth_method": "password",
                    "login_method": "native_client",
                    "session_id": "sess-jms-0002",
                    "start_time": "2026-07-09 10:36:11",
                },
            },
            {
                "id": "jms-command-20260709-0100",
                "type": "command_audit",
                "name": "prod-web-01 command audit",
                "ip": "10.10.8.23",
                "owner": "alice",
                "user": "alice",
                "status": "recorded",
                "severity": "medium",
                "summary": "堡垒机会话命令审计记录",
                "metadata": {"session_id": "sess-jms-0001", "command": "sudo systemctl restart nginx", "risk": "normal"},
            },
        ],
        "actions": [
            health_action(),
            action("query_login_records", "查询堡垒机登录记录", params=[p("username", "员工账号", required=False, order=0), p("target_ip", "目标设备 IP", required=False, order=1), p("limit", "返回数量", "integer", False, 50, 2)], filter_keys=["user", "metadata.target_ip"], sample={"username": "alice", "target_ip": "10.10.8.23"}),
            action("query_target_access", "查询员工访问目标设备的方式", params=[p("username", "员工账号", required=False, order=0), p("target_ip", "目标设备 IP", required=False, order=1)], filter_keys=["user", "metadata.target_ip"], sample={"username": "carol", "target_ip": "10.20.4.77"}),
            action("query_online_sessions", "查询当前在线堡垒机会话", params=[p("username", "员工账号", required=False, order=0), p("status", "会话状态", required=False, default="online", order=1)], filter_keys=["user", "status"], sample={"username": "carol"}),
            action("query_command_audit", "查询堡垒机命令审计", params=[p("session_id", "会话 ID", order=0)], filter_keys=["metadata.session_id", "session_id"], sample={"session_id": "sess-jms-0001"}),
            action("terminate_session", "终止堡垒机会话", "write", "write", params=[p("session_id", "会话 ID", order=0), p("reason", "终止原因", False, "安全处置", 1)], filter_keys=["metadata.session_id", "session_id"], result_status="terminated", sample={"session_id": "sess-jms-0002", "reason": "可疑远程访问"}),
            COMMON_HISTORY_ACTION,
        ],
    },
    {
        "name": "xvpn",
        "dir": "shakespeare-action-python-xvpn",
        "module": "xvpn",
        "product_name": "XVPN 远程接入",
        "description": "离线模拟 VPN 远程接入系统，支持登录状态、账号创建、账号禁用和踢人下线",
        "category": "网络设备",
        "letter": "P",
        "colors": ("#14532d", "#22c55e"),
        "records": [
            {
                "id": "vpn-user-alice",
                "type": "vpn_account",
                "name": "alice",
                "owner": "电商业务部",
                "user": "alice",
                "status": "enabled",
                "severity": "medium",
                "summary": "alice VPN 账号已启用，最近从异常公网 IP 登录",
                "metadata": {"mfa": True, "groups": ["vpn-users"], "last_login_ip": "203.0.113.77", "last_login_time": "2026-07-09 09:18:24"},
            },
            {
                "id": "vpn-session-alice-001",
                "type": "vpn_session",
                "name": "alice active vpn session",
                "owner": "alice",
                "user": "alice",
                "status": "online",
                "severity": "high",
                "ip": "10.60.8.11",
                "summary": "alice 当前 VPN 在线，会话源 IP 命中威胁情报",
                "metadata": {"session_id": "vpn-sess-0001", "source_ip": "203.0.113.77", "client": "macOS", "login_time": "2026-07-09 10:02:15"},
            },
            {
                "id": "vpn-user-carol",
                "type": "vpn_account",
                "name": "carol",
                "owner": "财务部",
                "user": "carol",
                "status": "enabled",
                "severity": "medium",
                "summary": "carol VPN 账号已启用",
                "metadata": {"mfa": False, "groups": ["vpn-users"], "last_login_ip": "198.51.100.23"},
            },
        ],
        "actions": [
            health_action(),
            action("query_login_status", "查询 VPN 用户登录状态", params=[p("username", "用户名", required=False, order=0), p("status", "状态", required=False, order=1)], filter_keys=["user", "name", "status"], sample={"username": "alice"}),
            action("query_online_users", "查询 VPN 在线用户", params=[p("username", "用户名", required=False, order=0), p("status", "登录状态", required=False, default="online", order=1), p("limit", "返回数量", "integer", False, 50, 2)], filter_keys=["user", "status"], sample={"username": "alice"}),
            action("create_vpn_account", "创建 VPN 账号", "write", "create", params=[p("username", "用户名", order=0), p("display_name", "显示名", False, "", 1), p("department", "部门", False, "未分配", 2)], result_status="enabled", sample={"username": "dave", "display_name": "Dave", "department": "安全运营"}),
            action("disable_vpn_account", "禁用 VPN 账号", "write", "write", params=[p("username", "用户名", order=0), p("reason", "禁用原因", False, "安全事件处置", 1)], filter_keys=["name", "user", "username"], result_status="disabled", sample={"username": "alice", "reason": "疑似账号失陷"}),
            action("enable_vpn_account", "启用 VPN 账号", "write", "write", params=[p("username", "用户名", order=0)], filter_keys=["name", "user", "username"], result_status="enabled", sample={"username": "alice"}),
            action("kick_vpn_user", "踢 VPN 用户下线", "write", "write", params=[p("username", "用户名", order=0), p("reason", "踢下线原因", False, "安全处置", 1)], filter_keys=["user", "name", "username"], result_status="offline", sample={"username": "alice", "reason": "异常公网 IP 登录"}),
            action("query_vpn_history", "查询 VPN 登录历史", operation="history", params=[p("username", "用户名", required=False, order=0), p("limit", "返回数量", "integer", False, 50, 1)], filter_keys=["username"], sample={"username": "alice"}),
        ],
    },
    {
        "name": "xsandbox",
        "dir": "shakespeare-action-python-xsandbox",
        "module": "xsandbox",
        "product_name": "XSandbox 文件沙箱",
        "description": "离线模拟沙箱分析平台，支持文件/URL 提交、分析报告和行为轨迹查询",
        "category": "安全产品",
        "letter": "B",
        "colors": ("#4a044e", "#e879f9"),
        "records": [
            {
                "id": "sandbox-44d8",
                "type": "file_analysis",
                "name": "invoice.exe",
                "status": "completed",
                "severity": "high",
                "indicator": "44d88612fea8a8f36de82e1278abb02f",
                "summary": "沙箱检测到持久化、下载器和 C2 连接行为",
                "metadata": {"score": 92, "behaviors": ["persistence", "network_c2", "process_injection"]},
            }
        ],
        "actions": [
            health_action(),
            action("submit_file", "提交文件样本", "write", "create", params=[p("file_hash", "文件 Hash", order=0), p("file_name", "文件名", False, "sample.bin", 1)], result_status="submitted", sample={"file_hash": "44d88612fea8a8f36de82e1278abb02f", "file_name": "invoice.exe"}),
            action("submit_url", "提交 URL 样本", "write", "create", params=[p("url", "URL", order=0)], result_status="submitted", sample={"url": "https://malicious.example/login"}),
            action("query_analysis_report", "查询分析报告", params=[p("sample_id", "样本 ID 或 Hash", order=0)], filter_keys=["id", "indicator", "sample_id", "file_hash"], sample={"sample_id": "44d88612fea8a8f36de82e1278abb02f"}),
            action("query_behavior_trace", "查询行为轨迹", params=[p("sample_id", "样本 ID 或 Hash", order=0)], filter_keys=["id", "indicator", "sample_id", "file_hash"], sample={"sample_id": "44d88612fea8a8f36de82e1278abb02f"}),
            COMMON_HISTORY_ACTION,
        ],
    },
    {
        "name": "xcloud",
        "dir": "shakespeare-action-python-xcloud",
        "module": "xcloud",
        "product_name": "XCloud 云平台",
        "description": "离线模拟云资产和安全组处置能力，支持云资产、安全组、封禁和快照",
        "category": "云服务",
        "letter": "C",
        "colors": ("#1e3a8a", "#93c5fd"),
        "records": [
            {
                "id": "ecs-prod-web-01",
                "type": "cloud_instance",
                "name": "prod-web-01",
                "ip": "10.10.8.23",
                "owner": "alice",
                "status": "running",
                "severity": "high",
                "summary": "云上 Web 服务器，绑定 sg-dmz-web",
                "metadata": {"region": "cn-example-1", "security_group": "sg-dmz-web", "instance_type": "c8.large"},
            },
            {
                "id": "sg-dmz-web",
                "type": "security_group",
                "name": "sg-dmz-web",
                "status": "active",
                "severity": "medium",
                "summary": "DMZ Web 安全组，允许 80/443",
                "metadata": {"rules": ["tcp/80", "tcp/443"], "blocked_ips": []},
            },
        ],
        "actions": [
            health_action(),
            action("query_cloud_assets", "查询云资产", params=[p("ip", "资产 IP", required=False, order=0), p("region", "云区域", required=False, order=1)], filter_keys=["ip", "metadata.region"], sample={"ip": "10.10.8.23"}),
            action("query_security_groups", "查询安全组", params=[p("security_group_id", "安全组 ID", required=False, order=0)], filter_keys=["id", "metadata.security_group", "security_group_id"], sample={"security_group_id": "sg-dmz-web"}),
            action("block_ip_in_security_group", "在安全组中封禁 IP", "write", "write", params=[p("security_group_id", "安全组 ID", order=0), p("ip", "需要封禁的 IP", order=1), p("reason", "封禁原因", False, "安全处置", 2)], filter_keys=["id", "security_group_id"], result_status="rule_updated", sample={"security_group_id": "sg-dmz-web", "ip": "203.0.113.77", "reason": "攻击源封禁"}),
            action("unblock_ip_in_security_group", "从安全组中解除 IP 封禁", "write", "write", params=[p("security_group_id", "安全组 ID", order=0), p("ip", "需要解封的 IP", order=1)], filter_keys=["id", "security_group_id"], result_status="rule_updated", sample={"security_group_id": "sg-dmz-web", "ip": "203.0.113.77"}),
            action("create_snapshot", "创建云主机快照", "write", "write", params=[p("instance_id", "云主机 ID", order=0), p("reason", "快照原因", False, "应急取证", 1)], filter_keys=["id", "instance_id"], result_status="snapshot_created", sample={"instance_id": "ecs-prod-web-01", "reason": "应急取证"}),
            COMMON_HISTORY_ACTION,
        ],
    },
]


MODULE_TEMPLATE = r'''# -*- coding: utf-8 -*-
import hashlib
import json
import os
import random
import sqlite3
import time
import uuid
from datetime import datetime


APP_NAME = {app_name!r}
PRODUCT_NAME = {product_name!r}
APP_DESCRIPTION = {description!r}
DEFAULT_RECORDS = json.loads({records_json!r})
ACTION_DEFINITIONS = json.loads({actions_json!r})


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _response(code=200, msg="", data=None, summary=None):
    return {{
        "code": code,
        "msg": msg,
        "data": data or {{}},
        "summary": summary or {{"statusCode": str(code), "msg": msg or "success"}},
    }}


def _db_path(assets):
    assets = assets or {{}}
    return assets.get("database_path") or f"/tmp/{{APP_NAME}}.db"


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
    metadata = record.get("metadata") or {{}}
    now = _now()
    cursor.execute(
        """
        INSERT OR REPLACE INTO records (
            id, record_type, name, ip, owner, user, status, severity,
            indicator, summary, metadata, created_time, updated_time
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            record.get("id") or f"{{APP_NAME}}-{{uuid.uuid4().hex[:10]}}",
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
            if item not in ("", None, [], {{}}):
                parts.append(f"{{key}}={{_compact_display_value(item)}}")
        return ",".join(parts)
    return str(value)


def _metadata_key_info(metadata):
    metadata = metadata or {{}}
    key_labels = {{
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
    }}
    preferred = list(key_labels)
    parts = []
    for key in preferred + [key for key in metadata if key not in preferred]:
        if key in ("last_params",):
            continue
        value = metadata.get(key)
        if value in ("", None, [], {{}}):
            continue
        label = key_labels.get(key, key)
        parts.append(f"{{label}}={{_compact_display_value(value)}}")
        if len(parts) >= 6:
            break
    return "；".join(parts)


def _record_from_row(row):
    metadata = {{}}
    if row["metadata"]:
        try:
            metadata = json.loads(row["metadata"])
        except Exception:
            metadata = {{"raw": row["metadata"]}}
    record = {{
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
    }}
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
        return " ".join(f"{{k}} {{_flatten(v)}}" for k, v in value.items())
    return str(value)


def _matches(record, params, filter_keys):
    params = params or {{}}
    active_filters = {{}}
    for key in filter_keys or []:
        param_key = key.split(".")[-1]
        param_aliases = {{
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
        }}
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
                {{"expected": str(raw).strip().lower(), "paths": []}},
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
    values = dict(params or {{}})
    for name, meta in (action_def.get("parameters") or {{}}).items():
        if name not in values and "default_value" in meta:
            values[name] = meta["default_value"]
    return values


def _limit(params, default=50):
    try:
        return max(1, min(int(params.get("limit", default)), 500))
    except Exception:
        return default


def _simulate_latency(assets):
    assets = assets or {{}}
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
    operation_id = f"op-{{datetime.now().strftime('%Y%m%d%H%M%S')}}-{{uuid.uuid4().hex[:8]}}"
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
            json.dumps(details or {{}}, ensure_ascii=False),
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
            (f"%{{target}}%", limit),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM operation_logs ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
    records = []
    for row in rows:
        details = {{}}
        if row["details"]:
            try:
                details = json.loads(row["details"])
            except Exception:
                details = {{"raw": row["details"]}}
        records.append({{
            "operation_id": row["id"],
            "action": row["action"],
            "target": row["target"],
            "status": row["status"],
            "reason": row["reason"],
            "affected_count": row["affected_count"],
            "latency_seconds": row["latency_seconds"],
            "timestamp": row["timestamp"],
            "details": details,
        }})
    return _response(data={{
        "result": f"查询到 {{len(records)}} 条操作历史",
        "records": records,
        "history_records": records,
        "total_count": len(records),
    }})


def _summary(records):
    by_status = {{}}
    by_severity = {{}}
    by_type = {{}}
    by_owner = {{}}
    by_user = {{}}
    for record in records:
        by_status[record["status"]] = by_status.get(record["status"], 0) + 1
        by_severity[record["severity"]] = by_severity.get(record["severity"], 0) + 1
        by_type[record["type"]] = by_type.get(record["type"], 0) + 1
        if record.get("owner"):
            by_owner[record["owner"]] = by_owner.get(record["owner"], 0) + 1
        if record.get("user"):
            by_user[record["user"]] = by_user.get(record["user"], 0) + 1
    return {{"status": by_status, "severity": by_severity, "type": by_type, "owner": by_owner, "user": by_user}}


def _health_check(params, assets, context_info):
    try:
        conn = _connect(assets)
        records = _all_records(conn)
        sample_values = {{
            "record_ids": sorted({{record["id"] for record in records if record.get("id")}})[:10],
            "owners": sorted({{record["owner"] for record in records if record.get("owner")}})[:10],
            "users": sorted({{record["user"] for record in records if record.get("user")}})[:10],
            "ips": sorted({{record["ip"] for record in records if record.get("ip")}})[:10],
            "indicators": sorted({{record["indicator"] for record in records if record.get("indicator")}})[:10],
        }}
        system_info = {{
            "product": PRODUCT_NAME,
            "version": "1.0.0",
            "status": "running",
            "database_path": _db_path(assets),
            "record_count": len(records),
            "scenario_profile": (assets or {{}}).get("scenario_profile", "default"),
            "sample_values": sample_values,
            "sample_records": records[:5],
            "components": [
                {{"name": "模拟数据引擎", "status": "running", "latency_ms": random.randint(8, 55)}},
                {{"name": "SQLite 状态库", "status": "connected", "path": _db_path(assets)}},
                {{"name": "动作执行器", "status": "ready", "queue_depth": random.randint(0, 5)}},
            ],
        }}
        conn.close()
        return _response(
            data={{"msg": f"{{PRODUCT_NAME}} 运行正常", "system_info": system_info}},
            summary={{"statusCode": "200", "msg": "健康检查成功"}},
        )
    except Exception as exc:
        return _response(
            code=500,
            msg=str(exc),
            data={{"msg": f"健康检查失败: {{exc}}", "system_info": {{}}}},
            summary={{"statusCode": "500", "msg": "健康检查失败"}},
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
    digest = hashlib.sha1(f"{{action_name}}:{{target}}".encode("utf-8")).hexdigest()[:10]
    metadata = dict(params or {{}})
    record_id = params.get("asset_id") or params.get("id") or f"{{APP_NAME}}-{{digest}}"
    record_type = params.get("asset_type") or params.get("indicator_type") or action_name
    if action_name == "create_asset" and not params.get("asset_id"):
        record_id = f"asset-{{digest}}"
    record = {{
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
        "summary": params.get("summary") or params.get("description") or params.get("message") or f"由 {{action_name}} 生成的模拟记录",
        "metadata": metadata,
    }}
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
    data = {{
        "result": f"查询完成，共 {{len(matches)}} 条匹配记录",
        "records": selected,
        "record": selected[0] if selected else {{}},
        "total_count": len(matches),
        "query": params,
        "statistics": _summary(matches),
    }}
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
        metadata = record.get("metadata") or {{}}
        if params.get("tag"):
            tags = metadata.get("tags") or []
            if not isinstance(tags, list):
                tags = [str(tags)]
            tag = str(params.get("tag")).strip()
            if tag and tag not in tags:
                tags.append(tag)
            metadata["tags"] = tags
            if params.get("value") is not None:
                tag_values = metadata.get("tag_values") or {{}}
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
        {{"params": params, "action": action_name}},
    )
    operation = {{
        "operation_id": operation_id,
        "action": action_name,
        "target": target,
        "status": new_status,
        "affected_count": len(updated_matches),
        "latency_seconds": latency,
        "timestamp": now,
    }}
    return _response(data={{
        "result": f"{{action_name}} 模拟执行完成，影响 {{len(updated_matches)}} 条记录",
        "operation": operation,
        "records": updated_matches,
        "affected_count": len(updated_matches),
    }})


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
    metadata = dict(metadata or {{}})
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
            tag_values = metadata.get("tag_values") or {{}}
            tag_values[tag] = params.get("value")
            metadata["tag_values"] = tag_values
    return metadata


def _update(conn, action_name, params, assets, action_def):
    latency = _simulate_latency(assets)
    records = _all_records(conn)
    matches = [record for record in records if _matches(record, params, action_def.get("filter_keys", []))]
    now = _now()
    for record in matches:
        metadata = _apply_metadata_params(record.get("metadata") or {{}}, params)
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
        {{"params": params, "action": action_name}},
    )
    operation = {{
        "operation_id": operation_id,
        "action": action_name,
        "target": target,
        "status": action_def.get("result_status") or params.get("status") or "updated",
        "affected_count": len(updated_matches),
        "latency_seconds": latency,
        "timestamp": now,
    }}
    return _response(data={{
        "result": f"{{action_name}} 更新完成，影响 {{len(updated_matches)}} 条记录",
        "operation": operation,
        "records": updated_matches,
        "affected_count": len(updated_matches),
    }})


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
        {{"params": params, "action": action_name, "deleted_ids": ids}},
    )
    operation = {{
        "operation_id": operation_id,
        "action": action_name,
        "target": target,
        "status": action_def.get("result_status") or "deleted",
        "affected_count": len(matches),
        "latency_seconds": latency,
        "timestamp": _now(),
    }}
    return _response(data={{
        "result": f"{{action_name}} 删除完成，影响 {{len(matches)}} 条记录",
        "operation": operation,
        "records": matches,
        "deleted_records": matches,
        "affected_count": len(matches),
    }})


def _create(conn, action_name, params, assets, action_def):
    latency = _simulate_latency(assets)
    status = action_def.get("result_status") or params.get("status") or "created"
    record = _synthetic_record(action_name, params, status)
    if action_name == "create_ticket":
        record["id"] = f"TCK-{{datetime.now().strftime('%Y%m%d')}}-{{uuid.uuid4().hex[:4].upper()}}"
        record["type"] = "security_ticket"
    if action_name == "create_asset":
        record["type"] = params.get("asset_type") or "asset"
        record["metadata"] = _apply_metadata_params(record.get("metadata") or {{}}, params)
        record["key_info"] = _metadata_key_info(record["metadata"])
    _insert_record(conn, record)
    target = record["id"]
    operation_id = _log_operation(conn, action_name, target, status, params.get("reason", ""), 1, latency, {{"params": params}})
    operation = {{
        "operation_id": operation_id,
        "action": action_name,
        "target": target,
        "status": status,
        "affected_count": 1,
        "latency_seconds": latency,
        "timestamp": _now(),
    }}
    return _response(data={{
        "result": f"{{action_name}} 创建模拟记录成功",
        "operation": operation,
        "record": record,
        "records": [record],
        "created_id": record["id"],
    }})


def _execute(action_name, params, assets, context_info):
    params = params or {{}}
    assets = assets or {{}}
    action_def = next((item for item in ACTION_DEFINITIONS if item["action"] == action_name), None)
    if not action_def:
        return _response(code=404, msg=f"未知动作: {{action_name}}", data={{"result": "动作不存在"}})
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
            result = _response(data={{
                "result": "统计摘要生成成功",
                "statistics": _summary(records),
                "records": records[:_limit(params, 20)],
                "total_count": len(records),
            }})
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
        return _response(code=500, msg=str(exc), data={{"result": f"{{action_name}} 执行失败: {{exc}}"}})


{function_defs}
'''


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
        "scenario_seed": {
            "data_type": "string",
            "description": "模拟数据种子，可用于固定演示场景",
            "default_value": "x-series-default",
            "required": False,
            "order": 2,
        },
        "delay_min_seconds": {
            "data_type": "integer",
            "description": "写入/处置动作的最小模拟延迟秒数",
            "default_value": 1,
            "required": False,
            "order": 3,
        },
        "delay_max_seconds": {
            "data_type": "integer",
            "description": "写入/处置动作的最大模拟延迟秒数",
            "default_value": 3,
            "required": False,
            "order": 4,
        },
    }
    actions = []
    for index, item in enumerate(spec["actions"]):
        op = item["operation"]
        outputs = [
            {"data_path": "action_result.code", "data_type": "integer", "description": "状态码"},
            {"data_path": "action_result.data.result", "data_type": "string", "description": "动作结果"},
        ]
        if op == "health":
            outputs.extend([
                {"data_path": "action_result.data.msg", "data_type": "string", "description": "健康检查信息"},
                {"data_path": "action_result.data.system_info", "data_type": "jsonobject", "description": "系统信息"},
            ])
        elif op in ("write", "create", "notify", "update", "delete"):
            outputs.extend([
                {"data_path": "action_result.data.operation", "data_type": "jsonobject", "description": "模拟操作信息"},
                {"data_path": "action_result.data.records", "data_type": "jsonarray", "description": "受影响记录"},
            ])
        elif op == "history":
            outputs.extend([
                {"data_path": "action_result.data.history_records", "data_type": "jsonarray", "description": "操作历史"},
                {"data_path": "action_result.data.total_count", "data_type": "integer", "description": "记录数量"},
            ])
        else:
            outputs.extend([
                {"data_path": "action_result.data.records", "data_type": "jsonarray", "description": "查询结果"},
                {"data_path": "action_result.data.total_count", "data_type": "integer", "description": "记录数量"},
                {"data_path": "action_result.data.statistics", "data_type": "jsonobject", "description": "统计信息"},
            ])
        actions.append({
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
        })
    return {
        "name": spec["name"],
        "description": spec["description"],
        "app_version": "1.0.0",
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


def build_module(spec):
    function_defs = []
    for item in spec["actions"]:
        function_defs.append(textwrap.dedent(f'''
            def {item["action"]}(params, assets, context_info):
                """{item["description"]}"""
                return _execute({item["action"]!r}, params, assets, context_info)
        ''').strip())
    actions_public = "\n\n\n".join(function_defs)
    return MODULE_TEMPLATE.format(
        app_name=spec["name"],
        product_name=spec["product_name"],
        description=spec["description"],
        records_json=json.dumps(spec["records"], ensure_ascii=False, indent=2),
        actions_json=json.dumps(spec["actions"], ensure_ascii=False, indent=2),
        function_defs=actions_public,
    )


def build_template(spec, item):
    title = f"{spec['product_name']} - {item['description']}"
    return f'''<div class="ant-table ant-table-default ant-table-bordered">
  <div class="ant-table-content">
    <div class="ant-table-body">
      {{% raw %}}{{{{each action_results action_result}}}}{{% endraw %}}
      <div style="margin-bottom: 16px;">
        <h3 style="color: #1890ff; margin-bottom: 8px;">{title}</h3>
        <div style="background: #f6ffed; padding: 12px; border-radius: 4px; margin-bottom: 12px;">
          <strong>执行结果: </strong>
          {{% raw %}}{{{{if action_result.code == 200}}}}{{% endraw %}}
            <span style="color: #52c41a;">{{% raw %}}{{{{action_result.data.result || action_result.data.msg || "成功"}}}}{{% endraw %}}</span>
          {{% raw %}}{{{{else}}}}{{% endraw %}}
            <span style="color: #f5222d;">{{% raw %}}{{{{action_result.msg}}}}{{% endraw %}}</span>
          {{% raw %}}{{{{/if}}}}{{% endraw %}}
        </div>
      </div>

      {{% raw %}}{{{{if action_result.data.operation}}}}{{% endraw %}}
      <table style="margin-bottom: 12px;">
        <thead class="ant-table-thead"><tr><th>操作项</th><th>值</th></tr></thead>
        <tbody class="ant-table-tbody">
          <tr><td>操作ID</td><td><code>{{% raw %}}{{{{action_result.data.operation.operation_id}}}}{{% endraw %}}</code></td></tr>
          <tr><td>目标</td><td>{{% raw %}}{{{{action_result.data.operation.target}}}}{{% endraw %}}</td></tr>
          <tr><td>状态</td><td>{{% raw %}}{{{{action_result.data.operation.status}}}}{{% endraw %}}</td></tr>
          <tr><td>影响记录</td><td>{{% raw %}}{{{{action_result.data.operation.affected_count}}}}{{% endraw %}}</td></tr>
          <tr><td>模拟耗时</td><td>{{% raw %}}{{{{action_result.data.operation.latency_seconds}}}}{{% endraw %}} 秒</td></tr>
        </tbody>
      </table>
      {{% raw %}}{{{{/if}}}}{{% endraw %}}

      {{% raw %}}{{{{if action_result.data.system_info}}}}{{% endraw %}}
      <table style="margin-bottom: 12px;">
        <thead class="ant-table-thead"><tr><th>系统信息</th><th>值</th></tr></thead>
        <tbody class="ant-table-tbody">
          <tr><td>产品</td><td>{{% raw %}}{{{{action_result.data.system_info.product}}}}{{% endraw %}}</td></tr>
          <tr><td>状态</td><td>{{% raw %}}{{{{action_result.data.system_info.status}}}}{{% endraw %}}</td></tr>
          <tr><td>记录数</td><td>{{% raw %}}{{{{action_result.data.system_info.record_count}}}}{{% endraw %}}</td></tr>
          <tr><td>数据库</td><td><code>{{% raw %}}{{{{action_result.data.system_info.database_path}}}}{{% endraw %}}</code></td></tr>
          <tr><td>样例负责人</td><td>{{% raw %}}{{{{action_result.data.system_info.sample_values.owners || "-"}}}}{{% endraw %}}</td></tr>
          <tr><td>样例用户</td><td>{{% raw %}}{{{{action_result.data.system_info.sample_values.users || "-"}}}}{{% endraw %}}</td></tr>
          <tr><td>样例 IP</td><td>{{% raw %}}{{{{action_result.data.system_info.sample_values.ips || "-"}}}}{{% endraw %}}</td></tr>
        </tbody>
      </table>
      {{% raw %}}{{{{/if}}}}{{% endraw %}}

      {{% raw %}}{{{{if action_result.data.records && action_result.data.records.length > 0}}}}{{% endraw %}}
      <table>
        <thead class="ant-table-thead">
          <tr><th>ID</th><th>类型</th><th>名称</th><th>负责人</th><th>用户/账号</th><th>IP/指标</th><th>状态</th><th>等级</th><th>关键信息</th><th>摘要</th></tr>
        </thead>
        <tbody class="ant-table-tbody">
          {{% raw %}}{{{{each action_result.data.records record}}}}{{% endraw %}}
          <tr class="ant-table-row">
            <td><code>{{% raw %}}{{{{record.id}}}}{{% endraw %}}</code></td>
            <td>{{% raw %}}{{{{record.type || "-"}}}}{{% endraw %}}</td>
            <td>{{% raw %}}{{{{record.name}}}}{{% endraw %}}</td>
            <td>{{% raw %}}{{{{record.owner || "-"}}}}{{% endraw %}}</td>
            <td>{{% raw %}}{{{{record.user || "-"}}}}{{% endraw %}}</td>
            <td>{{% raw %}}{{{{record.ip || record.indicator || "-"}}}}{{% endraw %}}</td>
            <td>{{% raw %}}{{{{record.status}}}}{{% endraw %}}</td>
            <td>{{% raw %}}{{{{record.severity}}}}{{% endraw %}}</td>
            <td>{{% raw %}}{{{{record.key_info || "-"}}}}{{% endraw %}}</td>
            <td>{{% raw %}}{{{{record.summary}}}}{{% endraw %}}</td>
          </tr>
          {{% raw %}}{{{{/each}}}}{{% endraw %}}
        </tbody>
      </table>
      {{% raw %}}{{{{else if action_result.data.total_count == 0}}}}{{% endraw %}}
      <div style="text-align: center; padding: 24px; color: #8c8c8c;">没有匹配记录</div>
      {{% raw %}}{{{{/if}}}}{{% endraw %}}
      {{% raw %}}{{{{/each}}}}{{% endraw %}}
    </div>
  </div>
</div>
'''.replace("{% raw %}", "").replace("{% endraw %}", "")


def build_logo(spec):
    bg, accent = spec["colors"]
    letter = spec["letter"]
    name = spec["product_name"]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512" role="img" aria-label="{name}">
  <rect width="512" height="512" rx="92" fill="{bg}"/>
  <path d="M256 54 404 118v112c0 95-59 178-148 228-89-50-148-133-148-228V118L256 54Z" fill="{accent}"/>
  <path d="M256 92 366 140v88c0 71-41 135-110 176-69-41-110-105-110-176v-88l110-48Z" fill="#ffffff" opacity="0.94"/>
  <circle cx="256" cy="256" r="92" fill="{bg}"/>
  <text x="256" y="292" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="116" font-weight="700" fill="#ffffff">{letter}</text>
  <path d="M134 414h244" stroke="#ffffff" stroke-width="24" stroke-linecap="round" opacity="0.72"/>
</svg>
'''


def compact_doc_value(value):
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return ",".join(str(item) for item in value)
    if isinstance(value, dict):
        parts = []
        for key, item in value.items():
            if item not in ("", None, [], {}):
                parts.append(f"{key}={compact_doc_value(item)}")
        return ",".join(parts)
    return str(value)


def metadata_key_info_for_doc(metadata):
    metadata = metadata or {}
    labels = {
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
    preferred = list(labels)
    parts = []
    for key in preferred + [key for key in metadata if key not in preferred]:
        value = metadata.get(key)
        if value in ("", None, [], {}):
            continue
        parts.append(f"{labels.get(key, key)}={compact_doc_value(value)}")
        if len(parts) >= 6:
            break
    return "；".join(parts) or "-"


def markdown_cell(value):
    return compact_doc_value(value).replace("|", "\\|").replace("\n", " ").strip() or "-"


def sample_params_for_doc(item):
    sample = sample_for_action(item)
    if not sample:
        return "-"
    return "`" + json.dumps(sample, ensure_ascii=False, separators=(",", ":")) + "`"


def build_readme(spec):
    rows = "\n".join(
        f"| `{item['action']}` | {item['classify']} | {sample_params_for_doc(item)} | {item['description']} |"
        for item in spec["actions"]
    )
    record_rows = "\n".join(
        "| `{id}` | {name} | {ip_or_indicator} | {owner} | {user} | {status} | {severity} | {key_info} | {summary} |".format(
            id=markdown_cell(record.get("id")),
            name=markdown_cell(record.get("name")),
            ip_or_indicator=markdown_cell(record.get("ip") or record.get("indicator")),
            owner=markdown_cell(record.get("owner")),
            user=markdown_cell(record.get("user")),
            status=markdown_cell(record.get("status")),
            severity=markdown_cell(record.get("severity")),
            key_info=markdown_cell(metadata_key_info_for_doc(record.get("metadata") or {})),
            summary=markdown_cell(record.get("summary")),
        )
        for record in spec["records"]
    )
    owners = sorted({record.get("owner") for record in spec["records"] if record.get("owner")})
    users = sorted({record.get("user") for record in spec["records"] if record.get("user")})
    ips = sorted({record.get("ip") for record in spec["records"] if record.get("ip")})
    indicators = sorted({record.get("indicator") for record in spec["records"] if record.get("indicator")})
    sample_values = []
    if owners:
        sample_values.append(f"- 负责人账号: {', '.join(f'`{owner}`' for owner in owners)}")
    if users:
        sample_values.append(f"- 用户/账号: {', '.join(f'`{user}`' for user in users)}")
    if ips:
        sample_values.append(f"- IP: {', '.join(f'`{ip}`' for ip in ips)}")
    if indicators:
        sample_values.append(f"- 指标: {', '.join(f'`{indicator}`' for indicator in indicators)}")
    sample_values_text = "\n".join(sample_values) or "- 当前应用无额外样例索引值"
    return f'''# {spec["product_name"]}

> 版本: v1.0.0
> 供应商: {SUPPLIER}
> 类型: 离线模拟产品

## 应用简介

{spec["description"]}。本应用不连接任何外部系统，所有动作均基于本地 SQLite 状态库和内置样例数据执行，适合开箱即用的 SOAR 剧本演示、培训和 PoC。

## 配置参数

- `database_path`: SQLite 模拟状态库路径，默认 `/tmp/{spec["name"]}.db`
- `scenario_profile`: 模拟场景名称，默认 `default`
- `scenario_seed`: 模拟数据种子，默认 `x-series-default`
- `delay_min_seconds`: 写入/处置动作最小模拟延迟秒数，默认 `1`
- `delay_max_seconds`: 写入/处置动作最大模拟延迟秒数，默认 `3`

## 动作列表

| 动作 | 类型 | 示例参数 | 说明 |
|---|---|---|---|
{rows}

## 内置样例索引

以下值可以直接用于动作参数测试，不需要连接外部系统。

{sample_values_text}

## 内置样例数据

| ID | 名称 | IP/指标 | 负责人 | 用户/账号 | 状态 | 等级 | 关键信息 | 摘要 |
|---|---|---|---|---|---|---|---|---|
{record_rows}

## 返回结构

所有动作统一返回 `code`、`msg`、`data`、`summary`。查询类动作返回 `records`、`record`、`total_count` 和 `statistics`；写入、通知、创建、更新和删除类动作返回 `operation`、`records` 和 `affected_count`；健康检查返回 `system_info`，其中包含 `sample_values` 和 `sample_records` 便于发现可用样例值。

## 适用剧本

- 安全告警查询、研判和上下文补全
- 恶意 IP、账号、主机、邮件、文件的模拟处置
- 工单、通知和审计留痕演示
- 无真实安全设备或 SaaS 服务时的产品体验与编排训练
'''


def sample_for_action(item):
    if item.get("sample"):
        return item["sample"]
    sample = {}
    for name, meta in item.get("parameters", {}).items():
        if meta.get("required"):
            dtype = meta.get("data_type")
            sample[name] = 10 if dtype == "integer" else f"sample_{name}"
    return sample


def build_test(spec):
    imports = ", ".join(item["action"] for item in spec["actions"])
    cases = [(item["action"], sample_for_action(item)) for item in spec["actions"]]
    cases_json = json.dumps(cases, ensure_ascii=False, indent=4)
    extra_methods = ""
    if spec["name"] == "xasset":
        extra_methods = '''
    def test_owner_query_returns_owner_context(self):
        ret = query_assets_by_owner({"owner": "carol"}, self.assets, self.context)
        self.assertEqual(ret["code"], 200)
        self.assertEqual(ret["data"]["total_count"], 1)
        record = ret["data"]["records"][0]
        self.assertEqual(record["owner"], "carol")
        self.assertIn("财务部", record["key_info"])

    def test_asset_crud_roundtrip(self):
        created = create_asset({
            "asset_id": "asset-unit-01",
            "asset_name": "unit-server-01",
            "ip": "10.99.1.10",
            "asset_type": "server",
            "owner": "secops",
            "status": "online",
            "summary": "单元测试新增资产"
        }, self.assets, self.context)
        self.assertEqual(created["code"], 200)
        self.assertEqual(created["data"]["created_id"], "asset-unit-01")

        queried = query_asset_by_ip({"ip": "10.99.1.10"}, self.assets, self.context)
        self.assertEqual(queried["data"]["total_count"], 1)
        self.assertEqual(queried["data"]["records"][0]["owner"], "secops")

        updated = update_asset({
            "asset_id": "asset-unit-01",
            "owner": "alice",
            "status": "maintenance",
            "severity": "low"
        }, self.assets, self.context)
        self.assertEqual(updated["code"], 200)
        self.assertEqual(updated["data"]["affected_count"], 1)
        self.assertEqual(updated["data"]["records"][0]["owner"], "alice")
        self.assertEqual(updated["data"]["records"][0]["status"], "maintenance")

        deleted = delete_asset({"asset_id": "asset-unit-01", "reason": "unit cleanup"}, self.assets, self.context)
        self.assertEqual(deleted["code"], 200)
        self.assertEqual(deleted["data"]["affected_count"], 1)

        missing = query_asset_by_ip({"ip": "10.99.1.10"}, self.assets, self.context)
        self.assertEqual(missing["data"]["total_count"], 0)
'''
    return f'''# -*- coding: utf-8 -*-
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from {spec["module"]} import {imports}


ACTION_CASES = {cases_json}


class Test{spec["name"].title().replace("_", "")}(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.assets = {{
            "database_path": os.path.join(self.tmpdir.name, "{spec["name"]}.db"),
            "delay_min_seconds": 0,
            "delay_max_seconds": 0,
            "scenario_profile": "unit-test",
        }}
        self.context = {{}}

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_health_check(self):
        ret = health_check({{}}, self.assets, self.context)
        self.assertEqual(ret["code"], 200)
        self.assertEqual(ret["summary"]["statusCode"], "200")
        self.assertGreaterEqual(ret["data"]["system_info"]["record_count"], 1)

    def test_all_actions_return_success(self):
        for action_name, params in ACTION_CASES:
            with self.subTest(action=action_name):
                func = globals()[action_name]
                ret = func(params, self.assets, self.context)
                self.assertEqual(ret["code"], 200)
                self.assertIn("data", ret)

{extra_methods}

if __name__ == "__main__":
    unittest.main()
'''


def write_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def generate_app(spec):
    app_dir = ROOT / spec["dir"]
    write_file(app_dir / "config.json", json.dumps(build_config(spec), ensure_ascii=False, indent=4) + "\n")
    write_file(app_dir / f"{spec['module']}.py", build_module(spec))
    write_file(app_dir / "resources" / "readme.md", build_readme(spec))
    write_file(app_dir / "resources" / f"{spec['name']}_logo.svg", build_logo(spec))
    write_file(app_dir / f"test_{spec['module']}.py", build_test(spec))
    for item in spec["actions"]:
        write_file(app_dir / "shakespeare-action-template" / f"{item['action']}.art", build_template(spec, item))


def main():
    for spec in APP_SPECS:
        generate_app(spec)
    print(f"Generated {len(APP_SPECS)} X-series simulated apps.")


if __name__ == "__main__":
    main()
