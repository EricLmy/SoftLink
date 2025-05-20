# 牧联 (SoftLink) 后端服务

## 1. 项目概览

本项目是"牧联"(SoftLink)软件框架的后端服务，基于 Flask (Python) 构建。它提供了一系列 RESTful API，用于支持用户认证、用户管理、子账户管理、VIP 体系、动态功能模块、用户反馈等核心业务逻辑。

后端服务旨在提供一个稳定、安全、可扩展的 API 层，供前端应用或其他客户端进行调用。

## 2. 目录结构

```
backend/
├── app/                      # Flask 应用核心代码目录
│   ├── api/                  # API 蓝图和路由定义
│   │   ├── admin.py          # 管理员相关 API
│   │   ├── auth.py           # 认证授权 API
│   │   ├── features.py       # 功能模块和动态菜单 API
│   │   ├── feedback.py       # 用户反馈 API
│   │   └── users.py          # 用户和子账户管理 API
│   ├── models.py             # SQLAlchemy 数据模型定义
│   ├── schemas.py            # Marshmallow Schema 定义 (用于数据序列化/反序列化和验证)
│   ├── utils.py              # 通用工具函数 (如日志记录)
│   ├── decorators.py         # 自定义装饰器 (如权限校验)
│   ├── __init__.py           # 应用工厂和初始化
│   └── extensions.py         # Flask 扩展实例化 (如 db, ma, migrate)
├── migrations/               # Flask-Migrate 数据库迁移脚本
├── tests/                    # 测试用例 (待完善)
├── .env.example              # 环境变量示例文件
├── .flaskenv                 # Flask CLI 环境变量
├── config.py                 # 应用配置文件 (开发、测试、生产)
├── requirements.txt          # Python 依赖包列表
└── wsgi.py                   # WSGI 入口点 (用于 Gunicorn 等服务器)
```

## 3. 环境搭建与运行

### 3.1 先决条件

*   Python 3.8+
*   pip (Python 包管理器)
*   virtualenv (或 conda 等其他虚拟环境工具)
*   PostgreSQL 数据库服务

### 3.2 步骤

1.  **克隆仓库** (假设已完成)
    ```bash
    # git clone <repository_url>
    # cd SoftLink-0517/backend
    ```

2.  **创建并激活虚拟环境**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **安装依赖**
    ```bash
    pip install -r requirements.txt
    ```

4.  **配置环境变量**
    *   复制 `.env.example` 为 `.env`：
        ```bash
        cp .env.example .env
        ```
    *   编辑 `.env` 文件，至少配置以下变量：
        *   `FLASK_APP=wsgi.py` (通常已在 `.flaskenv` 中配置)
        *   `FLASK_ENV=development` (或 `production`)
        *   `SECRET_KEY`: 一个强随机字符串，用于会话和安全。可以使用 `python -c 'import secrets; print(secrets.token_hex(16))'` 生成。
        *   `DATABASE_URL`: PostgreSQL 数据库连接字符串。格式：`postgresql://username:password@host:port/database_name`
            *   例如: `postgresql://softlink_user:yourpassword@localhost:5432/softlink_db`
        *   `JWT_SECRET_KEY`: 用于 JWT 签名的强随机字符串。
        *   (可选) `REDIS_URL`: 如果使用 Redis (例如用于 Celery 或缓存)。格式：`redis://localhost:6379/0`

5.  **数据库设置**
    *   确保 PostgreSQL 服务正在运行，并且你已创建了 `.env` 中指定的数据库。
    *   **初始化数据库迁移环境** (仅首次需要):
        ```bash
        flask db init 
        ```
        *(如果 `migrations` 文件夹已存在，则跳过此步)*
    *   **生成数据库迁移脚本**:
        ```bash
        flask db migrate -m "Initial migration with all models" 
        ```
        *(每当 `app/models.py` 中的模型发生更改时运行此命令)*
    *   **应用数据库迁移** (创建表结构):
        ```bash
        flask db upgrade
        ```

