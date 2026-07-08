# -*- coding: utf-8 -*-
from hg_api import HoneyGuideAPI
import concurrent.futures
import re
import time


def _parse_delimited_values(raw_text, split_symbol):
    if not isinstance(raw_text, str):
        raw_text = str(raw_text)
    if not isinstance(split_symbol, str):
        split_symbol = str(split_symbol)
    split_symbol = split_symbol or ","
    raw_values = [value.strip() for value in raw_text.split(split_symbol)]
    values = []
    seen_values = set()
    for value in raw_values:
        if value == "" or value in seen_values:
            continue
        values.append(value)
        seen_values.add(value)
    raw_count = len([value for value in raw_values if value != ""])
    return raw_count, values, split_symbol


def _parse_positive_int(value, default_value, field_name, min_value=1, max_value=None):
    if value is None or value == "":
        value = default_value
    try:
        int_value = int(value)
    except Exception:
        raise ValueError(f"{field_name}必须为正整数")
    if int_value < min_value:
        raise ValueError(f"{field_name}必须为正整数")
    if max_value is not None:
        int_value = min(int_value, max_value)
    return int_value

def list_generic_collections(params, assets, context_info):
    # 获取所有集合，并返回集合组成的列表
    json_ret = {
        "code": 200, 
        "msg": "", 
        "data": {
            "collections": [],
            "count": 0
        }, 
        "summary": {
            "statusCode": 0, 
            "msg": ""
        }
    }
    hg_host = assets["hg_host"].strip().strip("/")
    hg_token = assets["hg_token"].strip()
    timeout_seconds = assets.get("timeout_seconds", 10)
    hg_api = HoneyGuideAPI(hg_host, hg_token, context_info=context_info, timeout_seconds=timeout_seconds)
    batch_size = params.get("batch_size", 200)
    max_count = params.get("max_count", 200)
    try:
        batch_size = int(batch_size)
        max_count = int(max_count)
    except:
        json_ret["summary"]["statusCode"] = 400
        json_ret["summary"]["msg"] = "batch_size和max_count必须为正整数"
        return json_ret
    if batch_size <= 0 or max_count <= 0:
        json_ret["summary"]["statusCode"] = 400
        json_ret["summary"]["msg"] = "batch_size和max_count必须为正整数"
        return json_ret
    collection_list = hg_api.get_generic_collections(batch_size=batch_size, max_count=max_count)
    json_ret["summary"]["statusCode"] = hg_api.summary["statusCode"]
    json_ret["summary"]["msg"] = hg_api.summary["msg"]
    if hg_api.summary["statusCode"] == 0:
        json_ret["data"]["collections"] = collection_list
        json_ret["data"]["count"] = len(collection_list)
    return json_ret

def create_generic_collection(params, assets, context_info):
    # 创建通用集合
    json_ret = {
        "code": 200, 
        "msg": "", 
        "data": {
            "collection_id": 0,
            "duplicated": False
        }, 
        "summary": {
            "statusCode": 0, 
            "msg": ""
        }
    }
    hg_host = assets["hg_host"].strip().strip("/")
    hg_token = assets["hg_token"].strip()
    timeout_seconds = assets.get("timeout_seconds", 10)
    hg_api = HoneyGuideAPI(hg_host, hg_token, context_info=context_info, timeout_seconds=timeout_seconds)
    collection_name = params["collection_name"].strip()
    collection_cnname = params["collection_cnname"].strip()
    collection_description = params.get("collection_description", "").strip()
    # collection_name只能包含数字，英文字母，下划线，需要正则匹配，不符合条件则返回错误
    if not re.match("^[a-zA-Z0-9_]+$", collection_name):
        json_ret["summary"]["statusCode"] = 400
        json_ret["summary"]["msg"] = "集合名称只能包含数字，英文字母，下划线,最长64字符"
        return json_ret
    if collection_cnname == "":
        json_ret["summary"]["statusCode"] = 400
        json_ret["summary"]["msg"] = "集合中文名称不能为空"
        return json_ret

    # 创建集合
    collection_id = hg_api.create_generic_collection(collection_name, collection_cnname, collection_description)
    json_ret["summary"]["statusCode"]  = hg_api.summary["statusCode"]
    json_ret["summary"]["msg"] = hg_api.summary["msg"]
    json_ret["data"]["duplicated"] = hg_api.summary["duplicated"]
    if collection_id > 0:
        json_ret["data"]["collection_id"] = collection_id
    
    return json_ret

