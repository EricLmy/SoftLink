#!/bin/bash

# SoftLink项目一键部署脚本 (修复版)
# 用于在腾讯云CentOS服务器上快速部署整个项目环境

# 初始化变量
FORCE_MODE=false
RETURN_CODE=0

# 确保脚本以正确的权限运行
if [ "$(id -u)" != "0" ] && [ "$1" != "--no-root" ]; then
    echo "此脚本需要root权限运行。"
    echo "如果确定不需要root权限，请使用 --no-root 参数运行。"
    exec sudo "$0" "$@"
    exit $?
fi

# 设置环境变量隔离
set -e  # 遇到错误立即退出
export LC_ALL=C  # 使用标准语言环境
export LANG=C    # 使用标准语言环境
umask 022        # 设置安全的文件权限掩码

# 防止脚本重复运行
LOCK_FILE="/tmp/softlink_deploy.lock"
if [ -f "$LOCK_FILE" ]; then
    LOCK_PID=$(cat "$LOCK_FILE")
    if ps -p $LOCK_PID > /dev/null; then
        echo "错误：部署脚本已在运行 (PID: $LOCK_PID)"
        echo "如果确定没有其他实例在运行，请删除锁文件：$LOCK_FILE"
        exit 1
    fi
fi
echo $$ > "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"' EXIT

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # 无颜色

# 项目根目录
PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
# 修正：使用正确的前端构建目录名称
FRONTEND_BUILD_DIR="$FRONTEND_DIR/softlink-f"
LOG_DIR="$PROJECT_ROOT/logs"

# 确保日志目录存在
mkdir -p "$LOG_DIR"

LOG_FILE="$LOG_DIR/deploy_$(date +%Y%m%d_%H%M%S).log"
ERROR_LOG="$LOG_DIR/error.log"
CURRENT_LOG_LINK="$LOG_DIR/current.log"
MAX_LOG_FILES=10
BACKUP_DIR="$PROJECT_ROOT/backups/$(date +%Y%m%d_%H%M%S)"
CONFIG_BACKUP_DIR="$BACKUP_DIR/configs"

# 创建备份目录
mkdir -p "$CONFIG_BACKUP_DIR"

# 配置文件路径
ENV_FILE="$PROJECT_ROOT/.env"
NGINX_CONF="$FRONTEND_DIR/nginx.softlink.conf"

# 腾讯云服务配置
SERVER_IP=$(hostname -I | awk '{print $1}')
NGINX_PATH="/usr/local/nginx"
NGINX_BIN="/usr/sbin/nginx" # 系统安装的nginx位置
BACKEND_PORT=5000
FRONTEND_PORT=80

# 数据库配置（从环境变量读取，如果没有则使用默认值）
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-postgres}"
DB_PASS="${DB_PASS:-123.123.MengLi}"
DB_NAME="${DB_NAME:-softlink}"

# 是否更新安全密钥
UPDATE_SECURITY_KEYS=false

# 显示帮助信息
show_help() {
    cat << EOF
SoftLink项目部署脚本 (修复版)
用法: ./deploy_modified.sh [选项]

选项:
  --help          显示此帮助信息
  --update-keys   更新安全密钥（会使现有会话失效）
  --no-root       不使用root权限运行（不推荐）
  --force         强制模式，不询问确认
  --port <端口>   指定后端服务端口（默认: 5000）

示例:
  ./deploy_modified.sh              # 正常部署，保留现有密钥
  ./deploy_modified.sh --update-keys # 部署并更新安全密钥
  ./deploy_modified.sh --force      # 强制部署，自动停止冲突服务
  ./deploy_modified.sh --port 5001  # 指定后端端口为5001
EOF
}

# 初始化日志系统
init_logging() {
    # 创建日志目录
    mkdir -p "$LOG_DIR"
    
    # 创建新的日志文件
    touch "$LOG_FILE"
    
    # 更新当前日志链接
    ln -sf "$LOG_FILE" "$CURRENT_LOG_LINK"
    
    # 清理旧日志文件
    find "$LOG_DIR" -name "deploy_*.log" -type f | sort -r | tail -n +$((MAX_LOG_FILES + 1)) | xargs -r rm
    
    # 记录部署开始信息
    log "===== 开始部署 SoftLink 项目 ====="
    log "部署时间: $(date '+%Y-%m-%d %H:%M:%S')"
    log "服务器信息:"
    log "  - 主机名: $(hostname)"
    log "  - IP地址: $SERVER_IP"
    log "  - 操作系统: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
    log "  - 内核版本: $(uname -r)"
}

