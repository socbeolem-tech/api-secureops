# 📋 Phase 2: Evidence APIs Specification

**Status**: Ready to Implement  
**Target Endpoints**: MVP05, MVP06, MVP18  
**Conventions**: All 7 compliance standards from Phase 1  
**Date**: 2026-11-01  

---

## **Phase 2 Endpoints Overview**

| MVP | HTTP | Endpoint | Purpose | Status |
|-----|------|----------|---------|--------|
| **MVP05** | GET | `/api/v1/tasks/{taskId}/evidences` | List evidences for task | 📋 Spec |
| **MVP06** | GET | `/api/v1/evidences/{evidenceId}` | Evidence detail | 📋 Spec |
| **MVP18** | POST | `/api/v1/tasks/{taskId}/evidences/upload` | Create/upload evidence | 📋 Spec |

---

## **MVP05: GET /api/v1/tasks/{taskId}/evidences**

**Purpose**: List all evidences attached to a task

### **Request**
```http
GET /api/v1/tasks/123e4567-e89b-12d3-a456-426614174000/evidences?page=1&per_page=20&evidenceType=log
Authorization: Bearer <jwt>
```

### **Query Parameters**
| Param | Type | Required | Default | Purpose |
|-------|------|----------|---------|---------|
| `page` | int | ❌ | 1 | Pagination page |
| `per_page` | int | ❌ | 20 | Results per page (max 100) |
| `evidenceType` | string | ❌ | - | Filter by type (log, screenshot, file, network_capture) |
| `source` | string | ❌ | - | Filter by source (manual, l1_work, api, import) |
| `sortBy` | string | ❌ | createdAt | Sort field (createdAt, fileName, fileSizeBytes) |
| `sortOrder` | string | ❌ | desc | Order (asc, desc) |

### **Permissions Required**
- `evidence.read` (any role)
- System access verified via task.system_id

### **Successful Response (200)**
```json
{
  "success": true,
  "data": [
    {
      "id": "evidence-uuid-1",
      "taskId": "task-uuid",
      "evidenceType": "log",
      "fileName": "access_log_2026-11-01.txt",
      "fileSizeBytes": 2048,
      "mimeType": "text/plain",
      "sha256Hash": "abc123...",
      "source": "l1_work",
      "uploadVerified": true,
      "createdAt": "2026-11-01T10:30:00Z"
    },
    {
      "id": "evidence-uuid-2",
      "taskId": "task-uuid",
      "evidenceType": "screenshot",
      "fileName": "firewall_config.png",
      "fileSizeBytes": 51200,
      "mimeType": "image/png",
      "sha256Hash": "def456...",
      "source": "manual",
      "uploadVerified": true,
      "createdAt": "2026-11-01T09:15:00Z"
    }
  ],
  "meta": {
    "requestId": "req-uuid",
    "timestamp": "2026-11-01T23:40:00Z",
    "total": 2,
    "page": 1,
    "perPage": 20
  }
}
```

### **Error Responses**

**404 Not Found** (task not found OR unauthorized)
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Task not found",
    "details": null,
    "requestId": "req-uuid"
  },
  "timestamp": "2026-11-01T23:40:00Z"
}
```

**401 Unauthorized** (missing/invalid token)
```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Unauthorized",
    "details": null,
    "requestId": "req-uuid"
  },
  "timestamp": "2026-11-01T23:40:00Z"
}
```

**403 Forbidden** (lacks evidence.read permission)
```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "Insufficient permissions",
    "details": null,
    "requestId": "req-uuid"
  },
  "timestamp": "2026-11-01T23:40:00Z"
}
```

### **Implementation Notes**
- ✅ Task-scoped 404: Unauthorized → 404 (not 403)
- ✅ Pagination: Default 20, max 100 per page
- ✅ Filtering: Optional evidenceType, source filters
- ✅ Sorting: By createdAt desc default
- ✅ Concurrency: No ETag needed (read-only)
- ✅ Idempotency: No Idempotency-Key needed (read-only)

---

## **MVP06: GET /api/v1/evidences/{evidenceId}**

**Purpose**: Get full evidence detail with file metadata

### **Request**
```http
GET /api/v1/evidences/evidence-uuid-123
Authorization: Bearer <jwt>
```

### **Permissions Required**
- `evidence.read` (any role)
- System access via evidence.task.system_id

### **Successful Response (200)**
```json
{
  "success": true,
  "data": {
    "id": "evidence-uuid-123",
    "taskId": "task-uuid-456",
    "content": "2026-11-01 10:30:45 ERROR: Authentication failed from 192.168.1.100",
    "evidenceType": "log",
    "fileName": "access_log_2026-11-01.txt",
    "fileSizeBytes": 2048,
    "mimeType": "text/plain",
    "sha256Hash": "abc123def456ghi789jkl012mnopqr",
    "uploadId": "upload-session-uuid",
    "uploadVerified": true,
    "source": "l1_work",
    "l1WorkId": "l1work-uuid-or-null",
    "createdAt": "2026-11-01T10:30:00Z",
    "updatedAt": "2026-11-01T10:30:00Z"
  },
  "meta": {
    "requestId": "req-uuid",
    "timestamp": "2026-11-01T23:40:00Z"
  }
}
```

### **Response Headers**
```http
ETag: "1"
```

### **Error Responses**

**404 Not Found** (evidence not found OR unauthorized)
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Evidence not found",
    "details": null,
    "requestId": "req-uuid"
  },
  "timestamp": "2026-11-01T23:40:00Z"
}
```

