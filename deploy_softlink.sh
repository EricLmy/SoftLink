#!/bin/bash

# SoftLink项目一键部署脚本
# 用于在腾讯云服务器上快速部署整个项目环境

# 确保脚本以正确的权限运行
if [ "$(id -u)" != "0" ] && [ "$1" != "--no-root" ]; then
    echo "此脚本需要root权限运行。"
    echo "如果确定不需要root权限，请使用 --no-root 参数运行。"
    exec sudo "$0" "$@"
    exit $?
fi

# 设置环境变量隔离
set -e  # 遇到错误立即退出
set -u  # 使用未定义的变量时报错
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
# 注意：前端构建目录是softlin-f而不是softlink-f
FRONTEND_BUILD_DIR="$FRONTEND_DIR/softlin-f"
LOG_DIR="$PROJECT_ROOT/logs"
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

# 错误处理函数
handle_error() {
    local exit_code=$1
    local error_message=$2
    local function_name=$3
    
    error "在执行 $function_name 时发生错误 (代码: $exit_code)"
    error "$error_message"
    
    # 记录错误详情到错误日志
    {
        echo "----------------------------------------"
        echo "错误时间: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "错误位置: $function_name"
        echo "错误代码: $exit_code"
        echo "错误信息: $error_message"
        echo "调用栈:"
        local frame=0
        while caller $frame; do
            ((frame++))
        done
        echo "----------------------------------------"
    } >> "$ERROR_LOG"
    
    # 如果存在备份，提示恢复选项
    if [ -d "$BACKUP_DIR" ]; then
        warn "发现配置备份目录: $BACKUP_DIR"
        echo "您可以使用以下命令恢复配置:"
        echo "  cp $BACKUP_DIR/configs/.env.backup $PROJECT_ROOT/.env"
        echo "  cp $BACKUP_DIR/configs/nginx.softlink.conf.backup $FRONTEND_DIR/nginx.softlink.conf"
    fi
    
    # 清理临时文件和进程
    cleanup
    
    return $exit_code
}

# 清理函数
cleanup() {
    log "===== 清理临时文件和进程 ====="
    
    # 删除临时文件
    rm -f "$FRONTEND_DIR/nginx.temp.conf"
    
    # 如果部署失败，清理PID文件
    if [ $? -ne 0 ]; then
        rm -f "$PROJECT_ROOT/backend.pid"
    fi
    
    # 记录清理完成
    log "清理完成"
}

# 设置错误处理陷阱
trap 'handle_error $? "意外终止" "${FUNCNAME[0]}"' ERR

# 解析命令行参数
while [[ $# -gt 0 ]]; do
  case $1 in
    --update-keys)
      UPDATE_SECURITY_KEYS=true
      shift
      ;;
    --no-root)
      shift
      ;;
    --force)
      FORCE_MODE=true
      shift
      ;;
    --port)
      if [[ $2 =~ ^[0-9]+$ ]] && [ $2 -gt 1024 ] && [ $2 -lt 65535 ]; then
        BACKEND_PORT=$2
        log "使用自定义后端端口: $BACKEND_PORT"
      else
        error "无效的端口号: $2，必须是1024-65535之间的数字"
        exit 1
      fi
      shift 2
      ;;
    --help)
      show_help
      exit 0
      ;;
    *)
      # 未知参数
      echo "未知参数: $1"
      echo "可用参数: --update-keys (更新安全密钥), --no-root (不使用root权限), --force (强制模式), --port <端口号> (指定后端端口)"
      echo "使用 --help 查看完整帮助"
      shift
      ;;
  esac
done

