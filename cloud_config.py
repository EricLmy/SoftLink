#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
腾讯云服务器配置
"""

# 腾讯云服务器公网IP
PUBLIC_IP = "腾讯云服务器IP"  # 请替换为您的实际IP地址

# SSH连接信息
SSH_USER = "root"  # SSH用户名
SSH_PORT = 22      # SSH端口
SSH_KEY_PATH = ""  # SSH密钥路径，如果使用密钥认证

# 应用配置
BACKEND_PORT = 5000  # 后端服务端口
NGINX_PORT = 80      # 前端服务端口(Nginx)

# 项目目录配置
PROJECT_PATH = "/root/softlink"        # 项目在服务器上的路径
FRONTEND_PATH = "/root/softlink/frontend/softlink-f"   # 前端构建目录（注意拼写：softlin-f而非softlink-f）

# 数据库配置
DB_HOST = "localhost"
DB_PORT = 5432
DB_USER = "postgres"
DB_PASS = "123.123.MengLi"
DB_NAME = "softlink" 