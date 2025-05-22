#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SoftLink项目部署修复脚本
用于解决Windows测试环境和CentOS部署环境之间的兼容性问题
"""

import os
import sys
import shutil
import re
import platform
import argparse
import subprocess

# 定义颜色码
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
END = '\033[0m'
BOLD = '\033[1m'

def print_status(message, status='info'):
    """打印带有颜色的状态信息"""
    prefix = {
        'success': GREEN + "[✓]" + END + " ",
        'warning': YELLOW + "[!]" + END + " ",
        'error': RED + "[✗]" + END + " ",
        'info': BOLD + "[*]" + END + " "
    }.get(status, BOLD + "[*]" + END + " ")
    
    print("{}{}".format(prefix, message))

def get_project_root():
    """获取项目根目录"""
    return os.path.dirname(os.path.abspath(__file__))

def check_system():
    """检查当前系统环境"""
    system = platform.system()
    print_status(f"当前系统: {system}", 'info')
    
    if system == "Windows":
        print_status("检测到Windows测试环境", 'info')
        return "windows"
    elif system == "Linux":
        distro = ""
        try:
            # 尝试读取/etc/os-release文件获取发行版信息
            with open("/etc/os-release", "r") as f:
                for line in f:
                    if line.startswith("ID="):
                        distro = line.strip().split("=")[1].strip('"')
                        break
        except:
            pass
        
        if distro.lower() == "centos":
            print_status("检测到CentOS部署环境", 'info')
            return "centos"
        else:
            print_status(f"检测到Linux环境（发行版: {distro}）", 'info')
            return "linux"
    else:
        print_status(f"未知系统类型: {system}", 'warning')
        return "unknown"

def fix_directory_names():
    """修复目录名称问题"""
    project_root = get_project_root()
    frontend_dir = os.path.join(project_root, "frontend")
    
    # 检查前端构建目录
    softlin_f_dir = os.path.join(frontend_dir, "softlin-f")
    softlink_f_dir = os.path.join(frontend_dir, "softlink-f")
    
    if os.path.exists(softlin_f_dir) and not os.path.exists(softlink_f_dir):
        print_status(f"发现目录名称问题: softlin-f应为softlink-f", 'warning')
        try:
            # 重命名目录
            os.rename(softlin_f_dir, softlink_f_dir)
            print_status("已将softlin-f重命名为softlink-f", 'success')
        except Exception as e:
            print_status(f"重命名目录失败: {str(e)}", 'error')
    elif os.path.exists(softlink_f_dir):
        print_status("前端构建目录名称正确: softlink-f", 'success')
    else:
        print_status("未找到前端构建目录", 'warning')

def fix_nginx_config():
    """修复Nginx配置文件中的路径问题"""
    project_root = get_project_root()
    frontend_dir = os.path.join(project_root, "frontend")
    nginx_conf_path = os.path.join(frontend_dir, "nginx.softlink.conf")
    
    if not os.path.exists(nginx_conf_path):
        print_status(f"Nginx配置文件不存在: {nginx_conf_path}", 'error')
        return
    
    # 读取配置文件
    with open(nginx_conf_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 备份配置文件
    backup_path = f"{nginx_conf_path}.backup"
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(content)
    print_status(f"已备份Nginx配置文件到: {backup_path}", 'info')
    
    # 替换硬编码路径
    system = check_system()
    project_root_path = project_root.replace("\\", "/")  # 统一使用正斜杠
    
    if system == "windows":
        # 将/root/softlink/替换为项目根目录的路径
        content = re.sub(r'/root/softlink/frontend/softlink-f', 
                         fr'{project_root_path}/frontend/softlink-f', 
                         content)
    elif system in ["centos", "linux"]:
        # 确保使用当前目录路径
        content = re.sub(r'/root/softlink/frontend/softlink-f', 
                         fr'{project_root_path}/frontend/softlink-f', 
                         content)
    
    # 写入修改后的配置
    with open(nginx_conf_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print_status("已修复Nginx配置文件中的路径问题", 'success')

def fix_deploy_scripts():
    """修复部署脚本中的问题"""
    project_root = get_project_root()
    system = check_system()
    
    if system == "windows":
        # 修复Windows部署脚本
        bat_script_path = os.path.join(project_root, "deploy_softlink.bat")
        if os.path.exists(bat_script_path):
            with open(bat_script_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 备份脚本
            with open(f"{bat_script_path}.backup", "w", encoding="utf-8") as f:
                f.write(content)
            
            # 修复前端构建目录名称
            content = content.replace("softlin-f", "softlink-f")
            
            # 写入修改后的脚本
            with open(bat_script_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            print_status("已修复Windows部署脚本", 'success')
    elif system in ["centos", "linux"]:
        # 修复Linux部署脚本
        sh_script_path = os.path.join(project_root, "deploy_softlink.sh")
        if os.path.exists(sh_script_path):
            with open(sh_script_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 备份脚本
            with open(f"{sh_script_path}.backup", "w", encoding="utf-8") as f:
                f.write(content)
            
            # 修复前端构建目录名称
            content = content.replace("softlin-f", "softlink-f")
            
            # 写入修改后的脚本
            with open(sh_script_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            # 确保脚本有执行权限
            try:
                os.chmod(sh_script_path, 0o755)
                print_status("已为部署脚本添加执行权限", 'success')
            except Exception as e:
                print_status(f"无法为脚本添加执行权限: {str(e)}", 'error')
            
            print_status("已修复Linux部署脚本", 'success')

def fix_env_file():
    """确保.env文件存在并配置正确"""
    project_root = get_project_root()
    env_file = os.path.join(project_root, ".env")
    env_example = os.path.join(project_root, ".env.example")
    
    if not os.path.exists(env_file):
        if os.path.exists(env_example):
            print_status(".env文件不存在，将从.env.example创建", 'info')
            shutil.copy(env_example, env_file)
            print_status("已从.env.example创建.env文件", 'success')
        else:
            print_status("无法找到.env或.env.example文件，将创建新的.env文件", 'warning')
            
            # 创建新的.env文件
            system = check_system()
            with open(env_file, "w", encoding="utf-8") as f:
                f.write("""# Flask配置
