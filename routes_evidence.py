"""
Evidence APIs (MVP05-06, MVP18)
GET /api/v1/tasks/{taskId}/evidences - List evidences for task (MVP05)
GET /api/v1/evidences/{evidenceId} - Evidence detail (MVP06)
POST /api/v1/tasks/{taskId}/evidences/upload - Upload evidence (MVP18)
"""
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from models import db, Task, Evidence, System, User
from auth import token_required, permission_required, check_system_access
from utils import (
    success_response, error_response, list_response,
    generate_etag, get_pagination_params,
    bad_request, forbidden, not_found, conflict, validation_error,
    check_idempotency_key, store_idempotency_response
)
from schemas import (
    evidence_list_schema, evidence_detail_schema,
    evidence_upload_request
)
from datetime import datetime
import logging
import os
import hashlib
from pathlib import Path

evidence_bp = Blueprint('evidence', __name__, url_prefix='/api/v1')
logger = logging.getLogger(__name__)

# Configuration
UPLOAD_DIR = os.getenv('UPLOAD_DIR', './uploads')
MAX_UPLOAD_SIZE_MB = int(os.getenv('MAX_UPLOAD_SIZE_MB', 100))
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

# Create upload directory if not exists
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)


# ============================================================================
# MVP05: GET /api/v1/tasks/{taskId}/evidences - List evidences
# ============================================================================