def delete_generic_collection(params, assets, context_info):
    # 删除通用集合
    json_ret = {
        "code": 200, 
        "msg": "", 
        "data": {}, 
        "summary": {
            "statusCode": -1, 
            "msg": ""
        }
    }
        
    collection_id = params.get("collection_id", 0)
    collection_name = params.get("collection_name", "")
    if collection_id == 0 and collection_name == "":
        json_ret["summary"]["statusCode"] = 400
        json_ret["summary"]["msg"] = "collection_id和collection_name不能同时为空"
        return json_ret
    hg_host = assets["hg_host"].strip().strip("/")
    hg_token = assets["hg_token"].strip()
    timeout_seconds = assets.get("timeout_seconds", 10)
    hg_api = HoneyGuideAPI(hg_host, hg_token, context_info=context_info, timeout_seconds=timeout_seconds)
    if collection_id > 0:
        delete_result = hg_api.delete_generic_collection_by_id(collection_id)
    else:
        delete_result = hg_api.delete_generic_collection_by_name(collection_name)
    json_ret["summary"]["msg"] = hg_api.summary["msg"]
    json_ret["summary"]["statusCode"] = hg_api.summary["statusCode"]
    if delete_result:
        json_ret["summary"]["statusCode"] = 0
    return json_ret

def list_generic_collection_elements(params, assets, context_info):
    # 获取通用集合下的所有条目
    json_ret = {
        "code": 200, 
        "msg": "", 
        "data": {
            "elements": [],
            "count": 0
        }, 
        "summary": {
            "statusCode": 0, 
            "msg": ""
        }
    }

    hg_host = assets["hg_host"].strip().strip("/")
    hg_token = assets["hg_token"].strip()
    collection_id = params.get("collection_id", "")
    collection_name = params.get("collection_name", "")
    if isinstance(collection_id, str):
        collection_id = collection_id.strip()
    if isinstance(collection_name, str):
        collection_name = collection_name.strip()
    if collection_id != "":
        try:
            collection_id = int(collection_id)
        except:
            json_ret["summary"]["statusCode"] = 400
            json_ret["summary"]["msg"] = "collection_id必须为整数数字"
            return json_ret
    if (collection_id == "" or collection_id == 0) and collection_name == "":
        json_ret["summary"]["statusCode"] = 400
        json_ret["summary"]["msg"] = "collection_id和collection_name不能同时为空"
        return json_ret
    batch_size = params.get("batch_size", 200)
    max_count = params.get("max_count", 200)
    parallel_page_count = params.get("parallel_page_count", 5)
    try:
        batch_size = int(batch_size)
        max_count = int(max_count)
        parallel_page_count = int(parallel_page_count)
    except:
        json_ret["summary"]["statusCode"] = 400
        json_ret["summary"]["msg"] = "batch_size、max_count和parallel_page_count必须为正整数"
        return json_ret
    if batch_size <= 0 or max_count <= 0 or parallel_page_count <= 0:
        json_ret["summary"]["statusCode"] = 400
        json_ret["summary"]["msg"] = "batch_size、max_count和parallel_page_count必须为正整数"
        return json_ret
    timeout_seconds = assets.get("timeout_seconds", 10)
    hg_api = HoneyGuideAPI(hg_host, hg_token, context_info=context_info, timeout_seconds=timeout_seconds)
    element_list = hg_api.get_generic_collection_elements(
        collection_id=collection_id,
        collection_name=collection_name,
        batch_size=batch_size,
        max_count=max_count,
        parallel_page_count=parallel_page_count
    )
    json_ret["summary"]["msg"] = hg_api.summary["msg"]
    json_ret["summary"]["statusCode"] = hg_api.summary["statusCode"]
    if hg_api.summary["statusCode"] == 0:
        json_ret["data"]["elements"] = element_list
        json_ret["data"]["count"] = len(element_list)
        json_ret["summary"]["msg"] = f"执行成功，共获取到{len(element_list)}个条目"
    return json_ret

