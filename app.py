from flask import Flask, jsonify
from config import config
from models import db
from routes_tasks import task_bp
from routes_evidence import evidence_bp
from auth import create_auth_test_routes
from utils import error_response
import os

def create_app(config_name=None):
    """Factory function để tạo Flask app"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Khởi tạo database
    db.init_app(app)
    
    # Đăng ký blueprints
    app.register_blueprint(task_bp)
    app.register_blueprint(evidence_bp)
    
    # Register auth test routes (development only)
    if app.config.get('FLASK_ENV') == 'development':
        create_auth_test_routes(app)
    
    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({
            'status': 'healthy',
            'service': 'SecureOps API',
            'version': '0.22'
        }), 200
    
    # Global error handlers
    @app.errorhandler(404)
    def not_found(error):
        return error_response(
            'Endpoint not found',
            'NOT_FOUND',
            404
        )
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return error_response(
            'Method not allowed',
            'METHOD_NOT_ALLOWED',
            405
        )
    
    @app.errorhandler(500)
    def server_error(error):
        app.logger.error(f'Internal server error: {str(error)}')
        return error_response(
            'Internal server error',
            'INTERNAL_ERROR',
            500
        )
    
    # Context để tạo database tables
    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(
        debug=app.config.get('DEBUG', True),
        host=os.getenv('SERVER_HOST', '0.0.0.0'),
        port=int(os.getenv('SERVER_PORT', 5000))
    )
