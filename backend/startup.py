#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SoftLink 后端服务启动脚本
- 检查环境配置
- 验证数据库连接和表结构
- 启动后端服务
"""

import os
import sys
import subprocess
import time
import socket
import importlib
from contextlib import contextmanager

# 定义颜色码，用于终端输出
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
END = '\033[0m'
BOLD = '\033[1m'

def print_status(message, status='info'):
    """打印带有颜色的状态信息"""
    prefix = {
        'success': f"{GREEN}[✓]{END} ",
        'warning': f"{YELLOW}[!]{END} ",
        'error': f"{RED}[✗]{END} ",
        'info': f"{BOLD}[*]{END} "
    }.get(status, f"{BOLD}[*]{END} ")
    
    print(f"{prefix}{message}")

def check_python_version():
    """检查Python版本"""
    print_status("检查Python版本...", 'info')
    major, minor = sys.version_info[:2]
    if major < 3 or (major == 3 and minor < 6):
        print_status(f"Python版本过低: {major}.{minor}，需要3.6或更高版本", 'error')
        return False
    
    print_status(f"Python版本 {major}.{minor} 符合要求", 'success')
    return True

def check_dependencies():
    """检查所需的Python依赖是否已安装"""
    print_status("检查必要的Python依赖...", 'info')
    required_packages = [
        'flask', 'sqlalchemy', 'marshmallow', 'flask_sqlalchemy', 
        'flask_jwt_extended', 'werkzeug', 'redis'
    ]
    
    all_installed = True
    for package in required_packages:
        try:
            importlib.import_module(package)
            print_status(f"依赖 {package} 已安装", 'success')
        except ImportError:
            print_status(f"缺少依赖: {package}", 'error')
            all_installed = False
    
    return all_installed

def check_config_files():
    """检查必要的配置文件是否存在"""
    print_status("检查配置文件...", 'info')
    # 检查项目结构中可能的配置文件位置
    possible_config_files = [
        os.path.join('app', 'config.py'),
        os.path.join('instance', 'config.py'),
        os.path.join('config.py')
    ]
    
    # 至少有一个配置文件存在即可
    any_exists = False
    for config_file in possible_config_files:
        if os.path.exists(config_file):
            print_status(f"配置文件 {config_file} 存在", 'success')
            any_exists = True
        else:
            print_status(f"配置文件 {config_file} 不存在，将尝试其他位置", 'info')
    
    if not any_exists:
        print_status("未找到任何配置文件，可能使用了环境变量或默认配置", 'warning')
    
    # 对于Flask应用，配置可能在环境变量中或使用默认值，因此不一定要求配置文件存在
    return True

@contextmanager
def database_context():
    """创建一个临时的应用上下文来检查数据库连接"""
    try:
        # 动态导入，避免全局导入可能的问题
        from app import create_app, db
        app = create_app()
        with app.app_context():
            yield db
    except Exception as e:
        print_status(f"创建应用上下文时出错: {str(e)}", 'error')
        yield None

def check_database_connection():
    """检查数据库连接"""
    print_status("检查数据库连接...", 'info')
    with database_context() as db:
        if db is None:
            return False
        
        try:
            # 使用合适的查询方法验证连接
            from sqlalchemy import text
            db.session.execute(text("SELECT 1"))
            print_status("数据库连接成功", 'success')
            return True
        except Exception as e:
            print_status(f"数据库连接失败: {str(e)}", 'error')
            # 数据库问题通常不会阻止应用启动，SQLite会在需要时创建数据库
            print_status("数据库可能不存在，但服务可以启动并创建它", 'warning')
            return True

def check_database_tables():
    """检查数据库表是否已创建"""
    print_status("检查数据库表结构...", 'info')
    with database_context() as db:
        if db is None:
            return False
        
        try:
            # 获取所有表格名称
            from app.models import User, VIPLevel, Feedback, Feature
            required_tables = [
                User.__tablename__, 
                VIPLevel.__tablename__, 
                Feedback.__tablename__, 
                Feature.__tablename__
            ]
            
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            all_exist = True
            for table in required_tables:
                if table in existing_tables:
                    print_status(f"表 {table} 已存在", 'success')
                else:
                    print_status(f"表 {table} 不存在", 'error')
                    all_exist = False
            
            return all_exist
        except Exception as e:
            print_status(f"检查数据库表时出错: {str(e)}", 'error')
            return False

def check_port_available(port=5000):
    """检查端口是否可用"""
    print_status(f"检查端口 {port} 是否可用...", 'info')
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('127.0.0.1', port))
        s.close()
        print_status(f"端口 {port} 可用", 'success')
        return True
    except socket.error:
        print_status(f"端口 {port} 已被占用", 'error')
        return False

def create_tables_if_needed():
    """如果表不存在，则创建数据库表"""
    print_status("尝试创建数据库表...", 'info')
    try:
        from app import create_app, db
        app = create_app()
        with app.app_context():
            db.create_all()
            print_status("数据库表创建或验证成功", 'success')
            return True
    except Exception as e:
        print_status(f"创建数据库表时出错: {str(e)}", 'error')
        return False

def create_initial_user():
    """创建初始超级管理员用户（如果不存在）"""
    print_status("检查是否需要创建初始用户...", 'info')
    try:
        from app import create_app, db
        from app.models import User
        
        app = create_app()
        with app.app_context():
            # 检查是否有超级管理员用户
            super_admin = User.query.filter_by(role='super_admin').first()
            if super_admin:
                print_status("已存在超级管理员用户，无需创建初始用户", 'success')
                return True
            
            # 尝试运行创建初始用户的脚本
            if os.path.exists('create_initial_users.py'):
                print_status("运行初始用户创建脚本...", 'info')
                subprocess.run([sys.executable, 'create_initial_users.py'], check=True)
                print_status("初始用户创建成功", 'success')
                return True
            else:
                print_status("找不到初始用户创建脚本，请手动创建超级管理员用户", 'warning')
                return True
    except Exception as e:
        print_status(f"检查/创建初始用户时出错: {str(e)}", 'error')
        return False

def start_backend_service():
    """启动后端服务"""
    print_status("准备启动后端服务...", 'info')
    
    if os.path.exists('run.py'):
        print_status("正在启动后端服务...", 'info')
        try:
            subprocess.run([sys.executable, 'run.py'], check=True)
            return True
        except subprocess.CalledProcessError as e:
            print_status(f"启动后端服务时出错: {str(e)}", 'error')
            return False
    else:
        print_status("找不到运行脚本 run.py", 'error')
        return False

def main():
    """主函数：按顺序执行所有检查，然后启动服务"""
    print_status(f"{BOLD}开始 SoftLink 后端服务启动流程{END}", 'info')
    
    # 更改工作目录到脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # 执行检查
    checks = [
        ("Python版本检查", check_python_version),
        ("依赖检查", check_dependencies),
        ("配置文件检查", check_config_files),
        ("数据库连接检查", check_database_connection),
        ("端口可用性检查", check_port_available),
        ("数据库表检查", check_database_tables)
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        print_status(f"执行{check_name}...", 'info')
        passed = check_func()
        if not passed:
            all_passed = False
            print_status(f"{check_name}失败", 'error')
            
            # 对某些检查失败提供修复选项
            if check_name == "数据库表检查":
                fix = input("是否尝试创建数据库表? (y/n): ")
                if fix.lower() == 'y':
                    if create_tables_if_needed():
                        all_passed = True  # 继续启动
                    else:
                        continue  # 保持失败状态
            # 即使数据库表检查失败，也询问是否继续
            if check_name == "数据库表检查":
                continue_anyway = input("是否仍然启动服务? (y/n): ")
                if continue_anyway.lower() == 'y':
                    all_passed = True  # 强制继续
    
    # 如果所有检查都通过，检查是否需要创建初始用户
    if all_passed:
        create_initial_user()
        
        # 启动服务
        print_status(f"{BOLD}所有检查通过或被忽略，正在启动后端服务...{END}", 'success')
        start_backend_service()
    else:
        print_status(f"{BOLD}某些检查未通过，请解决问题后再尝试启动服务{END}", 'error')

if __name__ == "__main__":
    main() 