def add_generic_collection_item(params, assets, context_info):
    # 向通用集合中添加条目
    json_ret = {
        "code": 200, 
        "msg": "", 
        "data": {
            "duplicated": False
        }, 
        "summary": {
            "statusCode": -1, 
            "msg": ""
        }
    }

    hg_host = assets["hg_host"].strip().strip("/")
    hg_token = assets["hg_token"].strip()
    timeout_seconds = assets.get("timeout_seconds", 10)
    hg_api = HoneyGuideAPI(hg_host, hg_token, context_info=context_info, timeout_seconds=timeout_seconds)
    collection_name = params.get("collection_name", "")
    element_value = params.get("element_value", "")
    element_remark = params.get("element_remark", "")
    if collection_name == "" or element_value == "":
        json_ret["summary"]["statusCode"] = 400
        json_ret["summary"]["msg"] = "collection_name, element_value不能为空"
        return json_ret
    
    element_remark = params.get("element_remark", "")
    update_if_exist = params.get("update_if_exist", False)
    add_element_result = hg_api.add_generic_collection_element(collection_name=collection_name,element_value=element_value, element_remark=element_remark, update_if_exist=update_if_exist)
    json_ret["summary"]["statusCode"] = hg_api.summary["statusCode"]
    json_ret["summary"]["msg"] = hg_api.summary["msg"]
    if add_element_result:
        json_ret["summary"]["statusCode"] = 0
        json_ret["data"]["duplicated"] = hg_api.summary["duplicated"]
    return json_ret

def get_generic_collection_element_info(params, assets, context_info):
    # 获取通用集合元素信息
    json_ret = {
        "code": 200, 
        "msg": "", 
        "data": {
            "createdBy": "",
            "modifiedBy": "",
            "createdNickName": "",
            "modifiedNickName": "",
            "createTime": "",
            "updateTime": "",
            "id": 0,
            "value": "",
            "collectionId": 0,
            "collectionName": "",
            "remark": "",
            "expireTime": "",
            "expireTimeStr": "",
            "effectiveTime": None,
            "effectiveTimeStr": None
        },
        "summary": {
            "statusCode": -1, 
            "msg": ""
        }
    }

    hg_host = assets["hg_host"].strip().strip("/")
    hg_token = assets["hg_token"].strip()
    timeout_seconds = assets.get("timeout_seconds", 10)
    hg_api = HoneyGuideAPI(hg_host, hg_token, context_info=context_info, timeout_seconds=timeout_seconds)
    collection_id = params.get("collection_id", 0)
    collection_name = params.get("collection_name", "")
    element_value = params.get("element_value", "")
    if collection_id == 0 and collection_name == "":
        json_ret["summary"]["statusCode"] = 400
        json_ret["summary"]["msg"] = "collection_id和collection_name不能同时为空"
        return json_ret
    if element_value == "":
        json_ret["summary"]["statusCode"] = 400
        json_ret["summary"]["msg"] = "element_value不能为空"
        return json_ret
    
    if collection_id > 0:
        json_element_info = hg_api.get_generic_collection_element_info_by_value(collection_id=collection_id, element_value=element_value)
    else:
        json_element_info = hg_api.get_generic_collection_element_info_by_value(collection_name=collection_name, element_value=element_value)
    
    json_element_info = hg_api.get_generic_collection_element_info_by_value(collection_id, collection_name, element_value)
    json_ret["summary"]["statusCode"] = hg_api.summary["statusCode"]
    json_ret["summary"]["msg"] = hg_api.summary["msg"]
    if 'id' in json_element_info.keys()  and json_element_info['id'] > 0:
        json_ret["summary"]["statusCode"] = 0
        json_ret["summary"]["msg"] = "元素信息获取成功"
        json_ret["data"] = json_element_info
    return json_ret

