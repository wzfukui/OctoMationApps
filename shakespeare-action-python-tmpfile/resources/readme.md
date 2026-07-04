# tmpfile.link (tfLink) - Octomation App

## 简介

基于 [tmpfile.link (tfLink)](https://tmpfile.link) 的 Octomation SOAR 应用，支持从 Playbook 自动将本地文件或文本内容上传到临时文件托管服务，获取可直接分发的下载链接（包含 URL 编码版本）。

- **文件大小限制**：单文件最大 100MB
- **保留时长**：匿名上传 7 天自动删除；认证用户可获得更长保留期
- **下载域名**：安全文件（图片/文档/音视频）使用 `d.tmpfile.link`，其他文件使用 `d1-d10.tfdl.net`

---

## 配置项（Assets）

| 配置项 | 类型 | 说明 |
|--------|------|------|
| `user_id` | string | 用户ID，可选，匿名上传无需填写 |
| `auth_token` | password | 认证 Token，可选，匿名上传无需填写 |

> 若不填写 `user_id` 和 `auth_token`，App 将以匿名方式上传，文件 7 天后自动删除。

---

## Actions

### 1. upload_file — 上传本地文件

从指定的**本地文件路径**读取文件并上传到 tmpfile.link。

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_path` | string | ✅ | 本地文件的绝对路径，例如：`/tmp/report.pdf` |

**输出关键字段：**
- `action_result.data.download_link_encoded` — **URL 编码后的下载链接**（推荐在 Playbook 中引用）
- `action_result.data.download_link` — 原始下载链接
- `action_result.data.file_size` — 文件字节大小
- `action_result.data.file_type` — MIME 类型

---

### 2. upload_text — 上传文本内容

将字符串内容保存为临时文件后上传，适合上传**告警摘要、日志片段、报告文本**等。

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `content` | string | ✅ | 要上传的文本内容 |
| `file_name` | string | ❌ | 文件名，默认 `content.txt` |

---

### 3. health_check — 健康检查

上传一个极小的测试文件，验证 tmpfile.link 服务是否可达以及认证信息是否正确。

---

## 使用示例（curl 参考）

```bash
# 匿名上传
curl -X POST https://tmpfile.link/api/upload -F "file=@/path/to/file.pdf"

# 认证上传
curl -X POST \
  -H "X-User-Id: YOUR_USER_ID" \
  -H "X-Auth-Token: YOUR_AUTH_TOKEN" \
  https://tmpfile.link/api/upload \
  -F "file=@/path/to/file.pdf"
```

**API 响应示例：**
```json
{
  "fileName": "report.pdf",
  "downloadLink": "https://d.tmpfile.link/public/2026-05-14/uuid/report.pdf",
  "downloadLinkEncoded": "https://d.tmpfile.link/public/2026-05-14/uuid/report.pdf",
  "size": 102400,
  "type": "application/pdf",
  "uploadedTo": "public"
}
```
