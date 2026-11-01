"""
Request/Response schemas for API endpoints
Using marshmallow for validation and serialization
"""
from marshmallow import Schema, fields, validate, ValidationError
from datetime import datetime

# ============================================================================
# TASK SCHEMAS (MVP01-04)
# ============================================================================

class TaskListItemSchema(Schema):
    """Task summary for list view (mvp01)"""
    id = fields.String(required=True)
    title = fields.String(required=True)
    description = fields.String(allow_none=True)
    status = fields.String(required=True)
    priority = fields.String(required=True)
    system_id = fields.String(required=True)
    assigned_to = fields.String(allow_none=True)
    created_at = fields.DateTime(allow_none=True)
    updated_at = fields.DateTime(allow_none=True)
    
    class Meta:
        ordered = True


class TaskDetailSchema(Schema):
    """Task detail with assessment (mvp02)"""
    id = fields.String(required=True)
    title = fields.String(required=True)
    description = fields.String(allow_none=True)
    status = fields.String(required=True)
    priority = fields.String(required=True)
    system_id = fields.String(required=True)
    assigned_to = fields.String(allow_none=True)
    assessment = fields.String(allow_none=True)
    version = fields.Integer(allow_none=True)
    created_at = fields.DateTime(allow_none=True)
    updated_at = fields.DateTime(allow_none=True)
    
    class Meta:
        ordered = True


class TaskListResponseSchema(Schema):
    """Response envelope for task list (mvp01)"""
    success = fields.Boolean(required=True)
    data = fields.List(fields.Nested(TaskListItemSchema), required=True)
    meta = fields.Dict(required=True)


class TaskDetailResponseSchema(Schema):
    """Response envelope for task detail (mvp02)"""
    success = fields.Boolean(required=True)
    data = fields.Nested(TaskDetailSchema, required=True)
    meta = fields.Dict(required=True)


class UpdatesSeenRequestSchema(Schema):
    """Request body for mark-updates-seen (mvp03)"""
    seenThroughVersion = fields.String(
        required=False,
        allow_none=True,
        description="Watermark timestamp or version from previous response"
    )


class UpdatesSeenResponseSchema(Schema):
    """Response for mark-updates-seen (mvp03)"""
    success = fields.Boolean(required=True)
    data = fields.Dict(required=True)  # {taskId, hasNewUpdates, seenThroughVersion}
    meta = fields.Dict(required=True)


class TaskAssessmentUpdateSchema(Schema):
    """Request body for update assessment (mvp04)"""
    assessment = fields.String(
        required=True,
        validate=validate.Length(min=1, max=10000),
        description="CTV's assessment/findings"
    )


class TaskMutationResponseSchema(Schema):
    """Response for task mutations (mvp04)"""
    success = fields.Boolean(required=True)
    data = fields.Nested(TaskDetailSchema, required=True)
    meta = fields.Dict(required=True)


# ============================================================================
# EVIDENCE SCHEMAS (MVP05-06, 18)
# ============================================================================

class EvidenceSummarySchema(Schema):
    """Evidence summary for list (MVP05)"""
    id = fields.String(required=True)
    taskId = fields.String(required=True, data_key='task_id')
    evidenceType = fields.String(required=False, allow_none=True, data_key='evidence_type')
    fileName = fields.String(required=False, allow_none=True, data_key='file_name')
    fileSizeBytes = fields.Integer(required=False, allow_none=True, data_key='file_size_bytes')
    mimeType = fields.String(required=False, allow_none=True, data_key='mime_type')
    sha256Hash = fields.String(required=False, allow_none=True, data_key='sha256_hash')
    source = fields.String(required=False, allow_none=True)
    uploadVerified = fields.Boolean(required=False, allow_none=True, data_key='upload_verified')
    createdAt = fields.DateTime(required=False, allow_none=True, data_key='created_at')
    
    class Meta:
        ordered = True


