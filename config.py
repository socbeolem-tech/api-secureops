import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Cấu hình cơ bản"""
    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    JSON_SORT_KEYS = False
    
    # JSON Response
    JSON_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
    
    # Upload Configuration
    UPLOAD_DIR = os.getenv('UPLOAD_DIR', './uploads')
    MAX_UPLOAD_SIZE_MB = int(os.getenv('MAX_UPLOAD_SIZE_MB', 100))
    MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    
    # JWT Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'change_me_in_production')
    JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
    JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', 8))

class DevelopmentConfig(Config):
    """Cấu hình phát triển"""
    DEBUG = True
    FLASK_ENV = 'development'
    SQLALCHEMY_ECHO = True  # Log SQL queries
    
    # Kết nối PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://user:password@localhost:5432/secureops_db'
    )
    
    # Idempotency Key TTL (development: 1 hour)
    IDEMPOTENCY_KEY_TTL_SECONDS = 3600

class ProductionConfig(Config):
    """Cấu hình sản xuất"""
    DEBUG = False
    FLASK_ENV = 'production'
    SQLALCHEMY_ECHO = False
    
    # Database from environment
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    
    # Idempotency Key TTL (production: 24 hours)
    IDEMPOTENCY_KEY_TTL_SECONDS = 86400
    
    # Stricter JWT
    JWT_EXPIRATION_HOURS = 4  # Shorter expiration in prod

class TestingConfig(Config):
    """Cấu hình kiểm thử"""
    TESTING = True
    FLASK_ENV = 'testing'
    SQLALCHEMY_DATABASE_URI = 'postgresql://user:password@localhost:5432/test_db'
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False

# Config dictionary for easy access
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
