"""
Task & Workplace APIs (MVP01-MVP04)
GET /api/v1/my/tasks - Task list
GET /api/v1/tasks/{taskId} - Task detail
POST /api/v1/tasks/{taskId}/actions/mark-updates-seen - Mark seen
PUT /api/v1/tasks/{taskId}/assessment - Update assessment
"""
from flask import Blueprint, request, jsonify
from models import db, Task, System, User
from auth import token_required, permission_required, check_system_access
from utils import (
    success_response, error_response, list_response,
    generate_etag, validate_if_match, get_pagination_params,
    bad_request, forbidden, not_found, conflict, validation_error,
    check_idempotency_key, store_idempotency_response
)
from schemas import (
    task_list_schema, task_detail_schema,
    updates_seen_request, task_assessment_update
)
from datetime import datetime
import logging

task_bp = Blueprint('tasks', __name__, url_prefix='/api/v1')
logger = logging.getLogger(__name__)

# ============================================================================
# MVP01: GET /api/v1/my/tasks - List tasks for current CTV
# ============================================================================

@task_bp.route('/my/tasks', methods=['GET'])
@token_required
@permission_required('task.read')
def get_my_tasks(current_user):
    """
    Get all tasks assigned to current user
    DEC-01: Summary view only, no nested Evidence/Knowledge
    Supports pagination
    """
    try:
        # Get current user from DB
        user = User.query.filter_by(email=current_user['email']).first()
        if not user:
            return not_found('User not found')
        
        # Get pagination params
        page, per_page, offset = get_pagination_params()
        
        # Query tasks assigned to user
        query = Task.query.filter_by(assigned_to=user.id)
        total = query.count()
        
        tasks = query.offset(offset).limit(per_page).all()
        
        # Serialize to response
        task_dicts = [t.to_dict() for t in tasks]
        
        return list_response(
            task_dicts,
            total=total,
            page=page,
            per_page=per_page,
            status_code=200
        )
    
    except Exception as e:
        logger.error(f'Error fetching tasks: {str(e)}')
        return error_response('Failed to fetch tasks', 'INTERNAL_ERROR', 500)


# ============================================================================
# MVP02: GET /api/v1/tasks/{taskId} - Get task detail
# ============================================================================