### **Implementation Notes**
- ✅ ETag header: Version-based (like Task concurrency control)
- ✅ Task-scoped 404: Unauthorized → 404 (not 403)
- ✅ Full metadata: fileName, fileSizeBytes, sha256Hash for integrity
- ✅ Content field: Full log/text content if available
- ✅ Source tracking: manual, l1_work, api, import

---

## **MVP18: POST /api/v1/tasks/{taskId}/evidences/upload**

**Purpose**: Create and upload evidence file for task

### **Request**
```http
POST /api/v1/tasks/task-uuid-123/evidences/upload
Authorization: Bearer <jwt>
Idempotency-Key: upload-key-xyz
Content-Type: multipart/form-data

Form Fields:
- file: (binary file data)
- evidenceType: "log" | "screenshot" | "file" | "network_capture"
- fileName: "access_log_2026-11-01.txt" (optional, defaults to file.name)
- content: "Log content or metadata" (optional)
```

### **Permissions Required**
- `evidence.upload` (CTV, L2, L3, L4, ADMIN)
- System access via task.system_id

### **Successful Response (201)**
```json
{
  "success": true,
  "data": {
    "evidenceId": "evidence-uuid-new",
    "taskId": "task-uuid-123",
    "uploadId": "upload-session-uuid",
    "fileName": "access_log_2026-11-01.txt",
    "fileSizeBytes": 2048,
    "mimeType": "text/plain",
    "sha256Hash": "abc123def456ghi789jkl012mnopqr",
    "evidenceType": "log",
    "uploadVerified": false,
    "uploadState": "UPLOADED",
    "uploadedAt": "2026-11-01T23:40:00Z"
  },
  "meta": {
    "requestId": "req-uuid",
    "timestamp": "2026-11-01T23:40:00Z"
  }
}
```

### **Error Responses**

**400 Bad Request** (missing/invalid fields)
```json
{
  "success": false,
  "error": {
    "code": "BAD_REQUEST",
    "message": "Missing required field: file",
    "details": {
      "field": "file",
      "reason": "Multipart file is required"
    },
    "requestId": "req-uuid"
  },
  "timestamp": "2026-11-01T23:40:00Z"
}
```

**413 Payload Too Large** (file exceeds max size)
```json
{
  "success": false,
  "error": {
    "code": "PAYLOAD_TOO_LARGE",
    "message": "File exceeds maximum size of 100MB",
    "details": {
      "maxSizeBytes": 104857600,
      "receivedSizeBytes": 157286400
    },
    "requestId": "req-uuid"
  },
  "timestamp": "2026-11-01T23:40:00Z"
}
```

**404 Not Found** (task not found OR unauthorized)
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Task not found",
    "details": null,
    "requestId": "req-uuid"
  },
  "timestamp": "2026-11-01T23:40:00Z"
}
```

**409 Conflict** (Idempotency-Key duplicate)
```json
{
  "success": false,
  "error": {
    "code": "CONFLICT",
    "message": "Request already processed",
    "details": {
      "uploadId": "upload-session-uuid",
      "processedAt": "2026-11-01T23:39:00Z"
    },
    "requestId": "req-uuid"
  },
  "timestamp": "2026-11-01T23:40:00Z"
}
```

### **Implementation Notes**
- ✅ Idempotency-Key: Required header for replay protection (DEC-06)
- ✅ Multipart file upload: Binary file in form data
- ✅ File validation: Max 100MB, MIME type check
- ✅ SHA256 hash: Computed and stored for integrity verification
- ✅ Upload state: UPLOADED → VERIFIED (async validation)
- ✅ Task-scoped 404: Unauthorized → 404 (not 403)

---

## **MVP05-06-18 Design Decisions**

### **1. Evidence Type Categories** (evidenceType)
| Type | Example | Description |
|------|---------|-------------|
| `log` | access_log.txt | Log files from systems |
| `screenshot` | firewall_config.png | Screenshots of configs/findings |
| `file` | report.pdf | General files (documents, etc) |
| `network_capture` | traffic.pcap | Network packet captures |

### **2. Evidence Source Tracking** (source)
| Source | Created By | Use Case |
|--------|-----------|----------|
| `manual` | User via UI | User uploads evidence manually |
| `l1_work` | L1 automation | Automated evidence collection |
| `api` | External API | Third-party integration |
| `import` | Bulk import | Bulk evidence import from SIEM |

### **3. Upload State Machine** (uploadState)
```
ISSUED → UPLOADING → UPLOADED → VERIFIED → CONSUMED
                                           ↓
                                      REJECTED (if invalid)
                                           ↓
                                        EXPIRED (after 24h)
