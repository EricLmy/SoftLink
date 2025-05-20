import os
from app import create_app, db # 从当前目录的app模块导入
# from app.models import User # Example: Import models for migration or shell context

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

@app.shell_context_processor
def make_shell_context():
    # return dict(db=db, User=User) # Example: Make db and models available in 'flask shell'
    return dict(db=db)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('FLASK_RUN_PORT', 5000))) 