FLASK_ENV=production
FLASK_APP=app.py
FLASK_RUN_PORT=5000

# 数据库配置
DATABASE_URL=postgresql://postgres:123.123.MengLi@localhost:5432/softlink?client_encoding=utf8

# Redis配置
REDIS_URL=redis://localhost:6379/0

# 安全配置
SECRET_KEY=ce8f52d1b3a24e6a9c83e6f7e3c9f2b5a7d0e1f3c9b8a6d4e2f0c8b6a4d2e0f1
JWT_SECRET_KEY=a4b8c6d2e0f5g7h3i9j1k5l7m9n2o4p6q8r0s3t6u8v0w2x4y6z8a1b3c5d7

# 其他配置
DEBUG=False
TESTING=False
""")
            print_status("已创建新的.env文件", 'success')
    else:
        print_status(".env文件已存在", 'success')
        
        # 检查.env文件内容
        with open(env_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 确保数据库连接配置正确
        system = check_system()
        if system == "windows":
            # Windows环境通常使用localhost连接
            if "DATABASE_URL=" in content and "@localhost:" not in content:
                print_status(".env文件中的数据库连接配置可能需要调整", 'warning')
                response = input("是否将数据库连接调整为localhost连接? (y/n): ")
                if response.lower() == 'y':
                    content = re.sub(r'DATABASE_URL=.*', 
                             r'DATABASE_URL=postgresql://postgres:123.123.MengLi@localhost:5432/softlink?client_encoding=utf8', 
                             content)
                    with open(env_file, "w", encoding="utf-8") as f:
                        f.write(content)
                    print_status("已更新数据库连接配置", 'success')
        elif system in ["centos", "linux"]:
            # CentOS环境检查，可能需要调整
            pass

def test_db_connection():
    """测试数据库连接"""
    print_status("测试数据库连接...", 'info')
    
    # 尝试导入psycopg2库
    try:
        import psycopg2
    except ImportError:
        print_status("未安装psycopg2库，无法测试数据库连接", 'error')
        print_status("请安装psycopg2: pip install psycopg2-binary", 'info')
        return False
    
    # 从.env文件读取数据库配置
    project_root = get_project_root()
    env_file = os.path.join(project_root, ".env")
    
    if not os.path.exists(env_file):
        print_status(".env文件不存在，无法获取数据库配置", 'error')
        return False
    
    # 读取数据库配置
    db_host = "localhost"
    db_port = "5432"
    db_name = "softlink"
    db_user = "postgres"
    db_pass = "123.123.MengLi"
    
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("DATABASE_URL="):
                # 解析数据库连接URL
                url = line.strip().split("=", 1)[1]
                try:
                    # 尝试从URL提取配置
                    match = re.search(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/([^?]+)', url)
                    if match:
                        db_user = match.group(1)
                        db_pass = match.group(2)
                        db_host = match.group(3)
                        db_port = match.group(4)
                        db_name = match.group(5)
                except:
                    pass
    
    # 尝试连接数据库
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_pass
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        print_status("数据库连接成功", 'success')
        return True
    except Exception as e:
        print_status(f"数据库连接失败: {str(e)}", 'error')
        
        # 提供解决方案
        print_status("请确保PostgreSQL服务已启动，并检查连接配置:", 'info')
        print(f"  主机: {db_host}")
        print(f"  端口: {db_port}")
        print(f"  数据库: {db_name}")
        print(f"  用户: {db_user}")
        print(f"  密码: {'*' * len(db_pass)}")
        
        system = check_system()
        if system == "windows":
            print_status("Windows环境安装PostgreSQL指南:", 'info')
            print("1. 从https://www.postgresql.org/download/windows/下载并安装PostgreSQL")
            print("2. 安装过程中设置用户名和密码")
            print("3. 安装完成后，使用pgAdmin创建名为'softlink'的数据库")
        elif system in ["centos", "linux"]:
            print_status("CentOS环境安装PostgreSQL指南:", 'info')
            print("1. 安装PostgreSQL: sudo yum install -y postgresql-server postgresql-contrib")
            print("2. 初始化数据库: sudo postgresql-setup initdb")
            print("3. 启动服务: sudo systemctl start postgresql")
            print("4. 创建数据库: sudo -u postgres createdb softlink")
        
        return False

def create_deploy_script():
    """创建适合当前环境的部署脚本"""
    system = check_system()
    project_root = get_project_root()
    
    if system == "windows":
        script_path = os.path.join(project_root, "deploy_softlink_fixed.bat")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write("""@echo off
