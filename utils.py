"""
Utility functions for common patterns (response envelopes, validators, etc.)
"""
from flask import jsonify, request
from datetime import datetime
import uuid

# ============================================================================
# Common Response Envelope (Data/Meta pattern)
# ============================================================================

def success_response(data=None, meta=None, status_code=200):
    """
    Build standard success response envelope
    Pattern: {"success": true, "data": {...}, "meta": {...}}
    """
    if meta is None:
        meta = {}
    
    # Add standard meta fields
    if 'requestId' not in meta:
        meta['requestId'] = str(uuid.uuid4())
    
    if 'timestamp' not in meta:
        meta['timestamp'] = datetime.utcnow().isoformat() + 'Z'
    
    response = {
        'success': True,
        'data': data,
        'meta': meta
    }
    
    return jsonify(response), status_code


def list_response(items, total=None, page=None, per_page=None, status_code=200):
    """
    Build standard list response with pagination metadata
    """
    meta = {
        'requestId': str(uuid.uuid4()),
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'total': total or len(items) if items else 0,
    }
    
    if page is not None:
        meta['page'] = page
    if per_page is not None:
        meta['per_page'] = per_page
    
    return jsonify({
        'success': True,
        'data': items or [],
        'meta': meta
    }), status_code


def error_response(error, code=None, status_code=400, details=None):
    """
    Build standard error response envelope
    Pattern: {"success": false, "error": {"code": "...", "message": "...", "details": null, "requestId": "..."}}
    """
    response = {
        'success': False,
        'error': {
            'code': code or 'BAD_REQUEST',
            'message': error,
            'details': details,
            'requestId': str(uuid.uuid4())
        },
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    
    return jsonify(response), status_code


# Standard HTTP error responses
def bad_request(message='Bad request'):
    return error_response(message, 'BAD_REQUEST', 400)

def unauthorized(message='Unauthorized'):
    return error_response(message, 'UNAUTHORIZED', 401)

def forbidden(message='Forbidden'):
    return error_response(message, 'FORBIDDEN', 403)

def not_found(message='Resource not found'):
    return error_response(message, 'NOT_FOUND', 404)

def conflict(message='Conflict'):
    return error_response(message, 'CONFLICT', 409)

def validation_error(message='Validation failed'):
    return error_response(message, 'VALIDATION_ERROR', 422)

def internal_error(message='Internal server error'):
    return error_response(message, 'INTERNAL_ERROR', 500)


# ============================================================================
# ETag & Concurrency Control (P0-04)
# ============================================================================

def generate_etag(obj):
    """
    Generate ETag for object (based on version or hash)
    Used for If-Match concurrency control
    """
    if hasattr(obj, 'version'):
        # Use version field if available
        return f'"{obj.version}"'
    else:
        # Fallback: use object ID and timestamp
        obj_id = getattr(obj, 'id', str(uuid.uuid4()))
        timestamp = getattr(obj, 'updated_at', datetime.utcnow())
        return f'"{obj_id}:{timestamp}"'


def validate_if_match(expected_etag, provided_etag):
    """
    Validate If-Match header for concurrency control
    Returns: (is_valid, error_response)
    """
    if not provided_etag:
        return False, error_response(
            'If-Match header required for modification',
            'MISSING_IF_MATCH',
            400
        )
    
    if expected_etag != provided_etag:
        return False, error_response(
            'Resource has been modified (stale version)',
            'CONCURRENT_MODIFICATION',
            409
        )
    
    return True, None


# ============================================================================
# Idempotency Key Management (DEC-06)
# ============================================================================

def get_idempotency_key():
    """Extract Idempotency-Key from request headers"""
    return request.headers.get('Idempotency-Key')


def validate_idempotency_key(key):
    """
    Validate idempotency key format
    Should be a UUID or similar unique identifier
    """
    if not key:
        return False
    
    # Basic validation: non-empty string
    # In production, could enforce UUID format
    if len(key) < 1 or len(key) > 256:
        return False
    
    return True


# ============================================================================
# Pagination Helpers
# ============================================================================

def get_pagination_params():
    """Extract and validate pagination parameters from query string"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Validate ranges
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 20
        
        offset = (page - 1) * per_page
        return page, per_page, offset
    except (ValueError, TypeError):
        return 1, 20, 0


# ============================================================================
# Validation Helpers
# ============================================================================

def validate_uuid(value):
    """Validate UUID format"""
    if not value:
        return False
    
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


def validate_email(email):
    """Basic email validation"""
    if not email or '@' not in email or '.' not in email.split('@')[1]:
        return False
    return True


def validate_string(value, min_length=1, max_length=None):
    """Validate string length"""
    if not isinstance(value, str):
        return False
    if len(value) < min_length:
        return False
    if max_length and len(value) > max_length:
        return False
    return True


# ============================================================================
# JSON Field Helpers
# ============================================================================

def safe_json_get(json_obj, key, default=None):
    """Safely get value from JSON object"""
    if isinstance(json_obj, dict):
        return json_obj.get(key, default)
    return default


# ============================================================================
# Timestamp & DateTime Helpers
# ============================================================================

def get_timestamp_str():
    """Get current timestamp as ISO string"""
    return datetime.utcnow().isoformat() + 'Z'


def parse_timestamp(timestamp_str):
    """Parse ISO timestamp string to datetime"""
    try:
        # Remove 'Z' suffix and parse
        if timestamp_str.endswith('Z'):
            timestamp_str = timestamp_str[:-1]
        return datetime.fromisoformat(timestamp_str)
    except (ValueError, AttributeError):
        return None


# ============================================================================
# Idempotency Support (DEC-06)
# ============================================================================

def check_idempotency_key(idempotency_key, method, path):
    """
    Check if request was already processed (DEC-06)
    Returns: (was_processed, status_code, response_body, error_message)
    """
    from models import IdempotencyKey
    
    if not idempotency_key:
        return False, None, None, None  # No idempotency key provided
    
    # Look up existing key
    existing = IdempotencyKey.query.filter_by(id=idempotency_key).first()
    
    if not existing:
        return False, None, None, None  # Key not found, process request
    
    # Check if expired
    if existing.is_expired():
        # Remove expired key and process as new request
        from models import db
        db.session.delete(existing)
        db.session.commit()
        return False, None, None, None
    
    # Key exists and not expired - return cached response
    return True, existing.response_status, existing.response_body, None


def store_idempotency_response(idempotency_key, method, path, status_code, response_body):
    """
    Store response for idempotency key
    """
    from models import IdempotencyKey, db
    
    if not idempotency_key:
        return  # No key to store
    
    # Delete old entry if exists
    existing = IdempotencyKey.query.filter_by(id=idempotency_key).first()
    if existing:
        db.session.delete(existing)
    
    # Create new entry
    key = IdempotencyKey(
        id=idempotency_key,
        method=method,
        path=path,
        response_status=status_code,
        response_body=response_body
    )
    
    db.session.add(key)
    db.session.commit()
