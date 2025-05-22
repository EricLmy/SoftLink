#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SoftLink依赖检查和安装工具
- 检查Python环境
- 检查并安装必要的依赖项
"""

import os
import sys
import subprocess
import platform
import importlib
import time

# 颜色定义
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

def check_python_version():
    """检查Python版本是否满足要求"""
    major, minor = sys.version_info.major, sys.version_info.minor
    print_status("当前Python版本: {}.{}".format(major, minor), 'info')
    if major < 3 or (major == 3 and minor < 6):
        print_status("Python版本过低: {}.{}，需要3.6或更高版本".format(major, minor), 'error')
        return False
    else:
        print_status("Python版本 {}.{} 符合要求".format(major, minor), 'success')
        return True

def check_pip():
    """检查pip是否可用"""
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print_status("pip 可用", 'success')
        return True
    except subprocess.CalledProcessError:
        print_status("pip 不可用", 'error')
        return False

def check_dependencies():
    """检查依赖是否已安装"""
    required_packages = [
        'flask',
        'sqlalchemy',
        'psycopg2-binary',  # 使用binary版本避免编译问题
        'python-dotenv',
        'flask-sqlalchemy',
        'flask-migrate',
        'werkzeug',
        'marshmallow',
        'flask-jwt-extended',
        'redis'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            # 处理包名与导入名称不同的情况
            import_name = package.split("-")[0]  # 例如python-dotenv变为dotenv
            if import_name == 'psycopg2':
                import_name = 'psycopg2'
            elif import_name == 'python':
                import_name = 'dotenv'  # 处理python-dotenv的特殊情况
                
            importlib.import_module(import_name)
            print_status("依赖 {} 已安装".format(package), 'success')
        except ImportError:
            print_status("缺少依赖: {}".format(package), 'warning')
            missing_packages.append(package)
    
    return missing_packages

def install_dependencies(packages):
    """安装缺失的依赖"""
    if not packages:
        print_status("所有依赖已安装", 'success')
        return True
        
    print_status("准备安装缺失的依赖...", 'info')
    
    for package in packages:
        print_status("正在安装 {}...".format(package), 'info')
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print_status("{} 安装成功".format(package), 'success')
        except subprocess.CalledProcessError as e:
            print_status("{} 安装失败: {}".format(package, str(e)), 'error')
            return False
    
    return True

def setup_environment():
    """设置环境变量和配置文件"""
    print_status("检查项目配置...", 'info')
    
    # 检查是否在项目根目录
    if os.path.exists("backend") and os.path.isdir("backend"):
        os.chdir("backend")
        print_status("进入后端目录", 'info')
    
    # 检查.env文件
    if not os.path.exists(".env"):
        print_status("创建.env配置文件...", 'info')
        
        with open(".env", "w") as f:
            f.write("""# SoftLink环境配置
FLASK_APP=run.py
FLASK_ENV=development
DATABASE_URL=sqlite:///./softlink.db
SECRET_KEY=dev-secret-key-change-in-production
""")
        print_status(".env文件已创建", 'success')
    else:
        print_status(".env文件已存在", 'success')
    
    return True

def check_database():
    """检查数据库连接"""
    print_status("检查数据库连接...", 'info')
    
    # 首先检查是否在backend目录中
    if not os.path.exists("app") or not os.path.isdir("app"):
        if os.path.exists("backend/app") and os.path.isdir("backend/app"):
            os.chdir("backend")
    
    try:
        # 尝试运行数据库检查脚本
        if os.path.exists("test_db_connection.py"):
            subprocess.run(
                [sys.executable, "test_db_connection.py"],
                check=True
            )
            print_status("数据库连接检查完成", 'success')
            return True
        else:
            print_status("找不到数据库连接检查脚本", 'warning')
            # 可能需要创建数据库连接检查
            return True
    except subprocess.CalledProcessError:
        print_status("数据库连接检查失败", 'error')
        return False

def main():
    """主函数"""
    print_status("{}SoftLink依赖检查与安装工具{}".format(BOLD, END), 'info')
    
    # 检查Python版本
    if not check_python_version():
        print_status("请使用Python 3.6或更高版本", 'error')
        sys.exit(1)
    
    # 检查pip
    if not check_pip():
        print_status("请先安装pip", 'error')
        sys.exit(1)
    
    # 检查依赖
    missing_packages = check_dependencies()
    
    # 安装缺失的依赖
    if missing_packages:
        print_status("发现缺失的依赖，准备安装...", 'info')
        if not install_dependencies(missing_packages):
            print_status("依赖安装失败，请手动安装", 'error')
            sys.exit(1)
    
    # 设置环境
    setup_environment()
    
    # 检查数据库
    check_database()
    
    print_status("{}所有依赖检查完成，环境已准备就绪{}".format(BOLD, END), 'success')
    print_status("现在可以通过以下命令启动SoftLink后端服务:", 'info')
    print_status("python choose_env.py", 'info')

if __name__ == "__main__":
    main() 