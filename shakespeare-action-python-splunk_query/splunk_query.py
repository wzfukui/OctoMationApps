# -*- coding: utf-8 -*-
import json
import time
from datetime import datetime, timezone
from urllib.parse import urlparse, urlunparse

import requests

try:
    requests.packages.urllib3.disable_warnings()
except Exception:
    pass


def _bool_value(value, default=False):
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("1", "true", "yes", "y", "on")


def _int_value(value, default):
    try:
        if value is None or value == "":
            return default
        return int(value)
    except Exception:
        return default


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


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


def _normalise_api_url(assets):
    api_url = (assets.get("splunk_api_url") or "").strip()
    web_url = (assets.get("splunk_web_url") or assets.get("host") or "").strip()

    if api_url:
        url = api_url
    else:
        url = web_url
        if not url:
            raise ValueError("splunk_web_url or splunk_api_url is required")
        if "://" not in url:
            url = "http://" + url
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            raise ValueError("invalid splunk_web_url")
        url = urlunparse(("https", f"{hostname}:8089", "", "", "", ""))

    if "://" not in url:
        url = "https://" + url
    return url.rstrip("/")


def _normalise_web_url(assets):
    web_url = (assets.get("splunk_web_url") or "").strip()
    if not web_url:
        return ""
    if "://" not in web_url:
        web_url = "http://" + web_url
    return web_url.rstrip("/")


def _parse_fields(fields):
    if not fields:
        return []
    if isinstance(fields, list):
        return [str(item).strip() for item in fields if str(item).strip()]
    return [item.strip() for item in str(fields).split(",") if item.strip()]


class SplunkQueryClient:
    def __init__(self, assets):
        self.assets = assets or {}
        self.api_url = _normalise_api_url(self.assets)
        self.web_url = _normalise_web_url(self.assets)
        self.base_url = self.api_url
        self.connection_mode = (self.assets.get("connection_mode") or "auto").strip().lower()
        if self.connection_mode not in ("auto", "rest_api", "web_proxy"):
            self.connection_mode = "auto"
        self.username = self.assets.get("username")
        self.password = self.assets.get("password")
        self.verify_ssl = _bool_value(self.assets.get("verify_ssl"), False)
        self.timeout = _int_value(self.assets.get("timeout"), 30)
        self.web_session = None
        self.web_csrf_token = ""

        if not self.username or not self.password:
            raise ValueError("username and password are required")

    def _request(self, method, path, params=None, data=None):
        if self.connection_mode == "web_proxy":
            return self._request_web_proxy(method, path, params=params, data=data)

        try:
            return self._request_rest_api(method, path, params=params, data=data)
        except requests.RequestException:
            if self.connection_mode == "auto" and self.web_url:
                return self._request_web_proxy(method, path, params=params, data=data)
            raise

    def _request_rest_api(self, method, path, params=None, data=None):
        self.base_url = self.api_url
        session = requests.Session()
        request_func = getattr(session, method.lower())
        return request_func(
            self.api_url + path,
            params=params,
            data=data,
            auth=(self.username, self.password),
            verify=self.verify_ssl,
            timeout=self.timeout,
            headers={"Accept": "application/json"}
        )

    def _login_web_proxy(self):
        if not self.web_url:
            raise ValueError("splunk_web_url is required for web_proxy mode")

        session = requests.Session()
        login_url = self.web_url + "/en-US/account/login"
        session.get(login_url, timeout=self.timeout, verify=self.verify_ssl)
        cval = session.cookies.get("cval") or ""
        response = session.post(
            login_url,
            data={"username": self.username, "password": self.password, "cval": cval},
            timeout=self.timeout,
            verify=self.verify_ssl
        )
        try:
            payload = response.json()
        except Exception:
            payload = {}
        if response.status_code >= 400 or payload.get("status") not in (0, "0", None):
            raise ValueError("Splunk Web login failed")

        self.web_session = session
        self.web_csrf_token = session.cookies.get("splunkweb_csrf_token_8000") or ""

    def _request_web_proxy(self, method, path, params=None, data=None):
        if self.web_session is None:
            self._login_web_proxy()

        self.base_url = self.web_url
        headers = {"Accept": "application/json", "X-Requested-With": "XMLHttpRequest"}
        if self.web_csrf_token:
            headers["X-Splunk-Form-Key"] = self.web_csrf_token

        request_func = getattr(self.web_session, method.lower())
        return request_func(
            self.web_url + "/en-US/splunkd/__raw" + path,
            params=params,
            data=data,
            verify=self.verify_ssl,
            timeout=self.timeout,
            headers=headers
        )

    def health_check(self):
        response = self._request(
            "get",
            "/services/server/info",
            params={"output_mode": "json"}
        )
        payload = self._json_or_text(response)
        if response.status_code < 200 or response.status_code >= 300:
            return _response(
                code=200,
                msg="Splunk REST API health check failed",
                data={"status": "failed", "http_status": response.status_code, "response": payload},
                status_code=response.status_code,
                summary_msg="连接失败"
            )

        entry = {}
        if isinstance(payload, dict):
            entries = payload.get("entry") or []
            if entries:
                entry = entries[0].get("content") or {}

        data = {
            "status": "ok",
            "api_url": self.base_url,
            "connection_mode": "web_proxy" if self.base_url == self.web_url else "rest_api",
            "splunk_version": entry.get("version", ""),
            "server_name": entry.get("serverName", ""),
            "build": entry.get("build", "")
        }
        return _response(code=200, msg="Splunk REST API connected", data=data, status_code=200, summary_msg="连接成功")

    def export_search(self, search, earliest_time="-5m", latest_time="now", max_count=50, fields=None):
        search = (search or "").strip()
        if not search:
            raise ValueError("search is required")

        data = {
            "search": search,
            "output_mode": "json",
            "exec_mode": "oneshot"
        }
        if earliest_time:
            data["earliest_time"] = str(earliest_time).strip()
        if latest_time:
            data["latest_time"] = str(latest_time).strip()
        max_count = _int_value(max_count, 50)
        if max_count > 0:
            data["max_count"] = str(max_count)

        started_at = time.time()
        response = self._request("post", "/services/search/jobs/export", data=data)
        elapsed_ms = int((time.time() - started_at) * 1000)

        if response.status_code < 200 or response.status_code >= 300:
            return _response(
                code=200,
                msg="Splunk search failed",
                data={
                    "http_status": response.status_code,
                    "response": response.text,
                    "search": search,
                    "earliest_time": earliest_time,
                    "latest_time": latest_time
                },
                status_code=response.status_code,
                summary_msg="查询失败"
            )

        events, messages = self._parse_export_response(response.text, fields, max_count=max_count)
        data = {
            "search": search,
            "earliest_time": earliest_time,
            "latest_time": latest_time,
            "count": len(events),
            "events": events,
            "messages": messages,
            "elapsed_ms": elapsed_ms,
            "api_url": self.base_url,
            "connection_mode": "web_proxy" if self.base_url == self.web_url else "rest_api"
        }
        return _response(code=200, msg="Splunk search success", data=data, status_code=200, summary_msg="查询成功")

    @staticmethod
    def _json_or_text(response):
        try:
            return response.json()
        except Exception:
            return response.text

    @staticmethod
    def _parse_export_response(text, fields=None, max_count=0):
        selected_fields = _parse_fields(fields)
        max_count = _int_value(max_count, 0)
        events = []
        messages = []

        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except Exception:
                messages.append({"type": "parse_warning", "text": line})
                continue

            if "result" in item:
                result = item.get("result") or {}
                if selected_fields:
                    result = {key: result.get(key, "") for key in selected_fields}
                events.append(result)
                if max_count > 0 and len(events) >= max_count:
                    break
            elif "messages" in item:
                messages.extend(item.get("messages") or [])
            else:
                messages.append(item)

        return events, messages


