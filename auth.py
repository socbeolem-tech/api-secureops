"""
Authentication & Authorization Middleware
JWT Bearer Token verification and role-based access control
"""
import jwt
import uuid
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# JWT Configuration
# ============================================================================

SECRET_KEY = os.getenv('SECRET_KEY', 'your_super_secret_key_change_in_production')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', '8'))

# ============================================================================
# MOCK JWT Generation (Development)
# ============================================================================

def generate_mock_token(user_id, email, role='CTV', systems=None):
    """
    Generate a mock JWT token for development/testing
    Replace with real IdP token in production
    """
    if systems is None:
        systems = ['default']
    
    payload = {
        'sub': user_id,
        'email': email,
        'role': role,
        'permissions': get_role_permissions(role),
        'systems': systems,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def get_role_permissions(role):
    """Get permission list for a role"""
    permissions_map = {
        'CTV': [
            'task.read', 'task.write', 'task.assess',
            'evidence.read', 'evidence.upload', 'evidence.download',
            'investigation.read', 'knowledge.read'
        ],
        'L2': [
            'task.read', 'task.write', 'task.assess',
            'evidence.read', 'evidence.upload', 'evidence.download',
            'investigation.read', 'investigation.write',
            'knowledge.read'
        ],
        'L3': [
            'task.read', 'task.write', 'task.assess', 'task.manage',
            'evidence.read', 'evidence.upload', 'evidence.download',
            'investigation.read', 'investigation.write', 'investigation.manage',
            'l1work.read', 'l1work.write', 'l1work.manage',
            'knowledge.read', 'knowledge.write'
        ],
        'L4': [
            'task.read', 'task.write', 'task.assess', 'task.manage', 'task.delete',
            'evidence.read', 'evidence.upload', 'evidence.download', 'evidence.delete',
            'investigation.read', 'investigation.write', 'investigation.manage', 'investigation.delete',
            'l1work.read', 'l1work.write', 'l1work.manage', 'l1work.delete',
            'knowledge.read', 'knowledge.write', 'knowledge.publish',
            'audit.read', 'report.read'
        ],
        'ADMIN': ['*']
    }
    return permissions_map.get(role, [])


# ============================================================================
# JWT Verification & Extraction
# ============================================================================

def extract_token_from_header():
    """Extract JWT token from Authorization header"""
    auth_header = request.headers.get('Authorization', '')
    
    if not auth_header:
        return None
    
    try:
        # Format: "Bearer <token>"
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None
        return parts[1]
    except Exception:
        return None


def verify_token(token):
    """
    Verify JWT token and return decoded payload
    Returns: (decoded_payload, error_message)
    """
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return decoded, None
    except jwt.ExpiredSignatureError:
        return None, 'Token expired'
    except jwt.InvalidTokenError as e:
        return None, f'Invalid token: {str(e)}'


def get_current_user():
    """
    Extract and verify current user from request context
    Returns: (user_data_dict, error_response) or (None, error_response)
    """
    token = extract_token_from_header()
    
    if not token:
        return None, {
            'success': False,
            'error': 'Missing authorization token',
            'code': 'UNAUTHORIZED'
        }, 401
    
    payload, error = verify_token(token)
    
    if error:
        return None, {
            'success': False,
            'error': error,
            'code': 'UNAUTHORIZED'
        }, 401
    
    return payload, None, 200


# ============================================================================
# Decorators for Route Protection
# ============================================================================

def token_required(f):
    """
    Decorator to require valid JWT token on endpoint
    Injects 'current_user' into route function kwargs
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        current_user, error_response, status_code = get_current_user()
        
        if current_user is None:
            return jsonify(error_response), status_code
        
        return f(current_user=current_user, *args, **kwargs)
    
    return decorated


def permission_required(required_permission):
    """
    Decorator to require specific permission
    Usage: @permission_required('task.write')
    Should be stacked BELOW @token_required
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # If current_user already in kwargs (from token_required decorator), use it
            if 'current_user' in kwargs:
                current_user = kwargs['current_user']
            else:
                # Otherwise, get it from the request
                current_user, error_response, status_code = get_current_user()
                
                if current_user is None:
                    return jsonify(error_response), status_code
                
                # Don't re-inject current_user if already present
                kwargs['current_user'] = current_user
            
            # Check if ADMIN (has all permissions)
            permissions = current_user.get('permissions', [])
            if '*' in permissions or required_permission in permissions:
                return f(*args, **kwargs)
            
            return jsonify({
                'success': False,
                'error': f'Permission denied: {required_permission}',
                'code': 'FORBIDDEN'
            }), 403
        
        return decorated
    
    return decorator


def role_required(required_roles):
    """
    Decorator to require specific role(s)
    Usage: @role_required(['L2', 'L3', 'L4', 'ADMIN'])
    Should be stacked BELOW @token_required
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # If current_user already in kwargs (from token_required decorator), use it
            if 'current_user' in kwargs:
                current_user = kwargs['current_user']
            else:
                # Otherwise, get it from the request
                current_user, error_response, status_code = get_current_user()
                
                if current_user is None:
                    return jsonify(error_response), status_code
                
                # Don't re-inject current_user if already present
                kwargs['current_user'] = current_user
            
            user_role = current_user.get('role')
            if user_role in required_roles:
                return f(*args, **kwargs)
            
            return jsonify({
                'success': False,
                'error': f'Role required: one of {required_roles}',
                'code': 'FORBIDDEN'
            }), 403
        
        return decorated
    
    return decorator


# ============================================================================
# System Access Control
# ============================================================================

def check_system_access(current_user, system_id):
    """
    Check if user has access to a specific system
    Returns: (has_access, error_dict)
    """
    user_systems = current_user.get('systems', [])
    role = current_user.get('role')
    
    # ADMIN has access to all systems
    if role == 'ADMIN':
        return True, None
    
    # In development/testing, "default" grants access to all systems
    if 'default' in user_systems:
        return True, None
    
    # Check assigned systems
    if system_id in user_systems:
        return True, None
    
    return False, {
        'success': False,
        'error': f'Access denied to system: {system_id}',
        'code': 'FORBIDDEN'
    }


# ============================================================================
# Test/Development Routes
# ============================================================================

def create_auth_test_routes(app):
    """
    Create test routes for token generation and verification
    These should be REMOVED in production
    """
    
    @app.route('/auth/test-token', methods=['GET'])
    def get_test_token():
        """
        Generate a test token for development/testing
        Usage: GET /auth/test-token?role=CTV&email=user@example.com
        """
        # Note: Available on all environments for API testing
        
        from models import User
        
        role = request.args.get('role', 'CTV')
        email = request.args.get('email', f'user_{role}@secureops.local')
        user_id = request.args.get('user_id', None)
        systems = request.args.getlist('systems') or ['default']
        
        # If user_id not provided, find user with matching role
        if not user_id:
            user = User.query.filter_by(role=role).first()
            if user:
                user_id = user.id
                email = user.email
            else:
                user_id = f'test_user_{role}'
        
        token = generate_mock_token(user_id, email, role, systems)
        
        return jsonify({
            'success': True,
            'data': {
                'token': token,
                'user': {
                    'sub': user_id,
                    'email': email,
                    'role': role,
                    'systems': systems
                }
            },
            'meta': {
                'requestId': str(uuid.uuid4()),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
        }), 200
    
    
    @app.route('/auth/verify-token', methods=['POST'])
    def verify_token_endpoint():
        """
        Verify a token and return decoded payload
        POST /auth/verify-token with Authorization header
        """
        if current_app.config.get('FLASK_ENV') != 'development':
            return jsonify({'error': 'Not available in production'}), 403
        
        current_user, error_response, status_code = get_current_user()
        
        if current_user:
            return jsonify({
                'success': True,
                'decoded': current_user
            }), 200
        else:
            return jsonify(error_response), status_code
    
    
    @app.route('/auth/whoami', methods=['GET'])
    @token_required
    def whoami(current_user):
        """
        Get current user info
        GET /auth/whoami (requires token)
        """
        return jsonify({
            'success': True,
            'user': {
                'id': current_user.get('sub'),
                'email': current_user.get('email'),
                'role': current_user.get('role'),
                'permissions': current_user.get('permissions'),
                'systems': current_user.get('systems')
            }
        }), 200
