from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from celery import Celery

from config import config # Assuming config.py is in the parent directory of 'app'

db = SQLAlchemy()
migrate = Migrate()
ma = Marshmallow()
cors = CORS()
# Initialize Celery. The broker and backend are set in the config.
# The application context is needed for Celery tasks that interact with Flask app components.
celery_app = Celery(__name__)

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}}) # Adjust origins as needed

    # Update Celery configuration with app config
    celery_app.conf.update(app.config)
    # To make celery tasks aware of the Flask application context
    class ContextTask(celery_app.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    celery_app.Task = ContextTask

    # Register Blueprints here
    from .api.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    from .api.feedback import feedback_bp
    app.register_blueprint(feedback_bp, url_prefix='/api') # Feedback routes start with /api/feedback

    from .api.admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/api') # Admin routes also use /api prefix, e.g., /api/admin/dynamic-menu-items

    from .api.users import users_bp
    app.register_blueprint(users_bp, url_prefix='/api') # User-specific routes, e.g., /api/users/me

    from .api.features import features_bp
    app.register_blueprint(features_bp, url_prefix='/api') # Feature related routes, e.g., /api/features/dynamic-menu

    from .api.vip import vip_bp
    app.register_blueprint(vip_bp, url_prefix='/api') # VIP routes, e.g., /api/vip/levels

    from .api.preferences import preferences_bp
    app.register_blueprint(preferences_bp, url_prefix='/api') # User preferences routes, e.g., /api/users/me/preferences

    # Example route
    @app.route('/ping')
    def ping():
        return 'Pong!'

    return app 