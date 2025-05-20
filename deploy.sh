#!/bin/bash

# 设置错误时退出
set -e

echo "开始部署 SoftLink 系统..."

# 1. 检查环境
echo "检查环境..."
if ! command -v docker &> /dev/null; then
    echo "错误: 未找到 Docker，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "错误: 未找到 Docker Compose，请先安装 Docker Compose"
    exit 1
fi

# 2. 生成随机密钥
echo "生成安全密钥..."
if [ ! -f .env ]; then
    echo "创建 .env 文件..."
    SECRET_KEY=$(openssl rand -hex 32)
    JWT_SECRET_KEY=$(openssl rand -hex 32)
    
    cat > .env << EOL
# Flask配置
FLASK_ENV=production
FLASK_APP=app.py

# 数据库配置
DATABASE_URL=postgresql://postgres:postgres@db:5432/softlink

# Redis配置
REDIS_URL=redis://redis:6379/0

# 安全配置
SECRET_KEY=${SECRET_KEY}
JWT_SECRET_KEY=${JWT_SECRET_KEY}

# 其他配置
DEBUG=False
TESTING=False
EOL
fi

# 3. 构建镜像
echo "构建 Docker 镜像..."
docker-compose build

# 4. 启动服务
echo "启动服务..."
docker-compose up -d

# 5. 等待服务就绪
echo "等待服务就绪..."
sleep 10

# 6. 检查服务健康状态
echo "检查服务健康状态..."
if ! docker-compose ps | grep -q "Up"; then
    echo "错误: 服务未正常启动"
    docker-compose logs
    exit 1
fi

# 7. 初始化数据库
echo "初始化数据库..."
docker-compose exec backend flask db upgrade

echo "部署完成！"
echo "系统已启动，可以通过以下地址访问："
echo "前端: http://localhost"
echo "后端API: http://localhost:8000" 