6.  **运行开发服务器**
    ```bash
    flask run
    ```
    默认情况下，应用将在 `http://127.0.0.1:5000/` 上运行。

### 3.3 `.flaskenv` 文件说明
`.flaskenv` 文件用于设置 Flask CLI 的常用环境变量，如：
*   `FLASK_APP=wsgi.py`: 指定 Flask 应用的入口点。
*   `FLASK_ENV=development`: 设置为开发模式，会启用调试器和自动重载。
*   `FLASK_DEBUG=1`: (可选，在 `FLASK_ENV=development` 时通常已包含) 明确开启调试模式。

## 4. API 文档

(待补充) 建议后续引入 Swagger/OpenAPI 支持，并在此处提供访问链接。

## 5. 测试

(待补充) 测试用例位于 `tests/` 目录下。运行测试的命令 (例如使用 `pytest`) 将在此处说明。

## 6. 部署 (概要)

生产环境部署通常涉及以下步骤：

1.  **WSGI 服务器**: 使用 Gunicorn 或 uWSGI 运行 Flask 应用。
    ```bash
    # 示例 (Gunicorn)
    gunicorn --bind 0.0.0.0:5000 wsgi:app 
    ```
    这里的 `app` 是 `wsgi.py` 中创建的 Flask 应用实例。
2.  **反向代理**: 使用 Nginx 或类似的服务器作为反向代理，处理 HTTPS、静态文件、负载均衡等。
3.  **环境变量**: 生产环境应使用强密码和密钥，并将 `FLASK_ENV` 设置为 `production`。
4.  **数据库**: 确保数据库已正确配置、备份并可从应用服务器访问。
5.  **Docker (推荐)**:
    *   创建一个 `Dockerfile` 来容器化 Flask 应用。
    *   使用 Docker Compose (中小型项目) 或 Kubernetes (大型项目) 进行部署和管理。
    *   (Dockerfile 和 docker-compose.yml 文件将在后续步骤中创建)

## 7. 主要技术栈

*   **框架**: Flask
*   **ORM**: SQLAlchemy (通过 Flask-SQLAlchemy)
*   **数据库迁移**: Flask-Migrate (基于 Alembic)
*   **数据序列化/验证**: Marshmallow (通过 Flask-Marshmallow)
*   **认证**: JWT (JSON Web Tokens)
*   **数据库**: PostgreSQL
*   **异步任务 (可选)**: Celery (配合 Redis 或 RabbitMQ)
*   **缓存 (可选)**: Redis

## 启动说明

### 自动启动（推荐）

使用提供的启动脚本可以自动检查环境、数据库配置并启动后端服务：

#### Windows

1. 双击运行 `start_server.bat`
2. 等待系统检查和启动完成

#### Linux/Mac

1. 确保脚本有执行权限：`chmod +x startup.py`
2. 运行脚本：`./startup.py`
3. 或使用Python执行：`python startup.py`

### 手动启动

如果需要手动启动服务：

1. 确保所有依赖已安装
2. 初始化数据库（如果需要）：`python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('Tables created')"`
3. 创建初始用户（如果需要）：`python create_initial_users.py`
4. 启动服务：`python run.py`

## 启动脚本功能

启动脚本 `startup.py` 会执行以下检查：

- Python版本检查
- 必要依赖检查
- 配置文件检查
- 数据库连接检查
- 端口可用性检查
- 数据库表结构检查
- 初始超级管理员用户检查

如果发现问题，脚本会提供详细的错误信息和可能的修复选项。

## 系统要求

- Python 3.6+
- Flask及相关依赖
- SQLite（开发）或PostgreSQL（生产）数据库
- Redis（可选，用于缓存）

## 开发者说明

- 启动脚本位于 `/backend/startup.py`
- Windows批处理文件位于 `/backend/start_server.bat`
- 主应用运行脚本位于 `/backend/run.py`

---
*本文档提供了后端服务的基本设置和运行指南。随着项目的进展，请保持本文档的更新。* 