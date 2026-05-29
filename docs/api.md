# SleepBot API 文档

## 目录

- [通用说明](#通用说明)
  - [公共请求头](#公共请求头)
  - [响应格式](#响应格式)
  - [错误码说明](#错误码说明)
- [1. 用户睡眠时间配置](#1-用户睡眠时间配置)
  - [1.1 获取当前用户睡眠配置](#1-1-获取当前用户睡眠配置)
  - [1.2 设置/更新睡眠配置](#1-2-设置-更新睡眠配置)
  - [1.3 删除睡眠配置](#1-3-删除睡眠配置)
- [2. 用户状态上报](#2-用户状态上报)
  - [2.1 上报状态](#2-1-上报状态)
  - [2.2 获取最新状态](#2-2-获取最新状态)
  - [2.3 获取状态历史](#2-3-获取状态历史)
- [3. 好友监督关系管理](#3-好友监督关系管理)
  - [3.1 发送好友申请](#3-1-发送好友申请)
  - [3.2 处理好友申请](#3-2-处理好友申请)
  - [3.3 获取收到的好友申请](#3-3-获取收到的好友申请)
  - [3.4 获取发出的好友申请](#3-4-获取发出的好友申请)
  - [3.5 修改好友备注](#3-5-修改好友备注)
  - [3.6 删除好友关系](#3-6-删除好友关系)
   - [3.7 获取好友列表](#3-7-获取好友列表)
   - [3.8 解锁题库](#3-8-解锁题库)
     - [3.8.1 获取配置](#3-8-1-获取配置)
     - [3.8.2 更新配置](#3-8-2-更新配置)
     - [3.8.3 随机抽题](#3-8-3-随机抽题)

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

## 1. 用户睡眠时间配置

### 1.1 获取当前用户睡眠配置

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

### 1.2 设置/更新睡眠配置

```
POST /config
```

**请求体**:
```json
{
  "sleep_start_time": "23:00",
  "sleep_end_time": "08:00",
  "timezone": "Asia/Shanghai"
}
```

`timezone` 可选，默认为 `UTC`。使用 IANA 时区标识符（如 `Asia/Shanghai`、`America/New_York`、`Europe/London`）。

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

### 1.3 删除睡眠配置

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

## 2. 用户状态上报

### 2.1 上报状态

```
POST /status
```

**请求体**:
```json
{
  "status": "locked"
}
```

可选状态值: `locked`(锁屏), `active`(活跃), `idle`(空闲), `sleeping`(睡眠中), `awake`(清醒)

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

### 2.2 获取最新状态

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

### 2.3 获取状态历史

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

## 3. 好友监督关系管理

### 3.1 发送好友申请

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

### 3.2 处理好友申请

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

### 3.3 获取收到的好友申请

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

### 3.4 获取发出的好友申请

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

### 3.5 修改好友备注

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

### 3.6 删除好友关系

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

### 3.7 获取好友列表

```
GET /friends
```

**响应示例**:
```json
{
  "code": "OK",
  "data": [
    {
      "friendship_id": 1,
      "user_id": "friend_user_id",
      "friend_name": "小张",
      "apply_message": "",
      "created_at": "2026-05-25 10:00:00",
      "sleep_config": {
        "sleep_start_time": "23:00",
        "sleep_end_time": "08:00"
      },
      "latest_status": {
        "status": "locked",
        "reported_at": "2026-05-25 22:30:00"
      }
    }
  ]
}
```

### 3.8 解锁题库

题库以 JSON 格式存储在 `app_config` 表中，`config_type = 'quiz_questions'`，每条记录对应一种语言。题目字段包括 `type`（single_choice / multiple_choice）、`title`、`options[]`（含 `id`、`text`）、`answers`（正确答案 ID 数组）、`explanation`。

#### 3.8.1 获取配置

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

#### 3.8.2 更新配置

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

#### 3.8.3 随机抽题

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