```

### **4. File Size Limits** (maxUploadSizeBytes)
- Default: 100MB
- Configurable per environment
- Checked on upload, rejected if exceeded

### **5. SHA256 Hash** (for integrity)
- Computed on upload
- Stored for verification
- Used in evidence chain of custody

### **6. Pagination Defaults**
- Default page: 1
- Default per_page: 20
- Maximum per_page: 100

---

## **Compliance with Phase 1 Conventions**

| Convention | Implementation |
|-----------|-----------------|
| ✅ **Versioning** | `/api/v1` + camelCase fields (evidenceType, fileName, etc) |
| ✅ **Naming** | lowercase-kebab resources (evidences), action `/upload` |
| ✅ **Response Envelope** | `{success, data, meta: {requestId, timestamp}}` |
| ✅ **Error Envelope** | `{error: {code, message, details, requestId}}` |
| ✅ **Concurrency** | ETag header on GET, no If-Match (evidence immutable after upload) |
| ✅ **Task-Scoped Security** | Unauthorized → 404 (not 403) |
| ✅ **Idempotency** | Idempotency-Key required on POST /upload |
| ✅ **External IdP** | JWT token from Authorization header |

---

## **Database Model Requirements**

### **Evidence Model** (Already exists in models.py)
```python
class Evidence(db.Model):
    id              # UUID primary key
    task_id         # Foreign key to Task
    content         # Text content
    evidence_type   # log, screenshot, file, network_capture
    file_name       # Uploaded file name
    file_path       # Local/S3 path
    file_size_bytes # File size
    mime_type       # MIME type
    sha256_hash     # Integrity hash
    upload_id       # Session ID
    upload_verified # Boolean
    source          # manual, l1_work, api, import
    l1_work_id      # Reference to L1Work
    created_at      # Timestamp
    updated_at      # Timestamp
```

### **EvidenceUploadSession Model** (For tracking uploads)
```python
class EvidenceUploadSession(db.Model):
    id              # UUID primary key
    task_id         # Foreign key to Task
    upload_state    # ISSUED, UPLOADING, UPLOADED, VERIFIED, CONSUMED, REJECTED, EXPIRED
    upload_target   # URL or S3 key
    expires_at      # Expiration timestamp
    verified_at     # Verification timestamp
    created_at      # Timestamp
```

---

## **Implementation Checklist**

### **Routes**
- [ ] MVP05: GET /api/v1/tasks/{taskId}/evidences (list with pagination/filtering)
- [ ] MVP06: GET /api/v1/evidences/{evidenceId} (detail with ETag)
- [ ] MVP18: POST /api/v1/tasks/{taskId}/evidences/upload (multipart file upload)

### **Schemas** (Marshmallow validation)
- [ ] EvidenceSummarySchema (list items)
- [ ] EvidenceDetailSchema (full detail)
- [ ] EvidenceUploadRequestSchema (multipart validation)
- [ ] EvidenceUploadResponseSchema (response structure)

### **Utilities**
- [ ] Handle multipart file upload
- [ ] Compute SHA256 hash
- [ ] Validate file size/MIME type
- [ ] Store file to disk/S3

### **Error Handling**
- [ ] 400: Missing/invalid fields
- [ ] 401: Unauthorized
- [ ] 403: Forbidden (insufficient permissions)
- [ ] 404: Task/evidence not found (task-scoped masking)
- [ ] 409: Idempotency key conflict
- [ ] 413: File too large
- [ ] 422: Validation error
- [ ] 500: Internal error

### **Testing**
- [ ] Test list with pagination/filtering
- [ ] Test detail with ETag
- [ ] Test upload with valid file
- [ ] Test upload with oversized file
- [ ] Test upload idempotency (retry with same key)
- [ ] Test task-scoped 404 (unauthorized)
- [ ] Test camelCase response fields

---

## **Next Steps**

1. ✅ Create Phase 2 specification (THIS DOCUMENT)
2. 🔧 Implement routes_evidence.py with all 3 endpoints
3. 🔧 Add schemas.py validation for Evidence models
4. 🧪 Test all endpoints via Postman/curl
5. 📝 Commit Phase 2 implementation
6. 🎯 Phase 3: Investigation APIs (MVP08-12)

---

**Generated**: 2026-11-01  
**Status**: Ready for Implementation ✅
