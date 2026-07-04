import sys
import types
import unittest
from unittest.mock import patch


class _FakeLog:
    def info(self, _msg):
        pass


class _FakeHoneyGuide:
    def __init__(self, context_info=None):
        self.context_info = context_info or {}
        self.actionLog = _FakeLog()


action_sdk_module = types.ModuleType("action_sdk_for_cache")
action_cache_sdk_module = types.ModuleType("action_sdk_for_cache.action_cache_sdk")
action_cache_sdk_module.HoneyGuide = _FakeHoneyGuide
sys.modules.setdefault("action_sdk_for_cache", action_sdk_module)
sys.modules.setdefault("action_sdk_for_cache.action_cache_sdk", action_cache_sdk_module)

requests_module = types.ModuleType("requests")
requests_module.packages = types.SimpleNamespace(
    urllib3=types.SimpleNamespace(disable_warnings=lambda: None)
)
requests_module.get = lambda *args, **kwargs: None
requests_module.post = lambda *args, **kwargs: None
sys.modules.setdefault("requests", requests_module)

from generic_collection_manager import list_generic_collection_elements
from hg_api import HoneyGuideAPI


class _FakeResponse:
    status_code = 200

    def __init__(self, payload):
        self._payload = payload
        self.text = str(payload)

    def json(self):
        return self._payload


class _PagingHoneyGuideAPI(HoneyGuideAPI):
    def __init__(self):
        super().__init__("https://example.test", "token")
        self.requests = []
        self.include_totals = False
        self.total_elements = 1000

    def _request_api(self, method, url, headers=None, json_params=None, json_payload=None, retry_times=3):
        self.requests.append({
            "method": method,
            "url": url,
            "params": dict(json_params),
            "payload": dict(json_payload),
        })
        page = json_params["page"]
        size = json_params["size"]
        content = [
            {
                "id": (page - 1) * size + index + 1,
                "value": "value-{}".format((page - 1) * size + index + 1),
            }
            for index in range(size)
        ]
        result = {
            "empty": False,
            "content": content,
            "numberOfElements": size,
        }
        if self.include_totals:
            result["totalElements"] = self.total_elements
            result["totalPages"] = (self.total_elements + size - 1) // size
        return _FakeResponse({
            "code": 200,
            "result": result
        })


class TestGenericCollectionPaging(unittest.TestCase):
    def test_large_batch_size_is_capped_before_paging_end_check(self):
        api = _PagingHoneyGuideAPI()

        elements = api.get_generic_collection_elements(
            collection_name="test_collection",
            batch_size=20000,
            max_count=250,
        )

        self.assertEqual(len(elements), 250)
        self.assertEqual([request["params"]["page"] for request in api.requests], [1, 2])
        self.assertEqual([request["params"]["size"] for request in api.requests], [200, 200])
        self.assertEqual(api.requests[0]["payload"], {"collectionName": "test_collection"})

    def test_uses_total_pages_to_fetch_remaining_pages(self):
        api = _PagingHoneyGuideAPI()
        api.include_totals = True

        elements = api.get_generic_collection_elements(
            collection_name="test_collection",
            batch_size=200,
            max_count=550,
        )

        self.assertEqual(len(elements), 550)
        self.assertEqual(sorted(request["params"]["page"] for request in api.requests), [1, 2, 3])
        self.assertEqual([element["id"] for element in elements[:3]], [1, 2, 3])
        self.assertEqual([element["id"] for element in elements[-3:]], [548, 549, 550])

    def test_action_forwards_collection_filters_to_api(self):
        class FakeAPI:
            last_kwargs = None

            def __init__(self, *args, **kwargs):
                self.summary = {"statusCode": 0, "msg": ""}

            def get_generic_collection_elements(self, **kwargs):
                FakeAPI.last_kwargs = kwargs
                return []

        params = {
            "collection_id": "12345678901234567",
            "collection_name": "test_collection",
            "batch_size": "20000",
            "max_count": "20000",
            "parallel_page_count": "3",
        }
        assets = {
            "hg_host": "https://example.test/",
            "hg_token": "token",
        }

        with patch("generic_collection_manager.HoneyGuideAPI", FakeAPI):
            list_generic_collection_elements(params, assets, {})

        self.assertEqual(FakeAPI.last_kwargs["collection_id"], 12345678901234567)
        self.assertEqual(FakeAPI.last_kwargs["collection_name"], "test_collection")
        self.assertEqual(FakeAPI.last_kwargs["batch_size"], 20000)
        self.assertEqual(FakeAPI.last_kwargs["max_count"], 20000)
        self.assertEqual(FakeAPI.last_kwargs["parallel_page_count"], 3)

    def test_parallel_page_count_one_still_fetches_needed_pages(self):
        api = _PagingHoneyGuideAPI()
        api.include_totals = True

        elements = api.get_generic_collection_elements(
            collection_name="test_collection",
            batch_size=200,
            max_count=550,
            parallel_page_count=1,
        )

        self.assertEqual(len(elements), 550)
        self.assertEqual([request["params"]["page"] for request in api.requests], [1, 2, 3])
        self.assertEqual([element["id"] for element in elements[-3:]], [548, 549, 550])

    def test_action_rejects_missing_collection_filter(self):
        result = list_generic_collection_elements(
            {"batch_size": "30", "max_count": "200"},
            {"hg_host": "https://example.test/", "hg_token": "token"},
            {},
        )

        self.assertEqual(result["summary"]["statusCode"], 400)
        self.assertEqual(result["summary"]["msg"], "collection_id和collection_name不能同时为空")

    def test_action_rejects_invalid_collection_id(self):
        result = list_generic_collection_elements(
            {"collection_id": "not-a-number", "batch_size": "30", "max_count": "200"},
            {"hg_host": "https://example.test/", "hg_token": "token"},
            {},
        )

        self.assertEqual(result["summary"]["statusCode"], 400)
        self.assertEqual(result["summary"]["msg"], "collection_id必须为整数数字")

    def test_action_rejects_invalid_parallel_page_count(self):
        result = list_generic_collection_elements(
            {
                "collection_name": "test_collection",
                "batch_size": "200",
                "max_count": "200",
                "parallel_page_count": "0",
            },
            {"hg_host": "https://example.test/", "hg_token": "token"},
            {},
        )

        self.assertEqual(result["summary"]["statusCode"], 400)
        self.assertEqual(result["summary"]["msg"], "batch_size、max_count和parallel_page_count必须为正整数")


if __name__ == "__main__":
    unittest.main()