@task_bp.route('/tasks/<task_id>', methods=['GET'])
@token_required
@permission_required('task.read')
def get_task_detail(current_user, task_id):
    """
    Get task detail with full assessment
    Returns ETag header for If-Match concurrency control (P0-04)
    """
    try:
        # Get task
        task = Task.query.filter_by(id=task_id).first()
        if not task:
            return not_found(f'Task {task_id} not found')
        
        # Check system access - return 404 if unauthorized (security masking)
        has_access, error_resp = check_system_access(current_user, task.system_id)
        if not has_access:
            return not_found(f'Task {task_id} not found')
        
        # Generate ETag for concurrency control
        etag = generate_etag(task)
        
        # Build response with ETag header
        response_data = task.to_dict()
        
        resp = jsonify({
            'success': True,
            'data': response_data,
            'meta': {
                'requestId': request.headers.get('X-Request-ID', ''),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
        })
        
        # Add ETag header for If-Match validation on updates
        resp.headers['ETag'] = etag
        
        return resp, 200
    
    except Exception as e:
        logger.error(f'Error fetching task {task_id}: {str(e)}')
        return error_response('Failed to fetch task', 'INTERNAL_ERROR', 500)


# ============================================================================
# MVP03: POST /api/v1/tasks/{taskId}/actions/mark-updates-seen
# ============================================================================

@task_bp.route('/tasks/<task_id>/actions/mark-updates-seen', methods=['POST'])
@token_required
@permission_required('task.read')
def mark_updates_seen(current_user, task_id):
    """
    Mark task updates as seen by CTV
    P0-04: Updates watermark tracking
    DEC-06: Supports Idempotency-Key header for replay protection
    Supports If-Match (optional), Idempotency-Key (optional)
    """
    try:
        # DEC-06: Check idempotency key
        idempotency_key = request.headers.get('Idempotency-Key')
        was_processed, status_code, response_body, error = check_idempotency_key(
            idempotency_key, request.method, request.path
        )
        
        if was_processed:
            # Return cached response
            return jsonify(response_body), status_code
        
        # Get task
        task = Task.query.filter_by(id=task_id).first()
        if not task:
            return not_found(f'Task {task_id} not found')
        
        # Check system access - return 404 if unauthorized (security masking)
        has_access, error_resp = check_system_access(current_user, task.system_id)
        if not has_access:
            return not_found(f'Task {task_id} not found')
        
        # Parse request body
        data = request.get_json() or {}
        
        try:
            args = updates_seen_request.load(data)
        except Exception as validation_err:
            return validation_error(f'Invalid request: {str(validation_err)}')
        
        # Update seen timestamp
        old_version = task.version
        task.ctv_da_xem_cap_nhat_luc = datetime.utcnow()
        task.version += 1
        
        db.session.commit()
        
        # Response
        resp_data = {
            'taskId': task.id,
            'seenThroughVersion': str(task.version),
            'hasNewUpdates': False  # Since we just marked all as seen
        }
        
        response_body = {
            'success': True,
            'data': resp_data,
            'meta': {'requestId': request.headers.get('X-Request-ID', '')}
        }
        
        # DEC-06: Store idempotency response
        store_idempotency_response(
            idempotency_key, request.method, request.path, 200, response_body
        )
        
        return success_response(
            resp_data,
            meta={'requestId': request.headers.get('X-Request-ID', '')},
            status_code=200
        )
    
    except Exception as e:
        logger.error(f'Error marking updates seen: {str(e)}')
        db.session.rollback()
        return error_response('Failed to mark updates', 'INTERNAL_ERROR', 500)


# ============================================================================
# MVP04: PUT /api/v1/tasks/{taskId}/assessment - Update assessment
# ============================================================================

@task_bp.route('/tasks/<task_id>/assessment', methods=['PUT'])
@token_required
@permission_required('task.assess')
def update_task_assessment(current_user, task_id):
    """
    Update CTV assessment on task
    P0-04: Requires If-Match header for concurrency control
    DEC-06: Supports Idempotency-Key header for replay protection
    Returns 409 CONCURRENT_MODIFICATION if version mismatch
    """
    try:
        # DEC-06: Check idempotency key
        idempotency_key = request.headers.get('Idempotency-Key')
        was_processed, status_code, response_body, error = check_idempotency_key(
            idempotency_key, request.method, request.path
        )
        
        if was_processed:
            # Return cached response
            return jsonify(response_body), status_code
        
        # Get task
        task = Task.query.filter_by(id=task_id).first()
        if not task:
            return not_found(f'Task {task_id} not found')
        
        # Check system access - return 404 if unauthorized (security masking)
        has_access, error_resp = check_system_access(current_user, task.system_id)
        if not has_access:
            return not_found(f'Task {task_id} not found')
        
        # Validate If-Match header (P0-04 concurrency control)
        if_match = request.headers.get('If-Match')
        expected_etag = generate_etag(task)
        
        if if_match:
            is_valid, error_resp = validate_if_match(expected_etag, if_match)
            if not is_valid:
                return error_resp
        
        # Parse request body
        data = request.get_json() or {}
        
        try:
            args = task_assessment_update.load(data)
        except Exception as validation_err:
            return validation_error(f'Invalid request: {str(validation_err)}')
        
        # Validate assessment not empty
        assessment = args.get('assessment', '').strip()
        if not assessment:
            return validation_error('Assessment cannot be empty')
        
        # Update task
        task.assessment = assessment
        task.version += 1
        task.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Generate new ETag
        new_etag = generate_etag(task)
        
        # Response with new ETag
        task_data = task.to_dict()
        response_body = {
            'success': True,
            'data': task_data,
            'meta': {'requestId': request.headers.get('X-Request-ID', '')}
        }
        
        # DEC-06: Store idempotency response
        store_idempotency_response(
            idempotency_key, request.method, request.path, 200, response_body
        )
        
        resp = jsonify(response_body)
        resp.headers['ETag'] = new_etag
        
        return resp, 200
    
    except Exception as e:
        logger.error(f'Error updating assessment: {str(e)}')
        db.session.rollback()
        return error_response('Failed to update assessment', 'INTERNAL_ERROR', 500)


# ============================================================================
# HELPER: Create task (for testing)
# ============================================================================

@task_bp.route('/tasks', methods=['POST'])
@token_required
@permission_required('task.write')
def create_task(current_user):
    """
    Create a new task
    DEC-06: Supports Idempotency-Key header for replay protection
    For testing/admin use
    """
    try:
        # DEC-06: Check idempotency key
        idempotency_key = request.headers.get('Idempotency-Key')
        was_processed, status_code, response_body, error = check_idempotency_key(
            idempotency_key, request.method, request.path
        )
        
        if was_processed:
            # Return cached response
            return jsonify(response_body), status_code
        
        data = request.get_json() or {}
        
        # Validate required fields
        if not data.get('title'):
            return validation_error('Title is required')
        
        if not data.get('system_id'):
            return validation_error('System ID is required')
        
        # Check system exists and user has access
        system = System.query.filter_by(id=data['system_id']).first()
        if not system:
            return not_found(f'System {data["system_id"]} not found')
        
        has_access, error_resp = check_system_access(current_user, system.id)
        if not has_access:
            return not_found(f'System {data["system_id"]} not found')
        
        # Create task
        task = Task(
            title=data['title'],
            description=data.get('description'),
            status=data.get('status', 'pending'),
            priority=data.get('priority', 'medium'),
            system_id=system.id,
            assigned_to=data.get('assigned_to')
        )
        
        db.session.add(task)
        db.session.commit()
        
        response_data = task.to_dict()
        response_body = {
            'success': True,
            'data': response_data,
            'meta': {'requestId': request.headers.get('X-Request-ID', '')}
        }
        
        # DEC-06: Store idempotency response
        store_idempotency_response(
            idempotency_key, request.method, request.path, 201, response_body
        )
        
        return success_response(
            response_data,
            meta={'requestId': request.headers.get('X-Request-ID', '')},
            status_code=201
        )
    
    except Exception as e:
        logger.error(f'Error creating task: {str(e)}')
        db.session.rollback()
        return error_response('Failed to create task', 'INTERNAL_ERROR', 500)


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@task_bp.errorhandler(400)
def handle_bad_request(e):
    return error_response(str(e), 'BAD_REQUEST', 400)

@task_bp.errorhandler(401)
def handle_unauthorized(e):
    return error_response('Unauthorized', 'UNAUTHORIZED', 401)

@task_bp.errorhandler(403)
def handle_forbidden(e):
    return error_response('Forbidden', 'FORBIDDEN', 403)

@task_bp.errorhandler(404)
def handle_not_found(e):
    return error_response('Not found', 'NOT_FOUND', 404)

@task_bp.errorhandler(409)
def handle_conflict(e):
    return error_response('Conflict', 'CONFLICT', 409)

@task_bp.errorhandler(500)
def handle_internal_error(e):
    return error_response('Internal error', 'INTERNAL_ERROR', 500)