def update_generic_collection_element(params, assets, context_info):

    # 更新通用集合元素信息
    json_ret = {
        "code": 200, 
        "msg": "", 
        "data": {}, 
        "summary": {
            "statusCode": -1, 
            "msg": ""
        }
    }

    hg_host = assets["hg_host"].strip().strip("/")
    hg_token = assets["hg_token"].strip()
    timeout_seconds = assets.get("timeout_seconds", 10)
    hg_api = HoneyGuideAPI(hg_host, hg_token, context_info=context_info, timeout_seconds=timeout_seconds)
    collection_name = params.get("collection_name", "")
    element_value = params.get("element_value", "")
    element_remark = params.get("element_remark", "")
    if collection_name == "" or element_value == "":
        json_ret["summary"]["statusCode"] = 400
        json_ret["summary"]["msg"] = "collection_name和element_value不能为空"
        return json_ret

    update_result = hg_api.update_generic_collection_element_by_value(collection_name=collection_name, element_value=element_value, element_remark=element_remark)
    json_ret["summary"]["statusCode"] = hg_api.summary["statusCode"]
    json_ret["summary"]["msg"] = hg_api.summary["msg"]
    if update_result:
        json_ret["summary"]["statusCode"] = 0
        json_ret["summary"]["msg"] = "元素信息更新成功"
    return json_ret

def delete_generic_collection_element(params, assets, context_info): 
    # 删除通用集合元素
    json_ret = {
        "code": 200, 
        "msg": "", 
        "data": {}, 
        "summary": {
            "statusCode": -1, 
            "msg": ""
        }
    }

    hg_host = assets["hg_host"].strip().strip("/")
    hg_token = assets["hg_token"].strip()
    timeout_seconds = assets.get("timeout_seconds", 10)
    hg_api = HoneyGuideAPI(hg_host, hg_token, context_info=context_info, timeout_seconds=timeout_seconds)
    collection_name = params.get("collection_name", "")
    element_value = params.get("element_value", "")
    if collection_name == "" or element_value == "":
        json_ret["summary"]["statusCode"] = 400
        json_ret["summary"]["msg"] = "collection_name和element_value不能为空"
        return json_ret
    delete_result = hg_api.delete_generic_collection_element_by_value(collection_name, element_value)
    json_ret["summary"]["statusCode"] = hg_api.summary["statusCode"]
    json_ret["summary"]["msg"] = hg_api.summary["msg"]
    if delete_result:
        json_ret["summary"]["statusCode"] = 0
    return json_ret