# 检查端口是否被占用并尝试释放
check_and_free_port() {
    local PORT=$1
    local SERVICE_NAME=$2
    local FORCE=$3
    
    log "检查端口 $PORT 是否被占用..."
    
    # 检查端口是否被占用
    if lsof -i:$PORT -P -n &> /dev/null; then
        warn "端口 $PORT 已被占用，尝试识别占用进程..."
        
        # 获取占用端口的进程信息
        local PID_INFO=$(lsof -i:$PORT -P -n | grep LISTEN)
        local PID=$(echo "$PID_INFO" | awk '{print $2}')
        local PROCESS_NAME=$(echo "$PID_INFO" | awk '{print $1}')
        local PROCESS_USER=$(ps -o user= -p $PID)
        local PROCESS_CMD=$(ps -o cmd= -p $PID | head -c 50)
        
        warn "端口 $PORT 被进程 $PROCESS_NAME (PID: $PID, 用户: $PROCESS_USER) 占用"
        warn "进程命令: $PROCESS_CMD"
        
        # 检查是否是特定类型的进程
        local IS_OUR_SERVICE=false
        local IS_SYSTEM_SERVICE=false
        
        if [[ "$PROCESS_NAME" == *"python"* ]] && [[ "$SERVICE_NAME" == "backend" ]]; then
            IS_OUR_SERVICE=true
        elif [[ "$PROCESS_NAME" == *"nginx"* ]] && [[ "$SERVICE_NAME" == "nginx" ]]; then
            IS_OUR_SERVICE=true
        fi
        
        # 检查是否是系统服务或其他重要服务
        if [[ "$PROCESS_NAME" == *"commplex-main"* ]] || 
           [[ "$PROCESS_CMD" == *"commplex-main"* ]]; then
            IS_SYSTEM_SERVICE=true
            warn "检测到可能是系统服务 (commplex-main)"
        fi
        
        # 如果不是强制模式且不是我们的服务，询问用户
        if [ "$FORCE" != "true" ] && [ "$IS_OUR_SERVICE" != "true" ]; then
            echo -e "${YELLOW}警告：端口 $PORT 被其他服务占用。${NC}"
            echo "进程信息："
            echo "  名称：$PROCESS_NAME"
            echo "  PID：$PID"
            echo "  用户：$PROCESS_USER"
            echo "  命令：$PROCESS_CMD"
            
            if [ "$IS_SYSTEM_SERVICE" = true ]; then
                echo -e "${RED}警告：这可能是系统服务或其他重要服务！${NC}"
                echo "建议选项："
                echo "  1. 更改SoftLink后端使用的端口"
                echo "  2. 如果确认可以安全终止该服务，再选择终止"
            fi
            
            echo "请选择操作："
            echo "  [t] 尝试终止该进程"
            echo "  [c] 更改SoftLink使用的端口"
            echo "  [s] 跳过并退出部署"
            read -p "您的选择 [t/c/s]: " -n 1 -r PORT_ACTION
            echo
            
            case $PORT_ACTION in
                [Tt]* )
                    log "尝试终止进程 $PID..."
                    ;;
                [Cc]* )
                    read -p "请输入新的后端端口号: " NEW_PORT
                    if [[ $NEW_PORT =~ ^[0-9]+$ ]] && [ $NEW_PORT -gt 1024 ] && [ $NEW_PORT -lt 65535 ]; then
                        log "将后端端口从 $BACKEND_PORT 更改为 $NEW_PORT"
                        BACKEND_PORT=$NEW_PORT
                        # 更新.env文件中的端口配置
                        if [ -f "$ENV_FILE" ]; then
                            sed -i "s|FLASK_RUN_PORT=.*|FLASK_RUN_PORT=$NEW_PORT|g" "$ENV_FILE" || true
                        fi
                        return 0
                    else
                        error "无效的端口号，必须是1024-65535之间的数字"
                        return 1
                    fi
                    ;;
                * )
                    log "用户选择退出部署"
                    exit 0
                    ;;
            esac
        fi
        
        # 如果是系统服务且处于强制模式，给出额外警告
        if [ "$IS_SYSTEM_SERVICE" = true ] && [ "$FORCE" = true ]; then
            warn "正在强制模式下终止可能的系统服务，这可能导致系统不稳定！"
        fi
        
        # 尝试优雅终止进程
        log "尝试优雅终止进程 $PID..."
        kill -15 $PID
        
        # 等待进程终止
        local WAIT_TIME=0
        while ps -p $PID &> /dev/null && [ $WAIT_TIME -lt 10 ]; do
            sleep 1
            WAIT_TIME=$((WAIT_TIME + 1))
        done
        
        # 如果进程仍然存在，尝试强制终止
        if ps -p $PID &> /dev/null; then
            warn "进程未响应，尝试强制终止..."
            kill -9 $PID
            sleep 1
        fi
        
        # 最终检查
        if lsof -i:$PORT -P -n &> /dev/null; then
            error "无法释放端口 $PORT，请手动检查并终止占用进程"
            error "或者考虑更改SoftLink使用的端口"
            
            # 提供更改端口的选项
            if [ "$FORCE" != "true" ]; then
                read -p "是否更改SoftLink使用的端口? (y/n): " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    read -p "请输入新的后端端口号: " NEW_PORT
                    if [[ $NEW_PORT =~ ^[0-9]+$ ]] && [ $NEW_PORT -gt 1024 ] && [ $NEW_PORT -lt 65535 ]; then
                        log "将后端端口从 $BACKEND_PORT 更改为 $NEW_PORT"
                        BACKEND_PORT=$NEW_PORT
                        # 更新.env文件中的端口配置
                        if [ -f "$ENV_FILE" ]; then
                            sed -i "s|FLASK_RUN_PORT=.*|FLASK_RUN_PORT=$NEW_PORT|g" "$ENV_FILE" || true
                        fi
                        return 0
                    else
                        error "无效的端口号，必须是1024-65535之间的数字"
                        return 1
                    fi
                else
                    return 1
                fi
            else
                return 1
            fi
        else
            success "端口 $PORT 已成功释放"
        fi
    else
        success "端口 $PORT 可用"
    fi
    
    return 0
}

