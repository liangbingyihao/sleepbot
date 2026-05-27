# SleepBot API 文档

## 目录

- [通用说明](#通用说明)
  - [公共请求头](#公共请求头)
  - [响应格式](#响应格式)
  - [错误码说明](#错误码说明)
- [1. 用户睡眠时间配置](#1-用户睡眠时间配置)
  - [1.1 获取当前用户睡眠配置](#11-获取当前用户睡眠配置)
  - [1.2 设置/更新睡眠配置](#12-设置更新睡眠配置)
  - [1.3 删除睡眠配置](#13-删除睡眠配置)
- [2. 用户状态上报](#2-用户状态上报)
  - [2.1 上报状态](#21-上报状态)
  - [2.2 获取最新状态](#22-获取最新状态)
  - [2.3 获取状态历史](#23-获取状态历史)
- [3. 好友监督关系管理](#3-好友监督关系管理)
  - [3.1 发送好友申请](#31-发送好友申请)
  - [3.2 处理好友申请](#32-处理好友申请)
  - [3.3 获取收到的好友申请](#33-获取收到的好友申请)
  - [3.4 获取发出的好友申请](#34-获取发出的好友申请)
  - [3.5 获取好友列表](#35-获取好友列表)

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
  "apply_message": "一起监督早睡早起！"
}
```

**响应示例**:
```json
{
  "code": "OK",
  "data": {
    "id": 1,
    "from_user_id": "user123",
    "to_user_id": "target_user_id",
    "status": "pending",
    "apply_message": "一起监督早睡早起！",
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

### 3.5 获取好友列表

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