def batch_delete_elements_by_ids(params, assets, context_info):
    # 按元素ID批量删除通用集合元素
    json_ret = {
        "code": 200,
        "msg": "",
        "data": {
            "raw_count": 0,
            "total_count": 0,
            "success_count": 0,
            "failed_count": 0,
            "deleted_count": 0,
            "split_symbol": ",",
            "success_ids": [],
            "failed_ids": [],
            "delete_seconds": 0,
            "delete_milliseconds": 0
        },
        "summary": {
            "statusCode": -1,
            "msg": ""
        }
    }

    id_str = params.get("id_str", params.get("element_ids", ""))
    split_symbol = params.get("split_symbol", ",")
    try:
        raw_count, id_values, split_symbol = _parse_delimited_values(id_str, split_symbol)
        batch_size = _parse_positive_int(params.get("batch_size", 1000), 1000, "batch_size")
    except ValueError as e:
        json_ret["summary"]["statusCode"] = 400
        json_ret["summary"]["msg"] = str(e)
        return json_ret
    json_ret["data"]["raw_count"] = raw_count
    json_ret["data"]["total_count"] = len(id_values)
    json_ret["data"]["split_symbol"] = split_symbol
    if len(id_values) == 0:
        json_ret["summary"]["statusCode"] = 400
        json_ret["summary"]["msg"] = "id_str按分隔符拆分后没有有效id"
        return json_ret
    try:
        element_ids = [int(element_id) for element_id in id_values]
    except Exception:
        json_ret["summary"]["statusCode"] = 400
        json_ret["summary"]["msg"] = "id_str中存在非整数id"
        return json_ret

    hg_host = assets["hg_host"].strip().strip("/")
    hg_token = assets["hg_token"].strip()
    timeout_seconds = assets.get("timeout_seconds", assets.get("conn_time_out", 10))
    hg_api = HoneyGuideAPI(hg_host, hg_token, context_info=context_info, timeout_seconds=timeout_seconds)
    delete_started = time.perf_counter()
    for start_index in range(0, len(element_ids), batch_size):
        batch_ids = element_ids[start_index:start_index + batch_size]
        delete_result = hg_api.delete_generic_collection_elements_by_ids(batch_ids)
        delete_summary = {
            "ids": batch_ids,
            "statusCode": hg_api.summary["statusCode"],
            "msg": hg_api.summary["msg"]
        }
        if delete_result:
            json_ret["data"]["success_ids"].extend(batch_ids)
            json_ret["data"]["deleted_count"] += int(hg_api.summary.get("deleted_count", len(batch_ids)))
        else:
            json_ret["data"]["failed_ids"].append(delete_summary)
    delete_seconds = time.perf_counter() - delete_started
    json_ret["data"]["delete_seconds"] = round(delete_seconds, 3)
    json_ret["data"]["delete_milliseconds"] = int(round(delete_seconds * 1000))
    json_ret["data"]["success_count"] = len(json_ret["data"]["success_ids"])
    json_ret["data"]["failed_count"] = sum(len(item["ids"]) for item in json_ret["data"]["failed_ids"])
    if json_ret["data"]["failed_count"] == 0:
        json_ret["summary"]["statusCode"] = 0
        json_ret["summary"]["msg"] = f"批量删除完成，成功删除{json_ret['data']['deleted_count']}个id"
    else:
        json_ret["summary"]["statusCode"] = 207
        json_ret["summary"]["msg"] = (
            f"批量删除完成，成功{json_ret['data']['success_count']}个，"
            f"失败{json_ret['data']['failed_count']}个"
        )
    return json_ret


