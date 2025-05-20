import sqlite3
import os
import sys

def main():
    """手动将resolution_notes列添加到feedbacks表"""
    
    # 尝试几个可能的数据库路径
    possible_paths = [
        os.path.join(os.path.dirname(__file__), 'app', 'data', 'database.db'),
        os.path.join(os.path.dirname(__file__), 'database.db'),
        os.path.join(os.path.dirname(__file__), 'app.db'),
        os.path.join(os.path.dirname(__file__), 'instance', 'app.db'),
        'app.db',
        'database.db'
    ]
    
    db_path = None
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        # 尝试递归查找数据库文件
        for root, dirs, files in os.walk(os.path.dirname(__file__)):
            for file in files:
                if file.endswith('.db'):
                    db_path = os.path.join(root, file)
                    print(f"找到可能的数据库文件: {db_path}")
                    break
            if db_path:
                break
    
    if not db_path:
        print("找不到数据库文件，请确保数据库已创建。")
        return
    
    print(f"连接到数据库: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 首先获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        
        print(f"数据库中的表: {table_names}")
        
        if 'feedbacks' not in table_names:
            print("feedbacks表不存在，无法迁移。")
            return
        
        # 检查列是否已存在
        cursor.execute("PRAGMA table_info(feedbacks)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"feedbacks表中的列: {column_names}")
        
        if 'resolution_notes' not in column_names:
            print("添加resolution_notes列到feedbacks表...")
            cursor.execute("ALTER TABLE feedbacks ADD COLUMN resolution_notes TEXT")
            conn.commit()
            print("迁移成功完成!")
        else:
            print("resolution_notes列已存在，无需迁移。")
        
    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
        return
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main() 