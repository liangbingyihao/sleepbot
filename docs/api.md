# SleepBot API 文档

## 目录

- [通用说明](#通用说明)
  - [公共请求头](#公共请求头)
  - [响应格式](#响应格式)
  - [错误码说明](#错误码说明)
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
   - [4.8 轮询变更](#4-8-轮询变更)
   - [4.9 解锁题库](#4-9-解锁题库)
     - [4.9.1 获取配置](#4-9-1-获取配置)
     - [4.9.2 更新配置](#4-9-2-更新配置)
     - [4.9.3 随机抽题](#4-9-3-随机抽题)
- [5. 早睡鼓励素材](#5-早睡鼓励素材)
  - [5.1 生成上传 Session](#5-1-生成上传-session)
  - [5.2 查询 Session 状态](#5-2-查询-session-状态)
  - [5.3 素材采集页面](#5-3-素材采集页面)
  - [5.4 提交素材](#5-4-提交素材)
  - [5.5 获取收到的素材](#5-5-获取收到的素材)
  - [5.6 审核素材](#5-6-审核素材)
  - [5.7 采用/取消系统素材](#5-7-采用-取消系统素材)
  - [5.8 系统素材管理](#5-8-系统素材管理)
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
        "updated_at": "2026-05-25 10:00:00",
        "sleep_config": {
          "sleep_start_time": "23:00",
          "sleep_end_time": "08:00"
        },
        "sleep_status": "locked"
      }
    ]
  }
}
```

`sleep_status` 由服务端根据好友的睡眠配置和最新状态计算：

| 值 | 判定 |
|------|------|
| `awake` | 当前时间不在好友睡眠时段内 |
| `unlocked` | 在睡眠时段内，且存在被确认的解锁企图（`active` 且其后 60 秒内紧跟 `awake`） |
| `locked` | 在睡眠时段内，无被确认的解锁企图（否则视为 locked） |
| `no_config` | 好友未配置睡眠时间 |

`sleep_status` 仅在好友处于睡眠时段时查询 `user_status` 表，否则直接返回 `awake`，零额外查询。

**排序规则**：已配置睡眠时间的好友在前，未配置的在后；同级内 `friendship_id` 降序（新关系在前）。

### 4.8 轮询变更

```
GET /poll?friendship_id=123&material_id=456
```

轻量信号接口，基于自增 ID 返回好友和素材的新增变更。不返回具体数据，客户端收到变更信号后自行调用 `GET /friends` 和 `GET /assets/materials` 获取完整数据。

**查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| friendship_id | int | 否 | 客户端已读的最后一条 `Friendship.id`，返回 `id > friendship_id` 的 accepted 好友 |
| material_id | int | 否 | 客户端已读的最后一条 `UserOssFile.id`，返回 `id > material_id` 的 pending 素材 |

> 两个参数都不传 = 首次安装，返回系统素材计数。

**常规轮询（至少传一个参数）**:

```json
{
  "code": "OK",
  "data": {
    "has_friend_changes": true,
    "new_text": 2,
    "new_audio": 1
  }
}
```

| 字段 | 说明 |
|------|------|
| `has_friend_changes` | `Friendship.id > friendship_id AND status = 'accepted'` 的好友是否存在 |
| `new_text` | `UserOssFile.id > material_id AND status = 'pending'` 的 text 素材数量 |
| `new_audio` | `UserOssFile.id > material_id AND status = 'pending'` 的 audio 素材数量 |

> 注：poll 不检测好友信息更新（如改名），仅检测新增。

**首次安装（两个参数都不传）**:

```json
{
  "code": "OK",
  "data": {
    "has_friend_changes": false,
    "new_text": 0,
    "new_audio": 0,
    "system_text_count": 5,
    "system_audio_count": 3
  }
}
```

| 字段 | 说明 |
|------|------|
| `system_text_count` | 按 `X-Language` 匹配的活跃 text 系统素材数量 |
| `system_audio_count` | 按 `X-Language` 匹配的活跃 audio 系统素材数量 |

**客户端约定**:

客户端本地持久化两个已读 ID，配合 FCM 推送使用：

```
存储:
  last_friend_view_id   = 0
  last_material_view_id = 0

首次安装:
  └─ GET /poll
     → 初始化 last_friend_view_id = 0, last_material_view_id = 0

收到 FCM 推送 / 前台定时器 / 冷启动:
  └─ GET /poll?friendship_id={last_friend_view_id}&material_id={last_material_view_id}
     → has_friend_changes → GET /friends，friendship_id > last_friend_view_id 的好友标红
        → 用户打开好友页后 → 更新 last_friend_view_id = max(friendship_id)
     → new_text/new_audio > 0 → 下次进入素材页 GET /assets/materials
        → 用户打开素材页后 → 更新 last_material_view_id = max(id)
```

- FCM 推送为轻量信号（如 `{ type: "friend_change" }`），不承载数据，客户端收到后调 `/poll` 拉取增量
- 首次安装无参数，不标红任何好友——"新"是相对于上次查看的概念
- 前台定时器（建议 60s）作为 FCM 推送的兜底，防止推送丢失或延迟
- 好友改名更新不在 poll 检测范围内，用户打开 app 自然看到最新名称

### 4.9 解锁题库

题库以 JSON 格式存储在 `app_config` 表中，`config_type = 'quiz_questions'`，每条记录对应一种语言。题目字段包括 `type`（single_choice / multiple_choice）、`title`、`options[]`（含 `id`、`text`）、`answers`（正确答案 ID 数组）、`explanation`。

#### 4.9.1 获取配置

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

#### 4.9.2 更新配置

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

#### 4.9.3 随机抽题

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

**说明**: 每次调用会清理该用户已过期的 session。若存在未过期的活跃 session，则仅延长其有效期（id 不变，已分享的链接继续有效）；否则创建新 session。有效期在服务端配置（默认 1 小时）。

**请求体** (JSON, 可选):

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| invite_code | string | 否 | 邀请码，用于好友识别 |

**请求体示例**:
```json
{ "invite_code": "ABC123" }
```

**响应示例**:
```json
{
  "code": "OK",
  "data": {
    "session_id": "a1b2c3d4-...",
    "url": "http://localhost:5050/upload.html?session_id=a1b2c3d4-...",
    "invite_record": "http://localhost:5050/upload.html?session_id=a1b2c3d4-...",
    "invite_install": "http://localhost:5050/download?session_id=a1b2c3d4-...",
    "expires_at": "2026-05-26 10:00:00"
  }
}
```

| 字段 | 说明 |
|------|------|
| `url` | **已废弃**，保留兼容，等同于 `invite_record` |
| `invite_record` | 鼓励素材采集页面链接，分享给好友录制语音/文字 |
| `invite_install` | 邀请好友安装应用的链接（带 session_id 追踪） |
| `expires_at` | UTC 过期时间，客户端可据此判断是否需要续期 |

**客户端缓存策略建议**:

```
页面加载时 → POST /assets/session → 缓存 {url, expires_at}
用户点击"新增" → 对比 now 和 expires_at
  ├─ 未过期 → 直接用缓存 url（零延迟）
  └─ 已过期 → 重新 POST /assets/session → 用新 url

// 可选：过期前 1 分钟自动续期，避免点击时恰好过期
setTimeout(() => {
  POST /assets/session → 更新缓存
}, (expires_at - now - 60) * 1000);
```

### 5.2 查询 Session 状态

```
GET /assets/friend/session/<session_id>
```

无需鉴权。前端页面在加载时调用此接口判断 session 是否有效。

**基础响应**（不传任何参数，与旧版完全一致）:
```json
{
  "code": "OK",
  "data": {
    "valid": true,
    "expired": false,
    "expires_at": "2026-05-26 10:00:00",
    "creator_name": "张三",
    "invite_code": "ABC123"
  }
}
```

**Query 参数**（可选，隐式触发报告）:

| 参数 | 类型 | 触发的报告 | 说明 |
|---|---|---|---|
| `date` | string | 日报 + 周报 | 基准日期 `YYYY-MM-DD`，周报取该日所在周 |
| `month` | string | 月报 | 月份 `YYYY-MM` |

**说明**: 仅当传入合法 `date` / `month` 时才计算并追加对应报告字段（`date` → `daily_report` + `weekly_report`，`month` → `monthly_report`，两者都传 → 三份）。报告字段结构与 §6 报告接口的 `data` 完全一致（同一套逻辑生成）。当 session 已过期或创建者（session 用户）未配置睡眠时段时，被触发的报告为 `null`；未被触发的字段不出现。非法 `date` / `month` 会被忽略（等同未传，不报错）。

**携带参数时的响应**（`?date=2026-06-22&month=2026-06`）:
```json
{
  "code": "OK",
  "data": {
    "valid": true,
    "expired": false,
    "expires_at": "2026-05-26 10:00:00",
    "creator_name": "张三",
    "invite_code": "ABC123",
    "daily_report": {
      "type": "day",
      "custom_sleep_time": "23:00 – 07:00",
      "sleep_is_unhealthy": false,
      "timezone": "Asia/Shanghai",
      "lock_hour": "7小时21分",
      "lock_seconds": 26460,
      "unlock_count": 1,
      "day_type": "success",
      "show_save_time": true,
      "save_hour": "40分钟",
      "save_seconds": 2400,
      "save_tip": "比之前少玩40分钟，表现优秀！",
      "day_type_label": "很棒"
    },
    "weekly_report": {
      "type": "week",
      "custom_sleep_time": "23:00 – 07:00",
      "sleep_is_unhealthy": false,
      "timezone": "Asia/Shanghai",
      "total_lock_minute": 4320,
      "total_lock_hour": "72小时",
      "success_day": 5,
      "avg_unlock": 1.2,
      "show_rate": true,
      "rate": 35,
      "total_save_hour": "7小时40分",
      "encourage_text": "下周继续和搭档一起坚守作息，收获更好的睡眠吧",
      "week_day_list": [
        {"day": "1", "type": "success"}
      ]
    },
    "monthly_report": {
      "type": "month",
      "custom_sleep_time": "23:00 – 07:00",
      "sleep_is_unhealthy": false,
      "timezone": "Asia/Shanghai",
      "month_total_hour": "210小时",
      "avg_day_hour": "7小时",
      "success_month_day": 18,
      "max_serial_day": 9,
      "show_save_time": true,
      "month_save_hour": "42小时10分",
      "month_comment": "本月自控力稳步提升，熬夜次数明显减少，继续保持",
      "month_day_list": [
        {"day": "1", "type": "success"}
      ]
    }
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

返回当前用户的全部素材（系统+好友），单数组合并，按 `status=approved` 优先、更新时间倒序排列。`source` 区分来源。

新用户首次访问时自动采用默认系统文本+语音。

```json
{
  "code": "OK",
  "data": {
    "materials": [
      {
        "id": 1,
        "source": "system",
        "status": "approved",
        "file_type": "text",
        "content_text": "早睡早起身体好",
        ...
      },
      {
        "id": 2,
        "source": "system",
        "status": "pending",
        "file_type": "text",
        "content_text": "晚安好梦",
        ...
      },
      {
        "id": 5,
        "source": "friend",
        "status": "approved",
        "friend_name": "小红",
        "file_type": "text",
        "content_text": "早点休息哦！",
        "source_system_material_id": 0,
        ...
      }
    ],
    "full": false
  }
}
```

`source_system_material_id`：>0 表示该素材引用于系统素材，取系统表中最新内容填充。

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

`status` 可选值：`approved`（采用）、`rejected`（丢弃，物理删除数据库记录和 OSS 文件）、`pending`（取消采用）。允许的状态变更：`pending` → `approved`/`rejected`，`approved` → `pending`。

**响应示例**: 同素材对象。

### 5.7 采用/取消系统素材

```
POST   /assets/materials/system/<sys_id>/adopt     # 采用：创建或更新引用记录
DELETE /assets/materials/system/<sys_id>/dismiss   # 取消：status → pending
```

**采用**：建立 `source_system_material_id` 引用到 `UserOssFile`（`status='approved'`），同类型旧 approved 自动变 pending。若之前 dismiss 过则直接更新状态，不重复创建。

**取消采用**：对应引用记录 `status` 改为 `pending`，保留记录阻止重新自动初始化。`/assets/materials` 中不再展示该素材。

### 5.8 系统素材管理

系统兜底全员可见的鼓励素材，按语言区分。

```
GET    /assets/system_materials   # 按当前 locale 返回活跃素材
POST   /assets/system_materials   # 新增
PUT    /assets/system_materials/<id>  # 更新
DELETE /assets/system_materials/<id>  # 删除（同时删除 OSS 文件）
```

**GET** 自动从 `X-Language` 请求头读取 locale，只返回 `is_active=True` 的素材，按 `sort_order` 排序。

**POST 请求体**:
```json
{
  "file_type": "text",
  "content_text": "早睡早起身体好",
  "locale": "zh-CN",
  "sort_order": 1,
  "is_active": true
}
```

**PUT**：任一字段均可部分更新。

**响应**: 同 `SystemMaterial.to_dict()`。

## 6. 睡眠报告

睡眠报告基于用户自定义睡眠时段（来自 `SleepConfig`）计算。三档判定为比例制：

- 🟢 **success**: 有效锁屏时长 > 时段总时长 × 0.875
- 🟡 **warning**: 时段总时长 × 0.625 ≤ 有效锁屏时长 ≤ 时段总时长 × 0.875
- 🔴 **danger**: 有效锁屏时长 < 时段总时长 × 0.625

**状态统计规则**（`locked` / `awake` 由扩展 monitor 进入/退出锁定时产生）：

1. **稳定排序**：状态记录按 `(reported_at, id)` 升序，同秒记录顺序确定
2. **active 确认**：`active`（用户企图解锁）仅当其下一条记录为 `awake` 且间隔 ≤ 60 秒时才算真实解锁，否则丢弃
3. **窗口起始容差 2 分钟**：`[start, start+2min)` 内的上报只保留最后一条，消除进入睡眠时的回调抖动
4. **窗口结束容差 2 分钟**：查询扩展到 `end+2min`，捕获刚过界的起床 `awake`
5. **起床不计解锁**：落在结束容差区（`reported_at ≥ end`）的 `locked → awake` 属起床，不计入 `unlock_count`
6. **锁屏封顶**：锁屏时长封顶于窗口结束 `end`

所有报告均返回用户睡眠配置（`custom_sleep_time` 字符串、`sleep_is_unhealthy` 布尔），前端据此渲染时段文案和健康警示。

三个接口均支持可选参数 `?friend_id=xxx`，传入时查看好友的报告（需为 accepted 好友关系）。

### 6.1 日报

```
GET /report/daily?date=YYYY-MM-DD
GET /report/daily?date=YYYY-MM-DD&friend_id=xxx

**请求头**: `X-User-Id` 必填。

**响应示例**:
```json
{
  "code": "OK",
  "data": {
    "type": "day",
    "custom_sleep_time": "23:00 – 07:00",
    "sleep_is_unhealthy": false,
    "timezone": "Asia/Shanghai",
    "lock_hour": "7小时21分",
    "lock_seconds": 26460,
    "unlock_count": 1,
    "day_type": "success",
    "show_save_time": true,
    "save_hour": "7小时40分",
    "save_seconds": 27600,
    "save_tip": "比之前少玩7小时40分，表现优秀！",
    "day_type_label": "很棒"
  }
}
```

**字段说明**:

| 字段 | 说明 |
|------|------|
| `custom_sleep_time` | 用户自定义时段字符串，如 `"23:00 – 07:00"` |
| `sleep_is_unhealthy` | 自定义时长 <6h 时为 true |
| `timezone` | 时区，如 `"Asia/Shanghai"`，查看好友报告时显示好友时区 |
| `lock_hour` / `lock_seconds` | 自定义时段内有效锁屏时长 |
| `unlock_count` | 时段内解锁次数 |
| `day_type` | success / warning / danger / empty |
| `show_save_time` | 累计 ≥3 晚有效记录 且 当日挽回 ≥0 时为 true |
| `save_hour` / `save_seconds` | 比之前少玩手机时长 |
| `save_tip` | 睡眠总结文案，始终有值，包含锁屏/少玩/解锁等数据 |
| `day_type_label` | 日类型标签：很棒 / 还行 / 加油 / 无数据 |

**空态**（当日无数据）: `day_type: "empty"`, `lock_seconds: 0`。

### 6.2 周报

```
GET /report/weekly?date=YYYY-MM-DD
GET /report/weekly?date=YYYY-MM-DD&friend_id=xxx
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
    "timezone": "Asia/Shanghai",
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
GET /report/monthly?month=YYYY-MM&friend_id=xxx
```

**响应示例**:
```json
{
  "code": "OK",
  "data": {
    "type": "month",
    "custom_sleep_time": "23:00 – 07:00",
    "sleep_is_unhealthy": false,
    "timezone": "Asia/Shanghai",
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