def health_check(params, assets, context_info=None):
    try:
        client = SplunkQueryClient(assets)
        return client.health_check()
    except Exception as error:
        return _response(
            code=500,
            msg=str(error),
            data={"status": "failed"},
            status_code=500,
            summary_msg="连接异常"
        )


def run_search(params, assets, context_info=None):
    try:
        params = params or {}
        client = SplunkQueryClient(assets)
        return client.export_search(
            search=params.get("search", "search sourcetype=fortigate"),
            earliest_time=params.get("earliest_time", "-5m"),
            latest_time=params.get("latest_time", "now"),
            max_count=_int_value(params.get("max_count"), 50),
            fields=params.get("fields", "")
        )
    except Exception as error:
        return _response(code=500, msg=str(error), data={}, status_code=500, summary_msg="查询异常")


def poll_alerts(params, assets, context_info=None):
    try:
        params = params or {}
        client = SplunkQueryClient(assets)
        last_poll_time = (params.get("last_poll_time") or "").strip()
        earliest_time = last_poll_time or params.get("earliest_time", "-5m")
        latest_time = params.get("latest_time", "now")
        alert_time_field = params.get("alert_time_field", "_time") or "_time"

        result = client.export_search(
            search=params.get("base_search", "search sourcetype=fortigate"),
            earliest_time=earliest_time,
            latest_time=latest_time,
            max_count=_int_value(params.get("max_count"), 50),
            fields=params.get("fields", "")
        )

        events = result.get("data", {}).get("events", [])
        alert_times = []
        for event in events:
            if isinstance(event, dict) and event.get(alert_time_field):
                alert_times.append(str(event.get(alert_time_field)))

        next_poll_time = max(alert_times) if alert_times else _now_iso()
        result["data"]["last_poll_time"] = last_poll_time
        result["data"]["next_poll_time"] = next_poll_time
        result["data"]["alert_time_field"] = alert_time_field
        result["data"]["alert_times"] = alert_times
        return result
    except Exception as error:
        return _response(code=500, msg=str(error), data={}, status_code=500, summary_msg="轮询异常")