# 改进的日志函数
log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${BLUE}[$timestamp]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${GREEN}[$timestamp][成功]${NC} $1" | tee -a "$LOG_FILE"
}

warn() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${YELLOW}[$timestamp][警告]${NC} $1" | tee -a "$LOG_FILE"
    echo "[$timestamp][警告] $1" >> "$ERROR_LOG"
}

error() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${RED}[$timestamp][错误]${NC} $1" | tee -a "$LOG_FILE"
    echo "[$timestamp][错误] $1" >> "$ERROR_LOG"
}

# 检查命令是否存在，如不存在则尝试安装
check_command() {
    if ! command -v $1 &> /dev/null; then
        error "$1 未安装。尝试自动安装..."
        if [ "$OS" = "centos" ] || [ "$OS" = "rhel" ]; then
            sudo yum install -y $1 || {
                error "$1 安装失败。请手动执行: $2"
                return 1
            }
        elif [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
            sudo apt-get update && sudo apt-get install -y $1 || {
                error "$1 安装失败。请手动执行: $2"
                return 1
            }
        else
            error "$1 未安装。请安装后重试。"
            echo -e "  安装命令: $2" | tee -a $LOG_FILE
            return 1
        fi
        success "$1 已成功安装"
        return 0
    else
        success "$1 已安装"
        return 0
    fi
}

# 检查端口是否被占用并尝试释放
check_and_free_port() {
    local PORT=$1
    local SERVICE_NAME=$2
    local FORCE=$3
    
    log "检查端口 $PORT 是否被占用..."
    
    # 检查端口是否被占用 (支持lsof或netstat)
    local PORT_OCCUPIED=false
    local PID=""
    
    if command -v lsof &> /dev/null; then
        if lsof -i:$PORT -P -n &> /dev/null; then
            PORT_OCCUPIED=true
            PID=$(lsof -i:$PORT -P -n | grep LISTEN | awk '{print $2}')
        fi
    elif command -v netstat &> /dev/null; then
        if netstat -tuln | grep ":$PORT " &> /dev/null; then
            PORT_OCCUPIED=true
            PID=$(netstat -tulnp 2>/dev/null | grep ":$PORT " | awk '{print $7}' | cut -d'/' -f1)
        fi
    else
        warn "无法检查端口 $PORT，lsof和netstat都不可用"
        return 0
    fi
    
    if [ "$PORT_OCCUPIED" = true ]; then
        warn "端口 $PORT 已被占用 (PID: $PID)"
        
        # 如果是强制模式，尝试终止进程
        if [ "$FORCE" = true ]; then
            log "强制模式下终止进程 $PID..."
            kill -15 $PID 2>/dev/null || kill -9 $PID 2>/dev/null
            sleep 2
            
            # 验证端口是否已释放
            if lsof -i:$PORT -P -n &> /dev/null || netstat -tuln | grep ":$PORT " &> /dev/null; then
                error "无法释放端口 $PORT"
                return 1
            else
                success "端口 $PORT 已释放"
            fi
        else
            # 提示用户决定如何处理
            echo -e "${YELLOW}端口 $PORT 已被占用。${NC}"
            echo "请选择操作："
            echo "  [t] 终止占用进程"
            echo "  [c] 更改使用的端口"
            echo "  [s] 跳过并退出"
            read -p "您的选择 [t/c/s]: " -n 1 -r PORT_ACTION
            echo
            
            case $PORT_ACTION in
                [Tt]* )
                    log "尝试终止进程 $PID..."
                    kill -15 $PID 2>/dev/null || kill -9 $PID 2>/dev/null
                    sleep 2
                    
                    # 验证端口是否已释放
                    if lsof -i:$PORT -P -n &> /dev/null || netstat -tuln | grep ":$PORT " &> /dev/null; then
                        error "无法释放端口 $PORT"
                        return 1
                    else
                        success "端口 $PORT 已释放"
                    fi
                    ;;
                [Cc]* )
                    read -p "请输入新的端口号: " NEW_PORT
                    if [[ $NEW_PORT =~ ^[0-9]+$ ]] && [ $NEW_PORT -gt 1024 ] && [ $NEW_PORT -lt 65535 ]; then
                        if [ "$SERVICE_NAME" = "backend" ]; then
                            BACKEND_PORT=$NEW_PORT
                            log "将后端端口更改为 $BACKEND_PORT"
                            # 更新.env文件中的端口配置
                            if [ -f "$ENV_FILE" ]; then
                                sed -i "s|FLASK_RUN_PORT=.*|FLASK_RUN_PORT=$NEW_PORT|g" "$ENV_FILE" || true
                            fi
                        else
                            FRONTEND_PORT=$NEW_PORT
                            log "将前端端口更改为 $FRONTEND_PORT"
                        fi
                    else
                        error "无效的端口号: $NEW_PORT"
                        return 1
                    fi
                    ;;
                * )
                    log "用户选择退出部署"
                    exit 0
                    ;;
            esac
        fi
    else
        success "端口 $PORT 可用"
    fi
    
    return 0
}

