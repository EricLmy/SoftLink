#!/bin/bash

# 设置错误时退出
set -e

echo "开始启动 SoftLink 系统..."

# 当前工作目录
WORK_DIR=$(pwd)

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# 1. 检查环境
echo -e "${YELLOW}[1/7]${NC} 检查环境..."

# 检查PostgreSQL是否安装和运行
if ! command -v psql &> /dev/null; then
    echo -e "${RED}错误: 未找到 PostgreSQL 客户端，请先安装${NC}"
    exit 1
fi

# 检查PostgreSQL服务是否运行
if ! pg_isready &> /dev/null; then
    echo -e "${RED}错误: PostgreSQL 服务未运行，请先启动服务${NC}"
    echo -e "可以使用 ${YELLOW}sudo systemctl start postgresql${NC} 启动服务"
    exit 1
fi

# 2. 更新环境变量
echo -e "${YELLOW}[2/7]${NC} 更新环境配置..."

# 备份原有.env文件
if [ -f .env ]; then
    cp .env .env.backup
fi

# 修改.env文件以使用本地PostgreSQL
cat > .env << EOL
# Flask配置
FLASK_ENV=production
FLASK_APP=app.py

# 数据库配置 - 连接到本地PostgreSQL
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/softlink

# Redis配置 - 如果本地有Redis则使用本地Redis，否则注释掉
# REDIS_URL=redis://localhost:6379/0

# 安全配置
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)

# 其他配置
DEBUG=False
TESTING=False
EOL

echo -e "${GREEN}环境配置已更新${NC}"

# 3. 确保数据库存在
echo -e "${YELLOW}[3/7]${NC} 确保数据库存在..."

# 检查数据库是否存在，如果不存在则创建
PGPASSWORD=postgres psql -U postgres -h localhost -tc "SELECT 1 FROM pg_database WHERE datname = 'softlink'" | grep -q 1 || \
PGPASSWORD=postgres psql -U postgres -h localhost -c "CREATE DATABASE softlink"

echo -e "${GREEN}数据库已准备${NC}"

# 4. 进入后端目录
echo -e "${YELLOW}[4/7]${NC} 设置后端环境..."
cd "${WORK_DIR}/backend"

# 5. 创建或激活虚拟环境
if [ ! -d "venv" ]; then
    echo "创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 6. 安装依赖
echo -e "${YELLOW}[5/7]${NC} 安装后端依赖..."
pip install -r requirements.txt

# 7. 初始化数据库
echo -e "${YELLOW}[6/7]${NC} 初始化数据库..."
flask db upgrade

# 8. 启动后端服务
echo -e "${YELLOW}[7/7]${NC} 启动后端服务..."
cd "${WORK_DIR}"

# 如果没有gunicorn，使用flask内置服务器
if command -v gunicorn &> /dev/null; then
    echo "使用Gunicorn启动服务..."
    cd backend
    gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()" --daemon
else
    echo "使用Flask内置服务器启动..."
    cd backend
    nohup flask run --host=0.0.0.0 --port=8000 > ../flask.log 2>&1 &
fi

# 9. 提示前端部署
cd "${WORK_DIR}"
echo -e "${GREEN}后端服务已启动!${NC}"
echo -e "后端API服务地址: http://服务器IP:8000"
echo ""
echo -e "${YELLOW}注意: 前端需要单独部署${NC}"
echo "您可以:"
echo "1. 在本地构建前端: cd frontend && npm install && npm run build"
echo "2. 将构建后的文件上传到服务器"
echo "3. 配置Nginx提供前端服务"
echo ""
echo -e "${GREEN}如需停止服务，请运行:${NC}"
echo "pkill -f gunicorn 或 pkill -f 'flask run'"

exit 0 