# 检查服务是否已运行
check_service_status() {
    log "===== 检查服务状态 ====="
    
    local SERVICES_RUNNING=false
    local FORCE_STOP=${1:-false}
    
    # 检查后端服务
    local BACKEND_RUNNING=false
    if [ -f "$PROJECT_ROOT/backend.pid" ]; then
        BACKEND_PID=$(cat "$PROJECT_ROOT/backend.pid")
        if ps -p $BACKEND_PID > /dev/null; then
            warn "后端服务已在运行 (PID: $BACKEND_PID)"
            BACKEND_RUNNING=true
            SERVICES_RUNNING=true
        fi
    fi
    
    # 检查是否有Python进程运行startup.py
    STARTUP_PID=$(pgrep -f "python.*startup.py" || echo "")
    if [ ! -z "$STARTUP_PID" ]; then
        if [ "$BACKEND_RUNNING" = false ]; then
            warn "检测到startup.py进程正在运行 (PID: $STARTUP_PID)"
            SERVICES_RUNNING=true
        fi
    fi
    
    # 检查Nginx是否运行
    local NGINX_RUNNING=false
    if systemctl is-active --quiet nginx || pgrep nginx > /dev/null; then
        warn "Nginx服务已在运行"
        NGINX_RUNNING=true
        SERVICES_RUNNING=true
    fi
    
    # 检查关键端口
    local PORTS_OCCUPIED=false
    if lsof -i:$BACKEND_PORT -P -n &> /dev/null; then
        warn "后端端口 $BACKEND_PORT 被占用"
        PORTS_OCCUPIED=true
    fi
    
    if lsof -i:$FRONTEND_PORT -P -n &> /dev/null; then
        warn "前端端口 $FRONTEND_PORT 被占用"
        PORTS_OCCUPIED=true
    fi
    
    # 如果有服务正在运行或端口被占用
    if [ "$SERVICES_RUNNING" = true ] || [ "$PORTS_OCCUPIED" = true ]; then
        if [ "$FORCE_STOP" = true ]; then
            log "强制停止现有服务..."
            stop_services "force"
        else
            echo -e "${YELLOW}检测到SoftLink服务已在运行或端口被占用。${NC}"
            read -p "是否停止现有服务并重新部署? (y/n): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                log "停止现有服务..."
                stop_services
            else
                log "用户选择保留现有服务，退出部署"
                exit 0
            fi
        fi
    fi
    
    # 确保端口可用
    check_and_free_port $BACKEND_PORT "backend" "$FORCE_STOP" || exit 1
    check_and_free_port $FRONTEND_PORT "nginx" "$FORCE_STOP" || exit 1
    
    success "服务状态检查完成"
}

