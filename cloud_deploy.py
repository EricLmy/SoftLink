#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SoftLink 腾讯云部署脚本
自动连接腾讯云服务器并部署/启动SoftLink应用
"""

import os
import sys
import subprocess
import time
import platform
from cloud_config import *

# 设置颜色输出
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

# 打印带颜色的消息
def print_colored(message, color):
    print(f"{color}{message}{Colors.END}")

# 检查配置
def check_config():
    print_colored("检查配置...", Colors.HEADER)
    if PUBLIC_IP == "腾讯云服务器IP":
        print_colored("错误: 请在cloud_config.py中设置您的腾讯云服务器公网IP", Colors.RED)
        return False
    return True

# 获取当前项目根目录
def get_project_root():
    return os.path.dirname(os.path.abspath(__file__))

# 检查SSH连接
def check_ssh_connection():
    print_colored("检查SSH连接...", Colors.BLUE)
    
    # 构建SSH命令
    ssh_cmd = f"ssh -o ConnectTimeout=5"
    if SSH_KEY_PATH:
        ssh_cmd += f" -i {SSH_KEY_PATH}"
    ssh_cmd += f" -p {SSH_PORT} {SSH_USER}@{PUBLIC_IP} 'echo 连接成功'"
    
    try:
        result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print_colored("SSH连接正常", Colors.GREEN)
            return True
        else:
            print_colored(f"SSH连接失败: {result.stderr}", Colors.RED)
            return False
    except Exception as e:
        print_colored(f"SSH连接异常: {str(e)}", Colors.RED)
        return False

# 打开浏览器访问应用
def open_browser():
    print_colored("打开浏览器访问应用...", Colors.BLUE)
    url = f"http://{PUBLIC_IP}"
    
    # 根据不同操作系统打开浏览器
    if platform.system() == "Windows":
        os.system(f"start {url}")
    elif platform.system() == "Darwin":  # macOS
        os.system(f"open {url}")
    else:  # Linux
        os.system(f"xdg-open {url} 2>/dev/null || sensible-browser {url} 2>/dev/null || x-www-browser {url} 2>/dev/null || gnome-open {url}")
    
    print_colored(f"应用已在浏览器中打开: {url}", Colors.GREEN)

# 停止腾讯云服务器上的所有SoftLink服务
def stop_cloud_service():
    print_colored("停止腾讯云服务器上的所有SoftLink服务...", Colors.YELLOW)
    
    # 构建SSH命令
    ssh_cmd = f"ssh"
    if SSH_KEY_PATH:
        ssh_cmd += f" -i {SSH_KEY_PATH}"
    ssh_cmd += f" -p {SSH_PORT} {SSH_USER}@{PUBLIC_IP}"
    
    # 使用stop_softlink.sh停止服务
    print_colored("执行stop_softlink.sh脚本...", Colors.YELLOW)
    stop_cmd = f"{ssh_cmd} 'cd /root/SoftLink && chmod +x stop_softlink.sh && ./stop_softlink.sh'"
    subprocess.run(stop_cmd, shell=True)
    
    # 确保所有服务都已停止（双重检查）
    print_colored("确保所有服务都已停止...", Colors.YELLOW)
    double_check_cmd = f"{ssh_cmd} '"
    double_check_cmd += "pkill -f \"python.*startup.py\" 2>/dev/null || true; "
    double_check_cmd += "sudo systemctl stop nginx 2>/dev/null || sudo nginx -s stop 2>/dev/null || true; "
    double_check_cmd += "kill $(lsof -t -i:{BACKEND_PORT}) 2>/dev/null || true"
    double_check_cmd += "'"
    subprocess.run(double_check_cmd, shell=True)
    
    print_colored("所有服务已停止", Colors.GREEN)
    return True

# 启动腾讯云服务器上的SoftLink服务
def start_cloud_service():
    print_colored("启动腾讯云服务器上的SoftLink服务...", Colors.BLUE)
    
    # 构建SSH命令
    ssh_cmd = f"ssh"
    if SSH_KEY_PATH:
        ssh_cmd += f" -i {SSH_KEY_PATH}"
    ssh_cmd += f" -p {SSH_PORT} {SSH_USER}@{PUBLIC_IP}"
    
    # 使用deploy_softlink.sh启动服务
    print_colored("执行deploy_softlink.sh脚本...", Colors.BLUE)
    start_cmd = f"{ssh_cmd} 'cd /root/SoftLink && chmod +x deploy_softlink.sh && ./deploy_softlink.sh'"
    result = subprocess.run(start_cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print_colored("服务启动成功", Colors.GREEN)
        return True
    else:
        print_colored(f"服务启动失败: {result.stderr}", Colors.RED)
        
        # 尝试查看日志
        print_colored("尝试获取部署日志...", Colors.YELLOW)
        log_cmd = f"{ssh_cmd} 'cat /root/SoftLink/deploy_log.txt | tail -n 30'"
        subprocess.run(log_cmd, shell=True)
        
        return False

# 配置Nginx目录
def configure_nginx():
    print_colored("配置Nginx以使用frontend/softlin-f目录...", Colors.BLUE)
    
    # 构建SSH命令
    ssh_cmd = f"ssh"
    if SSH_KEY_PATH:
        ssh_cmd += f" -i {SSH_KEY_PATH}"
    ssh_cmd += f" -p {SSH_PORT} {SSH_USER}@{PUBLIC_IP}"
    
    # 检查并修正Nginx配置，确保使用正确的前端目录
    update_cmd = (
        f"{ssh_cmd} '"
        f"cd /root/SoftLink && "
        f"sed -i \"s|frontend/softlink-f|frontend/softlin-f|g\" frontend/nginx.softlink.conf && "
        f"echo \"Nginx配置已更新\""
        f"'"
    )
    subprocess.run(update_cmd, shell=True)
    
    print_colored("Nginx配置更新完成", Colors.GREEN)
    return True

# 主函数
def main():
    print_colored("===== SoftLink 腾讯云部署工具 =====", Colors.HEADER)
    
    # 检查配置
    if not check_config():
        return
    
    # 检查SSH连接
    if not check_ssh_connection():
        print_colored("无法连接到腾讯云服务器，请检查网络和SSH配置", Colors.RED)
        return
    
    # 停止现有服务
    stop_cloud_service()
    
    # 配置Nginx
    configure_nginx()
    
    # 启动服务
    if start_cloud_service():
        # 等待服务启动
        print_colored("等待服务启动...", Colors.YELLOW)
        time.sleep(10)
        
        # 打开浏览器
        open_browser()
        
        print_colored("===== 部署完成 =====", Colors.GREEN)
        print_colored(f"前端访问地址: http://{PUBLIC_IP}", Colors.GREEN)
        print_colored(f"后端API地址: http://{PUBLIC_IP}:{BACKEND_PORT}", Colors.GREEN)
    else:
        print_colored("部署失败，请检查云服务器日志", Colors.RED)

if __name__ == "__main__":
    main() 