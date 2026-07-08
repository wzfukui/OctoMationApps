# Generic_Collection_Manager通用集合管理工具

[toc]

## 一、APP介绍

通用集合管理工具，用于管理编排自动化系统中通用集合，包括功能：
- 列举集合名称及元素
- 创建和删除集合
- 创建、删除、修改集合元素

**各类操作均为原子化操作，涉及到批量处理、判断元素是否在集合中等需求，建议通过剧本中规则节点的判断逻辑实现。**


| 内容      | 详细描述       |
|:--------|:-----------|
| app上次版本 | 2.0.5      |
| app更新版本 | 2.0.6      |
| 发布时间    | 2022-12-20 |
| 更新时间    | 2026-07-08 |
| 原开发者     | S*B        |
| 更新人     | [wzfukui](https://github.com/wzfukui)   |
| 对接方式  | API |
| 开发语言    |  Python 3.6+  |
| 更新地址 |[flagify-com/OctoMationApps](https://github.com/flagify-com/OctoMationApps)|

## 二、APP使用注意事项


1）**发布或修改记录**

| 更新时间       | 更新记录                                    | 更新人| 更新版本  |
|------------|-----------------------------------------|----|-------|
| 2022-12-20 | APP发布（Python版）                          | S*B   | 1.1.0 |
| 2023-06-09 | 元素新增或覆盖动作添加生效时间参数逻辑；过期时间逻辑调整            | Han | 1.6.0 |
| 2023-07-04 | 向指定集合添加元素动作：修复添加url字符元素问题；捕获接口原报错信息输出   | Han | 1.6.1 |
| 2024-03-21 | db_util文件get_db函数修改SDK取Mysql连接信息 | Han | 1.6.1 |
| 2024-05-29 | 向指定集合添加元素动作：修复通用集合修改已存在元素备注字段问题         | Han | 1.6.2 |
| 2024-06-20 | 修改【判断元素存在于指定通用集合中】动作：输出渲染               | Han | 1.6.4 |
| 2024-07-27 | 添加集合元素时，结果中增加duplicated，表示是否有重复元素               | wzfukui | 1.6.5 |
| 2024-08-19 | 修复IP子网掩码方式，API报格式错误的问题               | wzfukui | 1.6.6 |
| 2024-08-26 | 废弃MySQL连接方式，纯API对接，降低依赖，删除不必要的功能（批量、导出excel）    | wzfukui | 2.0.0 |
| 2024-08-30 | 修复bug，优化健康检查代码，移除测试token    | wzfukui | 2.0.1 |
| 2026-07-04 | 修复集合元素列表查询的集合筛选参数传递；适配HG平台单页200条上限，避免batch_size超过200时提前停止翻页；将batch_size默认值调整为200；基于HG分页返回的totalPages对后续页使用受控并发查询；补充参数说明 | Codex | 2.0.2 |
| 2026-07-04 | 为集合元素列表查询新增parallel_page_count参数，支持按需调整后续页并发查询数量 | Codex | 2.0.3 |
| 2026-07-08 | 新增按ID批量删除动作batch_delete_elements_by_ids；优化按value批量删除动作，默认并发查询元素ID后调用batchDelete批量删除，保留direct_by_value兼容模式；补充目标服务器性能测试工具和说明 | Codex | 2.0.5 |
| 2026-07-08 | 修复并发查ID时SDK日志上下文缺少activeId等字段导致动作失败的问题；兼容activieId拼写，并将单个查询线程异常降级为失败明细 | Codex | 2.0.6 |

2）**API使用说明**
- 列举集合所有元素，会因为元素过多而耗费大量时间，不宜高频使用，即使使用，也建议使用异步动作完成
- `batch_size` 表示每次分页请求的返回数量，默认200。HG平台单页上限为200，输入超过200时动作会按200分页查询。
- `max_count` 表示本动作累计返回的最大数量，默认200。需要向下游传递更多元素时可调大，例如1000或20000；实际耗时取决于元素总量、网络和动作超时时间。
- `parallel_page_count` 表示集合元素列表查询后续页的最大并发查询数量，默认5，最大10；设置为1时等同顺序查询。
- 集合元素列表查询会先请求第一页；当HG返回 `totalPages` 时，动作会对后续页使用受控并发查询并按页码顺序合并结果。
- 执行结果页面可能因为平台展示性能只渲染部分数据，实际下游输出数量以 `action_result.data.count` 和 `action_result.data.elements` 为准。
- 所有功能是通过API接口方式完成的，速度和效率上肯定部署直接数据库操作。但因为集合操作除了涉及到数据库同步，还涉及到zk信息同步，因此并发不要太高，如有必要可以在前面节点，随机Sleep。
- IP地址集合是另一种高性能集合，为保证应用功能聚焦和稳定性，由单独的APP实现，
- **创建一个已经存在的集合/元素，默认返回为0， 创建成功**
- **删除一个不存在集合/元素元，默认返回为0， 删除成功**

## 三、资源配置说明 

| 参数 | 类型 | 样例 | 必须 | 默认值 | 说明 |
|:-----|:-----|:-----|:-----|:-----|:-----|
| hg_host | 字符串 | | 是 | | API 服务器URL，例https://192.168.1.1 |
| hg_token | password | | 是 | | API Token，通过系统设置界面生成API Token |
| conn_time_out | 整数 | | 是 | 10 | 请求API服务连接时间超时，单位：秒 |



## 四、动作说明

### list_generic_collections

**描述**：集合_返回所有通用集合名单列表

**入参说明**

| 参数 | 类型 | 数据样例 | 必须 | 默认值 | 说明 |
|:-----|:-----|:---------|:-----|:-----|:-----|
| batch_size | 整数 | | 否 | 200 | 每次分页请求的返回数量；HG平台单页上限为200，超过200会按200处理 |
| max_count | 整数 | | 否 | 200 | 本动作累计返回的最大数量；需要更多结果时可调大 |

**出参说明**

| 参数 | 类型 | 数据样例 | 默认值 | 说明 |
|:-----|:-----|:---------|:-----|:-----|
| action_result.data.collections | JSON数组 | | | 所有集合的属性及元素情况，组成的数组 |
| action_result.data.collections.*.id | 整数 | | | 集合的ID号 |
| action_result.data.collections.*.name | 字符串 | | | 集合名称 |
| action_result.data.collections.*.cnName | 字符串 | | | 集合中文名 |
| action_result.data.collections.*.description | 字符串 | | | 集合描述 |
| action_result.data.collections.*.num | 整数 | | | 集合元素数量 |
| action_result.data.collections.*.createTime | 字符串 | | | 集合创建时间 |
| action_result.data.count | 整数 | | | 本次查询到的集合总数量 |
| action_result.summary.statusCode | 整数 | | 0 | 返回错误码 |
| action_result.summary.msg | 字符串 | | | 返回错误消息 |

### create_generic_collection

**描述**：集合_创建一个通用集合

**入参说明**

| 参数 | 类型 | 数据样例 | 必须 | 默认值 | 说明 |
|:-----|:-----|:---------|:-----|:-----|:-----|
| collection_name | 字符串 | | 是 | | 集合的名称，仅支持：英文/数字/下划线，最长64字符 |
| collection_cnname | 字符串 | | 是 | | 集合的中文名称，最长64字符 |
| collection_description | 字符串 | | 否 | | 集合的描述信息，最长64字符 |

**出参说明**

| 参数 | 类型 | 数据样例 | 默认值 | 说明 |
|:-----|:-----|:---------|:-----|:-----|
| action_result.data.element_id | 整数 | | | 集合ID号（数字） |
| action_result.data.duplicated | 布尔值 | | | 集合创建前是否已经存在 |
| action_result.summary.statusCode | 整数 | | 0 | 返回错误码 |
| action_result.summary.msg | 字符串 | | | 返回错误消息 |


### delete_generic_collection

**描述**：集合_删除一个通用集合

**入参说明**

| 参数 | 类型 | 数据样例 | 必须 | 默认值 | 说明 |
|:-----|:-----|:---------|:-----|:-----|:-----|
| collection_id | 整数 | | 否 | | 集合的ID号，一长串数字，如：11268278432702172 |
| collection_name | 字符串 | | 否 | | 集合名称（集合ID与集合名称，两者不能同时为空） |

**出参说明**

| 参数 | 类型 | 数据样例 | 默认值 | 说明 |
|:-----|:-----|:---------|:-----|:-----|
| action_result.summary.statusCode | 整数 | | 0 | 返回错误码 |
| action_result.summary.msg | 字符串 | | | 返回错误消息 |

### list_generic_collection_elements

**描述**：集合_返回指定集合的元素列表（耗时，不建议在剧本中直接使用，建议使用异步动作执行）

**入参说明**

| 参数 | 类型 | 数据样例 | 必须 | 默认值 | 说明 |
|:-----|:-----|:---------|:-----|:-----|:-----|
| collection_id | 整数 | | 否 | | 集合ID号，一长串数字，如：1126827843270217 |
| collection_name | 字符串 | | 否 | | 集合名称，例：BLACKLIST，集合名称与ID不能同时为空 |
| batch_size | 整数 | | 否 | 200 | 每次分页请求的返回数量；HG平台单页上限为200，超过200会按200处理 |
| max_count | 整数 | | 否 | 200 | 本动作累计返回的最大数量；需要更多结果时可调大 |
| parallel_page_count | 整数 | | 否 | 5 | 后续页最大并发查询数量；最大10；设置为1时等同顺序查询 |

**出参说明**

| 参数 | 类型 | 数据样例 | 默认值 | 说明 |
|:-----|:-----|:---------|:-----|:-----|
| action_result.data.elements | JSON数组 | | | 所有元素的信息，组成的数组 |
| action_result.data.elements.*.id | 整数 | | | 元素的ID号 |
| action_result.data.elements.*.value | 字符串 | | | 元素的值 |
| action_result.data.elements.*.remark | 字符串 | | | 元素的备注 |
| action_result.data.elements.*.collectionId | 整数 | | | 元素所在集合的ID号 |
| action_result.data.elements.*.collectionName | 字符串 | | | 元素所在集合的名称 |
| action_result.data.elements.*.createTime | 字符串 | | | 元素创建时间 |
| action_result.data.elements.*.updateTime | 字符串 | | | 元素更新时间 |
| action_result.data.count | 整数 | | | 本次查询到的元素总数量 |
| action_result.summary.statusCode | 整数 | | 0 | 返回错误码 |
| action_result.summary.msg | 字符串 | | | 返回错误消息 |

### get_generic_collection_element_info

**描述**：元素_获取集合中指定元素的信息

**入参说明**

| 参数 | 类型 | 数据样例 | 必须 | 默认值 | 说明 |
|:-----|:-----|:---------|:-----|:-----|:-----|
| collection_id | 整数 | | 否 | | 集合ID号，一长串数字，如：1126827843270217 |
| collection_name | 字符串 | | 否 | | 集合名称，例：BLACKLIST，集合名称与ID不能同时为空 |
| element_value | 字符串 | | 是 | | 元素的值（精准匹配） |

**出参说明**

| 参数 | 类型 | 数据样例 | 默认值 | 说明 |
|:-----|:-----|:---------|:-----|:-----|
| action_result.data.id | 整数 | | | 元素的ID号 |
| action_result.data.value | 字符串 | | | 元素的值 |
| action_result.data.remark | 字符串 | | | 元素的备注 |
| action_result.data.collectionId | 整数 | | | 元素的所在集合ID |
| action_result.data.collectionName | 字符串 | | | 元素的所在集合名 |
| action_result.data.createTime | 字符串 | | | 元素的创建时间 |
| action_result.data.updateTime | 字符串 | | | 元素的更新时间 |
| action_result.summary.statusCode | 整数 | | 0 | 返回错误码 |
| action_result.summary.msg | 字符串 | | | 返回错误消息 |


### add_generic_collection_item

**描述**：元素_向通用集合添加元素

**入参说明**

| 参数 | 类型 | 数据样例 | 必须 | 默认值 | 说明 |
|:-----|:-----|:---------|:-----|:-----|:-----|
| collection_name | 字符串 | | 是 | | 集合名称，例：BLACKLIST |
| element_value | 字符串 | | 是 | | 元素值 |
| element_remark | 字符串 | | 否 | | 元素备注 |
| update_if_exist | 布尔值 | | 否 | false | 元素已经存在时，是否强制更新备注 |

**出参说明**

| 参数 | 类型 | 数据样例 | 默认值 | 说明 |
|:-----|:-----|:---------|:-----|:-----|
| action_result.data.duplicated | 布尔值 | | false | 元素是否已经存在 |
| action_result.summary.statusCode | 整数 | | 0 | 返回错误码 |
| action_result.summary.msg | 字符串 | | | 返回错误消息 |

### update_generic_collection_element

**描述**：元素_更新集合元素信息（备注）

**入参说明**

| 参数 | 类型 | 数据样例 | 必须 | 默认值 | 说明 |
|:-----|:-----|:---------|:-----|:-----|:-----|
| collection_name | 字符串 | | 是 | | 集合名称，例：BLACKLIST |
| element_value | 字符串 | | 是 | | 元素的值，元素ID和值不能同时为空 |
| element_remark | 字符串 | | 是 | | 元素备注 |

**出参说明**

| 参数 | 类型 | 数据样例 | 默认值 | 说明 |
|:-----|:-----|:---------|:-----|:-----|
| action_result.summary.statusCode | 整数 | | 0 | 返回错误码 |
| action_result.summary.msg | 字符串 | | | 返回错误消息 |

### delete_generic_collection_element

**描述**：元素_从集合中删除元素

**入参说明**

| 参数 | 类型 | 数据样例 | 必须 | 默认值 | 说明 |
|:-----|:-----|:---------|:-----|:-----|:-----|
| collection_name | 字符串 | | 是 | | 集合名称，例：BLACKLIST，不能为空 |
| element_value | 字符串 | | 是 | | 元素的值，不能为空 |

**出参说明**

| 参数 | 类型 | 数据样例 | 默认值 | 说明 |
|:-----|:-----|:---------|:-----|:-----|
| action_result.summary.statusCode | 字符串 | | 0 | 返回错误码 |
| action_result.summary.msg | 字符串 | | | 返回错误消息 |

### batch_delete_elements_by_ids

**描述**：元素_按ID批量删除集合元素

此动作直接调用服务端批量删除接口 `/api/collectionElement/batchDelete`，请求体为元素ID数组。适合剧本中已经提前拿到元素ID的场景，写操作只需要一次或少量几次请求。

**入参说明**

| 参数 | 类型 | 数据样例 | 必须 | 默认值 | 说明 |
|:-----|:-----|:---------|:-----|:-----|:-----|
| id_str | 字符串 | 367710,367709,367708 | 是 | | 待删除的多个元素ID，按分隔符拆分 |
| split_symbol | 字符串 | , | 否 | , | id_str的分隔符，默认英文逗号 |
| batch_size | 整数 | 1000 | 否 | 1000 | 每次调用batchDelete提交的ID数量 |

**出参说明**

| 参数 | 类型 | 数据样例 | 默认值 | 说明 |
|:-----|:-----|:---------|:-----|:-----|
| action_result.data.total_count | 整数 | 3 | 0 | 去重后的实际删除ID数量 |
| action_result.data.deleted_count | 整数 | 3 | 0 | 服务端返回的实际删除数量 |
| action_result.data.delete_milliseconds | 整数 | 200 | 0 | 批量删除耗时，单位毫秒 |
| action_result.summary.statusCode | 字符串 | | 0 | 返回错误码。全部成功为0，部分失败为207 |
| action_result.summary.msg | 字符串 | | | 返回错误消息 |

### batch_delete_elements_by_value

**描述**：元素_批量删除集合中的多个value

默认模式为 `lookup_ids_then_batch_delete`：先按 value 并发查询元素ID，再调用 `/api/collectionElement/batchDelete` 按ID批量删除。这样可以把多 value 删除的写操作压缩为一次或少量几次批量请求。也可设置 `delete_mode=direct_by_value`，改为逐个调用 `/api/collectionElement/deleteElement` 按 `collectionName + value` 直接删除。

**入参说明**

| 参数 | 类型 | 数据样例 | 必须 | 默认值 | 说明 |
|:-----|:-----|:---------|:-----|:-----|:-----|
| collection_name | 字符串 | BLACKLIST | 是 | | 集合名称 |
| value_str | 字符串 | 1.1.1.1,2.2.2.2 | 是 | | 待删除的多个value，按分隔符拆分 |
| split_symbol | 字符串 | , | 否 | , | value_str的分隔符，默认英文逗号 |
| delete_mode | 字符串 | lookup_ids_then_batch_delete | 否 | lookup_ids_then_batch_delete | 删除模式：先查ID再批量删除，或逐个按value直删 |
| parallel_count | 整数 | 5 | 否 | 5 | 并发查ID数量，最大20 |
| batch_size | 整数 | 1000 | 否 | 1000 | 每次调用batchDelete提交的ID数量 |

**出参说明**

| 参数 | 类型 | 数据样例 | 默认值 | 说明 |
|:-----|:-----|:---------|:-----|:-----|
| action_result.data.raw_count | 整数 | 3 | 0 | 输入拆分并过滤空值后的value数量，包含重复项 |
| action_result.data.total_count | 整数 | 2 | 0 | 去重后的实际删除value数量 |
| action_result.data.success_count | 整数 | 2 | 0 | 删除成功的value数量 |
| action_result.data.failed_count | 整数 | 0 | 0 | 删除失败的value数量 |
| action_result.data.deleted_count | 整数 | 2 | 0 | 服务端返回的实际删除数量 |
| action_result.data.not_found_count | 整数 | 0 | 0 | 未查询到ID、无需删除的value数量 |
| action_result.data.lookup_milliseconds | 整数 | 1200 | 0 | 查ID耗时，单位毫秒 |
| action_result.data.delete_milliseconds | 整数 | 200 | 0 | 批量删除耗时，单位毫秒 |
| action_result.data.success_values | 数组 | | | 删除成功的value明细 |
| action_result.data.failed_values | 数组 | | | 删除失败的value明细 |
| action_result.summary.statusCode | 字符串 | | 0 | 返回错误码。全部成功为0，部分失败为207 |
| action_result.summary.msg | 字符串 | | | 返回错误消息 |

**目标服务器性能测试**

仓库内提供 `benchmark_batch_delete.py`，可在目标服务器环境上创建临时测试集合、添加指定数量元素，然后用逗号拼接的 `value_str` 调用 `batch_delete_elements_by_value` 并输出删除耗时。脚本只操作自动创建的 `unitest_batch_delete_...` 临时集合，结束时会删除该集合。

```bash
HG_API_URL="https://example.test" HG_TOKEN="***" python3 benchmark_batch_delete.py --count 1000 --parallel-count 5
```

### check_generic_collection_element_exists

**描述**：元素_判断元素在集合中是否存在

**入参说明**

| 参数 | 类型 | 数据样例 | 必须 | 默认值 | 说明 |
|:-----|:-----|:---------|:-----|:-----|:-----|
| collection_name | 字符串 | | 是 | | 集合名称，例：BLACKLIST，不能为空 |
| element_value | 字符串 | | 是 | | 元素的值，不能为空 |

**出参说明**

| 参数 | 类型 | 数据样例 | 默认值 | 说明 |
|:-----|:-----|:---------|:-----|:-----|
| action_result.data.element_exist | 布尔值 | | false | 元素是否存在 |
| action_result.summary.statusCode | 字符串 | | 0 | 返回错误码 |
| action_result.summary.msg | 字符串 | | | 返回错误消息 |

### health_check

**描述**：健康检查

**入参说明**

此动作没有入参。

**出参说明**

| 参数 | 类型 | 数据样例 | 默认值 | 说明 |
|:-----|:-----|:---------|:-----|:-----|
| action_result.summary.statusCode | 字符串 | | 200 | 返回错误码 |
| action_result.summary.msg | 字符串 | | | 返回错误消息 |