class EvidenceDetailSchema(Schema):
    """Evidence detail with full content (MVP06)"""
    id = fields.String(required=True)
    taskId = fields.String(required=True, data_key='task_id')
    content = fields.String(required=False, allow_none=True)
    evidenceType = fields.String(required=False, allow_none=True, data_key='evidence_type')
    fileName = fields.String(required=False, allow_none=True, data_key='file_name')
    fileSizeBytes = fields.Integer(required=False, allow_none=True, data_key='file_size_bytes')
    mimeType = fields.String(required=False, allow_none=True, data_key='mime_type')
    sha256Hash = fields.String(required=False, allow_none=True, data_key='sha256_hash')
    uploadId = fields.String(required=False, allow_none=True, data_key='upload_id')
    uploadVerified = fields.Boolean(required=False, allow_none=True, data_key='upload_verified')
    source = fields.String(required=False, allow_none=True)
    l1WorkId = fields.String(required=False, allow_none=True, data_key='l1_work_id')
    createdAt = fields.DateTime(required=False, allow_none=True, data_key='created_at')
    updatedAt = fields.DateTime(required=False, allow_none=True, data_key='updated_at')
    
    class Meta:
        ordered = True


class EvidenceListResponseSchema(Schema):
    """Response for evidence list (MVP05)"""
    success = fields.Boolean(required=True)
    data = fields.List(fields.Nested(EvidenceSummarySchema), required=True)
    meta = fields.Dict(required=True)


class EvidenceDetailResponseSchema(Schema):
    """Response for evidence detail (MVP06)"""
    success = fields.Boolean(required=True)
    data = fields.Nested(EvidenceDetailSchema, required=True)
    meta = fields.Dict(required=True)


class EvidenceUploadRequestSchema(Schema):
    """Request body for upload (MVP18)"""
    evidenceType = fields.String(
        required=True,
        validate=validate.OneOf(['log', 'screenshot', 'file', 'network_capture']),
        data_key='evidenceType',
        description="Type of evidence"
    )
    fileName = fields.String(
        required=False,
        allow_none=True,
        data_key='fileName',
        description="Override file name (optional)"
    )
    content = fields.String(
        required=False,
        allow_none=True,
        data_key='content',
        description="Text content or metadata (optional)"
    )


class EvidenceUploadResponseSchema(Schema):
    """Response for upload (MVP18)"""
    success = fields.Boolean(required=True)
    data = fields.Dict(required=True)  # {evidenceId, uploadId, fileName, fileSizeBytes, ...}
    meta = fields.Dict(required=True)


# ============================================================================
# USER & SYSTEM SCHEMAS
# ============================================================================

class UserSummarySchema(Schema):
    """User summary"""
    id = fields.String(required=True)
    email = fields.String(required=True)
    full_name = fields.String(allow_none=True)
    role = fields.String(required=True)
    is_active = fields.Boolean(required=True)


class SystemSummarySchema(Schema):
    """System summary"""
    id = fields.String(required=True)
    name = fields.String(required=True)
    description = fields.String(allow_none=True)
    sensitivity_level = fields.String(allow_none=True)


# ============================================================================
# ERROR RESPONSE SCHEMA
# ============================================================================

class ErrorResponseSchema(Schema):
    """Standard error response"""
    success = fields.Boolean(required=True)
    error = fields.String(required=True)
    code = fields.String(required=True)
    requestId = fields.String(required=True)
    timestamp = fields.String(required=True)


# ============================================================================
# SCHEMA INSTANCES FOR USE
# ============================================================================

task_list_schema = TaskListResponseSchema()
task_detail_schema = TaskDetailResponseSchema()
updates_seen_request = UpdatesSeenRequestSchema()
updates_seen_response = UpdatesSeenResponseSchema()
task_assessment_update = TaskAssessmentUpdateSchema()
task_mutation_response = TaskMutationResponseSchema()

evidence_list_schema = EvidenceListResponseSchema()
evidence_detail_schema = EvidenceDetailResponseSchema()
evidence_upload_request = EvidenceUploadRequestSchema()
evidence_upload_response = EvidenceUploadResponseSchema()

user_summary_schema = UserSummarySchema()
system_summary_schema = SystemSummarySchema()
