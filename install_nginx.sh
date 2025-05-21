#!/bin/bash

# 设置错误时退出
set -e

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}开始安装和配置Nginx前端服务...${NC}"

# 1. 安装Nginx
echo -e "${YELLOW}[1/5]${NC} 检查并安装Nginx..."

# 检查操作系统类型
if [ -f /etc/debian_version ]; then
    # Debian/Ubuntu系统
    echo "检测到Debian/Ubuntu系统"
    sudo apt update
    sudo apt install -y nginx
elif [ -f /etc/redhat-release ]; then
    # CentOS/RHEL系统
    echo "检测到CentOS/RHEL系统"
    sudo yum install -y epel-release
    sudo yum install -y nginx
else
    echo -e "${RED}不支持的操作系统，请手动安装Nginx${NC}"
    exit 1
fi

# 启动Nginx并设置开机自启
sudo systemctl start nginx
sudo systemctl enable nginx

echo -e "${GREEN}Nginx已安装并启动${NC}"

# 2. 获取当前工作目录和服务器IP
WORK_DIR=$(pwd)
SERVER_IP=$(hostname -I | awk '{print $1}')

# 3. 创建前端目录
echo -e "${YELLOW}[2/5]${NC} 创建前端目录..."
sudo mkdir -p /var/www/softlink
sudo chown -R $USER:$USER /var/www/softlink

echo -e "${GREEN}前端目录已创建: /var/www/softlink${NC}"

# 4. 提示用户上传前端文件
echo -e "${YELLOW}[3/5]${NC} 前端文件部署..."
echo -e "${YELLOW}请确保前端文件已上传到/var/www/softlink目录${NC}"
echo "如果您还没有上传前端文件，请按照以下步骤操作:"
echo "1. 在开发机器上构建前端: cd frontend && npm install && npm run build"
echo "2. 将build/dist目录下的文件上传到服务器的/var/www/softlink目录"
echo -e "   可以使用命令: ${GREEN}scp -r build/* user@${SERVER_IP}:/var/www/softlink/${NC}"

read -p "前端文件是否已准备好? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}请准备好前端文件后再继续${NC}"
    echo -e "脚本将继续创建Nginx配置，但前端可能无法正常访问，直到文件上传完成"
fi

# 5. 配置Nginx
echo -e "${YELLOW}[4/5]${NC} 配置Nginx..."

# 创建Nginx配置文件
sudo cat > /etc/nginx/conf.d/softlink.conf << EOL
server {
    listen 80;
    server_name ${SERVER_IP};
    
    root /var/www/softlink;
    index index.html;
    
    # 处理前端路由
    location / {
        try_files \$uri \$uri/ /index.html;
    }
    
    # API代理
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
    }
    
    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico)$ {
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
}
EOL

# 检查Nginx配置语法
sudo nginx -t

# 如果配置有误，则退出
if [ $? -ne 0 ]; then
    echo -e "${RED}Nginx配置有误，请检查配置文件${NC}"
    exit 1
fi

# 重启Nginx
sudo systemctl reload nginx

echo -e "${GREEN}Nginx已配置完成${NC}"

# 6. 防火墙配置
echo -e "${YELLOW}[5/5]${NC} 配置防火墙..."

# 检查系统使用的防火墙
if command -v ufw &> /dev/null; then
    # Ubuntu等使用ufw
    sudo ufw allow 80/tcp
    sudo ufw allow 8000/tcp
elif command -v firewall-cmd &> /dev/null; then
    # CentOS等使用firewalld
    sudo firewall-cmd --permanent --add-service=http
    sudo firewall-cmd --permanent --add-port=8000/tcp
    sudo firewall-cmd --reload
else
    echo -e "${YELLOW}未检测到防火墙或不支持自动配置，请手动确保端口80和8000开放${NC}"
fi

echo -e "${GREEN}防火墙已配置${NC}"

# 7. 完成
echo -e "${GREEN}=======================================${NC}"
echo -e "${GREEN}Nginx安装和配置完成!${NC}"
echo -e "${GREEN}=======================================${NC}"
echo -e "前端访问地址: ${GREEN}http://${SERVER_IP}${NC}"
echo -e "后端API地址: ${GREEN}http://${SERVER_IP}:8000${NC}"
echo -e "前端文件目录: ${GREEN}/var/www/softlink${NC}"
echo
echo -e "${YELLOW}如需更新前端文件，请上传到/var/www/softlink目录${NC}"

exit 0 