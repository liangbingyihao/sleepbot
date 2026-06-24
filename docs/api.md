# SleepBot API 文档

## 目录

- [通用说明](#通用说明)
  - [公共请求头](#公共请求头)
  - [响应格式](#响应格式)
  - [错误码说明](#错误码说明)
- [1. 用户基本信息](#1-用户基本信息)
  - [1.1 获取用户信息](#1-1-获取用户信息)
  - [1.2 初始化用户信息](#1-2-初始化用户信息)
  - [1.3 修改昵称](#1-3-修改昵称)
- [2. 用户睡眠时间配置](#2-用户睡眠时间配置)
  - [2.1 获取当前用户睡眠配置](#2-1-获取当前用户睡眠配置)
  - [2.2 设置/更新睡眠配置](#2-2-设置-更新睡眠配置)
  - [2.3 删除睡眠配置](#2-3-删除睡眠配置)
- [3. 用户状态上报](#3-用户状态上报)
  - [3.1 上报状态](#3-1-上报状态)
  - [3.2 获取最新状态](#3-2-获取最新状态)
  - [3.3 获取状态历史](#3-3-获取状态历史)
- [4. 好友监督关系管理](#4-好友监督关系管理)
  - [4.1 发送好友申请](#4-1-发送好友申请)
  - [4.2 处理好友申请](#4-2-处理好友申请)
  - [4.3 获取收到的好友申请](#4-3-获取收到的好友申请)
  - [4.4 获取发出的好友申请](#4-4-获取发出的好友申请)
  - [4.5 修改好友备注](#4-5-修改好友备注)
  - [4.6 删除好友关系](#4-6-删除好友关系)
   - [4.7 获取好友列表](#4-7-获取好友列表)
   - [4.8 解锁题库](#4-8-解锁题库)
     - [4.8.1 获取配置](#4-8-1-获取配置)
     - [4.8.2 更新配置](#4-8-2-更新配置)
     - [4.8.3 随机抽题](#4-8-3-随机抽题)
- [5. 早睡鼓励素材](#5-早睡鼓励素材)
  - [5.1 生成上传 Session](#5-1-生成上传-session)
  - [5.2 查询 Session 状态](#5-2-查询-session-状态)
  - [5.3 素材采集页面](#5-3-素材采集页面)
  - [5.4 提交素材](#5-4-提交素材)
  - [5.5 获取收到的素材](#5-5-获取收到的素材)
  - [5.6 审核素材](#5-6-审核素材)
- [6. 睡眠报告](#6-睡眠报告)
  - [6.1 日报](#6-1-日报)
  - [6.2 周报](#6-2-周报)
  - [6.3 月报](#6-3-月报)

---

## 通用说明

- **Base URL**: `http://localhost:5050/api/sleep`
- **Content-Type**: `application/json`

### 公共请求头

所有接口需要在请求头中携带以下公共参数：

| 请求参数 | 说明 | 必填 |
|---|---|---|
| X-User-Id | 用户 ID | 是 |
| X-Bundle-ID | 包名 | 否 |
| X-App-Version | 版本号 | 否 |
| X-Device-ID | 设备 ID | 否 |
| X-Timezone | 时区，如 Asia/Hong_Kong | 否 |
| X-Language | 语言，如 zh-Hant-TW | 否 |

### 响应格式

**成功响应**:

```json
{"code": "OK", "data": {}}
```

HTTP 状态码: 200

**错误响应**:

```json
{"code": "XXX", "msg": "xxxx"}
```

### 错误码说明

| 错误码 | 说明 |
|---|---|
| INVALID_PARAMETER | 参数错误 |
| INTERNAL_SERVER_ERROR | 服务器内部错误 |
| NOT_FOUND | 接口未存在 |
| AUTH_REQUIRED | 需要用户认证，或未通过 |
| TOKEN_EXPIRED | 特指 Access Token 过期 |
| MEMBERSHIP_REQUIRED | 需要会员的操作 |
| DUPLICATE_OPERATION | 重复的操作 |

---

## 1. 用户基本信息

### 1.1 获取用户信息

```
GET /profile
```

**请求头**: `X-User-Id` 必填。

**响应示例**:
```json
{
  "code": "OK",
  "data": {
    "id": 1,
    "user_id": "user123",
    "nickname": "张三",
    "avatar_url": "https://...",
    "region": "cn",
    "source_code": "ABC123",
    "created_at": "2026-05-25 10:00:00",
    "updated_at": "2026-05-25 10:00:00"
  }
}
```

### 1.2 初始化用户信息

```
POST /profile
```

**请求体**:
```json
{
  "nickname": "张三",
  "avatar_url": "https://...",
  "region": "cn",
  "source_code": "ABC123"
}
```

所有字段可选。

**响应示例**: 同获取接口。

### 1.3 修改昵称

```
PATCH /profile/nickname
```

**请求体**:
```json
{
  "nickname": "新昵称"
}
```

**响应示例**: 同获取接口。

---

## 2. 用户睡眠时间配置

### 2.1 获取当前用户睡眠配置

```
GET /config
```

**响应示例**:
```json
{
  "code": "OK",
  "data": {
    "id": 1,
    "user_id": "user123",
    "sleep_start_time": "23:00",
    "sleep_end_time": "08:00",
    "timezone": "Asia/Shanghai",
    "created_at": "2026-05-25 10:00:00",
    "updated_at": "2026-05-25 10:00:00"
  }
}
```

### 2.2 设置/更新睡眠配置

```
POST /config
```

**请求体**:
```json
{
  "sleep_start_time": "23:00",
  "sleep_end_time": "08:00",
  "timezone": "Asia/Shanghai",
  "sleep_is_unhealthy": false
}
```

`timezone` 可选，默认为 `UTC`。使用 IANA 时区标识符（如 `Asia/Shanghai`、`America/New_York`、`Europe/London`）。`sleep_is_unhealthy` 可选，默认 false，由客户端在用户坚持使用 <6h 时段时设为 true。

**响应示例**:
```json
{
  "code": "OK",
  "data": {
    "id": 1,
    "user_id": "user123",
    "sleep_start_time": "23:00",
    "sleep_end_time": "08:00",
    "timezone": "Asia/Shanghai",
    "created_at": "2026-05-25 10:00:00",
    "updated_at": "2026-05-25 10:00:00"
  }
}
```

### 2.3 删除睡眠配置

```
DELETE /config
```

**响应示例**:
```json
{
  "code": "OK",
  "msg": "删除成功"
}
```

---

## 3. 用户状态上报

### 3.1 上报状态

```
POST /status
```

**请求体**:
```json
{
  "status": "locked",
  "reported_at": "2026-06-22T18:19:00+08:00"
}
```

可选状态值: `locked`(锁屏), `active`(活跃), `idle`(空闲), `sleeping`(睡眠中), `awake`(清醒)

`reported_at` 可选，ISO 格式时间戳。带时区偏移时服务端自动转 UTC 存储；不带时区则视为 UTC。不传则使用服务器当前 UTC 时间。

**响应示例**:
```json
{
  "code": "OK",
  "data": {
    "id": 1,
    "user_id": "user123",
    "status": "locked",
    "reported_at": "2026-05-25 22:30:00"
  }
}
```

### 3.2 获取最新状态

```
GET /status/latest
```

**响应示例**:
```json
{
  "code": "OK",
  "data": {
    "id": 1,
    "user_id": "user123",
    "status": "locked",
    "reported_at": "2026-05-25 22:30:00"
  }
}
```

### 3.3 获取状态历史

```
GET /status/history?page=1&per_page=20
```

**响应示例**:
```json
{
  "code": "OK",
  "data": {
    "items": [
      {
        "id": 1,
        "user_id": "user123",
        "status": "locked",
        "reported_at": "2026-05-25 22:30:00"
      }
    ],
    "page": 1,
    "per_page": 20,
    "total": 1,
    "pages": 1
  }
}
```

---

## 4. 好友监督关系管理

### 4.1 发送好友申请

```
POST /friends/requests
```

**请求体**:
```json
{
  "to_user_id": "target_user_id",
  "from_name": "张三",
  "to_name": "李四",
  "apply_message": "一起监督早睡早起！"
}
```

`to_user_id` 必填。`from_name`（对方将看到的你的备注）、`to_name`（你将看到的对方的备注）、`apply_message` 均为可选。

**响应示例**:
```json
{
  "code": "OK",
  "data": {
    "id": 1,
    "from_user_id": "user123",
    "to_user_id": "target_user_id",
    "status": "accepted",
    "apply_message": "一起监督早睡早起！",
    "from_name": "张三",
    "to_name": "李四",
    "created_at": "2026-05-25 10:00:00",
    "updated_at": "2026-05-25 10:00:00"
  }
}
```

### 4.2 处理好友申请

```
POST /friends/requests/<request_id>/respond
```

**请求体**:
```json
{
  "action": "accept"
}
```

`action` 可选值: `accept`(接受), `reject`(拒绝)

**响应示例**:
```json
{
  "code": "OK",
  "data": {
    "id": 1,
    "from_user_id": "user123",
    "to_user_id": "target_user_id",
    "status": "accepted",
    "created_at": "2026-05-25 10:00:00",
    "updated_at": "2026-05-25 10:00:00"
  }
}
```

### 4.3 获取收到的好友申请

```
GET /friends/requests/incoming
```

**响应示例**:
```json
{
  "code": "OK",
  "data": [
    {
      "id": 1,
      "from_user_id": "user456",
      "to_user_id": "user123",
      "status": "pending",
      "apply_message": "一起监督早睡早起！",
      "created_at": "2026-05-25 10:00:00",
      "updated_at": "2026-05-25 10:00:00"
    }
  ]
}
```

### 4.4 获取发出的好友申请

```
GET /friends/requests/outgoing
```

**响应示例**:
```json
{
  "code": "OK",
  "data": [
    {
      "id": 1,
      "from_user_id": "user123",
      "to_user_id": "user456",
      "status": "pending",
      "apply_message": "一起监督早睡早起！",
      "created_at": "2026-05-25 10:00:00",
      "updated_at": "2026-05-25 10:00:00"
    }
  ]
}
```

### 4.5 修改好友备注

```
PATCH /friends/<friendship_id>/name
```

**请求体**:
```json
{
  "name": "小张"
}
```

当前用户为 `from_user` 时修改 `to_name`，为 `to_user` 时修改 `from_name`。

**响应示例**:
```json
{
  "code": "OK",
  "data": {
    "id": 1,
    "from_user_id": "user123",
    "to_user_id": "friend_user_id",
    "status": "accepted",
    "apply_message": "",
    "from_name": "",
    "to_name": "小张",
    "created_at": "2026-05-25 10:00:00",
    "updated_at": "2026-05-25 10:00:00"
  }
}
```

### 4.6 删除好友关系

```
DELETE /friends/<friendship_id>
```

任一方均可删除。逻辑删除，好友列表中不再显示。

**响应示例**:
```json
{
  "code": "OK",
  "data": {
    "msg": "删除成功"
  }
}
```

### 4.7 获取好友列表

```
GET /friends
```

**响应示例**:
```json
{
  "code": "OK",
  "data": {
    "friends": [
      {
        "friendship_id": 1,
        "user_id": "friend_user_id",
        "friend_name": "张小凡",
        "friend_avatar": "https://...",
        "apply_message": "",
        "created_at": "2026-05-25 10:00:00",
        "sleep_config": {
          "sleep_start_time": "23:00",
          "sleep_end_time": "08:00"
        },
        "sleep_status": "locked"
      }
    ],
    "next_poll_at": "2026-06-24 15:01:00"
  }
}
```

`sleep_status` 由服务端根据好友的睡眠配置和最新状态计算：

| 值 | 判定 |
|------|------|
| `awake` | 当前时间不在好友睡眠时段内 |
| `unlocked` | 在睡眠时段内，且好友上报过解锁操作（最新状态非 locked） |
| `locked` | 在睡眠时段内，好友未上报解锁操作（最新状态为 locked 或无数据） |
| `no_config` | 好友未配置睡眠时间 |

`sleep_status` 仅在好友处于睡眠时段时查询 `user_status` 表，否则直接返回 `awake`，零额外查询。

`next_poll_at` 为客户端下一次应轮询的 UTC 时间，算法：取所有好友窗口结束时间（在窗口内）和窗口开始时间（不在窗口内）的最早值，最小间隔 60 秒保底。客户端只需：

```
setTimeout(() => GET /friends, next_poll_at - now)
```

### 4.8 解锁题库

题库以 JSON 格式存储在 `app_config` 表中，`config_type = 'quiz_questions'`，每条记录对应一种语言。题目字段包括 `type`（single_choice / multiple_choice）、`title`、`options[]`（含 `id`、`text`）、`answers`（正确答案 ID 数组）、`explanation`。

#### 4.8.1 获取配置

```
GET /configs/<config_type>?locale=zh-CN
```

`locale` 可选，默认从 `X-Language` 请求头读取；未匹配时回退到 `locale=''` 的记录。

**响应示例**:
```json
{
  "code": "OK",
  "data": {
    "id": 1,
    "config_type": "quiz_questions",
    "locale": "zh-CN",
    "data": {
      "questions": [
        {
          "id": 1,
          "type": "single_choice",
          "title": "睡眠的黄金时间段是？",
          "options": [
            {"id": 1, "text": "22:00-06:00"},
            {"id": 2, "text": "00:00-08:00"},
            {"id": 3, "text": "02:00-10:00"},
            {"id": 4, "text": "23:00-07:00"}
          ],
          "answers": [1],
          "explanation": "人体褪黑素分泌高峰期在22:00-06:00"
        }
      ]
    },
    "version": 1,
    "created_at": "2026-05-25 10:00:00",
    "updated_at": "2026-05-25 10:00:00"
  }
}
```

#### 4.8.2 更新配置

```
PUT /configs/<config_type>?locale=zh-CN
```

**请求体**: 直接传入 JSON 对象作为 `data` 字段的值。

```json
{
  "questions": [...]
}
```

**响应**: 同获取接口。

#### 4.8.3 随机抽题

```
GET /quiz/random?locale=zh-CN
```

从 `config_type = 'quiz_questions'` 的配置中随机返回一道题。

**响应示例**:
```json
{
  "code": "OK",
  "data": {
    "id": 1,
    "type": "single_choice",
    "title": "睡眠的黄金时间段是？",
    "options": [
      {"id": 1, "text": "22:00-06:00"},
      {"id": 2, "text": "00:00-08:00"},
      {"id": 3, "text": "02:00-10:00"},
      {"id": 4, "text": "23:00-07:00"}
    ],
    "answers": [1],
    "explanation": "人体褪黑素分泌高峰期在22:00-06:00"
  }
}
```

## 5. 早睡鼓励素材

### 5.1 生成上传 Session

```
POST /assets/session
```

**请求头**: `X-User-Id` 必填。

**响应示例**:
```json
{
  "code": "OK",
  "data": {
    "session_id": "a1b2c3d4-...",
    "url": "http://localhost:5050/api/sleep/assets/upload/a1b2c3d4-...",
    "expires_at": "2026-05-26 10:00:00"
  }
}
```

`url` 为采集页面链接，可分享给好友。有效期在服务端配置（默认 24 小时）。

### 5.2 查询 Session 状态

```
GET /assets/friend/session/<session_id>
```

无需鉴权。前端页面在加载时调用此接口判断 session 是否有效。

**响应示例**:
```json
{
  "code": "OK",
  "data": {
    "valid": true,
    "expired": false,
    "expires_at": "2026-05-26 10:00:00"
  }
}
```

### 5.3 素材采集页面

采集页面为纯静态页面（`templates/upload.html`），可直接部署到 CDN 或 Nginx 等静态服务器。页面通过 URL 参数获取配置：

| 参数 | 说明 |
|---|---|
| `session_id` | 必填，session ID |
| `api_base` | 后端 API 地址，默认取当前域名 |

Flask 同源部署：`/upload.html?session_id=xxx`  
CDN 跨域部署：`https://cdn.example.com/upload.html?session_id=xxx&api_base=https://api.example.com`

若由 Flask 直接托管，也可通过以下地址访问（URL 路径中包含 session_id）：

```
GET /assets/friend/upload/<session_id>
```

### 5.4 提交素材

```
POST /assets/friend/upload/<session_id>
```

**Content-Type**: `multipart/form-data`

| 字段 | 说明 |
|---|---|
| `friend_name` | 好友昵称，必填 |
| `type` | 素材类型：`image`、`audio`、`text` |
| `file` | 文件（type 为 image/audio 时必填） |
| `content` | 文字内容（type 为 text 时必填） |

支持的图片格式：JPEG、PNG、GIF、WebP。支持的音频格式：MP3、M4A、WAV、OGG。文件最大 20MB。

**响应示例**:
```json
{
  "code": "OK",
  "data": {
    "msg": "上传成功，感谢你的鼓励！"
  }
}
```

### 5.5 获取收到的素材

```
GET /assets/materials
```

**请求头**: `X-User-Id` 必填。

返回当前用户收到的素材，按时间倒序。`rejected` 的素材不会返回。图片和音频会附带 `presigned_url`（有效期 15 分钟）。`full` 字段标识图片/音频素材库是否已达上限（默认上限 5，可通过环境变量 `MATERIAL_LIMIT` 调整）。

**响应示例**:
```json
{
  "code": "OK",
  "data": {
    "materials": [
      {
        "id": 1,
        "user_id": "user123",
        "session_id": "a1b2c3d4-...",
        "friend_name": "小明",
        "file_type": "image",
        "bucket": "cn-bucket",
        "object_key": "assets/user123/a1b2c3d4-....jpg",
        "content_text": "",
        "file_size": 102400,
        "mime_type": "image/jpeg",
        "status": "pending",
        "presigned_url": "https://...",
        "created_at": "2026-05-25 10:00:00",
        "updated_at": "2026-05-25 10:00:00"
      },
      {
        "id": 2,
        "user_id": "user123",
        "session_id": "a1b2c3d4-...",
        "friend_name": "小红",
        "file_type": "text",
        "bucket": "",
        "object_key": "",
        "content_text": "早点休息哦！",
        "file_size": 0,
        "mime_type": "text/plain",
        "status": "approved",
        "presigned_url": null,
        "created_at": "2026-05-25 10:00:00",
        "updated_at": "2026-05-25 10:00:00"
      }
    ],
    "full": false
  }
}
```

### 5.6 审核素材

```
PATCH /assets/materials/<material_id>/status
```

**请求头**: `X-User-Id` 必填。

**请求体**:
```json
{
  "status": "approved"
}
```

`status` 可选值：`approved`（采用）、`rejected`（丢弃）、`pending`（取消采用）。允许的状态变更：`pending` → `approved`/`rejected`，`approved` → `pending`。设为 `rejected` 时，对应的 OSS 文件会被删除。

**响应示例**: 同素材对象。

## 6. 睡眠报告

睡眠报告基于用户自定义睡眠时段（来自 `SleepConfig`）计算。三档判定为比例制：

- 🟢 **success**: 有效锁屏时长 > 时段总时长 × 0.875
- 🟡 **warning**: 时段总时长 × 0.625 ≤ 有效锁屏时长 ≤ 时段总时长 × 0.875
- 🔴 **danger**: 有效锁屏时长 < 时段总时长 × 0.625

所有报告均返回用户睡眠配置（`custom_sleep_time` 字符串、`sleep_is_unhealthy` 布尔），前端据此渲染时段文案和健康警示。

### 6.1 日报

```
GET /report/daily?date=YYYY-MM-DD
```

**请求头**: `X-User-Id` 必填。

**响应示例**:
```json
{
  "code": "OK",
  "data": {
    "type": "day",
    "custom_sleep_time": "23:00 – 07:00",
    "sleep_is_unhealthy": false,
    "lock_hour": "7小时21分",
    "lock_seconds": 26460,
    "unlock_count": 1,
    "day_type": "success",
    "show_save_time": true,
    "save_hour": "7小时40分",
    "save_seconds": 27600,
    "save_tip": ""
  }
}
```

**字段说明**:

| 字段 | 说明 |
|------|------|
| `custom_sleep_time` | 用户自定义时段字符串，如 `"23:00 – 07:00"` |
| `sleep_is_unhealthy` | 自定义时长 <6h 时为 true |
| `lock_hour` / `lock_seconds` | 自定义时段内有效锁屏时长 |
| `unlock_count` | 时段内解锁次数 |
| `day_type` | success / warning / danger / empty |
| `show_save_time` | 累计 ≥3 晚有效记录 且 当日挽回 ≥0 时为 true |
| `save_hour` / `save_seconds` | 挽回熬夜时长 |
| `save_tip` | 空数据 / 不足3晚 / 挽回为负时的文案提示 |

**空态**（当日无数据）: `day_type: "empty"`, `lock_seconds: 0`。

### 6.2 周报

```
GET /report/weekly?date=YYYY-MM-DD
```

取该日期所在周的周一~周日。

**响应示例**:
```json
{
  "code": "OK",
  "data": {
    "type": "week",
    "custom_sleep_time": "23:00 – 07:00",
    "sleep_is_unhealthy": false,
    "total_lock_minute": 4320,
    "total_lock_hour": "72小时",
    "success_day": 5,
    "avg_unlock": 1.2,
    "show_rate": true,
    "rate": 35,
    "total_save_hour": "7小时40分",
    "encourage_text": "下周继续和搭档一起坚守作息，收获更好的睡眠吧",
    "week_day_list": [
      {"day": "1", "type": "success"},
      {"day": "2", "type": "success"},
      {"day": "3", "type": "danger"},
      {"day": "4", "type": "success"},
      {"day": "5", "type": "warning"},
      {"day": "6", "type": "success"},
      {"day": "7", "type": "empty"}
    ]
  }
}
```

| 字段 | 说明 |
|------|------|
| `total_lock_minute` | 本周总锁屏分钟数 |
| `total_lock_hour` | 人性化格式 |
| `success_day` | 本周成功打卡天数 |
| `avg_unlock` | 平均每晚解锁次数 |
| `show_rate` | 上周有完整7天数据时 true |
| `rate` | 环比上周解锁下降百分比（正数=进步） |
| `total_save_hour` | 本周累计挽回时长，≥3晚才计算 |
| `week_day_list` | 7天色块，type: success/warning/danger/empty |

### 6.3 月报

```
GET /report/monthly?month=YYYY-MM
```

**响应示例**:
```json
{
  "code": "OK",
  "data": {
    "type": "month",
    "custom_sleep_time": "23:00 – 07:00",
    "sleep_is_unhealthy": false,
    "month_total_hour": "210小时",
    "avg_day_hour": "7小时",
    "success_month_day": 18,
    "max_serial_day": 9,
    "show_save_time": true,
    "month_save_hour": "42小时10分",
    "month_comment": "本月自控力稳步提升，熬夜次数明显减少，继续保持",
    "month_day_list": [
      {"day": "1", "type": "success"},
      {"day": "2", "type": "warning"},
      ...
    ]
  }
}
```

| 字段 | 说明 |
|------|------|
| `month_total_hour` | 本月累计有效锁屏总时长 |
| `avg_day_hour` | 日均坚守时长 |
| `success_month_day` | 本月打卡成功天数 |
| `max_serial_day` | 月度最高连续打卡天数 |
| `show_save_time` | 累计 ≥3 晚且有挽回数据 |
| `month_save_hour` | 本月累计挽回时长 |
| `month_comment` | 自动评语（≥5天数据才生成），不健康用户自动追加睡眠提醒 |
| `month_day_list` | 当月每日色块，type: success/warning/danger/empty |