# 检查系统环境
check_system_env() {
    log "===== 检查系统环境 ====="
    
    # 检查操作系统
    OS=$(cat /etc/os-release | grep -oP '(?<=^ID=).+' | tr -d '"')
    VER=$(cat /etc/os-release | grep -oP '(?<=^VERSION_ID=).+' | tr -d '"')
    log "操作系统: $OS $VER"
    
    # 检查必要工具
    check_command "python3" "sudo yum install -y python3"
    check_command "pip3" "sudo yum install -y python3-pip"
    check_command "nginx" "sudo yum install -y nginx"
    check_command "git" "sudo yum install -y git"
    
    # 检查是否已安装PostgreSQL
    if ! command -v psql &> /dev/null; then
        warn "PostgreSQL未安装，将尝试安装"
        if [ "$OS" = "centos" ]; then
            log "安装PostgreSQL..."
            sudo yum install -y postgresql-server postgresql-contrib
            sudo postgresql-setup initdb || true
            sudo systemctl enable postgresql
            sudo systemctl start postgresql
            
            # 创建数据库和用户
            log "配置PostgreSQL数据库..."
            sudo -u postgres psql -c "CREATE DATABASE softlink;" || true
            sudo -u postgres psql -c "CREATE USER postgres WITH PASSWORD '123.123.MengLi';" || true
            sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE softlink TO postgres;" || true
        fi
    else
        success "PostgreSQL已安装"
        # 确保PostgreSQL服务运行
        sudo systemctl start postgresql || true
    fi
    
    # 检查端口占用情况
    check_and_free_port $BACKEND_PORT "backend" $FORCE_MODE
    check_and_free_port $FRONTEND_PORT "nginx" $FORCE_MODE
    
    success "系统环境检查完成"
}

