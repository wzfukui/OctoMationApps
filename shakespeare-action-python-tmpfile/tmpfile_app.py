# -*- coding: utf-8 -*-
"""
tmpfile.link Octomation App
支持匿名/认证两种方式上传本地文件或文本内容到 tmpfile.link，返回 URL 编码后的下载链接。

API 文档:
  POST https://tmpfile.link/api/upload
  - 匿名上传: 直接 POST multipart/form-data, 字段名 "file"
  - 认证上传: 附加请求头 X-User-Id 和 X-Auth-Token
  - 响应 JSON: { fileName, downloadLink, downloadLinkEncoded, size, type, uploadedTo }
  - 文件大小上限: 100MB
  - 匿名文件保留: 7 天
"""
import os
import json
import tempfile
import requests


# ─────────────────────────────────────────
# 内部工具函数
# ─────────────────────────────────────────

def _build_headers(assets: dict) -> dict:
    """根据 assets 中是否有认证信息构建请求头。"""
    headers = {}
    user_id = assets.get("user_id", "").strip()
    auth_token = assets.get("auth_token", "").strip()
    if user_id and auth_token:
        headers["X-User-Id"] = user_id
        headers["X-Auth-Token"] = auth_token
    return headers


def _do_upload(file_path: str, file_name: str, headers: dict) -> dict:
    """
    执行文件上传，返回标准化的结果字典。
    若上传失败，抛出异常。
    """
    url = "https://tmpfile.link/api/upload"
    with open(file_path, "rb") as f:
        resp = requests.post(
            url,
            headers=headers,
            files={"file": (file_name, f)},
            timeout=60
        )
    resp.raise_for_status()
    resp_json = resp.json()
    return {
        "file_name": resp_json.get("fileName", file_name),
        "download_link": resp_json.get("downloadLink", ""),
        "download_link_encoded": resp_json.get("downloadLinkEncoded", ""),
        "file_size": resp_json.get("size", 0),
        "file_type": resp_json.get("type", ""),
        "uploaded_to": resp_json.get("uploadedTo", "public"),
    }


# ─────────────────────────────────────────
# Action: upload_file
# ─────────────────────────────────────────

def upload_file(params, assets, context_info):
    """上传本地文件到 tmpfile.link，返回下载链接（含 URL 编码版本）。"""

    # ── 参数读取 ──
    file_path = params.get("file_path", "").strip()

    # ── 返回值骨架 ──
    json_ret = {
        "code": 200,
        "msg": "",
        "data": {
            "file_name": "",
            "download_link": "",
            "download_link_encoded": "",
            "file_size": 0,
            "file_type": "",
            "uploaded_to": "",
        }
    }

    # ── 参数校验 ──
    if not file_path:
        json_ret["code"] = 400
        json_ret["msg"] = "file_path 参数不能为空"
        return json_ret

    if not os.path.isfile(file_path):
        json_ret["code"] = 404
        json_ret["msg"] = f"文件不存在：{file_path}"
        return json_ret

    file_size_bytes = os.path.getsize(file_path)
    if file_size_bytes > 100 * 1024 * 1024:
        json_ret["code"] = 413
        json_ret["msg"] = f"文件超过 100MB 限制，当前大小：{file_size_bytes} 字节"
        return json_ret

    # ── 执行上传 ──
    file_name = os.path.basename(file_path)
    headers = _build_headers(assets)

    try:
        result = _do_upload(file_path, file_name, headers)
        json_ret["data"].update(result)
    except requests.HTTPError as e:
        json_ret["code"] = e.response.status_code if e.response else 500
        json_ret["msg"] = f"上传失败（HTTP错误）：{str(e)}"
    except Exception as e:
        json_ret["code"] = 500
        json_ret["msg"] = f"上传失败：{str(e)}"

    return json_ret


# ─────────────────────────────────────────
# Action: upload_text
# ─────────────────────────────────────────

def upload_text(params, assets, context_info):
    """将文本内容保存为临时文件，上传到 tmpfile.link，返回下载链接。"""

    # ── 参数读取 ──
    content = params.get("content", "")
    file_name = params.get("file_name", "content.txt").strip() or "content.txt"

    # ── 返回值骨架 ──
    json_ret = {
        "code": 200,
        "msg": "",
        "data": {
            "file_name": "",
            "download_link": "",
            "download_link_encoded": "",
            "file_size": 0,
            "file_type": "",
            "uploaded_to": "",
        }
    }

    # ── 参数校验 ──
    if not content:
        json_ret["code"] = 400
        json_ret["msg"] = "content 参数不能为空"
        return json_ret

    # ── 写入临时文件并上传 ──
    headers = _build_headers(assets)
    tmp_file = None
    try:
        # 使用 NamedTemporaryFile，确保文件名正确传递
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=f"_{file_name}",
            delete=False,
            encoding="utf-8"
        ) as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name

        result = _do_upload(tmp_path, file_name, headers)
        json_ret["data"].update(result)
        # 用户指定的文件名覆盖临时文件名
        json_ret["data"]["file_name"] = result["file_name"] if result["file_name"] != os.path.basename(tmp_path) else file_name

    except requests.HTTPError as e:
        json_ret["code"] = e.response.status_code if e.response else 500
        json_ret["msg"] = f"上传失败（HTTP错误）：{str(e)}"
    except Exception as e:
        json_ret["code"] = 500
        json_ret["msg"] = f"上传失败：{str(e)}"
    finally:
        # 清理临时文件
        if tmp_file and os.path.exists(tmp_file.name):
            try:
                os.unlink(tmp_file.name)
            except Exception:
                pass

    return json_ret


# ─────────────────────────────────────────
# Action: health_check
# ─────────────────────────────────────────

def health_check(params, assets, context_info):
    """健康检查：上传一个极小的测试文件，验证 tmpfile.link 服务可达。"""

    json_ret = {
        "code": 200,
        "msg": "",
        "data": {"msg": ""},
        "summary": {"statusCode": 200, "msg": "健康检查成功"}
    }

    headers = _build_headers(assets)
    tmp_file = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix="_octomation_health.txt",
            delete=False,
            encoding="utf-8"
        ) as tmp_file:
            tmp_file.write("Octomation tmpfile health check")
            tmp_path = tmp_file.name

        result = _do_upload(tmp_path, "octomation_health.txt", headers)
        if result.get("download_link_encoded"):
            json_ret["data"]["msg"] = f"服务正常，测试链接：{result['download_link_encoded']}"
        else:
            raise ValueError("未获取到下载链接，服务异常")

    except Exception as e:
        json_ret["code"] = 500
        json_ret["msg"] = str(e)
        json_ret["data"]["msg"] = f"健康检查失败：{str(e)}"
        json_ret["summary"]["statusCode"] = 500
        json_ret["summary"]["msg"] = "健康检查失败"
    finally:
        if tmp_file and os.path.exists(tmp_file.name):
            try:
                os.unlink(tmp_file.name)
            except Exception:
                pass

    return json_ret
