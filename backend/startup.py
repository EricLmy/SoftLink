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
import argparse
from contextlib import contextmanager

# 定义颜色码，用于终端输出
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
END = '\033[0m'
BOLD = '\033[1m'

# 解析命令行参数
def parse_args():
    parser = argparse.ArgumentParser(description='SoftLink后端服务启动脚本')
    parser.add_argument('--port', type=int, default=int(os.environ.get('FLASK_RUN_PORT', 5000)),
                      help='指定后端服务端口（默认：5000或环境变量FLASK_RUN_PORT）')
    return parser.parse_args()

def print_status(message, status='info'):
    """打印带有颜色的状态信息"""
    prefix = {
        'success': GREEN + "[成功]" + END + " ",
        'warning': YELLOW + "[警告]" + END + " ",
        'error': RED + "[错误]" + END + " ",
        'info': BOLD + "[信息]" + END + " "
    }.get(status, BOLD + "[信息]" + END + " ")
    
    print("{}{}".format(prefix, message))

def check_python_version():
    """检查Python版本是否满足要求"""
    major, minor = sys.version_info.major, sys.version_info.minor
    if major < 3 or (major == 3 and minor < 6):
        print_status("Python版本过低: {}.{}，需要3.6或更高版本".format(major, minor), 'error')
        return False
    else:
        print_status("Python版本 {}.{} 符合要求".format(major, minor), 'success')
        return True

def check_dependencies():
    """检查必要依赖是否已安装"""
    packages = ['flask', 'sqlalchemy', 'psycopg2', 'dotenv', 'werkzeug']
    for package in packages:
        try:
            importlib.import_module(package)
            print_status("依赖 {} 已安装".format(package), 'success')
        except ImportError:
            print_status("缺少依赖: {}".format(package), 'error')
            return False
    return True

def check_config_files():
    """检查必要的配置文件是否存在"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(current_dir, '.env')
    
    if os.path.exists(config_file):
        print_status("配置文件 {} 存在".format(config_file), 'success')
        return True
    else:
        print_status("配置文件 {} 不存在，将尝试其他位置".format(config_file), 'info')
        
        # 检查上层目录
        parent_dir = os.path.dirname(current_dir)
        config_file = os.path.join(parent_dir, '.env')
        if os.path.exists(config_file):
            return True
        return False

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
    try:
        # 假设app已经导入
        from app import create_app
        app = create_app()
        
        with app.app_context():
            from app.models import db
            # 执行一个简单的查询以验证连接
            with db.engine.connect() as conn:
                conn.execute(db.text("SELECT 1"))
            return True
    except Exception as e:
        print_status("创建应用上下文时出错: {}".format(str(e)), 'error')
        return False

def check_database_structure():
    """检查数据库表结构"""
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            from app.models import db
            # 连接到数据库
            conn = db.engine.connect()
            
            # 测试连接是否有效
            try:
                conn.execute(db.text("SELECT 1"))
            except Exception as e:
                print_status("数据库连接失败: {}".format(str(e)), 'error')
                return False
                
            # 列出所有要检查的表名
            required_tables = ['users', 'roles', 'feedbacks', 'categories']
            
            # 检查表是否存在
            for table in required_tables:
                # 这里使用SQL来检查表是否存在
                query = db.text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = :table_name
                );
                """)
                
                result = conn.execute(query, {"table_name": table}).scalar()
                
                if result:
                    print_status("表 {} 已存在".format(table), 'success')
                else:
                    print_status("表 {} 不存在".format(table), 'error')
                    return False
            
            return True
    except Exception as e:
        print_status("检查数据库表时出错: {}".format(str(e)), 'error')
        return False

def check_port_available(port):
    """检查端口是否可用"""
    print_status("检查端口 {} 是否可用...".format(port), 'info')
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('localhost', port))
        sock.close()
        print_status("端口 {} 可用".format(port), 'success')
        return True
    except socket.error:
        sock.close()
        print_status("端口 {} 已被占用".format(port), 'error')
        # 自动查找可用端口
        return suggest_available_port()