# 首先停止可能已经运行的服务
stop_services() {
    log "===== 停止已运行的服务 ====="
    
    # 停止后端服务
    if [ -f "$PROJECT_ROOT/backend.pid" ]; then
        BACKEND_PID=$(cat "$PROJECT_ROOT/backend.pid")
        if ps -p $BACKEND_PID > /dev/null; then
            log "停止后端服务 (PID: $BACKEND_PID)..."
            kill $BACKEND_PID
            sleep 2
            if ps -p $BACKEND_PID > /dev/null; then
                log "后端服务未响应，强制终止..."
                kill -9 $BACKEND_PID
            fi
        fi
        rm -f "$PROJECT_ROOT/backend.pid"
    fi
    
    # 查找并停止其他可能正在运行的后端进程
    log "查找并停止其他Python进程..."
    STARTUP_PIDS=$(pgrep -f "python.*startup.py" || echo "")
    if [ ! -z "$STARTUP_PIDS" ]; then
        log "找到startup.py进程，终止中..."
        echo $STARTUP_PIDS | xargs kill -9 2>/dev/null || true
    fi
    
    # 确保没有进程占用后端端口
    log "确保端口$BACKEND_PORT没有被占用..."
    PROCESS_USING_PORT=$(lsof -t -i:$BACKEND_PORT 2>/dev/null || echo "")
    if [ ! -z "$PROCESS_USING_PORT" ]; then
        log "终止占用端口$BACKEND_PORT的进程: $PROCESS_USING_PORT"
        echo $PROCESS_USING_PORT | xargs kill -9 2>/dev/null || true
    fi
    
    # 停止Nginx服务
    log "停止Nginx服务..."
    sudo systemctl stop nginx 2>/dev/null || sudo nginx -s stop 2>/dev/null || true
    
    # 确保Nginx完全停止
    NGINX_PIDS=$(pgrep nginx || echo "")
    if [ ! -z "$NGINX_PIDS" ]; then
        log "强制终止所有Nginx进程..."
        echo $NGINX_PIDS | xargs kill -9 2>/dev/null || true
    fi
    
    # 确保没有进程占用前端端口
    log "确保端口$FRONTEND_PORT没有被占用..."
    PROCESS_USING_PORT=$(lsof -t -i:$FRONTEND_PORT 2>/dev/null || echo "")
    if [ ! -z "$PROCESS_USING_PORT" ]; then
        log "终止占用端口$FRONTEND_PORT的进程: $PROCESS_USING_PORT"
        echo $PROCESS_USING_PORT | xargs kill -9 2>/dev/null || true
    fi
    
    # 等待所有进程完全终止
    sleep 2
    
    # 最终检查
    if lsof -i:$BACKEND_PORT -P -n &> /dev/null || lsof -i:$FRONTEND_PORT -P -n &> /dev/null; then
        warn "某些端口仍被占用，可能需要手动干预"
    else
        success "所有服务已停止，端口已释放"
    fi
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        error "$1 未安装。请安装后重试。"
        echo -e "  安装命令: $2" | tee -a $LOG_FILE
        return 1
    else
        success "$1 已安装"
        return 0
    fi
}

# 检查系统环境
check_system_env() {
    log "===== 检查系统环境 ====="
    
    # 检查操作系统
    OS=$(cat /etc/os-release | grep -oP '(?<=^ID=).+' | tr -d '"')
    VER=$(cat /etc/os-release | grep -oP '(?<=^VERSION_ID=).+' | tr -d '"')
    log "操作系统: $OS $VER"
    
    # 检查内存
    MEM_TOTAL=$(free -m | awk '/^Mem:/{print $2}')
    MEM_FREE=$(free -m | awk '/^Mem:/{print $4}')
    log "系统内存: 总计 ${MEM_TOTAL}MB，可用 ${MEM_FREE}MB"
    
    if [ $MEM_FREE -lt 1000 ]; then
        warn "可用内存不足1GB，可能会影响系统性能"
    fi
    
    # 检查磁盘空间
    DISK_FREE=$(df -h / | awk '/\//{print $4}')
    log "磁盘空间: 可用 $DISK_FREE"
    
    # 检查必要工具
    check_command "python3" "sudo apt update && sudo apt install -y python3"
    check_command "pip3" "sudo apt update && sudo apt install -y python3-pip"
    check_command "nginx" "sudo apt update && sudo apt install -y nginx"
    check_command "git" "sudo apt update && sudo apt install -y git"
    
    # 检查端口占用情况
    check_and_free_port $BACKEND_PORT "backend" false
    check_and_free_port $FRONTEND_PORT "nginx" false
}

