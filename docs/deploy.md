# SleepBot 部署文档

## 环境要求

- Python 3.8+
- MySQL 5.7+
- pip

## 快速开始

### 1. 克隆项目

```bash
git clone <repo_url>
cd sleepbot
```

### 2. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置 MySQL

创建数据库：

```sql
CREATE DATABASE sleepbot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 5. 配置环境变量

```bash
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=your_password
export MYSQL_DB=sleepbot
```

或在 `config.py` 中直接修改默认值。

### 6. 启动服务

**开发模式（前台）**:

```bash
python app.py
```

**后台运行（关闭终端后保持）**:

```bash
nohup python app.py > app.log 2>&1 &
```

- 日志输出到 `app.log`
- 进程 ID 可通过 `ps aux | grep app.py` 或 `echo $!` 查看
- 停止进程: `kill <pid>`

**生产模式 (uWSGI)**:

```bash
nohup uwsgi --http 0.0.0.0:5050 --module app:create_app() --callable app > uwsgi.log 2>&1 &
```

或使用 uwsgi 配置文件 `uwsgi.ini`:

```ini
[uwsgi]
http = 0.0.0.0:5050
module = app:create_app()
callable = app
master = true
processes = 4
threads = 2
buffer-size = 32768
```

启动:

```bash
nohup uwsgi uwsgi.ini > uwsgi.log 2>&1 &
```

## 验证部署

```bash
curl -H "X-User-Id: test_user" http://localhost:5050/api/sleep-config
```
