#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
临时脚本：测试数据库连接
"""

import os
import sys
from urllib.parse import quote_plus

# 尝试直接连接数据库
def test_raw_connection():
    try:
        import psycopg2
        
        # 获取环境变量中的数据库配置
        db_host = os.environ.get('DB_HOST', 'localhost')
        db_port = os.environ.get('DB_PORT', '5432')
        db_name = os.environ.get('DB_NAME', 'softlink')
        db_user = os.environ.get('DB_USER', 'postgres')
        db_pass = os.environ.get('DB_PASS', '123.123.MengLi')
        
        # 打印要连接的数据库信息
        print(f"尝试连接到数据库:")
        print(f"  主机: {db_host}")
        print(f"  端口: {db_port}")
        print(f"  数据库: {db_name}")
        print(f"  用户: {db_user}")
        print(f"  密码: {'*' * len(db_pass)}")
        
        # 编码密码中的特殊字符
        encoded_pass = quote_plus(db_pass)
        
        # 创建连接字符串
        conn_string = f"host={db_host} port={db_port} dbname={db_name} user={db_user} password={db_pass}"
        conn_string_safe = f"host={db_host} port={db_port} dbname={db_name} user={db_user} password={'*' * len(db_pass)}"
        
        print(f"连接字符串: {conn_string_safe}")
        
        # 尝试连接
        conn = psycopg2.connect(conn_string)
        print("数据库连接成功!")
        
        # 执行简单查询
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"PostgreSQL版本: {version[0]}")
        
        # 关闭连接
        cursor.close()
        conn.close()
        
    except ModuleNotFoundError:
        print("错误: 未安装psycopg2模块，请安装: pip install psycopg2-binary")
    except Exception as e:
        print(f"数据库连接错误: {str(e)}")

# 测试SQLAlchemy连接
def test_sqlalchemy_connection():
    try:
        from sqlalchemy import create_engine, text
        
        # 获取环境变量中的数据库配置
        database_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:123.123.MengLi@localhost:5432/softlink')
        print(f"连接URL: {database_url.replace('postgres:', 'postgres:***')}")
        
        # 尝试编码URL
        if '123.123.MengLi' in database_url:
            encoded_url = database_url.replace('123.123.MengLi', quote_plus('123.123.MengLi'))
            print(f"编码后URL: {encoded_url.replace('postgres:', 'postgres:***')}")
            database_url = encoded_url
        
        # 尝试连接
        engine = create_engine(database_url)
        conn = engine.connect()
        
        # 执行简单查询
        result = conn.execute(text("SELECT version()"))
        version = result.scalar()
        print(f"SQLAlchemy连接成功! PostgreSQL版本: {version}")
        
        # 关闭连接
        conn.close()
        
    except ModuleNotFoundError:
        print("错误: 未安装SQLAlchemy模块，请安装: pip install sqlalchemy")
    except Exception as e:
        print(f"SQLAlchemy连接错误: {str(e)}")

if __name__ == "__main__":
    print("======== 测试直接数据库连接 ========")
    test_raw_connection()
    
    print("\n======== 测试SQLAlchemy连接 ========")
    test_sqlalchemy_connection() 