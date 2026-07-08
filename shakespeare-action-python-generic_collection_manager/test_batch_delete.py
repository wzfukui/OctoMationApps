import json
import os
import sys
import threading
import types
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class _FakeActionLog:
    def info(self, _message):
        pass


class _FakeHoneyGuide:
    def __init__(self, context_info=None):
        self.context_info = context_info or {}
        self.actionLog = _FakeActionLog()


sdk_package = types.ModuleType("action_sdk_for_cache")
sdk_module = types.ModuleType("action_sdk_for_cache.action_cache_sdk")
sdk_module.HoneyGuide = _FakeHoneyGuide
sys.modules.setdefault("action_sdk_for_cache", sdk_package)
sys.modules.setdefault("action_sdk_for_cache.action_cache_sdk", sdk_module)
sys.path.insert(0, os.path.dirname(__file__))

from generic_collection_manager import (  # noqa: E402
    batch_delete_elements_by_ids,
    batch_delete_elements_by_value,
    delete_generic_collection_element,
)


class _HoneyGuideHandler(BaseHTTPRequestHandler):
    requests = []
    direct_delete_supported = True
    id_by_value = {
        "1.1.1.1": 101,
        "2.2.2.2": 102,
        "3.3.3.3": 321,
    }

    def log_message(self, _format, *_args):
        pass

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _send_json(self, status_code, payload):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def do_POST(self):
        payload = self._read_json()
        self.__class__.requests.append({"path": self.path, "body": payload})
        if self.path.startswith("/api/collectionElement/deleteElement"):
            if not self.__class__.direct_delete_supported:
                self._send_json(404, {"code": 404, "msg": "not found"})
                return
            if payload.get("value") == "bad":
                self._send_json(200, {"code": 500, "msg": "delete failed", "result": 0})
                return
            self._send_json(200, {"code": 200, "msg": "ok", "result": 1})
            return
        if self.path.startswith("/api/collectionElement/batchDelete"):
            if not isinstance(payload, list):
                self._send_json(400, {"code": 400, "msg": "参数解析失败，请检查"})
                return
            self._send_json(200, {"code": 200, "msg": "ok", "result": len(payload)})
            return
        if self.path.startswith("/api/collectionElement/find"):
            if payload.get("value") == "lookup_error":
                self._send_json(500, {"code": 500, "msg": "lookup failed"})
                return
            element_id = self.__class__.id_by_value.get(payload.get("value"), 0)
            if element_id == 0:
                self._send_json(
                    200,
                    {
                        "code": 200,
                        "result": {
                            "empty": True,
                            "content": [],
                            "numberOfElements": 0,
                            "totalPages": 0,
                        },
                    },
                )
                return
            self._send_json(
                200,
                {
                    "code": 200,
                    "result": {
                        "empty": False,
                        "content": [{"id": element_id, "value": payload.get("value")}],
                        "numberOfElements": 1,
                        "totalPages": 1,
                    },
                },
            )
            return
        if self.path.startswith("/api/collectionElement/delete/321"):
            self._send_json(200, {"code": 200, "msg": "ok", "result": 1})
            return
        self._send_json(404, {"code": 404, "msg": "unexpected path"})


class BatchDeleteTest(unittest.TestCase):
    def setUp(self):
        _HoneyGuideHandler.requests = []
        _HoneyGuideHandler.direct_delete_supported = True
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), _HoneyGuideHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.assets = {
            "hg_host": f"http://127.0.0.1:{self.server.server_port}",
            "hg_token": "test-token",
            "timeout_seconds": 2,
        }

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def test_single_delete_uses_condition_delete_first(self):
        result = delete_generic_collection_element(
            {"collection_name": "BLACKLIST", "element_value": "1.1.1.1"},
            self.assets,
            {},
        )

        self.assertEqual(0, result["summary"]["statusCode"])
        paths = [request["path"] for request in _HoneyGuideHandler.requests]
        self.assertEqual(["/api/collectionElement/deleteElement"], paths)
        self.assertEqual(
            {"collectionName": "BLACKLIST", "value": "1.1.1.1"},
            _HoneyGuideHandler.requests[0]["body"],
        )

    def test_batch_delete_by_ids_posts_id_list_to_batch_delete(self):
        result = batch_delete_elements_by_ids(
            {
                "id_str": "101, 102, 102, 103",
            },
            self.assets,
            {},
        )

        self.assertEqual(0, result["summary"]["statusCode"])
        self.assertEqual(4, result["data"]["raw_count"])
        self.assertEqual(3, result["data"]["total_count"])
        self.assertEqual(3, result["data"]["deleted_count"])
        self.assertEqual(["/api/collectionElement/batchDelete"], [request["path"] for request in _HoneyGuideHandler.requests])
        self.assertEqual([101, 102, 103], _HoneyGuideHandler.requests[0]["body"])

    def test_batch_delete_by_value_looks_up_ids_and_uses_batch_delete(self):
        result = batch_delete_elements_by_value(
            {
                "collection_name": "BLACKLIST",
                "value_str": "1.1.1.1; 2.2.2.2; missing; ;1.1.1.1",
                "split_symbol": ";",
                "parallel_count": 2,
            },
            self.assets,
            {},
        )

        self.assertEqual(0, result["summary"]["statusCode"])
        self.assertEqual(4, result["data"]["raw_count"])
        self.assertEqual(3, result["data"]["total_count"])
        self.assertEqual(3, result["data"]["success_count"])
        self.assertEqual(0, result["data"]["failed_count"])
        self.assertEqual(2, result["data"]["deleted_count"])
        self.assertEqual(["missing"], result["data"]["not_found_values"])
        batch_requests = [request for request in _HoneyGuideHandler.requests if request["path"].startswith("/api/collectionElement/batchDelete")]
        self.assertEqual(1, len(batch_requests))
        self.assertEqual([101, 102], batch_requests[0]["body"])

    def test_batch_delete_by_value_direct_mode_keeps_condition_delete_path(self):
        result = batch_delete_elements_by_value(
            {
                "collection_name": "BLACKLIST",
                "value_str": "1.1.1.1; bad",
                "split_symbol": ";",
                "delete_mode": "direct_by_value",
            },
            self.assets,
            {},
        )

        self.assertEqual(207, result["summary"]["statusCode"])
        self.assertEqual(1, result["data"]["success_count"])
        self.assertEqual(1, result["data"]["failed_count"])
        self.assertEqual(
            ["1.1.1.1", "bad"],
            [request["body"]["value"] for request in _HoneyGuideHandler.requests if request["path"].startswith("/api/collectionElement/deleteElement")],
        )

    def test_single_delete_falls_back_to_id_delete_when_condition_delete_is_missing(self):
        _HoneyGuideHandler.direct_delete_supported = False
        result = delete_generic_collection_element(
            {"collection_name": "BLACKLIST", "element_value": "3.3.3.3"},
            self.assets,
            {},
        )

        self.assertEqual(0, result["summary"]["statusCode"])
        paths = [request["path"] for request in _HoneyGuideHandler.requests]
        self.assertEqual(
            [
                "/api/collectionElement/deleteElement",
                "/api/collectionElement/find?page=1&size=200",
                "/api/collectionElement/delete/321",
            ],
            paths,
        )


if __name__ == "__main__":
    unittest.main()
