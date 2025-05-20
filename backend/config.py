import os
from dotenv import load_dotenv

load_dotenv()  # 加载 .env 文件中的环境变量

# Construct the absolute path for the instance folder and the SQLite database
# Assuming this config.py is in the 'backend' directory.
BASE_DIR = os.path.abspath(os.path.dirname(__file__)) # backend directory
INSTANCE_FOLDER_PATH = os.path.join(BASE_DIR, 'instance')
DEFAULT_DB_PATH = os.path.join(INSTANCE_FOLDER_PATH, 'site.db')
TEST_DB_PATH = os.path.join(INSTANCE_FOLDER_PATH, 'test_site.db')

# Ensure the instance folder exists
os.makedirs(INSTANCE_FOLDER_PATH, exist_ok=True)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-default-secret-key'
    # Use SQLite as a sensible default if DATABASE_URL is not set
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{DEFAULT_DB_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or REDIS_URL
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or REDIS_URL
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'your-jwt-default-secret-key'
    ACCESS_TOKEN_EXPIRE_HOURS = int(os.environ.get('ACCESS_TOKEN_EXPIRE_HOURS', 1))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get('REFRESH_TOKEN_EXPIRE_DAYS', 30))
    # Add other configurations as needed based on the design document

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True # Log SQL queries

class TestingConfig(Config):
    TESTING = True
    # Use a separate SQLite database for testing if TEST_DATABASE_URL is not set
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or f'sqlite:///{TEST_DB_PATH}'
    SQLALCHEMY_ECHO = False # Usually false for tests unless debugging specific query issues
    # Ensure a separate test database

class ProductionConfig(Config):
    DEBUG = False
    # Production should absolutely use DATABASE_URL from environment variables
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') # No default here, must be set in prod env
    # Add production specific configurations like logging, security headers, etc.

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 