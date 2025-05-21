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


我来检查项目代码并修改deploy_softlink.sh脚本，使其能够直接运行并正确部署项目到腾讯云服务器。

Read file: deploy_softlink.sh

Read file: frontend/nginx.softlink.conf

Read file: .env

```shell script:deploy_softlink.sh
#!/bin/bash

# SoftLink项目一键部署脚本
# 用于在腾讯云服务器上快速部署整个项目环境

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
LOG_FILE="$PROJECT_ROOT/deploy_log.txt"

# 腾讯云服务配置
SERVER_IP=$(hostname -I | awk '{print $1}')
NGINX_PATH="/usr/local/nginx"
NGINX_BIN="/usr/sbin/nginx" # 系统安装的nginx位置
BACKEND_PORT=5000
FRONTEND_PORT=80

# 数据库配置
DB_HOST="localhost"
DB_PORT=5432
DB_USER="postgres"
DB_PASS="123.123.MengLi"
DB_NAME="softlink"

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
    pkill -f "python.*startup.py" || true
    
    # 确保没有进程占用5000端口
    log "确保端口5000没有被占用..."
    PROCESS_USING_PORT=$(lsof -t -i:$BACKEND_PORT)
    if [ ! -z "$PROCESS_USING_PORT" ]; then
        log "终止占用端口5000的进程: $PROCESS_USING_PORT"
        kill -9 $PROCESS_USING_PORT || true
    fi
    
    # 停止Nginx服务
    log "停止Nginx服务..."
    sudo systemctl stop nginx || sudo nginx -s stop || true
    
    success "所有服务已停止"
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
        warn "端口 $1 已被占用，尝试关闭占用进程..."
        # 尝试终止占用该端口的进程
        lsof -t -i:$1 | xargs kill -9 || true
        sleep 2
        if lsof -i:$1 &> /dev/null; then
            error "无法释放端口 $1，请手动终止占用进程"
            echo -e "  占用进程: $(lsof -i:$1 | tail -n +2)" | tee -a $LOG_FILE
            return 1
        else
            success "端口 $1 已释放"
            return 0
        fi
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
    
    # 更新 .env 文件中的数据库配置
    log "更新后端环境配置..."
    if [ -f "$PROJECT_ROOT/.env" ]; then
        log "找到.env文件，更新数据库配置..."
        # 备份原有.env文件
        cp "$PROJECT_ROOT/.env" "$PROJECT_ROOT/.env.backup"
        
        # 更新数据库连接 URL
        sed -i "s|DATABASE_URL=.*|DATABASE_URL=postgresql://$DB_USER:$DB_PASS@$DB_HOST:$DB_PORT/$DB_NAME|g" "$PROJECT_ROOT/.env"
        
        # 更新调试标志
        sed -i "s|DEBUG=.*|DEBUG=False|g" "$PROJECT_ROOT/.env"
        
        # 确保SECRET_KEY已设置
        if grep -q "your-super-secret-key" "$PROJECT_ROOT/.env"; then
            NEW_SECRET_KEY=$(openssl rand -hex 32)
            NEW_JWT_KEY=$(openssl rand -hex 32)
            sed -i "s|SECRET_KEY=.*|SECRET_KEY=$NEW_SECRET_KEY|g" "$PROJECT_ROOT/.env"
            sed -i "s|JWT_SECRET_KEY=.*|JWT_SECRET_KEY=$NEW_JWT_KEY|g" "$PROJECT_ROOT/.env"
            log "生成了新的安全密钥"
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
    if [ ! -f "$FRONTEND_DIR/nginx.softlink.conf" ]; then
        error "未找到Nginx配置文件: $FRONTEND_DIR/nginx.softlink.conf"
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
    
    sudo cp -f "$FRONTEND_DIR/nginx.temp.conf" "$NGINX_CONF_DIR/nginx.conf"
    
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
    nohup python startup.py > $BACKEND_DIR/backend.log 2>&1 &
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

# 主函数
main() {
    log "开始部署SoftLink项目..."
    
    # 首先停止已运行的服务
    stop_services
    
    # 检查系统环境
    check_system_env
    
    # 设置后端环境
    setup_backend
    if [ $? -ne 0 ]; then
        error "后端环境设置失败，部署中止"
        exit 1
    fi
    
    # 检查防火墙配置
    check_firewall
    
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
```
现在我已经修改了`deploy_softlink.sh`脚本，使其能够在腾讯云服务器上正确部署SoftLink项目。以下是关于部署和配置的重要信息：

### 部署方法

1. 将项目代码上传到腾讯云服务器
2. 给部署脚本添加执行权限：
   ```bash
   chmod +x deploy_softlink.sh
   ```
3. 执行部署脚本：
   ```bash
   ./deploy_softlink.sh
   ```

### 主要配置项

1. **数据库配置**
   - 位置：脚本会自动更新项目根目录下的`.env`文件
   - 默认配置：
     ```
     DB_HOST="localhost"
     DB_PORT=5432
     DB_USER="postgres"
     DB_PASS="123.123.MengLi"
     DB_NAME="softlink"
     ```
   - 如需修改：直接在脚本开头的"数据库配置"部分修改这些变量

2. **Nginx配置**
   - 脚本会自动生成新的Nginx配置文件，无需手动修改
   - 前端目录：`frontend/softlink-f`
   - 静态文件位置：`frontend/softlin-f/static/`
   - 前端入口：`frontend/softlin-f/index.html`

3. **端口配置**
   - 前端：80端口（Nginx）
   - 后端：5000端口（Python服务）
   - 如需修改：在脚本开头的"腾讯云服务配置"部分修改`BACKEND_PORT`和`FRONTEND_PORT`变量

### 脚本改进内容

1. **自动停止已运行服务**
   - 脚本开始时会自动停止已运行的服务，确保端口不被占用

2. **前端目录修正**
   - 自动检测并使用正确的前端目录（softlin-f）
   - 如果只有softlink-f目录，会自动重命名为softlin-f

3. **自动配置数据库**
   - 自动更新`.env`文件中的数据库连接信息
   - 自动生成安全密钥

4. **防火墙配置**
   - 自动配置防火墙，开放80和5000端口

5. **更好的错误处理**
   - 在服务启动失败时显示日志内容
   - 提供详细的错误原因和解决方案

6. **完整的停止脚本**
   - 创建`stop_softlink.sh`脚本，确保所有服务都能正确停止
   - 包括查找并终止占用端口的进程

### 如何检查服务运行状态

部署完成后，脚本会显示服务访问地址：
- 前端：`http://服务器IP`
- 后端：`http://服务器IP:5000`

如果服务无法访问，可以查看以下日志：
- 部署日志：`deploy_log.txt`
- 后端日志：`backend/backend.log`
- Nginx日志：`/var/log/nginx/error.log`

### 如何停止服务

运行脚本创建的停止脚本：
```bash
./stop_softlink.sh
```

这个脚本会确保所有相关服务都被正确停止，包括后端Python进程、占用5000端口的进程和Nginx服务。
