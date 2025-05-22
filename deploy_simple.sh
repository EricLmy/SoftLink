#!/bin/bash
# SoftLink极简部署脚本 - 避免任何复杂特性

echo "开始部署SoftLink到腾讯云服务器..."
PORT=5001
WORK_DIR=$(pwd)

echo "1. 停止已有服务..."
# 停止后端
if [ -f "backend.pid" ]; then
  PID=$(cat backend.pid)
  kill $PID 2>/dev/null || kill -9 $PID 2>/dev/null || true
  rm -f backend.pid
fi
# 停止可能的Python进程
pkill -f "python.*startup.py" 2>/dev/null || true
# 停止Nginx
sudo systemctl stop nginx 2>/dev/null || sudo nginx -s stop 2>/dev/null || true

echo "2. 安装必要依赖..."
# 安装Python和Nginx
if [ -f "/etc/redhat-release" ]; then
  # CentOS
  sudo yum update -y
  sudo yum install -y python3 python3-pip nginx git
else
  # Ubuntu/Debian
  sudo apt-get update
  sudo apt-get install -y python3 python3-pip nginx git
fi

echo "3. 配置后端环境..."
cd $WORK_DIR/backend
# 安装Python依赖
pip3 install -r requirements.txt

echo "4. 确保.env文件存在并配置正确..."
if [ ! -f "$WORK_DIR/.env" ]; then
  # 创建新.env文件
  echo "创建.env配置文件..."
  cat > "$WORK_DIR/.env" << EOL
# Flask配置
FLASK_ENV=production
FLASK_APP=app.py
FLASK_RUN_PORT=$PORT

# 数据库配置
DATABASE_URL=postgresql://postgres:123.123.MengLi@localhost:5432/softlink?client_encoding=utf8

# 安全配置
SECRET_KEY=ce8f52d1b3a24e6a9c83e6f7e3c9f2b5a7d0e1f3c9b8a6d4e2f0c8b6a4d2e0f1
JWT_SECRET_KEY=a4b8c6d2e0f5g7h3i9j1k5l7m9n2o4p6q8r0s3t6u8v0w2x4y6z8a1b3c5d7

# 其他配置
DEBUG=False
TESTING=False
EOL
else
  # 更新端口配置
  echo "更新.env中的端口配置为$PORT..."
  sed -i "s|FLASK_RUN_PORT=.*|FLASK_RUN_PORT=$PORT|g" "$WORK_DIR/.env" || true
fi

echo "5. 配置Nginx..."
# 检查前端目录
if [ ! -d "$WORK_DIR/frontend/softlin-f" ] && [ -d "$WORK_DIR/frontend/softlink-f" ]; then
  echo "重命名前端目录: softlink-f -> softlin-f..."
  mv "$WORK_DIR/frontend/softlink-f" "$WORK_DIR/frontend/softlin-f"
fi

# 创建Nginx配置
echo "创建Nginx配置文件..."
SERVER_IP=$(hostname -I | awk '{print $1}')
sudo bash -c "cat > /etc/nginx/conf.d/softlink.conf << EOL
server {
    listen 80;
    server_name $SERVER_IP;
    
    location /static/ {
        alias $WORK_DIR/frontend/softlin-f/static/;
        expires 30d;
    }
    
    location /api/ {
        proxy_pass http://localhost:$PORT/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \\\$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \\\$host;
        proxy_set_header X-Real-IP \\\$remote_addr;
        proxy_set_header X-Forwarded-For \\\$proxy_add_x_forwarded_for;
    }
    
    location / {
        root $WORK_DIR/frontend/softlin-f;
        try_files \\\$uri \\\$uri/ /index.html;
        index index.html;
    }
}
EOL"

# 测试并重启Nginx
echo "重启Nginx服务..."
sudo nginx -t && sudo systemctl restart nginx

echo "6. 启动后端服务..."
cd $WORK_DIR/backend
# 启动后端服务
nohup python3 startup.py --port $PORT > "$WORK_DIR/backend.log" 2>&1 &
# 保存PID
echo $! > "$WORK_DIR/backend.pid"
echo "后端服务已启动 (PID: $(cat $WORK_DIR/backend.pid))"

echo "7. 配置防火墙..."
# CentOS
if command -v firewall-cmd > /dev/null; then
  sudo firewall-cmd --permanent --add-port=80/tcp
  sudo firewall-cmd --permanent --add-port=$PORT/tcp
  sudo firewall-cmd --reload
# Ubuntu
elif command -v ufw > /dev/null; then
  sudo ufw allow 80/tcp
  sudo ufw allow $PORT/tcp
fi

echo "------------------------"
echo "SoftLink部署完成!"
echo "------------------------"
echo "前端访问: http://$SERVER_IP"
echo "后端API: http://$SERVER_IP:$PORT"
echo "注意: 请确保腾讯云安全组已开放80和$PORT端口"
echo "日志文件: $WORK_DIR/backend.log"
echo "------------------------"

# 成功退出
exit 0 