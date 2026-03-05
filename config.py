import os
from datetime import timedelta

class Config:
    """Base configuration"""
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:password@localhost/smart_parking_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT Configuration
    JWT_SECRET_KEY = 'your-super-secret-jwt-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # Secret Key
    SECRET_KEY = 'your-secret-key-change-in-production'
    
    # Email Configuration (for notifications)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'your-email@gmail.com'
    MAIL_PASSWORD = 'your-app-password'
    
    # Parking Fee Configuration (in currency units per hour)
    PARKING_FEE_PER_HOUR = 5.0
    MINIMUM_CHARGE = 2.0  # Minimum charge for less than 1 hour

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}