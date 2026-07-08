import argparse
import importlib.util
import json
import os
import sys
import time
import types
from datetime import datetime


def _install_honeyguide_stub_if_needed():
    try:
        if importlib.util.find_spec("action_sdk_for_cache.action_cache_sdk") is not None:
            return
    except ModuleNotFoundError:
        pass

    class _ActionLog:
        def info(self, _message):
            pass

    class _HoneyGuide:
        def __init__(self, context_info=None):
            self.context_info = context_info or {}
            self.actionLog = _ActionLog()

    sdk_package = types.ModuleType("action_sdk_for_cache")
    sdk_module = types.ModuleType("action_sdk_for_cache.action_cache_sdk")
    sdk_module.HoneyGuide = _HoneyGuide
    sys.modules.setdefault("action_sdk_for_cache", sdk_package)
    sys.modules.setdefault("action_sdk_for_cache.action_cache_sdk", sdk_module)


_install_honeyguide_stub_if_needed()

from generic_collection_manager import batch_delete_elements_by_value  # noqa: E402
from hg_api import HoneyGuideAPI  # noqa: E402


def _build_args():
    parser = argparse.ArgumentParser(description="Benchmark batch_delete_elements_by_value against an HG server.")
    parser.add_argument("--count", type=int, default=1000, help="number of values to add and delete")
    parser.add_argument("--delimiter", default=",", help="delimiter used to join value_str")
    parser.add_argument("--delete-mode", default="lookup_ids_then_batch_delete", help="delete mode for batch_delete_elements_by_value")
    parser.add_argument("--parallel-count", type=int, default=5, help="parallel lookup count")
    parser.add_argument("--batch-size", type=int, default=1000, help="ids per batchDelete request")
    parser.add_argument("--timeout-seconds", type=int, default=30, help="API request timeout in seconds")
    parser.add_argument("--hg-api-url", default=os.environ.get("HG_API_URL", "").strip(), help="HG server URL")
    parser.add_argument("--hg-token", default=os.environ.get("HG_TOKEN", "").strip(), help="HG token")
    parser.add_argument("--collection-name", default="", help="optional temporary collection name")
    return parser.parse_args()


def _make_context():
    return {
        "appName": "generic_collection_manager",
        "actionName": "Benchmark:batch_delete_elements_by_value",
        "eventId": "benchmark",
        "activieId": "benchmark",
        "logMode": False,
    }


def main():
    args = _build_args()
    if not args.hg_api_url or not args.hg_token:
        raise SystemExit("Set HG_API_URL and HG_TOKEN or pass --hg-api-url and --hg-token.")
    if args.count <= 0:
        raise SystemExit("--count must be positive.")
    if args.delimiter == "":
        raise SystemExit("--delimiter cannot be empty.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    collection_name = args.collection_name or f"unitest_batch_delete_{timestamp}_{os.getpid()}"
    collection_cnname = f"批量删除性能测试_{timestamp}"
    assets = {
        "hg_host": args.hg_api_url,
        "hg_token": args.hg_token,
        "timeout_seconds": args.timeout_seconds,
    }
    context_info = _make_context()
    hg_api = HoneyGuideAPI(args.hg_api_url.strip().strip("/"), args.hg_token, context_info=context_info, timeout_seconds=args.timeout_seconds)
    values = [f"batch_delete_value_{timestamp}_{index}" for index in range(args.count)]

    create_started = time.perf_counter()
    collection_id = hg_api.create_generic_collection(
        collection_name,
        collection_cnname,
        "batch_delete_elements_by_value benchmark temporary collection",
    )
    if collection_id <= 0:
        raise SystemExit(json.dumps({"stage": "create_collection", "summary": hg_api.summary}, ensure_ascii=False))
    create_seconds = time.perf_counter() - create_started

    add_started = time.perf_counter()
    added_count = 0
    try:
        for value in values:
            if not hg_api.add_generic_collection_element(
                collection_name=collection_name,
                element_value=value,
                element_remark="batch delete benchmark",
            ):
                raise RuntimeError(json.dumps({"stage": "add_element", "value": value, "summary": hg_api.summary}, ensure_ascii=False))
            added_count += 1
        add_seconds = time.perf_counter() - add_started

        delete_started = time.perf_counter()
        delete_result = batch_delete_elements_by_value(
            {
                "collection_name": collection_name,
                "value_str": args.delimiter.join(values),
                "split_symbol": args.delimiter,
                "delete_mode": args.delete_mode,
                "parallel_count": args.parallel_count,
                "batch_size": args.batch_size,
            },
            assets,
            context_info,
        )
        action_seconds = time.perf_counter() - delete_started
        report = {
            "collection_name": collection_name,
            "count": args.count,
            "added_count": added_count,
            "create_seconds": round(create_seconds, 3),
            "add_seconds": round(add_seconds, 3),
            "delete_mode": args.delete_mode,
            "parallel_count": args.parallel_count,
            "batch_size": args.batch_size,
            "action_seconds": round(action_seconds, 3),
            "lookup_seconds": delete_result["data"].get("lookup_seconds", 0),
            "delete_seconds": delete_result["data"].get("delete_seconds", round(action_seconds, 3)),
            "action_ms_per_value": round(action_seconds * 1000 / args.count, 3),
            "delete_status_code": delete_result["summary"]["statusCode"],
            "delete_msg": delete_result["summary"]["msg"],
            "success_count": delete_result["data"]["success_count"],
            "failed_count": delete_result["data"]["failed_count"],
            "deleted_count": delete_result["data"].get("deleted_count", 0),
            "not_found_count": delete_result["data"].get("not_found_count", 0),
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if delete_result["summary"]["statusCode"] != 0:
            raise SystemExit(1)
    finally:
        hg_api.delete_generic_collection_by_name(collection_name)


if __name__ == "__main__":
    main()
