#!/bin/bash

echo "正在启动SoftLink前端服务..."

# 设置Nginx路径变量（需要修改为你的Nginx安装位置）
NGINX_PATH="/usr/local/nginx"
NGINX_BIN="$NGINX_PATH/sbin/nginx"

# 检查Nginx是否已安装
if [ ! -f "$NGINX_BIN" ]; then
  echo "错误: 在 $NGINX_PATH 未找到Nginx。请修改脚本中的NGINX_PATH变量为你的Nginx安装路径。"
  echo "如果使用系统包管理器安装的Nginx，可能位于 /usr/sbin/nginx"
  exit 1
fi

# 获取脚本所在目录的绝对路径
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

# 停止可能已经运行的Nginx进程
echo "停止现有Nginx进程..."
sudo killall nginx 2>/dev/null

# 复制配置文件到Nginx配置目录
echo "正在应用SoftLink配置..."
sudo cp -f "$SCRIPT_DIR/nginx.softlink.conf" "$NGINX_PATH/conf/nginx.conf"

# 启动Nginx
echo "启动Nginx..."
sudo $NGINX_BIN

echo ""
echo "SoftLink前端服务已启动成功！"
echo "请访问: http://localhost"
echo "" 