def suggest_available_port():
    """建议一个可用的端口"""
    print_status("尝试查找可用端口...", 'info')
    for test_port in range(5000, 5100):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('localhost', test_port))
            sock.close()
            print_status("找到可用端口: {}".format(test_port), 'success')
            response = input("是否使用端口 {}? (y/n): ".format(test_port))
            if response.lower() == 'y':
                return test_port
        except socket.error:
            sock.close()
            continue
    
    print_status("在端口范围5000-5099中找不到可用端口", 'error')
    response = input("是否尝试使用更高端口号? (y/n): ")
    if response.lower() == 'y':
        # 尝试更高的端口范围
        for test_port in range(8000, 8100):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.bind(('localhost', test_port))
                sock.close()
                print_status("找到可用端口: {}".format(test_port), 'success')
                response = input("是否使用端口 {}? (y/n): ".format(test_port))
                if response.lower() == 'y':
                    return test_port
            except socket.error:
                sock.close()
                continue
    
    return False

def create_database_tables():
    """创建数据库表"""
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            from app.models import db
            # 创建所有表
            db.create_all()
        return True
    except Exception as e:
        print_status("创建数据库表时出错: {}".format(str(e)), 'error')
        return False

def create_initial_users():
    """创建初始管理员用户"""
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            # 导入User和Role模型
            from app.models import User, Role, db
            
            # 检查角色是否存在，不存在则创建
            admin_role = Role.query.filter_by(name='admin').first()
            if not admin_role:
                admin_role = Role(name='admin', description='Administrator')
                db.session.add(admin_role)
                db.session.commit()
            
            # 创建管理员用户（如果不存在）
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    role=admin_role
                )
                admin.set_password('admin')  # 设置默认密码
                db.session.add(admin)
                db.session.commit()
            
        return True
    except Exception as e:
        print_status("检查/创建初始用户时出错: {}".format(str(e)), 'error')
        return False

def start_backend(port):
    """启动后端服务"""
    print_status("准备启动后端服务在端口 {}...".format(port), 'info')
    
    try:
        # 使用flask run命令启动服务
        os.environ['FLASK_APP'] = 'run.py'
        os.environ['FLASK_RUN_PORT'] = str(port)
        
        print_status("正在启动后端服务在端口 {}...".format(port), 'info')
        
        # 使用subprocess启动Flask应用
        subprocess.Popen(
            ['python', '-m', 'flask', 'run', '--host=0.0.0.0', '--port={}'.format(port)],
            cwd=os.path.dirname(os.path.abspath(__file__))  # 确保在正确的目录下执行
        )
        
        return True
    except Exception as e:
        print_status("启动后端服务时出错: {}".format(str(e)), 'error')
        return False

def main():
    """主函数：执行所有检查并启动服务"""
    # 解析命令行参数
    args = parse_args()
    port = args.port
    
    # 显示启动信息
    print_status("开始 SoftLink 后端服务启动流程".format(BOLD, END), 'info')
    print_status("将使用端口: {}".format(port), 'info')
    
    # 检查项及其描述
    checks = [
        (check_python_version, "Python版本检查"),
        (check_dependencies, "依赖检查"),
        (check_config_files, "配置文件检查"),
        (check_database_connection, "数据库连接检查"),
        (check_database_structure, "数据库结构检查")
    ]
    
    # 记录哪些检查未通过
    failed_checks = []
    
    # 执行所有检查
    for check_func, check_name in checks:
        print_status("执行{}...".format(check_name), 'info')
        time.sleep(0.5)  # 为了更好的用户体验，添加短暂延迟
        
        if not check_func():
            print_status("{}失败".format(check_name), 'error')
            failed_checks.append(check_name)
            
            # 根据检查项目，可能需要执行修复操作
            if check_name == "数据库结构检查":
                # 如果数据库结构检查失败，尝试创建表
                if create_database_tables():
                    # 创建初始用户
                    create_initial_users()
                    # 从失败列表中移除
                    failed_checks.remove(check_name)
    
    # 检查端口
    port_check_result = check_port_available(port)
    if port_check_result is not True:
        if isinstance(port_check_result, int):
            # 端口已调整为新值
            port = port_check_result
        else:
            # 端口检查失败且无法调整
            print_status("无法找到可用端口，请手动指定其他端口", 'error')
            sys.exit(1)
    
    # 如果所有检查都通过或者修复了问题，启动后端服务
    if not failed_checks:
        print_status("所有检查通过或被忽略，正在启动后端服务...", 'success')
        start_backend(port)
    else:
        print_status("某些检查未通过，请解决问题后再尝试启动服务", 'error')
        sys.exit(1)

if __name__ == "__main__":
    main() 