# 设置后端环境
setup_backend() {
    log "===== 设置后端环境 ====="
    
    cd $BACKEND_DIR
    
    # 检查虚拟环境
    if [ ! -d "venv" ]; then
        log "创建Python虚拟环境..."
        python3 -m venv venv
        if [ $? -ne 0 ]; then
            error "创建虚拟环境失败"
            return 1
        fi
    else
        log "已存在虚拟环境"
    fi
    
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
    
    # 更新 .env 文件中的数据库配置
    log "更新后端环境配置..."
    if [ -f "$PROJECT_ROOT/.env" ]; then
        log "找到.env文件，更新数据库配置..."
        # 备份原有.env文件
        cp "$PROJECT_ROOT/.env" "$CONFIG_BACKUP_DIR/.env.backup"
        
        # 更新数据库连接 URL
        sed -i "s|DATABASE_URL=.*|DATABASE_URL=postgresql://$DB_USER:$DB_PASS@$DB_HOST:$DB_PORT/$DB_NAME|g" "$PROJECT_ROOT/.env"
        
        # 更新调试标志
        sed -i "s|DEBUG=.*|DEBUG=False|g" "$PROJECT_ROOT/.env"
        
        # 根据参数决定是否更新安全密钥
        if [ "$UPDATE_SECURITY_KEYS" = true ]; then
            log "更新安全密钥..."
            NEW_SECRET_KEY=$(openssl rand -hex 32)
            NEW_JWT_KEY=$(openssl rand -hex 32)
            sed -i "s|SECRET_KEY=.*|SECRET_KEY=$NEW_SECRET_KEY|g" "$PROJECT_ROOT/.env"
            sed -i "s|JWT_SECRET_KEY=.*|JWT_SECRET_KEY=$NEW_JWT_KEY|g" "$PROJECT_ROOT/.env"
            success "已生成新的安全密钥"
            warn "注意：更新密钥会导致所有现有用户会话和JWT令牌失效"
        else
            # 确保SECRET_KEY已设置
            if grep -q "your-super-secret-key" "$PROJECT_ROOT/.env"; then
                NEW_SECRET_KEY=$(openssl rand -hex 32)
                NEW_JWT_KEY=$(openssl rand -hex 32)
                sed -i "s|SECRET_KEY=.*|SECRET_KEY=$NEW_SECRET_KEY|g" "$PROJECT_ROOT/.env"
                sed -i "s|JWT_SECRET_KEY=.*|JWT_SECRET_KEY=$NEW_JWT_KEY|g" "$PROJECT_ROOT/.env"
                log "生成了新的安全密钥"
            else
                log "保留现有安全密钥"
            fi
        fi
    else
        log "未找到.env文件，创建新文件..."
        NEW_SECRET_KEY=$(openssl rand -hex 32)
        NEW_JWT_KEY=$(openssl rand -hex 32)
        
        cat > "$PROJECT_ROOT/.env" << EOL
# Flask配置
FLASK_ENV=production
FLASK_APP=app.py

# 数据库配置
DATABASE_URL=postgresql://$DB_USER:$DB_PASS@$DB_HOST:$DB_PORT/$DB_NAME

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

# 配置Nginx
setup_nginx() {
    log "===== 配置Nginx ====="
    
    # 检查Nginx配置文件
    if [ ! -f "$NGINX_CONF" ]; then
        error "未找到Nginx配置文件: $NGINX_CONF"
        return 1
    fi
    
    # 修改Nginx配置中的路径和服务名
    log "更新Nginx配置文件..."
    
    # 创建临时配置文件
    cat > "$FRONTEND_DIR/nginx.temp.conf" << EOL
server {
    listen 80;
    server_name $SERVER_IP;
    
    # GZIP压缩配置，提高传输效率
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
        alias $PROJECT_ROOT/frontend/softlin-f/static/;
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
    
    # 所有其他请求返回index.html (单页应用配置)
    location / {
        root $PROJECT_ROOT/frontend/softlin-f;
        try_files \$uri \$uri/ /index.html;
        index index.html;
    }
    
    # 错误页面配置
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root $PROJECT_ROOT/frontend/softlin-f;
    }
}
EOL
    
    # 复制配置文件
    log "应用Nginx配置..."
    if [ -f "/etc/nginx/nginx.conf" ]; then
        NGINX_CONF_DIR="/etc/nginx"
    elif [ -f "$NGINX_PATH/conf/nginx.conf" ]; then
        NGINX_CONF_DIR="$NGINX_PATH/conf"
    else
        error "无法找到Nginx配置目录"
        return 1
    fi
    
    log "将Nginx配置写入 $NGINX_CONF_DIR/conf.d/softlink.conf"
    sudo mkdir -p "$NGINX_CONF_DIR/conf.d"
    sudo cp -f "$FRONTEND_DIR/nginx.temp.conf" "$NGINX_CONF_DIR/conf.d/softlink.conf"
    
    # 确保主配置文件包含conf.d目录
    if ! grep -q "include.*conf.d" "$NGINX_CONF_DIR/nginx.conf"; then
        log "更新主Nginx配置文件以包含conf.d目录..."
        sudo sed -i '/http {/a \    include /etc/nginx/conf.d/*.conf;' "$NGINX_CONF_DIR/nginx.conf"
    fi
    
    # 测试配置
    log "测试Nginx配置..."
    sudo nginx -t
    if [ $? -ne 0 ]; then
        error "Nginx配置测试失败"
        return 1
    fi
    
    success "Nginx配置完成"
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
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 确保环境变量中包含端口设置
    export FLASK_RUN_PORT=$BACKEND_PORT
    
    # 启动后端服务
    log "启动后端服务在端口 $BACKEND_PORT..."
    nohup python startup.py --port $BACKEND_PORT > $BACKEND_DIR/backend.log 2>&1 &
    BACKEND_PID=$!
    
    # 检查服务是否成功启动
    sleep 5
    if ps -p $BACKEND_PID > /dev/null; then
        success "后端服务启动成功 (PID: $BACKEND_PID)"
        echo $BACKEND_PID > "$PROJECT_ROOT/backend.pid"
    else
        error "后端服务启动失败，请检查backend.log文件"
        cat $BACKEND_DIR/backend.log | tail -n 20 | tee -a $LOG_FILE
        return 1
    fi
    
    # 检查端口是否正常监听
    sleep 2
    if lsof -i:$BACKEND_PORT -P -n | grep LISTEN > /dev/null; then
        success "后端服务正在监听端口 $BACKEND_PORT"
    else
        warn "后端服务可能未正确监听端口 $BACKEND_PORT，尝试查看日志..."
        cat $BACKEND_DIR/backend.log | tail -n 20 | tee -a $LOG_FILE
    fi
    
    return 0
}