@evidence_bp.route('/tasks/<task_id>/evidences', methods=['GET'])
@token_required
@permission_required('evidence.read')
def get_evidences_list(current_user, task_id):
    """
    List all evidences for a task
    Supports pagination and filtering (evidenceType, source)
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
        
        # Get pagination params
        page, per_page, offset = get_pagination_params()
        
        # Build query with filters
        query = Evidence.query.filter_by(task_id=task_id)
        
        # Filter by evidenceType if provided
        evidence_type = request.args.get('evidenceType')
        if evidence_type:
            query = query.filter_by(evidence_type=evidence_type)
        
        # Filter by source if provided
        source = request.args.get('source')
        if source:
            query = query.filter_by(source=source)
        
        # Apply sorting
        sort_by = request.args.get('sortBy', 'created_at')
        sort_order = request.args.get('sortOrder', 'desc')
        
        if sort_by == 'createdAt':
            sort_by = 'created_at'
        elif sort_by == 'fileName':
            sort_by = 'file_name'
        elif sort_by == 'fileSizeBytes':
            sort_by = 'file_size_bytes'
        
        if sort_order.lower() == 'asc':
            query = query.order_by(getattr(Evidence, sort_by).asc())
        else:
            query = query.order_by(getattr(Evidence, sort_by).desc())
        
        total = query.count()
        evidences = query.offset(offset).limit(per_page).all()
        
        # Serialize to response
        evidence_dicts = [e.to_dict() for e in evidences]
        
        return list_response(
            evidence_dicts,
            total=total,
            page=page,
            per_page=per_page,
            status_code=200
        )
    
    except Exception as e:
        logger.error(f'Error fetching evidences: {str(e)}')
        return error_response('Failed to fetch evidences', 'INTERNAL_ERROR', 500)


# ============================================================================
# MVP06: GET /api/v1/evidences/{evidenceId} - Get evidence detail
# ============================================================================

@evidence_bp.route('/evidences/<evidence_id>', methods=['GET'])
@token_required
@permission_required('evidence.read')
def get_evidence_detail(current_user, evidence_id):
    """
    Get full evidence detail with file metadata
    Returns ETag header for concurrency control
    """
    try:
        # Get evidence
        evidence = Evidence.query.filter_by(id=evidence_id).first()
        if not evidence:
            return not_found(f'Evidence {evidence_id} not found')
        
        # Get task to check system access
        task = Task.query.filter_by(id=evidence.task_id).first()
        if not task:
            return not_found(f'Evidence {evidence_id} not found')
        
        # Check system access - return 404 if unauthorized (security masking)
        has_access, error_resp = check_system_access(current_user, task.system_id)
        if not has_access:
            return not_found(f'Evidence {evidence_id} not found')
        
        # Generate ETag
        etag = generate_etag(evidence)
        
        # Build response
        evidence_data = evidence.to_dict()
        
        resp = jsonify({
            'success': True,
            'data': evidence_data,
            'meta': {
                'requestId': request.headers.get('X-Request-ID', ''),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
        })
        
        # Add ETag header
        resp.headers['ETag'] = etag
        
        return resp, 200
    
    except Exception as e:
        logger.error(f'Error fetching evidence {evidence_id}: {str(e)}')
        return error_response('Failed to fetch evidence', 'INTERNAL_ERROR', 500)


# ============================================================================
# MVP18: POST /api/v1/tasks/{taskId}/evidences/upload - Upload evidence
# ============================================================================

@evidence_bp.route('/tasks/<task_id>/evidences/upload', methods=['POST'])
@token_required
@permission_required('evidence.upload')
def upload_evidence(current_user, task_id):
    """
    Upload/create evidence for a task
    DEC-06: Supports Idempotency-Key header for replay protection
    Multipart file upload with metadata
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
        
        # Validate file in request
        if 'file' not in request.files:
            return validation_error('Missing required field: file')
        
        file = request.files['file']
        if file.filename == '':
            return validation_error('No file selected')
        
        # Get form data
        evidence_type = request.form.get('evidenceType', 'file')
        file_name = request.form.get('fileName') or secure_filename(file.filename)
        content = request.form.get('content', '')
        
        # Validate evidenceType
        valid_types = ['log', 'screenshot', 'file', 'network_capture']
        if evidence_type not in valid_types:
            return validation_error(f'Invalid evidenceType. Must be one of: {", ".join(valid_types)}')
        
        # Read file data
        file_data = file.read()
        file_size = len(file_data)
        
        # Check file size limit
        if file_size > MAX_UPLOAD_SIZE_BYTES:
            return error_response(
                f'File exceeds maximum size of {MAX_UPLOAD_SIZE_MB}MB',
                'PAYLOAD_TOO_LARGE',
                413,
            )
        
        # Compute SHA256 hash
        sha256_hash = hashlib.sha256(file_data).hexdigest()
        
        # Get MIME type
        mime_type = file.content_type or 'application/octet-stream'
        
        # Save file to disk
        file_path = os.path.join(UPLOAD_DIR, task_id, sha256_hash)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        try:
            with open(file_path, 'wb') as f:
                f.write(file_data)
        except Exception as e:
            logger.error(f'Failed to save file: {str(e)}')
            return error_response('Failed to save file', 'INTERNAL_ERROR', 500)
        
        # Create evidence record
        evidence = Evidence(
            task_id=task_id,
            content=content,
            evidence_type=evidence_type,
            file_name=file_name,
            file_path=file_path,
            file_size_bytes=file_size,
            mime_type=mime_type,
            sha256_hash=sha256_hash,
            source='manual',
            upload_verified=True,  # Manual uploads are pre-verified
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(evidence)
        db.session.commit()
        
        # Response data
        response_data = {
            'evidenceId': evidence.id,
            'taskId': task_id,
            'fileName': file_name,
            'fileSizeBytes': file_size,
            'mimeType': mime_type,
            'sha256Hash': sha256_hash,
            'evidenceType': evidence_type,
            'uploadVerified': True,
            'uploadedAt': datetime.utcnow().isoformat() + 'Z'
        }
        
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
        logger.error(f'Error uploading evidence: {str(e)}')
        db.session.rollback()
        return error_response('Failed to upload evidence', 'INTERNAL_ERROR', 500)


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@evidence_bp.errorhandler(400)
def handle_bad_request(e):
    return error_response(str(e), 'BAD_REQUEST', 400)

@evidence_bp.errorhandler(401)
def handle_unauthorized(e):
    return error_response('Unauthorized', 'UNAUTHORIZED', 401)

@evidence_bp.errorhandler(403)
def handle_forbidden(e):
    return error_response('Forbidden', 'FORBIDDEN', 403)

@evidence_bp.errorhandler(404)
def handle_not_found(e):
    return error_response('Not found', 'NOT_FOUND', 404)

@evidence_bp.errorhandler(409)
def handle_conflict(e):
    return error_response('Conflict', 'CONFLICT', 409)

@evidence_bp.errorhandler(500)
def handle_internal_error(e):
    return error_response('Internal error', 'INTERNAL_ERROR', 500)
