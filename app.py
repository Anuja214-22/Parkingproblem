from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from models import db
from config import config
import os

def create_app(config_name='development'):
    """
    Application factory function
    Args:
        config_name: Configuration environment ('development' or 'production')
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    JWTManager(app)
    Mail(app)
    CORS(app)
    
    # Register blueprints (routes)
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.parking import parking_bp
    from routes.analytics import analytics_bp
    from routes.booking import booking_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(parking_bp)
    app.register_blueprint(booking_bp)
    app.register_blueprint(analytics_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        print("✓ Database initialized")
    
    # Health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health():
        return {'status': 'healthy'}, 200
    
    return app

if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    app.run(debug=True, host='0.0.0.0', port=5000)