# 启动前端服务
start_frontend() {
    log "===== 启动前端服务 ====="
    
    # 检查前端构建目录
    if [ ! -d "$FRONTEND_BUILD_DIR" ]; then
        warn "未找到前端构建目录: $FRONTEND_BUILD_DIR"
        log "检查是否存在softlink-f目录..."
        
        # 尝试重命名目录
        if [ -d "$FRONTEND_DIR/softlink-f" ]; then
            log "找到softlink-f目录，重命名为softlin-f..."
            mv "$FRONTEND_DIR/softlink-f" "$FRONTEND_BUILD_DIR"
        else
            error "未找到任何前端构建目录"
            return 1
        fi
    fi
    
    # 检查index.html
    if [ ! -f "$FRONTEND_BUILD_DIR/index.html" ]; then
        error "前端构建目录中未找到index.html文件"
        return 1
    fi
    
    # 重启Nginx
    log "重启Nginx服务..."
    sudo systemctl restart nginx
    if [ $? -ne 0 ]; then
        error "Nginx重启失败"
        log "尝试使用命令行启动Nginx..."
        sudo nginx -s reload || sudo $NGINX_BIN
        if [ $? -ne 0 ]; then
            error "Nginx启动失败"
            return 1
        fi
    fi
    
    # 检查Nginx是否正常运行
    sleep 2
    if systemctl is-active --quiet nginx || pgrep nginx > /dev/null; then
        success "Nginx服务启动成功"
    else
        error "Nginx服务启动失败"
        log "检查Nginx错误日志..."
        cat /var/log/nginx/error.log | tail -n 20 | tee -a $LOG_FILE
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
    
    # 检查后端API可访问性
    log "检查后端API可访问性..."
    if curl -s --head http://localhost:$BACKEND_PORT > /dev/null; then
        success "后端API可以访问"
    else
        error "无法访问后端API"
        warn "可能原因: 1.后端服务未启动 2.防火墙阻止 3.端口配置错误"
        warn "解决方案: 检查后端日志($BACKEND_DIR/backend.log)，确保服务正常启动且监听正确端口"
    fi
    
    # 检查Nginx服务
    log "检查Nginx服务..."
    if systemctl is-active --quiet nginx || pgrep nginx > /dev/null; then
        success "Nginx服务运行正常"
    else
        error "Nginx服务未运行"
        warn "解决方案: 运行 'sudo systemctl start nginx' 或 'sudo nginx' 启动服务"
    fi
    
    # 检查前端可访问性
    log "检查前端可访问性..."
    if curl -s --head http://localhost > /dev/null; then
        success "前端页面可以访问"
    else
        error "无法访问前端页面"
        warn "可能原因: 1.Nginx配置错误 2.防火墙阻止 3.前端文件路径错误"
        warn "解决方案: 检查Nginx错误日志(/var/log/nginx/error.log)，确保配置正确"
    fi
    
    log "健康检查完成，详细日志请查看: $LOG_FILE"
}

