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