def batch_delete_elements_by_value(params, assets, context_info):
    # 批量删除通用集合元素
    json_ret = {
        "code": 200,
        "msg": "",
        "data": {
            "raw_count": 0,
            "total_count": 0,
            "success_count": 0,
            "failed_count": 0,
            "deleted_count": 0,
            "not_found_count": 0,
            "split_symbol": ",",
            "delete_mode": "lookup_ids_then_batch_delete",
            "parallel_count": 5,
            "lookup_seconds": 0,
            "delete_seconds": 0,
            "lookup_milliseconds": 0,
            "delete_milliseconds": 0,
            "success_values": [],
            "failed_values": [],
            "not_found_values": []
        },
        "summary": {
            "statusCode": -1,
            "msg": ""
        }
    }

    collection_name = params.get("collection_name", "")
    value_str = params.get("value_str", params.get("element_values", ""))
    split_symbol = params.get("split_symbol", ",")
    delete_mode = params.get("delete_mode", "lookup_ids_then_batch_delete")
    if not isinstance(collection_name, str):
        collection_name = str(collection_name)
    collection_name = collection_name.strip()
    if collection_name == "" or value_str.strip() == "":
        json_ret["summary"]["statusCode"] = 400
        json_ret["summary"]["msg"] = "collection_name和value_str不能为空"
        return json_ret

    try:
        raw_count, values, split_symbol = _parse_delimited_values(value_str, split_symbol)
        parallel_count = _parse_positive_int(params.get("parallel_count", 5), 5, "parallel_count", max_value=20)
        batch_size = _parse_positive_int(params.get("batch_size", 1000), 1000, "batch_size")
    except ValueError as e:
        json_ret["summary"]["statusCode"] = 400
        json_ret["summary"]["msg"] = str(e)
        return json_ret
    json_ret["data"]["raw_count"] = raw_count
    json_ret["data"]["total_count"] = len(values)
    json_ret["data"]["split_symbol"] = split_symbol
    json_ret["data"]["delete_mode"] = delete_mode
    json_ret["data"]["parallel_count"] = parallel_count
    if len(values) == 0:
        json_ret["summary"]["statusCode"] = 400
        json_ret["summary"]["msg"] = "value_str按分隔符拆分后没有有效value"
        return json_ret
    if delete_mode not in ["lookup_ids_then_batch_delete", "direct_by_value"]:
        json_ret["summary"]["statusCode"] = 400
        json_ret["summary"]["msg"] = "delete_mode仅支持lookup_ids_then_batch_delete或direct_by_value"
        return json_ret

    hg_host = assets["hg_host"].strip().strip("/")
    hg_token = assets["hg_token"].strip()
    timeout_seconds = assets.get("timeout_seconds", assets.get("conn_time_out", 10))
    hg_api = HoneyGuideAPI(hg_host, hg_token, context_info=context_info, timeout_seconds=timeout_seconds)

    if delete_mode == "direct_by_value":
        delete_started = time.perf_counter()
        for value in values:
            delete_result = hg_api.delete_generic_collection_element_by_value(collection_name, value)
            delete_summary = {
                "value": value,
                "statusCode": hg_api.summary["statusCode"],
                "msg": hg_api.summary["msg"]
            }
            if delete_result:
                if "deleted_count" in hg_api.summary:
                    delete_summary["deleted_count"] = hg_api.summary["deleted_count"]
                    json_ret["data"]["deleted_count"] += int(hg_api.summary["deleted_count"])
                json_ret["data"]["success_values"].append(delete_summary)
            else:
                json_ret["data"]["failed_values"].append(delete_summary)
        delete_seconds = time.perf_counter() - delete_started
        json_ret["data"]["delete_seconds"] = round(delete_seconds, 3)
        json_ret["data"]["delete_milliseconds"] = int(round(delete_seconds * 1000))
    else:
        def lookup_value(value):
            lookup_api = HoneyGuideAPI(hg_host, hg_token, context_info=context_info, timeout_seconds=timeout_seconds)
            element_id = lookup_api.get_generic_collection_element_id_by_value(collection_name=collection_name, element_value=value)
            return {
                "value": value,
                "element_id": element_id,
                "statusCode": lookup_api.summary["statusCode"],
                "msg": lookup_api.summary["msg"]
            }

        lookup_started = time.perf_counter()
        lookup_results = []
        value_order = {value: index for index, value in enumerate(values)}
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(parallel_count, len(values))) as executor:
            future_map = {executor.submit(lookup_value, value): value for value in values}
            for future in concurrent.futures.as_completed(future_map):
                value = future_map[future]
                try:
                    lookup_results.append(future.result())
                except Exception as e:
                    lookup_results.append({
                        "value": value,
                        "element_id": 0,
                        "statusCode": 500,
                        "msg": f"查询元素ID失败：{e}"
                    })
        lookup_results.sort(key=lambda item: value_order[item["value"]])
        lookup_seconds = time.perf_counter() - lookup_started
        json_ret["data"]["lookup_seconds"] = round(lookup_seconds, 3)
        json_ret["data"]["lookup_milliseconds"] = int(round(lookup_seconds * 1000))

        element_ids = []
        id_to_value = {}
        for result in lookup_results:
            if result["element_id"] > 0:
                element_ids.append(result["element_id"])
                id_to_value[result["element_id"]] = result["value"]
            elif result["statusCode"] == 0:
                not_found_summary = {
                    "value": result["value"],
                    "statusCode": 0,
                    "msg": f"元素{result['value']}本来就不存在"
                }
                json_ret["data"]["success_values"].append(not_found_summary)
                json_ret["data"]["not_found_values"].append(result["value"])
            else:
                json_ret["data"]["failed_values"].append(result)

        delete_started = time.perf_counter()
        for start_index in range(0, len(element_ids), batch_size):
            batch_ids = element_ids[start_index:start_index + batch_size]
            delete_result = hg_api.delete_generic_collection_elements_by_ids(batch_ids)
            if delete_result:
                deleted_count = int(hg_api.summary.get("deleted_count", len(batch_ids)))
                json_ret["data"]["deleted_count"] += deleted_count
                for element_id in batch_ids:
                    json_ret["data"]["success_values"].append({
                        "value": id_to_value[element_id],
                        "element_id": element_id,
                        "statusCode": 0,
                        "msg": "批量删除元素成功。"
                    })
            else:
                for element_id in batch_ids:
                    json_ret["data"]["failed_values"].append({
                        "value": id_to_value[element_id],
                        "element_id": element_id,
                        "statusCode": hg_api.summary["statusCode"],
                        "msg": hg_api.summary["msg"]
                    })
        delete_seconds = time.perf_counter() - delete_started
        json_ret["data"]["delete_seconds"] = round(delete_seconds, 3)
        json_ret["data"]["delete_milliseconds"] = int(round(delete_seconds * 1000))

    json_ret["data"]["success_count"] = len(json_ret["data"]["success_values"])
    json_ret["data"]["failed_count"] = len(json_ret["data"]["failed_values"])
    json_ret["data"]["not_found_count"] = len(json_ret["data"]["not_found_values"])
    if json_ret["data"]["failed_count"] == 0:
        json_ret["summary"]["statusCode"] = 0
        json_ret["summary"]["msg"] = (
            f"批量删除完成，成功处理{json_ret['data']['success_count']}个value，"
            f"实际删除{json_ret['data']['deleted_count']}个"
        )
    else:
        json_ret["summary"]["statusCode"] = 207
        json_ret["summary"]["msg"] = (
            f"批量删除完成，成功{json_ret['data']['success_count']}个，"
            f"失败{json_ret['data']['failed_count']}个"
        )
    return json_ret

