import os
import sys
import subprocess
import time

import importlib.util
from sqlalchemy import text
from app import create_app
from app.extensions import db
from app.models import *

def check_python_version():
    if sys.version_info < (3, 8):
        print('❌ Python 版本需 >= 3.8，当前：', sys.version)
        sys.exit(1)
    print('✅ Python 版本检查通过')

def check_env_file():
    if not os.path.exists('.env'):
        print('⚠️  未检测到 .env 文件，尝试使用 .env.example')
        if os.path.exists('.env.example'):
            import shutil
            shutil.copy('.env.example', '.env')
            print('✅ 已自动复制 .env.example 为 .env')
        else:
            print('❌ 缺少 .env 配置文件')
            sys.exit(1)
    else:
        print('✅ .env 文件存在')

def check_dependencies():
    required = [
        'flask', 'flask_restx', 'flask_sqlalchemy', 'flask_migrate', 'flask_jwt_extended',
        'psycopg2', 'celery', 'redis', 'flask_cors', 'dotenv', 'bcrypt'
    ]
    missing = []
    for pkg in required:
        if importlib.util.find_spec(pkg.replace('-', '_')) is None:
            missing.append(pkg)
    if missing:
        print('❌ 缺少依赖包：', ', '.join(missing))
        print('请先运行：pip install -r requirements.txt')
        sys.exit(1)
    print('✅ 依赖包检查通过')

def check_database():
    with app.app_context():
        try:
            db.session.execute(text('SELECT 1'))
            print('✅ 数据库连接成功')
        except Exception as e:
            print('❌ 数据库连接失败:', e)
            sys.exit(1)

def check_redis():
    import redis
    redis_url = app.config.get('CELERY_BROKER_URL')
    try:
        r = redis.from_url(redis_url)
        r.ping()
        print('✅ Redis 连接成功')
    except Exception as e:
        print('❌ Redis 连接失败:', e)
        sys.exit(1)

def run_flask():
    print('🚀 启动 Flask 服务...')
    subprocess.run([sys.executable, 'run.py'])

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'init-db':
        app = create_app()
        with app.app_context():
            db.create_all()
            print('数据库初始化完成！')
    else:
        print('==== 后端一键启动检查 ====' )
        check_python_version()
        check_env_file()
        check_dependencies()
        app = create_app()
        check_database()
        check_redis()
        print('==== 所有检查通过，准备启动后端服务 ====' )
        time.sleep(1)
        run_flask() 