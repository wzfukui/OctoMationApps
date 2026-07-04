# -*- coding: utf-8 -*-
import csv
import os


CSV_ASSET_KEYS = ("cmdb_csv_file", "csv_file", "file", "cmdb_file")


FIELD_ALIASES = {
    "ip": ("ip", "ip_address", "asset_ip", "host_ip", "ipv4"),
    "hostname": ("hostname", "host_name", "asset_name", "device_name", "name"),
    "owner_name": ("owner_name", "owner", "user_name", "username", "姓名", "负责人"),
    "owner_id": ("owner_id", "owner_ad_id", "ad_account", "ad_id", "account", "user_id"),
    "mobile": ("mobile", "phone", "telephone", "tel", "手机号", "电话"),
    "email": ("email", "mail", "邮箱"),
    "department": ("department", "dept", "部门"),
    "ad_account": ("ad_account", "ad_id", "account", "owner_id", "owner_ad_id"),
    "wechat_work_id": ("wechat_work_id", "wework_id", "wechat", "企业微信"),
    "asset_type": ("asset_type", "type", "资产类型"),
    "location": ("location", "位置"),
    "status": ("status", "状态"),
}


def _result(data=None, status_code=0, msg=""):
    return {
        "code": 200 if status_code == 0 else 400,
        "msg": msg,
        "data": data or {},
        "summary": {
            "statusCode": status_code,
            "msg": msg,
        },
    }


def _normalize_key(value):
    return str(value or "").strip().lower()


def _get_csv_path(params, assets):
    for source in (assets or {}, params or {}):
        for key in CSV_ASSET_KEYS:
            value = source.get(key)
            if value:
                return str(value).strip()
    return ""


def _get_by_alias(row, canonical_name):
    for field_name in FIELD_ALIASES.get(canonical_name, (canonical_name,)):
        if field_name in row and row[field_name] is not None:
            return str(row[field_name]).strip()
    return ""


def _normalize_row(row):
    normalized = {str(key).strip(): ("" if value is None else str(value).strip()) for key, value in row.items()}
    asset = dict(normalized)

    for canonical_name in FIELD_ALIASES:
        asset[canonical_name] = _get_by_alias(normalized, canonical_name)

    if not asset.get("owner_id"):
        asset["owner_id"] = asset.get("ad_account", "")
    if not asset.get("ad_account"):
        asset["ad_account"] = asset.get("owner_id", "")

    return asset


def _read_cmdb_rows(csv_path):
    if not csv_path:
        raise ValueError("CMDB CSV file is not configured")
    if not os.path.isfile(csv_path):
        raise ValueError("CMDB CSV file does not exist: {}".format(csv_path))

    rows = []
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if not reader.fieldnames:
            raise ValueError("CMDB CSV file has no header")

        for row in reader:
            asset = _normalize_row(row)
            if any(asset.values()):
                rows.append(asset)

    return rows


def _owner_from_asset(asset):
    return {
        "owner_id": asset.get("owner_id", ""),
        "owner_name": asset.get("owner_name", ""),
        "ad_account": asset.get("ad_account", ""),
        "email": asset.get("email", ""),
        "mobile": asset.get("mobile", ""),
        "department": asset.get("department", ""),
        "wechat_work_id": asset.get("wechat_work_id", ""),
    }


def health_check(params, assets, context_info):
    csv_path = _get_csv_path(params, assets)
    try:
        rows = _read_cmdb_rows(csv_path)
        msg = "CMDB CSV 文件可读取，共 {} 条资产记录".format(len(rows))
        return _result({
            "status": "ok",
            "msg": msg,
            "csv_file": csv_path,
            "asset_count": len(rows),
        }, msg=msg)
    except Exception as e:
        msg = str(e)
        return _result({
            "status": "error",
            "msg": msg,
            "csv_file": csv_path,
            "asset_count": 0,
        }, status_code=400, msg=msg)


def query_owner_by_ip(params, assets, context_info):
    ip = str(params.get("ip", "")).strip()
    if not ip:
        return _result({"matched": False, "ip": ip}, status_code=400, msg="ip is required")

    try:
        rows = _read_cmdb_rows(_get_csv_path(params, assets))
    except Exception as e:
        return _result({"matched": False, "ip": ip}, status_code=400, msg=str(e))

    for asset in rows:
        if asset.get("ip") == ip:
            return _result({
                "matched": True,
                "ip": ip,
                "owner": _owner_from_asset(asset),
                "asset": asset,
                "owner_id": asset.get("owner_id", ""),
                "owner_name": asset.get("owner_name", ""),
                "ad_account": asset.get("ad_account", ""),
                "email": asset.get("email", ""),
                "mobile": asset.get("mobile", ""),
                "department": asset.get("department", ""),
                "wechat_work_id": asset.get("wechat_work_id", ""),
            })

    return _result({
        "matched": False,
        "ip": ip,
        "owner": {},
        "asset": {},
    })


def query_assets_by_ad_id(params, assets, context_info):
    ad_account = str(params.get("ad_account", params.get("owner_id", ""))).strip()
    if not ad_account:
        return _result({"matched": False, "assets": [], "count": 0}, status_code=400, msg="ad_account is required")

    try:
        rows = _read_cmdb_rows(_get_csv_path(params, assets))
    except Exception as e:
        return _result({"matched": False, "assets": [], "count": 0}, status_code=400, msg=str(e))

    normalized_ad_account = _normalize_key(ad_account)
    matched_assets = [
        asset for asset in rows
        if _normalize_key(asset.get("ad_account")) == normalized_ad_account
        or _normalize_key(asset.get("owner_id")) == normalized_ad_account
    ]
    owner = _owner_from_asset(matched_assets[0]) if matched_assets else {}

    return _result({
        "matched": bool(matched_assets),
        "ad_account": ad_account,
        "owner": owner,
        "assets": matched_assets,
        "count": len(matched_assets),
    })