# 检查防火墙配置
check_firewall() {
    log "===== 检查防火墙配置 ====="
    
    # 检查常见防火墙工具
    if command -v ufw &> /dev/null; then
        # Ubuntu等使用ufw
        log "使用ufw配置防火墙..."
        sudo ufw allow 80/tcp
        sudo ufw allow $BACKEND_PORT/tcp
        sudo ufw status | tee -a $LOG_FILE
    elif command -v firewall-cmd &> /dev/null; then
        # CentOS等使用firewalld
        log "使用firewalld配置防火墙..."
        sudo firewall-cmd --permanent --add-port=80/tcp
        sudo firewall-cmd --permanent --add-port=$BACKEND_PORT/tcp
        sudo firewall-cmd --reload
        sudo firewall-cmd --list-all | tee -a $LOG_FILE
    else
        warn "未检测到标准防火墙工具，请手动确保端口80和$BACKEND_PORT开放"
    fi
    
    success "防火墙配置检查完成"
}

# 显示系统信息
show_system_info() {
    log "===== SoftLink系统信息 ====="
    
    # 获取服务器IP
    SERVER_IP=$(hostname -I | awk '{print $1}')
    
    echo -e "\n${GREEN}==================================${NC}"
    echo -e "${GREEN}  SoftLink系统部署完成${NC}"
    echo -e "${GREEN}==================================${NC}"
    echo -e "前端访问地址: ${BLUE}http://$SERVER_IP${NC}"
    echo -e "后端API地址: ${BLUE}http://$SERVER_IP:$BACKEND_PORT${NC}"
    echo -e "部署日志文件: ${YELLOW}$LOG_FILE${NC}"
    echo -e "\n如需停止服务，请运行: ${YELLOW}$PROJECT_ROOT/stop_softlink.sh${NC}"
    
    # 显示安全密钥更新信息
    if [ "$UPDATE_SECURITY_KEYS" = true ]; then
        echo -e "${YELLOW}安全密钥已更新，所有现有会话将失效${NC}"
    fi
    
    echo -e "${GREEN}==================================${NC}\n"
}

# 创建停止脚本
create_stop_script() {
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
            echo "后端服务未响应，强制终止..."
            kill -9 \$BACKEND_PID
        fi
    else
        echo "后端服务已经停止"
    fi
    rm -f "$PROJECT_ROOT/backend.pid"
else
    echo "未找到后端PID文件，尝试查找并停止进程..."
    pkill -f "python.*startup.py"
fi

# 查找并终止占用5000端口的进程
echo "查找并终止占用5000端口的进程..."
PROCESS_USING_PORT=\$(lsof -t -i:$BACKEND_PORT)
if [ ! -z "\$PROCESS_USING_PORT" ]; then
    echo "终止占用端口$BACKEND_PORT的进程: \$PROCESS_USING_PORT"
    kill -9 \$PROCESS_USING_PORT || true
fi

# 停止Nginx服务
echo "停止Nginx服务..."
sudo systemctl stop nginx || sudo nginx -s stop || true

echo "SoftLink服务已停止"
EOF

    chmod +x "$PROJECT_ROOT/stop_softlink.sh"
    success "已创建停止脚本: $PROJECT_ROOT/stop_softlink.sh"
}

# 显示帮助信息
show_help() {
    cat << EOF
SoftLink项目部署脚本
用法: ./deploy_softlink.sh [选项]

选项:
  --help          显示此帮助信息
  --update-keys   更新安全密钥（会使现有会话失效）
  --no-root       不使用root权限运行（不推荐）
  --force         强制模式，不询问确认
  --port <端口>   指定后端服务端口（默认: 5000）

示例:
  ./deploy_softlink.sh              # 正常部署，保留现有密钥
  ./deploy_softlink.sh --update-keys # 部署并更新安全密钥
  ./deploy_softlink.sh --force      # 强制部署，自动停止冲突服务
  ./deploy_softlink.sh --port 5001  # 指定后端端口为5001

注意:
  1. 建议在部署前备份重要数据
  2. 部署日志将保存在 $LOG_DIR 目录
  3. 如遇问题，请查看错误日志: $ERROR_LOG
  4. 如果默认端口5000被占用，可以使用--port选项指定其他端口

端口冲突处理:
  - 如果检测到端口冲突，脚本会提供以下选项:
    a) 终止占用端口的进程（谨慎使用）
    b) 更改SoftLink使用的端口
    c) 退出部署
  - 对于系统服务，建议更改SoftLink使用的端口而非终止服务
EOF
}

