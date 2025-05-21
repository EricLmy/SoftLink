#!/bin/bash

# SoftLink项目一键部署脚本
# 用于在云服务器上快速部署整个项目环境

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
FRONTEND_BUILD_DIR="$FRONTEND_DIR/softlink-f"
LOG_FILE="$PROJECT_ROOT/deploy_log.txt"

# 服务配置
NGINX_PATH="/usr/local/nginx"
NGINX_BIN="/usr/sbin/nginx" # 系统安装的nginx位置
BACKEND_PORT=5000
FRONTEND_PORT=80

# 清空日志文件
> $LOG_FILE

# 输出信息函数
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a $LOG_FILE
}

success() {
    echo -e "${GREEN}[成功]${NC} $1" | tee -a $LOG_FILE
}

warn() {
    echo -e "${YELLOW}[警告]${NC} $1" | tee -a $LOG_FILE
}

error() {
    echo -e "${RED}[错误]${NC} $1" | tee -a $LOG_FILE
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

# 检查端口是否被占用
check_port() {
    if lsof -i:$1 &> /dev/null; then
        warn "端口 $1 已被占用，可能会导致服务启动失败"
        echo -e "  占用进程: $(lsof -i:$1 | tail -n +2)" | tee -a $LOG_FILE
        return 1
    else
        success "端口 $1 可用"
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
    check_port $BACKEND_PORT
    check_port $FRONTEND_PORT
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
    
    success "后端环境设置完成"
    return 0
}

# 配置Nginx
setup_nginx() {
    log "===== 配置Nginx ====="
    
    # 检查Nginx配置文件
    if [ ! -f "$FRONTEND_DIR/nginx.softlink.conf" ]; then
        error "未找到Nginx配置文件: $FRONTEND_DIR/nginx.softlink.conf"
        return 1
    fi
    
    # 修改Nginx配置中的路径为实际路径
    log "更新Nginx配置文件..."
    sed -i "s|D:/workplace/SoftLink/SoftLink-0517|$PROJECT_ROOT|g" "$FRONTEND_DIR/nginx.softlink.conf"
    
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
    
    sudo cp -f "$FRONTEND_DIR/nginx.softlink.conf" "$NGINX_CONF_DIR/nginx.conf"
    
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
    
    # 启动后端服务
    log "启动后端服务..."
    nohup python startup.py > backend.log 2>&1 &
    BACKEND_PID=$!
    
    # 检查服务是否成功启动
    sleep 5
    if ps -p $BACKEND_PID > /dev/null; then
        success "后端服务启动成功 (PID: $BACKEND_PID)"
        echo $BACKEND_PID > "$PROJECT_ROOT/backend.pid"
    else
        error "后端服务启动失败，请检查backend.log文件"
        return 1
    fi
    
    # 检查端口是否正常监听
    sleep 2
    if lsof -i:$BACKEND_PORT -P -n | grep LISTEN > /dev/null; then
        success "后端服务正在监听端口 $BACKEND_PORT"
    else
        warn "后端服务可能未正确监听端口 $BACKEND_PORT"
    fi
    
    return 0
}

# 启动前端服务
start_frontend() {
    log "===== 启动前端服务 ====="
    
    # 检查前端构建目录
    if [ ! -d "$FRONTEND_BUILD_DIR" ]; then
        error "未找到前端构建目录: $FRONTEND_BUILD_DIR"
        return 1
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
        warn "解决方案: 检查后端日志(backend.log)，确保服务正常启动且监听正确端口"
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

# 停止Nginx服务
echo "停止Nginx服务..."
sudo systemctl stop nginx || sudo nginx -s stop

echo "SoftLink服务已停止"
EOF

    chmod +x "$PROJECT_ROOT/stop_softlink.sh"
    success "已创建停止脚本: $PROJECT_ROOT/stop_softlink.sh"
}

# 主函数
main() {
    log "开始部署SoftLink项目..."
    
    # 检查系统环境
    check_system_env
    
    # 设置后端环境
    setup_backend
    if [ $? -ne 0 ]; then
        error "后端环境设置失败，部署中止"
        exit 1
    fi
    
    # 配置Nginx
    setup_nginx
    if [ $? -ne 0 ]; then
        error "Nginx配置失败，部署中止"
        exit 1
    fi
    
    # 启动后端服务
    start_backend
    if [ $? -ne 0 ]; then
        error "后端服务启动失败，部署中止"
        exit 1
    fi
    
    # 启动前端服务
    start_frontend
    if [ $? -ne 0 ]; then
        error "前端服务启动失败，部署中止"
        exit 1
    fi
    
    # 创建停止脚本
    create_stop_script
    
    # 健康检查
    health_check
    
    # 显示系统信息
    show_system_info
    
    log "SoftLink项目部署完成"
}

# 执行主函数
main 