"""
SecureOps API Database Models
Comprehensive schema supporting OpenAPI v0.22 MVP endpoints
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import uuid
import hashlib

db = SQLAlchemy()

# ============================================================================
# HELPER: Many-to-Many Tables
# ============================================================================

user_system_access = db.Table(
    'user_system_access',
    db.Column('user_id', db.String(36), db.ForeignKey('users.id'), primary_key=True),
    db.Column('system_id', db.String(36), db.ForeignKey('systems.id'), primary_key=True)
)

# ============================================================================
# USER & AUTHENTICATION MODELS
# ============================================================================

class User(db.Model):
    """User model with role-based access control"""
    __tablename__ = 'users'
    
    # Primary Key & Identity
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(255))
    
    # Role & Permissions
    role = db.Column(db.String(20), default='CTV', nullable=False)  # CTV, L2, L3, L4, ADMIN
    is_active = db.Column(db.Boolean, default=True)
    
    # System Access (Many-to-Many)
    assigned_systems = db.relationship(
        'System',
        secondary=user_system_access,
        backref=db.backref('users', lazy='dynamic')
    )
    
    # Relationships
    tasks_assigned = db.relationship('Task', backref='assigned_user', lazy=True)
    investigations = db.relationship('Investigation', backref='investigator', lazy=True)
    l1_works = db.relationship('L1Work', backref='created_by_user', lazy=True)
    
    # Audit Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def get_permissions(self):
        """Return permission list for role"""
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
            'ADMIN': [
                '*'  # All permissions
            ]
        }
        return permissions_map.get(self.role, [])
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'fullName': self.full_name,
            'role': self.role,
            'isActive': self.is_active,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'lastLogin': self.last_login.isoformat() if self.last_login else None
        }


# ============================================================================
# SYSTEM & CONFIGURATION MODELS
# ============================================================================

class System(db.Model):
    """System model - represents a security system/asset group"""
    __tablename__ = 'systems'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    
    # Sensitivity Level: Public, Internal, Confidential, Top Secret
    sensitivity_level = db.Column(db.String(50), default='Confidential')
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    tasks = db.relationship('Task', backref='system', lazy=True, cascade='all, delete-orphan')
    
    # Audit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'sensitivityLevel': self.sensitivity_level,
            'isActive': self.is_active,
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }


# ============================================================================
# TASK & EVIDENCE MODELS (Core)
# ============================================================================

class Task(db.Model):
    """Task model - represents a work item/incident"""
    __tablename__ = 'tasks'
    
    # Primary Key
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Task Content
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    
    # Task Status & Priority
    status = db.Column(
        db.String(50),
        default='pending',
        nullable=False
    )  # pending, in_progress, completed, cancelled
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    
    # Assignment & System Context
    system_id = db.Column(db.String(36), db.ForeignKey('systems.id'), nullable=False, index=True)
    assigned_to = db.Column(db.String(36), db.ForeignKey('users.id'), index=True)
    
    # Assessment (CTV findings)
    assessment = db.Column(db.Text)
    
    # Concurrency Control (P0-04: ETag/If-Match support)
    version = db.Column(db.Integer, default=1)  # Increment on each update
    
    # Snapshot Watermark (P0-04: Track updates seen by CTV)
    ctv_da_xem_cap_nhat_luc = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    evidences = db.relationship('Evidence', backref='task', lazy=True, cascade='all, delete-orphan')
    investigations = db.relationship('Investigation', backref='task', lazy=True, cascade='all, delete-orphan')
    l1_works = db.relationship('L1Work', backref='task', lazy=True, cascade='all, delete-orphan')
    
    # Audit Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
    
    def to_dict(self, include_evidences=False):
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'systemId': self.system_id,
            'assignedTo': self.assigned_to,
            'assessment': self.assessment,
            'version': self.version,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_evidences:
            data['evidences'] = [e.to_dict() for e in self.evidences]
        return data


class Evidence(db.Model):
    """Evidence model - represents proof/findings attached to a task"""
    __tablename__ = 'evidences'
    
    # Primary Key
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign Key
    task_id = db.Column(db.String(36), db.ForeignKey('tasks.id'), nullable=False, index=True)
    
    # Evidence Content
    content = db.Column(db.Text)
    evidence_type = db.Column(db.String(100))  # log, screenshot, file, network_capture, etc
    
    # File Metadata (P0-05: Upload mechanism)
    file_name = db.Column(db.String(255))
    file_path = db.Column(db.String(1024))  # Local path or S3 key
    file_size_bytes = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    sha256_hash = db.Column(db.String(64), index=True)  # For integrity verification
    
    # Upload Session Tracking
    upload_id = db.Column(db.String(36), index=True)  # Temporary session ID
    upload_verified = db.Column(db.Boolean, default=False)
    
    # Source/Provenance (who/what created this evidence)
    l1_work_id = db.Column(db.String(36), db.ForeignKey('l1_works.id'), nullable=True)
    source = db.Column(db.String(50), default='manual')  # manual, l1_work, api, import
    
    # Audit
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'taskId': self.task_id,
            'content': self.content,
            'evidenceType': self.evidence_type,
            'fileName': self.file_name,
            'fileSizeBytes': self.file_size_bytes,
            'mimeType': self.mime_type,
            'sha256Hash': self.sha256_hash,
            'source': self.source,
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }


# ============================================================================
# EVIDENCE UPLOAD SESSION (P0-05: Temporary upload management)
# ============================================================================

class EvidenceUploadSession(db.Model):
    """Temporary session for file uploads before finalization"""
    __tablename__ = 'evidence_upload_sessions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Context
    task_id = db.Column(db.String(36), db.ForeignKey('tasks.id'), nullable=False, index=True)
    created_by_user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # Upload Tracking
    upload_state = db.Column(
        db.String(50),
        default='ISSUED',
        nullable=False
    )  # ISSUED, UPLOADING, UPLOADED, VERIFIED, CONSUMED, EXPIRED, REJECTED
    
    # Upload Target & Credentials (temporary, scoped)
    upload_target = db.Column(db.String(1024))  # Temporary URL or S3 presigned URL
    required_headers = db.Column(db.JSON)  # Headers client must send (auth tokens, etc)
    
    # File Verification (server-validated)
    sha256_hash = db.Column(db.String(64))
    expected_size_bytes = db.Column(db.Integer)
    actual_size_bytes = db.Column(db.Integer)
    
    # TTL & Expiration (P0-05: temporary session)
    expires_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(hours=24))
    verified_at = db.Column(db.DateTime)
    consumed_at = db.Column(db.DateTime)
    
    # Audit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def is_expired(self):
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self):
        return {
            'uploadId': self.id,
            'uploadState': self.upload_state,
            'uploadTarget': self.upload_target,
            'expectedSizeBytes': self.expected_size_bytes,
            'actualSizeBytes': self.actual_size_bytes,
            'sha256Hash': self.sha256_hash,
            'expiresAt': self.expires_at.isoformat() if self.expires_at else None,
            'verifiedAt': self.verified_at.isoformat() if self.verified_at else None,
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }


# ============================================================================
# INVESTIGATION MODELS
# ============================================================================

class Investigation(db.Model):
    """Investigation model - represents analysis/investigation context"""
    __tablename__ = 'investigations'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Context
    task_id = db.Column(db.String(36), db.ForeignKey('tasks.id'), nullable=False, index=True)
    investigator_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    
    # Investigation State
    status = db.Column(db.String(50), default='open')  # open, in_progress, closed, archived
    title = db.Column(db.String(255))
    notes = db.Column(db.Text)
    
    # Relationships
    checks = db.relationship('InvestigationCheck', backref='investigation', lazy=True, cascade='all, delete-orphan')
    excerpts = db.relationship('EvidenceExcerpt', backref='investigation', lazy=True, cascade='all, delete-orphan')
    
    # Audit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'status': self.status,
            'title': self.title,
            'investigator_id': self.investigator_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class InvestigationCheck(db.Model):
    """Investigation Check - specific check/verification within investigation"""
    __tablename__ = 'investigation_checks'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Context
    investigation_id = db.Column(db.String(36), db.ForeignKey('investigations.id'), nullable=False, index=True)
    
    # Check Details
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    check_type = db.Column(db.String(100))  # system_health, network_analysis, log_review, etc
    
    # Result
    result = db.Column(db.String(50), default='pending')  # pending, pass, fail, inconclusive
    result_notes = db.Column(db.Text)
    
    # Audit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'investigation_id': self.investigation_id,
            'title': self.title,
            'check_type': self.check_type,
            'result': self.result,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class EvidenceExcerpt(db.Model):
    """Evidence Excerpt - extracted/highlighted portion of evidence"""
    __tablename__ = 'evidence_excerpts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Context
    investigation_id = db.Column(db.String(36), db.ForeignKey('investigations.id'), nullable=False, index=True)
    evidence_id = db.Column(db.String(36), db.ForeignKey('evidences.id'), nullable=False)
    
    # Excerpt
    excerpt_text = db.Column(db.Text, nullable=False)
    excerpt_type = db.Column(db.String(100))  # quote, highlight, summary, etc
    
    # Context Reference
    line_start = db.Column(db.Integer)
    line_end = db.Column(db.Integer)
    
    # Audit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'evidence_id': self.evidence_id,
            'excerpt_text': self.excerpt_text,
            'excerpt_type': self.excerpt_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# ============================================================================
# L1 WORK MODELS (Level 1 Work Requests)
# ============================================================================

class L1Work(db.Model):
    """L1 Work - represents work to be done at system level"""
    __tablename__ = 'l1_works'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Context
    task_id = db.Column(db.String(36), db.ForeignKey('tasks.id'), nullable=False, index=True)
    created_by_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # Work Details
    title = db.Column(db.String(255), nullable=False)
    request_content = db.Column(db.Text, nullable=False)
    
    # Status
    status = db.Column(db.String(50), default='pending')  # pending, assigned, in_progress, completed, cancelled
    
    # Originating Context
    originating_context = db.Column(db.JSON)  # Task/Investigation context that sparked this L1 work
    
    # AI Origin Flag
    generated_by_ai = db.Column(db.Boolean, default=False)
    ai_draft_id = db.Column(db.String(36))  # Reference to AI draft if came from AI suggestion
    
    # Audit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'title': self.title,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# ============================================================================
# KNOWLEDGE MODELS
# ============================================================================

class Knowledge(db.Model):
    """Knowledge base item - reusable information/procedures"""
    __tablename__ = 'knowledge'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Content
    type = db.Column(db.String(100), nullable=False)  # procedure, guideline, pattern, technique
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    
    # Sensitivity & Access Control
    sensitivity = db.Column(db.String(50), default='Confidential')  # Public, Internal, Confidential, TopSecret
    
    # Lifecycle
    is_published = db.Column(db.Boolean, default=False)
    effectiveFrom = db.Column(db.DateTime)
    effectiveTo = db.Column(db.DateTime)
    verifiedAt = db.Column(db.DateTime)
    
    # Relationships
    sources = db.relationship('KnowledgeSource', backref='knowledge', lazy=True, cascade='all, delete-orphan')
    
    # Audit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'content': self.content,
            'sensitivity': self.sensitivity,
            'is_published': self.is_published,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class KnowledgeSource(db.Model):
    """Source reference for Knowledge items"""
    __tablename__ = 'knowledge_sources'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    knowledge_id = db.Column(db.String(36), db.ForeignKey('knowledge.id'), nullable=False)
    
    # Source Info
    source_type = db.Column(db.String(100))  # documentation, blog, tool, system, observation
    source_ref = db.Column(db.String(255))  # URL, document ID, etc
    title = db.Column(db.String(255))
    
    # Audit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'source_type': self.source_type,
            'source_ref': self.source_ref,
            'title': self.title
        }


# ============================================================================
# IDEMPOTENCY & AUDIT MODELS
# ============================================================================

class IdempotencyKey(db.Model):
    """Store idempotency keys to prevent duplicate operations (DEC-06)"""
    __tablename__ = 'idempotency_keys'
    
    id = db.Column(db.String(36), primary_key=True)
    
    # Request Identity
    method = db.Column(db.String(10), nullable=False)  # POST, PUT, DELETE
    path = db.Column(db.String(1024), nullable=False)
    
    # Response Caching
    response_status = db.Column(db.Integer)
    response_body = db.Column(db.JSON)
    
    # TTL
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(hours=24))
    
    def is_expired(self):
        return datetime.utcnow() > self.expires_at


class AuditLog(db.Model):
    """Audit trail for compliance & debugging"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Action Identity
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(255), nullable=False)  # task.create, evidence.upload, etc
    resource_type = db.Column(db.String(100))  # task, evidence, investigation
    resource_id = db.Column(db.String(36))
    
    # Request Details
    method = db.Column(db.String(10))  # GET, POST, PUT, DELETE
    path = db.Column(db.String(1024))
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6
    user_agent = db.Column(db.String(1024))
    
    # Result
    status_code = db.Column(db.Integer)
    error_message = db.Column(db.Text)
    
    # Audit
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'status_code': self.status_code,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