# 修复Nginx配置
fix_nginx_config() {
    log "===== 修复Nginx配置 ====="
    
    if [ -f "$NGINX_CONF" ]; then
        # 备份原始配置
        cp "$NGINX_CONF" "$CONFIG_BACKUP_DIR/nginx.softlink.conf.backup"
        
        # 修改配置文件中的路径
        log "更新Nginx配置文件中的路径..."
        sed -i "s|/root/softlink/frontend/softlink-f|$FRONTEND_BUILD_DIR|g" "$NGINX_CONF"
        
        # 确保端口配置正确
        sed -i "s|proxy_pass http://localhost:[0-9]\+/;|proxy_pass http://localhost:$BACKEND_PORT/;|g" "$NGINX_CONF"
        
        success "Nginx配置文件已修复"
    else
        error "Nginx配置文件不存在: $NGINX_CONF"
        
        # 创建新的配置文件
        log "创建新的Nginx配置文件..."
        cat > "$NGINX_CONF" << EOL
server {
    listen $FRONTEND_PORT;
    server_name localhost;
    
    # GZIP压缩配置
    gzip on;
    gzip_comp_level 5;
    gzip_min_length 256;
    gzip_proxied any;
    gzip_types
        application/javascript
        application/json
        application/xml
        text/css
        text/plain
        text/xml
        image/svg+xml;
    
    # 静态资源缓存设置
    location /static/ {
        alias $FRONTEND_BUILD_DIR/static/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
    
    # API请求代理到后端
    location /api/ {
        proxy_pass http://localhost:$BACKEND_PORT/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
    
    # 所有其他请求返回index.html
    location / {
        root $FRONTEND_BUILD_DIR;
        try_files \$uri \$uri/ /index.html;
        index index.html;
    }
    
    # 错误页面配置
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root $FRONTEND_BUILD_DIR;
    }
}
EOL
        success "已创建新的Nginx配置文件"
    fi
    
    # 应用Nginx配置
    log "应用Nginx配置..."
    mkdir -p /etc/nginx/conf.d
    cp "$NGINX_CONF" /etc/nginx/conf.d/softlink.conf
    
    # 测试配置
    if nginx -t; then
        success "Nginx配置测试通过"
    else
        error "Nginx配置测试失败"
        return 1
    fi
    
    return 0
}

# 设置后端环境
setup_backend() {
    log "===== 设置后端环境 ====="
    
    cd $BACKEND_DIR
    
    # 检查虚拟环境
    if [ ! -d "venv" ]; then
        log "创建Python虚拟环境..."
        python3 -m venv venv || {
            warn "创建虚拟环境失败，尝试直接安装依赖"
            pip3 install -r requirements.txt
            if [ $? -ne 0 ]; then
                error "安装依赖失败"
                return 1
            fi
            success "已直接安装Python依赖"
            USE_VENV=false
        }
    else
        log "已存在虚拟环境"
    fi
    
    # 如果USE_VENV未设置为false，则使用虚拟环境
    if [ "${USE_VENV:-true}" = true ]; then
        # 激活虚拟环境
        log "激活虚拟环境..."
        source venv/bin/activate
        
        # 安装依赖
        log "安装Python依赖..."
        pip install -r requirements.txt
        if [ $? -ne 0 ]; then
            error "安装依赖失败"
            return 1
        fi
    fi
    
    # 更新 .env 文件中的数据库配置
    log "更新后端环境配置..."
    if [ -f "$PROJECT_ROOT/.env" ]; then
        log "找到.env文件，更新数据库配置..."
        # 备份原有.env文件
        cp "$PROJECT_ROOT/.env" "$CONFIG_BACKUP_DIR/.env.backup"
        
        # 更新数据库连接 URL
        sed -i "s|DATABASE_URL=.*|DATABASE_URL=postgresql://$DB_USER:$DB_PASS@$DB_HOST:$DB_PORT/$DB_NAME?client_encoding=utf8|g" "$PROJECT_ROOT/.env"
        
        # 更新后端端口
        sed -i "s|FLASK_RUN_PORT=.*|FLASK_RUN_PORT=$BACKEND_PORT|g" "$PROJECT_ROOT/.env"
        
        success "已更新.env配置文件"
    else
        log "未找到.env文件，创建新文件..."
        NEW_SECRET_KEY=$(openssl rand -hex 32)
        NEW_JWT_KEY=$(openssl rand -hex 32)
        
        cat > "$PROJECT_ROOT/.env" << EOL
# Flask配置
FLASK_ENV=production
FLASK_APP=app.py
FLASK_RUN_PORT=$BACKEND_PORT

# 数据库配置
DATABASE_URL=postgresql://$DB_USER:$DB_PASS@$DB_HOST:$DB_PORT/$DB_NAME?client_encoding=utf8

# Redis配置
# REDIS_URL=redis://localhost:6379/0

# 安全配置
SECRET_KEY=$NEW_SECRET_KEY
JWT_SECRET_KEY=$NEW_JWT_KEY

# 其他配置
DEBUG=False
TESTING=False
EOL
        log "创建了新的.env配置文件"
    fi
    
    success "后端环境设置完成"
    return 0
}

# 启动后端服务
start_backend() {
    log "===== 启动后端服务 ====="
    
    cd $BACKEND_DIR
    
    # 检查后端启动脚本
    if [ ! -f "startup.py" ]; then
        error "未找到后端启动脚本: startup.py"
        return 1
    fi
    
    # 启动后端服务
    log "启动后端服务..."
    nohup python3 startup.py > backend.log 2>&1 &
    echo $! > "$PROJECT_ROOT/backend.pid"
    
    # 等待服务启动
    log "等待后端服务启动..."
    sleep 5
    
    # 检查服务是否正常启动
    if ps -p $(cat "$PROJECT_ROOT/backend.pid") > /dev/null; then
        success "后端服务已启动 (PID: $(cat "$PROJECT_ROOT/backend.pid"))"
    else
        error "后端服务启动失败，请检查backend.log日志"
        return 1
    fi
    
    return 0
}

# 启动前端服务
start_frontend() {
    log "===== 启动前端服务 ====="
    
    # 修复前端目录路径问题
    log "检查前端构建目录..."
    if [ ! -d "$FRONTEND_BUILD_DIR" ]; then
        error "前端构建目录不存在: $FRONTEND_BUILD_DIR"
        
        # 检查是否存在名称错误的目录
        if [ -d "$FRONTEND_DIR/softlin-f" ]; then
            log "发现错误命名的目录，尝试修复..."
            mv "$FRONTEND_DIR/softlin-f" "$FRONTEND_BUILD_DIR"
            success "已将softlin-f重命名为softlink-f"
        else
            error "无法找到前端构建目录"
            return 1
        fi
    fi
    
    # 检查index.html是否存在
    if [ ! -f "$FRONTEND_BUILD_DIR/index.html" ]; then
        error "前端构建目录中未找到index.html文件"
        return 1
    fi
    
    # 重启Nginx
    log "重启Nginx服务..."
    systemctl restart nginx
    if [ $? -ne 0 ]; then
        warn "使用systemctl重启Nginx失败，尝试其他方法..."
        nginx -s reload || nginx
        if [ $? -ne 0 ]; then
            error "Nginx启动失败"
            return 1
        fi
    fi
    
    # 检查Nginx是否正常运行
    sleep 2
    if pgrep nginx > /dev/null; then
        success "Nginx服务启动成功"
    else
        error "Nginx服务启动失败"
        return 1
    fi
    
    return 0
}

# 健康检查
health_check() {
    log "===== 系统健康检查 ====="
    
    # 检查后端服务
    log "检查后端服务..."
    if [ -f "$PROJECT_ROOT/backend.pid" ]; then
        BACKEND_PID=$(cat "$PROJECT_ROOT/backend.pid")
        if ps -p $BACKEND_PID > /dev/null; then
            success "后端服务运行正常 (PID: $BACKEND_PID)"
        else
            error "后端服务已停止运行"
        fi
    else
        error "未找到后端服务PID文件"
    fi
    
    # 检查Nginx服务
    log "检查Nginx服务..."
    if pgrep nginx > /dev/null; then
        success "Nginx服务运行正常"
    else
        error "Nginx服务未运行"
    fi
    
    # 获取公网IP
    PUBLIC_IP=$(curl -s http://ifconfig.me 2>/dev/null || curl -s https://ipinfo.io/ip 2>/dev/null || echo "$SERVER_IP")
    
    log "部署完成。系统访问信息:"
    echo -e "${GREEN}前端访问地址: http://$PUBLIC_IP${NC}"
    echo -e "${GREEN}后端API地址: http://$PUBLIC_IP:$BACKEND_PORT${NC}"
    
    return 0
}

# 创建停止脚本
create_stop_script() {
    log "===== 创建停止脚本 ====="
    
    cat > "$PROJECT_ROOT/stop_softlink.sh" << EOF
#!/bin/bash

# SoftLink项目停止脚本

echo "正在停止SoftLink服务..."

# 停止后端服务
if [ -f "$PROJECT_ROOT/backend.pid" ]; then
    BACKEND_PID=\$(cat "$PROJECT_ROOT/backend.pid")
    if ps -p \$BACKEND_PID > /dev/null; then
        echo "停止后端服务 (PID: \$BACKEND_PID)..."
        kill \$BACKEND_PID
        sleep 2
        if ps -p \$BACKEND_PID > /dev/null; then
            echo "强制终止后端服务..."
            kill -9 \$BACKEND_PID
        fi
    fi
    rm -f "$PROJECT_ROOT/backend.pid"
fi

# 停止Nginx服务
echo "停止Nginx服务..."
systemctl stop nginx || nginx -s stop || true

echo "SoftLink服务已停止"
EOF

    chmod +x "$PROJECT_ROOT/stop_softlink.sh"
    success "已创建停止脚本: $PROJECT_ROOT/stop_softlink.sh"
    
    return 0
}

# 主函数
main() {
    # 初始化日志系统
    init_logging
    
    # 检查系统环境
    check_system_env || {
        error "系统环境检查失败"
        RETURN_CODE=1
        return 1
    }
    
    # 修复Nginx配置
    fix_nginx_config || {
        error "Nginx配置修复失败"
        RETURN_CODE=1
        return 1
    }
    
    # 设置后端环境
    setup_backend || {
        error "后端环境设置失败"
        RETURN_CODE=1
        return 1
    }
    
    # 启动后端服务
    start_backend || {
        error "后端服务启动失败"
        RETURN_CODE=1
        return 1
    }
    
    # 启动前端服务
    start_frontend || {
        error "前端服务启动失败"
        RETURN_CODE=1
        return 1
    }
    
    # 创建停止脚本
    create_stop_script || {
        warn "停止脚本创建失败"
    }
    
    # 健康检查
    health_check || {
        warn "健康检查发现问题"
    }
    
    success "SoftLink项目部署完成"
    log "详细部署日志请查看: $LOG_FILE"
    
    RETURN_CODE=0
    return 0
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
  case $1 in
    --help)
      show_help
      exit 0
      ;;
    --force)
      FORCE_MODE=true
      shift
      ;;
    --update-keys)
      UPDATE_SECURITY_KEYS=true
      shift
      ;;
    --port)
      BACKEND_PORT=$2
      shift 2
      ;;
    --no-root)
      shift
      ;;
    *)
      echo "未知参数: $1"
      echo "使用 --help 查看帮助"
      exit 1
      ;;
  esac
done

# 运行主函数
main
exit $RETURN_CODE 