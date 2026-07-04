# -*- coding: utf-8 -*-
import json
import sqlite3
import time
import os
import ipaddress
import uuid
from datetime import datetime, timedelta
import hashlib
import random


class XFirewallDB:
    """XFirewall 数据库管理类"""

    def __init__(self, db_path="/tmp/xfirewall.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """初始化数据库表"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建封禁规则表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blocked_ips (
                id TEXT PRIMARY KEY,
                ip_address TEXT NOT NULL,
                reason TEXT NOT NULL,
                created_time TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                rule_hash TEXT UNIQUE
            )
        ''')

        # 创建操作日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS operation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_type TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                reason TEXT,
                operator TEXT DEFAULT 'system',
                timestamp TEXT NOT NULL,
                result TEXT NOT NULL
            )
        ''')

        conn.commit()
        conn.close()

    def add_blocked_ip(self, ip, reason):
        """添加封禁 IP"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        rule_id = str(uuid.uuid4())
        created_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        rule_hash = hashlib.md5(f"{ip}:{reason}".encode()).hexdigest()

        try:
            cursor.execute('''
                INSERT INTO blocked_ips (id, ip_address, reason, created_time, rule_hash)
                VALUES (?, ?, ?, ?, ?)
            ''', (rule_id, ip, reason, created_time, rule_hash))

            # 记录操作日志
            cursor.execute('''
                INSERT INTO operation_logs (operation_type, ip_address, reason, timestamp, result)
                VALUES (?, ?, ?, ?, ?)
            ''', ('block', ip, reason, created_time, 'success'))

            conn.commit()
            return rule_id

        except sqlite3.IntegrityError:
            # IP 已经存在相同的封禁规则
            cursor.execute('''
                SELECT id FROM blocked_ips WHERE rule_hash = ? AND status = 'active'
            ''', (rule_hash,))
            existing = cursor.fetchone()
            if existing:
                return existing[0]
            else:
                raise
        finally:
            conn.close()

    def remove_blocked_ip(self, ip):
        """移除封禁 IP"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 先查询匹配的记录用于调试
        cursor.execute('''
            SELECT ip_address, status FROM blocked_ips WHERE ip_address = ? AND status = 'active'
        ''', (ip,))
        matching_records = cursor.fetchall()

        # 执行更新
        cursor.execute('''
            UPDATE blocked_ips SET status = 'removed' WHERE ip_address = ? AND status = 'active'
        ''', (ip,))

        affected_rows = cursor.rowcount

        # 记录操作日志（包含调试信息）
        log_result = 'success' if affected_rows > 0 else f'no_match_found_for_{repr(ip)}_matches_{len(matching_records)}'
        cursor.execute('''
            INSERT INTO operation_logs (operation_type, ip_address, timestamp, result)
            VALUES (?, ?, ?, ?)
        ''', ('unblock', ip, current_time, log_result))

        conn.commit()
        conn.close()

        return affected_rows

    def get_blocked_ips(self, limit=100):
        """获取当前封禁的 IP 列表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 获取活跃的封禁记录（使用rowid确保一致的排序）
        cursor.execute('''
            SELECT ip_address, reason, created_time, id
            FROM blocked_ips
            WHERE status = 'active'
            ORDER BY created_time DESC, rowid DESC
            LIMIT ?
        ''', (limit,))

        results = cursor.fetchall()

        # 获取总数
        cursor.execute('''
            SELECT COUNT(*) FROM blocked_ips WHERE status = 'active'
        ''')
        total_count = cursor.fetchone()[0]

        conn.close()

        blocked_ips = []
        for row in results:
            blocked_ips.append({
                'ip_address': row[0],
                'reason': row[1],
                'created_time': row[2],
                'rule_id': row[3]
            })

        return blocked_ips, total_count

    def get_operation_history(self, ip=None, start_time=None, end_time=None, limit=100):
        """获取操作历史"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = '''
            SELECT operation_type, ip_address, reason, operator, timestamp, result
            FROM operation_logs
            WHERE 1=1
        '''
        params = []

        if ip:
            query += ' AND ip_address = ?'
            params.append(ip)

        if start_time:
            query += ' AND timestamp >= ?'
            params.append(start_time)

        if end_time:
            query += ' AND timestamp <= ?'
            params.append(end_time)

        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)

        cursor.execute(query, params)
        results = cursor.fetchall()

        # 获取总数
        count_query = query.replace('SELECT operation_type, ip_address, reason, operator, timestamp, result', 'SELECT COUNT(*)')
        count_query = count_query.replace('ORDER BY timestamp DESC LIMIT ?', '')
        cursor.execute(count_query, params[:-1])
        total_count = cursor.fetchone()[0]

        conn.close()

        history = []
        for row in results:
            history.append({
                'operation_type': row[0],
                'ip_address': row[1],
                'reason': row[2],
                'operator': row[3],
                'timestamp': row[4],
                'result': row[5]
            })

        return history, total_count


def validate_ip_address(ip):
    """验证 IP 地址格式"""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def create_response(code=200, msg="", data=None, summary=None):
    """创建标准响应格式"""
    return {
        "code": code,
        "msg": msg,
        "data": data or {},
        "summary": summary or {}
    }


def simulate_firewall_latency(assets):
    """模拟防火墙控制面提交策略时的响应延迟"""
    min_delay = float(assets.get("delay_min_seconds", 1))
    max_delay = float(assets.get("delay_max_seconds", 3))
    if min_delay < 0:
        min_delay = 0
    if max_delay < min_delay:
        max_delay = min_delay

    delay_seconds = round(random.uniform(min_delay, max_delay), 2)
    if delay_seconds > 0:
        time.sleep(delay_seconds)
    return delay_seconds


def build_policy_commit_info(operation, delay_seconds):
    """生成模拟策略下发信息，让防火墙操作结果更接近真实设备。"""
    return {
        "operation": operation,
        "commit_id": f"commit-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}",
        "policy_engine": "XFirewall Policy Engine",
        "sync_status": random.choice(["committed", "committed", "distributed"]),
        "device_node": random.choice(["fw-node-a", "fw-node-b", "fw-node-c"]),
        "latency_seconds": delay_seconds
    }


def build_firewall_status(total_blocked=0, database_status="connected", database_path="/tmp/xfirewall.db"):
    """构造防火墙健康状态，模拟设备运行指标和安全组件状态。"""
    cpu_usage = round(random.uniform(8.0, 42.0), 1)
    memory_usage = round(random.uniform(38.0, 76.0), 1)
    session_usage = round(random.uniform(16.0, 68.0), 1)
    threat_db_age_minutes = random.randint(3, 45)

    status = "running"
    health_level = "healthy"
    if cpu_usage > 85 or memory_usage > 85 or database_status != "connected":
        status = "degraded"
        health_level = "warning"

    components = [
        {"name": "管理平面", "status": "running", "latency_ms": random.randint(12, 60)},
        {"name": "策略引擎", "status": "running", "latency_ms": random.randint(25, 120)},
        {"name": "威胁情报库", "status": "synced", "last_update": f"{threat_db_age_minutes} 分钟前"},
        {"name": "日志管道", "status": "running", "queue_depth": random.randint(0, 20)},
        {"name": "本地规则库", "status": database_status, "path": database_path}
    ]

    return {
        "version": "XFirewall v1.0.2",
        "status": status,
        "health_level": health_level,
        "uptime": f"{random.randint(7, 31)} days, {random.randint(0, 23)} hours, {random.randint(0, 59)} minutes",
        "total_blocked_ips": total_blocked,
        "cpu_usage": f"{cpu_usage}%",
        "memory_usage": f"{memory_usage}%",
        "session_usage": f"{session_usage}%",
        "active_sessions": random.randint(12000, 88000),
        "policy_revision": random.randint(1200, 9999),
        "threat_db_version": datetime.now().strftime("TI-%Y%m%d"),
        "database_status": database_status,
        "database_path": database_path,
        "components": components
    }


def block_ip(params, assets, context_info):
    """封禁 IP 地址"""
    try:
        # 获取参数
        ip = params["ip"].strip()
        reason = params.get("reason", "安全策略封禁")

        # 验证 IP 地址格式
        if not validate_ip_address(ip):
            return create_response(
                code=400,
                msg="无效的 IP 地址格式",
                data={"result": "无效的 IP 地址格式"}
            )

        # 获取数据库路径
        db_path = assets.get("database_path", "/tmp/xfirewall.db")
        db = XFirewallDB(db_path)

        # 模拟防火墙策略提交和分发耗时
        delay_seconds = simulate_firewall_latency(assets)

        # 添加封禁规则
        rule_id = db.add_blocked_ip(ip, reason)
        policy_commit = build_policy_commit_info("block", delay_seconds)

        result_msg = f"IP {ip} 封禁成功"

        return create_response(
            data={
                "result": result_msg,
                "rule_id": rule_id,
                "policy_commit": policy_commit,
                "debug_info": {
                    "database_path": db_path,
                    "ip_blocked": ip,
                    "simulated_latency_seconds": delay_seconds,
                    "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            }
        )

    except Exception as e:
        return create_response(
            code=500,
            msg=str(e),
            data={"result": f"封禁失败：{str(e)}"}
        )


def unblock_ip(params, assets, context_info):
    """解封 IP 地址"""
    try:
        # 获取参数
        original_ip = params["ip"]
        ip = original_ip.strip()

        # 验证 IP 地址格式
        if not validate_ip_address(ip):
            return create_response(
                code=400,
                msg="无效的 IP 地址格式",
                data={"result": "无效的 IP 地址格式"}
            )

        # 获取数据库路径
        db_path = assets.get("database_path", "/tmp/xfirewall.db")
        db = XFirewallDB(db_path)

        # 模拟防火墙策略提交和分发耗时
        delay_seconds = simulate_firewall_latency(assets)

        # 移除封禁规则
        unblocked_count = db.remove_blocked_ip(ip)
        policy_commit = build_policy_commit_info("unblock", delay_seconds)

        if unblocked_count > 0:
            result_msg = f"IP {ip} 解封成功，移除了 {unblocked_count} 条规则"
        else:
            # 添加调试信息
            debug_info = f"(原始输入: {repr(original_ip)}, 处理后: {repr(ip)})"
            result_msg = f"IP {ip} 没有找到活跃的封禁规则 {debug_info}"

        return create_response(
            data={
                "result": result_msg,
                "unblocked_count": unblocked_count,
                "policy_commit": policy_commit,
                "debug_info": {
                    "database_path": db_path,
                    "simulated_latency_seconds": delay_seconds,
                    "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            }
        )

    except Exception as e:
        return create_response(
            code=500,
            msg=str(e),
            data={"result": f"解封失败：{str(e)}"}
        )


def query_blocked_ips(params, assets, context_info):
    """查询当前封禁的 IP 列表"""
    try:
        # 获取参数
        limit = params.get("limit", 100)

        # 获取数据库路径
        db_path = assets.get("database_path", "/tmp/xfirewall.db")
        db = XFirewallDB(db_path)

        # 获取封禁 IP 列表
        blocked_ips, total_count = db.get_blocked_ips(limit)

        return create_response(
            data={
                "blocked_ips": blocked_ips,
                "total_count": total_count,
                "debug_info": {
                    "database_path": db_path,
                    "query_limit": limit,
                    "records_found": len(blocked_ips)
                }
            }
        )

    except Exception as e:
        return create_response(
            code=500,
            msg=str(e),
            data={"blocked_ips": [], "total_count": 0}
        )


def query_block_history(params, assets, context_info):
    """查询封禁历史记录"""
    try:
        # 获取参数
        ip = params.get("ip", "").strip() or None
        start_time = params.get("start_time", "").strip() or None
        end_time = params.get("end_time", "").strip() or None
        limit = params.get("limit", 100)

        # 验证 IP 地址格式（如果提供了的话）
        if ip and not validate_ip_address(ip):
            return create_response(
                code=400,
                msg="无效的 IP 地址格式",
                data={"history_records": [], "total_count": 0}
            )

        # 获取数据库路径
        db_path = assets.get("database_path", "/tmp/xfirewall.db")
        db = XFirewallDB(db_path)

        # 获取历史记录
        history, total_count = db.get_operation_history(ip, start_time, end_time, limit)

        return create_response(
            data={
                "history_records": history,
                "total_count": total_count
            }
        )

    except Exception as e:
        return create_response(
            code=500,
            msg=str(e),
            data={"history_records": [], "total_count": 0}
        )


def health_check(params, assets, context_info):
    """健康检查"""
    try:
        # 获取数据库路径
        db_path = assets.get("database_path", "/tmp/xfirewall.db")

        # 检查数据库连接
        db = XFirewallDB(db_path)
        blocked_ips, total_blocked = db.get_blocked_ips(1)

        # 模拟系统信息
        system_info = build_firewall_status(total_blocked, "connected", db_path)

        return create_response(
            data={
                "msg": "XFirewall 运行正常",
                "system_info": system_info
            },
            summary={
                "statusCode": "200",
                "msg": "健康检查成功"
            }
        )

    except Exception as e:
        return create_response(
            code=500,
            msg=str(e),
            data={
                "msg": f"健康检查失败：{str(e)}",
                "system_info": {}
            },
            summary={
                "statusCode": "500",
                "msg": "健康检查失败"
            }
        )


def query_firewall_status(params, assets, context_info):
    """查询防火墙运行状态和关键组件状态"""
    try:
        db_path = assets.get("database_path", "/tmp/xfirewall.db")
        db = XFirewallDB(db_path)
        blocked_ips, total_blocked = db.get_blocked_ips(1)
        system_info = build_firewall_status(total_blocked, "connected", db_path)

        return create_response(
            data={
                "status": system_info["status"],
                "health_level": system_info["health_level"],
                "system_info": system_info,
                "components": system_info["components"]
            },
            summary={
                "statusCode": "200",
                "msg": "防火墙状态查询成功"
            }
        )

    except Exception as e:
        system_info = build_firewall_status(0, "disconnected", assets.get("database_path", "/tmp/xfirewall.db"))
        return create_response(
            code=500,
            msg=str(e),
            data={
                "status": "degraded",
                "health_level": "warning",
                "system_info": system_info,
                "components": system_info["components"]
            },
            summary={
                "statusCode": "500",
                "msg": "防火墙状态查询失败"
            }
        )