setlocal enabledelayedexpansion

:: SoftLink项目一键部署脚本 (Windows版本 - 修复版)
:: 用于在Windows环境上部署测试环境

echo [*] 开始部署SoftLink项目...

:: 项目根目录
set PROJECT_ROOT=%~dp0
set BACKEND_DIR=%PROJECT_ROOT%backend
set FRONTEND_DIR=%PROJECT_ROOT%frontend
set FRONTEND_BUILD_DIR=%FRONTEND_DIR%\\softlink-f

:: 设置后端环境
echo [*] 设置后端环境...
cd /d %BACKEND_DIR%

:: 检查虚拟环境
if not exist "venv" (
    echo [*] 创建Python虚拟环境...
    python -m venv venv
) else (
    echo [*] 已存在虚拟环境
)

:: 激活虚拟环境
call venv\\Scripts\\activate.bat

:: 安装依赖
echo [*] 安装Python依赖...
pip install -r requirements.txt

:: 启动后端服务
echo [*] 启动后端服务...
start /B python startup.py

:: 启动前端服务
echo [*] 启动前端服务...
cd /d %PROJECT_ROOT%
start http://localhost

echo [*] SoftLink项目部署完成
echo [*] 前端访问地址: http://localhost
echo [*] 后端API地址: http://localhost:5000

pause
""")
        print_status(f"已创建Windows部署脚本: {script_path}", 'success')
    
    elif system in ["centos", "linux"]:
        script_path = os.path.join(project_root, "deploy_softlink_fixed.sh")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write("""#!/bin/bash

# SoftLink项目一键部署脚本 (Linux版本 - 修复版)
# 用于在CentOS腾讯云服务器上部署

# 设置颜色
GREEN='\\033[0;32m'
NC='\\033[0m'

echo -e "${GREEN}[*] 开始部署SoftLink项目...${NC}"

# 项目根目录
PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
FRONTEND_BUILD_DIR="$FRONTEND_DIR/softlink-f"

# 确保数据库服务启动
echo -e "${GREEN}[*] 确保PostgreSQL服务启动...${NC}"
sudo systemctl start postgresql || true

# 设置后端环境
echo -e "${GREEN}[*] 设置后端环境...${NC}"
cd $BACKEND_DIR

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo -e "${GREEN}[*] 创建Python虚拟环境...${NC}"
    python3 -m venv venv || python -m venv venv
else
    echo -e "${GREEN}[*] 已存在虚拟环境${NC}"
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo -e "${GREEN}[*] 安装Python依赖...${NC}"
pip install -r requirements.txt

# 配置Nginx
echo -e "${GREEN}[*] 配置Nginx...${NC}"
sudo cp $FRONTEND_DIR/nginx.softlink.conf /etc/nginx/conf.d/softlink.conf
sudo systemctl restart nginx

# 启动后端服务
echo -e "${GREEN}[*] 启动后端服务...${NC}"
cd $BACKEND_DIR
nohup python startup.py > backend.log 2>&1 &
echo $! > "$PROJECT_ROOT/backend.pid"

echo -e "${GREEN}===== SoftLink项目部署完成 =====${NC}"
echo -e "前端访问地址: ${GREEN}http://$(hostname -I | awk '{print $1}')${NC}"
echo -e "后端API地址: ${GREEN}http://$(hostname -I | awk '{print $1}'):5000${NC}"
""")
        
        # 添加执行权限
        try:
            os.chmod(script_path, 0o755)
        except:
            pass
        
        print_status(f"已创建Linux部署脚本: {script_path}", 'success')

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='SoftLink项目部署修复脚本')
    parser.add_argument('--test-db', action='store_true', help='测试数据库连接')
    args = parser.parse_args()
    
    print_status("SoftLink项目部署修复脚本", 'info')
    print_status("该脚本用于解决Windows测试环境和CentOS部署环境之间的兼容性问题", 'info')
    
    # 检查系统环境
    system = check_system()
    
    # 修复目录名称问题
    fix_directory_names()
    
    # 修复Nginx配置
    fix_nginx_config()
    
    # 修复部署脚本
    fix_deploy_scripts()
    
    # 确保.env文件配置正确
    fix_env_file()
    
    # 测试数据库连接
    if args.test_db:
        test_db_connection()
    
    # 创建适合当前环境的部署脚本
    create_deploy_script()
    
    print_status("修复完成", 'success')
    print_status("请使用新生成的部署脚本进行部署", 'info')

if __name__ == "__main__":
    main() 