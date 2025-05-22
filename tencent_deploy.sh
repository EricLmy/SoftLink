#!/bin/bash

# SoftLink腾讯云一键部署脚本 (简化版)

# 工作目录
WORK_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd $WORK_DIR

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # 无颜色

# 打印函数
log() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 设置端口
BACKEND_PORT=5001
log "使用后端端口: $BACKEND_PORT"

# 检查并安装依赖
log "正在检查系统依赖..."

# 安装必要软件包
install_deps() {
    if [ -f "/etc/redhat-release" ]; then # CentOS
        sudo yum update -y
        sudo yum install -y python3 python3-pip nginx git
    else # Ubuntu/Debian
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip nginx git
    fi
    
    # 检查命令是否安装成功
    if ! command -v python3 &> /dev/null; then
        error "Python3 安装失败"
        exit 1
    fi
    
    if ! command -v pip3 &> /dev/null; then
        error "pip3 安装失败"
        exit 1
    fi
    
    if ! command -v nginx &> /dev/null; then
        error "nginx 安装失败"
        exit 1
    fi
    
    if ! command -v git &> /dev/null; then
        error "git 安装失败"
        exit 1
    fi
}

# 停止已存在的服务
stop_services() {
    log "停止已存在的服务..."
    
    # 停止后端
    if [ -f "$WORK_DIR/backend.pid" ]; then
        pid=$(cat "$WORK_DIR/backend.pid")
        if ps -p $pid > /dev/null; then
            log "停止后端进程 (PID: $pid)"
            kill $pid || kill -9 $pid
        fi
        rm -f "$WORK_DIR/backend.pid"
    fi
    
    # 停止可能运行的Python进程
    pkill -f "python.*startup.py" || true
    
    # 停止Nginx
    sudo systemctl stop nginx || sudo nginx -s stop || true
    
    log "服务已停止"
}

# 设置后端环境
setup_backend() {
    log "设置后端环境..."
    cd "$WORK_DIR/backend"
    
    # 创建虚拟环境
    python3 -m venv venv || python3 -m virtualenv venv || true
    
    # 安装依赖
    if [ -d "venv" ]; then
        source venv/bin/activate
        pip install -r requirements.txt
    else
        pip3 install -r requirements.txt
    fi
    
    # 创建/更新.env文件
    if [ ! -f "$WORK_DIR/.env" ]; then
        cat > "$WORK_DIR/.env" << EOL
# Flask配置
FLASK_ENV=production
FLASK_APP=app.py
FLASK_RUN_PORT=$BACKEND_PORT

# 数据库配置
DATABASE_URL=postgresql://postgres:123.123.MengLi@localhost:5432/softlink?client_encoding=utf8

# Redis配置
REDIS_URL=redis://localhost:6379/0

# 安全配置
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)

# 其他配置
DEBUG=False
TESTING=False
EOL
    else
        # 更新端口
        sed -i "s|FLASK_RUN_PORT=.*|FLASK_RUN_PORT=$BACKEND_PORT|g" "$WORK_DIR/.env" || true
    fi
    
    log "后端环境设置完成"
}

# 配置Nginx
setup_nginx() {
    log "配置Nginx..."
    
    # 获取服务器IP
    SERVER_IP=$(hostname -I | awk '{print $1}')
    
    # 创建Nginx配置
    sudo tee /etc/nginx/conf.d/softlink.conf > /dev/null << EOL
server {
    listen 80;
    server_name $SERVER_IP;
    
    # 静态资源缓存设置
    location /static/ {
        alias $WORK_DIR/frontend/softlin-f/static/;
        expires 30d;
    }
    
    # API请求代理到后端
    location /api/ {
        proxy_pass http://localhost:$BACKEND_PORT/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
    
    # 所有其他请求返回index.html
    location / {
        root $WORK_DIR/frontend/softlin-f;
        try_files \$uri \$uri/ /index.html;
        index index.html;
    }
}
EOL
    
    # 检查前端目录
    if [ ! -d "$WORK_DIR/frontend/softlin-f" ]; then
        if [ -d "$WORK_DIR/frontend/softlink-f" ]; then
            log "重命名前端目录 softlink-f -> softlin-f"
            mv "$WORK_DIR/frontend/softlink-f" "$WORK_DIR/frontend/softlin-f"
        else
            error "前端目录不存在"
            return 1
        fi
    fi
    
    # 测试并重启Nginx
    sudo nginx -t && sudo systemctl restart nginx
    
    log "Nginx配置完成"
}

# 启动后端服务
start_backend() {
    log "启动后端服务..."
    cd "$WORK_DIR/backend"
    
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # 启动后端
    nohup python startup.py --port $BACKEND_PORT > "$WORK_DIR/backend.log" 2>&1 &
    echo $! > "$WORK_DIR/backend.pid"
    
    # 等待确认启动
    sleep 5
    if [ -f "$WORK_DIR/backend.pid" ]; then
        pid=$(cat "$WORK_DIR/backend.pid")
        if ps -p $pid > /dev/null; then
            log "后端服务已启动 (PID: $pid)"
        else
            error "后端服务启动失败"
            cat "$WORK_DIR/backend.log" | tail -20
            return 1
        fi
    else
        error "无法创建PID文件"
        return 1
    fi
    
    log "后端服务启动成功"
}

# 设置防火墙
setup_firewall() {
    log "配置防火墙..."
    
    # CentOS
    if command -v firewall-cmd &> /dev/null; then
        sudo firewall-cmd --permanent --add-port=80/tcp
        sudo firewall-cmd --permanent --add-port=$BACKEND_PORT/tcp
        sudo firewall-cmd --reload
    # Ubuntu
    elif command -v ufw &> /dev/null; then
        sudo ufw allow 80/tcp
        sudo ufw allow $BACKEND_PORT/tcp
    fi
    
    log "请确保腾讯云安全组已开放端口: 80, $BACKEND_PORT"
}

# 显示部署结果
show_result() {
    # 获取IP地址
    SERVER_IP=$(hostname -I | awk '{print $1}')
    PUBLIC_IP=$(curl -s http://ifconfig.me 2>/dev/null || curl -s https://ipinfo.io/ip 2>/dev/null || echo "$SERVER_IP")
    
    echo -e "\n${GREEN}=== SoftLink 部署完成 ===${NC}"
    echo -e "前端地址: ${GREEN}http://$PUBLIC_IP${NC}"
    echo -e "后端地址: ${GREEN}http://$PUBLIC_IP:$BACKEND_PORT${NC}"
    echo -e "内网地址: ${GREEN}http://$SERVER_IP${NC}"
    echo -e "\n${YELLOW}注意事项:${NC}"
    echo -e "1. 请确保腾讯云安全组已开放端口 80 和 $BACKEND_PORT"
    echo -e "2. 日志文件: $WORK_DIR/backend.log"
    echo -e "3. 停止服务: systemctl stop nginx && kill \$(cat $WORK_DIR/backend.pid)"
}

# 主函数
main() {
    log "==== 开始部署 SoftLink 到腾讯云 ===="
    
    # 1. 安装依赖
    install_deps
    
    # 2. 停止现有服务
    stop_services
    
    # 3. 设置后端
    setup_backend || { error "后端配置失败"; exit 1; }
    
    # 4. 配置Nginx
    setup_nginx || { error "Nginx配置失败"; exit 1; }
    
    # 5. 启动后端
    start_backend || { error "后端启动失败"; exit 1; }
    
    # 6. 配置防火墙
    setup_firewall
    
    # 7. 显示结果
    show_result
}

# 执行主函数
main
exit 0 