# 备份现有配置文件
backup_configs() {
    log "===== 备份配置文件 ====="
    
    # 备份.env文件
    if [ -f "$ENV_FILE" ]; then
        cp "$ENV_FILE" "$CONFIG_BACKUP_DIR/.env.backup"
        success "已备份.env文件"
    fi
    
    # 备份Nginx配置
    if [ -f "$NGINX_CONF" ]; then
        cp "$NGINX_CONF" "$CONFIG_BACKUP_DIR/nginx.softlink.conf.backup"
        success "已备份Nginx配置文件"
    fi
    
    # 备份数据库配置（如果存在）
    if [ -f "$BACKEND_DIR/config.py" ]; then
        cp "$BACKEND_DIR/config.py" "$CONFIG_BACKUP_DIR/config.py.backup"
        success "已备份数据库配置文件"
    fi
    
    # 创建备份信息文件
    cat > "$BACKUP_DIR/backup_info.txt" << EOL
备份时间: $(date '+%Y-%m-%d %H:%M:%S')
服务器IP: $SERVER_IP
后端端口: $BACKEND_PORT
前端端口: $FRONTEND_PORT
数据库配置:
  主机: $DB_HOST
  端口: $DB_PORT
  数据库: $DB_NAME
  用户: $DB_USER
EOL
    
    success "配置文件备份完成，备份目录: $BACKUP_DIR"
}

# 验证配置文件
validate_configs() {
    log "===== 验证配置文件 ====="
    local has_error=false
    
    # 验证.env文件
    if [ -f "$ENV_FILE" ]; then
        if ! grep -q "^SECRET_KEY=" "$ENV_FILE" || ! grep -q "^JWT_SECRET_KEY=" "$ENV_FILE"; then
            error ".env文件缺少必要的密钥配置"
            has_error=true
        fi
    else
        warn "未找到.env文件，将在部署时创建"
    fi
    
    # 验证Nginx配置
    if [ -f "$NGINX_CONF" ]; then
        if ! nginx -t -c "$NGINX_CONF" &>/dev/null; then
            error "Nginx配置文件验证失败"
            has_error=true
        fi
    else
        warn "未找到Nginx配置文件，将在部署时创建"
    fi
    
    # 验证数据库连接
    log "验证数据库连接..."
    if command -v pg_isready &>/dev/null; then
        if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" &>/dev/null; then
            error "无法连接到数据库服务器"
            has_error=true
        fi
    else
        warn "未安装pg_isready工具，跳过数据库连接验证"
    fi
    
    if [ "$has_error" = true ]; then
        error "配置验证失败，请修复上述错误后重试"
        return 1
    fi
    
    success "配置验证完成"
    return 0
}

# 主函数
main() {
    # 初始化日志系统
    init_logging
    
    # 显示脚本参数信息
    log "开始部署SoftLink项目..."
    if [ "$UPDATE_SECURITY_KEYS" = true ]; then
        log "参数: 将更新安全密钥"
    fi
    
    # 创建备份
    backup_configs
    
    # 验证配置文件
    validate_configs || {
        error "配置验证失败"
        return 1
    }
    
    # 检查服务状态并处理端口占用问题
    check_service_status || {
        error "服务状态检查失败"
        return 1
    }
    
    # 检查系统环境
    check_system_env || {
        error "系统环境检查失败"
        return 1
    }
    
    # 设置后端环境
    setup_backend || {
        error "后端环境设置失败"
        return 1
    }
    
    # 配置Nginx
    setup_nginx || {
        error "Nginx配置失败"
        return 1
    }
    
    # 启动后端服务
    start_backend || {
        error "后端服务启动失败"
        return 1
    }
    
    # 启动前端服务
    start_frontend || {
        error "前端服务启动失败"
        stop_services
        return 1
    }
    
    # 检查防火墙配置
    check_firewall || {
        warn "防火墙配置可能存在问题，请手动检查"
    }
    
    # 执行健康检查
    health_check || {
        warn "健康检查发现潜在问题，请查看日志了解详情"
    }
    
    # 创建停止脚本
    create_stop_script || {
        warn "停止脚本创建失败，请手动管理服务"
    }
    
    # 显示系统信息
    show_system_info
    
    # 清理临时文件
    cleanup
    
    success "SoftLink项目部署完成"
    log "详细部署日志请查看: $LOG_FILE"
    return 0
}

# 解析命令行参数并执行主函数
case "$1" in
    --help)
        show_help
        exit 0
        ;;
    *)
        main "$@"
        exit $?
        ;;
esac 