def check_generic_collection_element_exists(params, assets, context_info):
    # 检查通用集合元素是否存在
    json_ret = {
        "code": 200, 
        "msg": "",  
        "data": {
            "element_exists": False
        },
        "summary": {            
            "statusCode": -1, 
            "msg": ""
        }
    }

    hg_host = assets["hg_host"].strip().strip("/")
    hg_token = assets["hg_token"].strip()
    timeout_seconds = assets.get("timeout_seconds", 10)
    hg_api = HoneyGuideAPI(hg_host, hg_token, context_info=context_info, timeout_seconds=timeout_seconds)
    collection_name = params.get("collection_name", "")
    element_value = params.get("element_value", "")
    if element_value == 0 or collection_name == "":
        json_ret["summary"]["statusCode"] = 400
        json_ret["summary"]["msg"] = "collection_name和element_value不能为空"
        return json_ret
    element_exists = hg_api.check_generic_collection_element_exists(collection_name=collection_name, element_value=element_value)
    json_ret["summary"]["statusCode"] = hg_api.summary["statusCode"]
    json_ret["summary"]["msg"] = hg_api.summary["msg"]
    if element_exists:
        json_ret["data"]["element_exists"] = True
        json_ret["summary"]["statusCode"] = 0
    else:
        json_ret["data"]["element_exists"] = False
        json_ret["summary"]["statusCode"] = 404
    return json_ret

def health_check(params, assets, context_info):
    # 健康检查
    json_ret = {
        "code": 200, 
        "msg": "", 
        "data": {}, 
        "summary": {
            "statusCode": -1, 
            "msg": ""
        }
    }
    if context_info is None:
        context_info ={
            "appName": "generic_collection_manager", 
            "actionName": "health_check", 
            "eventId": "1", 
            "activieId": "1", 
            "logMode": False
        }
    elif isinstance(context_info, dict):
        context_info["eventId"] = "1"
        context_info["activieId"] = "1"
        context_info["logMode"] = False
    
    hg_host = assets["hg_host"].strip().strip("/")
    hg_token = assets["hg_token"].strip()
    timeout_seconds = assets.get("timeout_seconds", 10)
    
    hg_api = HoneyGuideAPI(hg_host, hg_token, context_info=context_info, timeout_seconds=timeout_seconds)
    health_check_result = hg_api.health_check()
    json_ret["summary"]["statusCode"] = hg_api.summary["statusCode"]
    json_ret["summary"]["msg"] = hg_api.summary["msg"]
    if health_check_result:
        json_ret["summary"]["statusCode"] = 200
        json_ret["summary"]["msg"] = "健康检查成功"
    return json_ret
