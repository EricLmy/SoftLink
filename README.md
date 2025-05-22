# SoftLink (牧联)

SoftLink是一个现代化的软件框架系统，提供用户管理、权限控制、功能模块化等核心功能。

## 系统要求

- Docker
- Docker Compose
- Git

## 快速开始

1. 克隆仓库
```bash
git clone https://github.com/EricLmy/SoftLink.git
cd SoftLink
```

2. 部署系统
```bash
chmod +x deploy.sh
./deploy.sh
```

3. 访问系统
- 前端界面：http://localhost
- 后端API：http://localhost:8000

## 系统架构

- 前端：React + Nginx
- 后端：Flask + Gunicorn
- 数据库：PostgreSQL
- 缓存：Redis

## 主要功能

- 用户管理系统
- 权限控制
- 动态菜单
- API接口服务
- 静态资源服务

## 开发环境设置

1. 后端开发
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
flask run
```

2. 前端开发
```bash
cd frontend
npm install
npm start
```

## 生产环境部署

使用提供的`deploy.sh`脚本进行一键部署：

```bash
./deploy.sh
```

## 许可证

[MIT License](LICENSE) 


# SoftLink 后端服务

## 简介
SoftLink 后端服务是一个基于Flask的Web应用程序，提供API接口支持前端应用。

## 系统要求
- Python 3.6 或更高版本
- pip 包管理器
- 支持的操作系统：Windows、Linux、macOS

## 快速启动

### 使用自动环境检测工具启动（推荐）

我们提供了一个自动环境检测工具，可以自动选择合适的Python环境并启动后端服务。

```bash
# 在项目根目录执行
python choose_env.py

# 指定自定义端口（默认5000）
python choose_env.py --port 5001
```

### 检查和安装依赖

如果您遇到缺少依赖的问题，可以使用我们的依赖检查和安装工具。

```bash
# 在项目根目录执行
python check_dependencies.py
```

此工具会自动检查并安装必要的依赖项，包括：

- Flask
- SQLAlchemy
- psycopg2-binary
- python-dotenv
- flask-sqlalchemy
- flask-migrate
- werkzeug
- marshmallow
- flask-jwt-extended
- redis

### 手动启动后端服务

如果您更喜欢手动控制启动过程，可以直接运行启动脚本。

```bash
# 在backend目录下执行
cd backend
python startup.py

# 指定自定义端口（默认5000）
python startup.py --port 5001
```

## 端口占用问题

如果默认端口（5000）已被其他程序占用，系统会自动查找可用端口并提示您是否使用。您可以：

1. 接受建议的可用端口（输入 `y`）
2. 拒绝建议并手动指定端口（输入 `n`，然后使用 `--port` 参数重新启动）
3. 关闭占用端口的程序后重新尝试

## 常见问题

### 环境问题

- **Python版本过低**：请安装Python 3.6或更高版本
- **缺少依赖**：运行`python check_dependencies.py`安装所需依赖
- **配置文件缺失**：运行依赖检查工具将自动创建默认配置

### 数据库问题

- **数据库连接失败**：检查`.env`文件中的数据库配置
- **表结构不匹配**：系统会尝试自动创建缺失的表

### 启动问题

- **端口被占用**：按照提示使用自动推荐的端口，或手动指定其他端口
- **权限问题**：确保使用适当的权限运行脚本

## 配置说明

配置文件位于`.env`，主要配置项包括：

```
FLASK_APP=run.py
FLASK_ENV=development/production
DATABASE_URL=<数据库连接字符串>
SECRET_KEY=<密钥>
```

## 开发与贡献

如需参与开发或提交贡献，请参考贡献指南。

## 许可证

本项目基于MIT许可证进行分发。
