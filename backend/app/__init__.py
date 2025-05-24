import os
from flask import Flask
from .extensions import db, migrate, jwt, cors
from .config import config_by_name
from flask_cors import CORS
from app.api import (
    user_bp, product_bp, inventory_bp, stock_record_bp,
    order_bp, auth_bp, alert_bp
)

def create_app(config_name=None):
    app = Flask(__name__)
    config_name = config_name or os.getenv('FLASK_ENV', 'development')
    app.config.from_object(config_by_name[config_name])

    # 初始化扩展
    CORS(app)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app)

    # 注册蓝图（只注册，不调用init_app）
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(product_bp, url_prefix='/api')
    app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
    app.register_blueprint(stock_record_bp, url_prefix='/api')
    app.register_blueprint(order_bp, url_prefix='/api')
    app.register_blueprint(auth_bp)
    app.register_blueprint(alert_bp, url_prefix='/api')

    return app 