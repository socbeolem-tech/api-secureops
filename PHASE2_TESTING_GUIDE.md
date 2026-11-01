# 🧪 Phase 2 Testing Guide - Evidence APIs

**Status**: ✅ Phase 2 Implementation Complete  
**Date**: 2026-11-01  
**Coverage**: MVP05, MVP06, MVP18  

---

## **Quick Start - Testing Phase 2 Endpoints**

### **1️⃣ Generate Test Token**

```bash
# PowerShell
$token = (Invoke-WebRequest -Uri "http://localhost:5000/auth/test-token?role=CTV" `
  -Headers @{"Authorization"="Bearer test"} `
  -Method GET).Content | ConvertFrom-Json | Select-Object -ExpandProperty data | Select-Object -ExpandProperty token

# Linux/Mac
token=$(curl -s http://localhost:5000/auth/test-token?role=CTV -H "Authorization: Bearer test" | jq -r '.data.token')
```

---

## **MVP05: GET /api/v1/tasks/{taskId}/evidences - List Evidences**

**Purpose**: Get all evidences attached to a task with pagination and filtering

### **Test 1: List evidences (no filter)**

```bash
# PowerShell
$taskId = "786ed2b9-377e-4ea0-9ff6-5bd5250648d4"  # From seed data
Invoke-WebRequest -Uri "http://localhost:5000/api/v1/tasks/$taskId/evidences?page=1&per_page=20" `
  -Headers @{"Authorization"="Bearer $token"} `
  -Method GET | Select-Object -ExpandProperty Content | ConvertFrom-Json | ConvertTo-Json -Depth 10

# curl
curl http://localhost:5000/api/v1/tasks/$taskId/evidences \
  -H "Authorization: Bearer $token" \
  -H "Content-Type: application/json"
```

**Expected Response (200)**:
```json
{
  "success": true,
  "data": [
    {
      "id": "evidence-uuid",
      "taskId": "task-uuid",
      "evidenceType": "log",
      "fileName": "access_log.txt",
      "fileSizeBytes": 2048,
      "mimeType": "text/plain",
      "sha256Hash": "abc123...",
      "source": "manual",
      "uploadVerified": true,
      "createdAt": "2026-11-01T10:30:00Z"
    }
  ],
  "meta": {
    "requestId": "req-uuid",
    "timestamp": "2026-11-01T23:45:00Z",
    "total": 1,
    "page": 1,
    "perPage": 20
  }
}
```

### **Test 2: Filter by evidenceType**

```bash
curl "http://localhost:5000/api/v1/tasks/$taskId/evidences?evidenceType=log" \
  -H "Authorization: Bearer $token"
```

### **Test 3: Sorting**

```bash
# Sort by file size, ascending
curl "http://localhost:5000/api/v1/tasks/$taskId/evidences?sortBy=fileSizeBytes&sortOrder=asc" \
  -H "Authorization: Bearer $token"
```

### **Test 4: Unauthorized Access (404 Masking)**

```bash
# Create invalid token for different system
$badToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."  # Invalid token

curl "http://localhost:5000/api/v1/tasks/$taskId/evidences" \
  -H "Authorization: Bearer $badToken"
```

**Expected Response (404)** - Security masking (not 403):
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Task not found",
    "details": null,
    "requestId": "req-uuid"
  },
  "timestamp": "2026-11-01T23:45:00Z"
}
```

---

## **MVP06: GET /api/v1/evidences/{evidenceId} - Get Evidence Detail**

**Purpose**: Get full evidence detail with file metadata and ETag header

### **Test 1: Get evidence detail**

First, upload evidence using MVP18, then use the returned `evidenceId`:

```bash
# PowerShell
$evidenceId = "evidence-uuid-from-upload"
Invoke-WebRequest -Uri "http://localhost:5000/api/v1/evidences/$evidenceId" `
  -Headers @{"Authorization"="Bearer $token"} `
  -Method GET | Select-Object -ExpandProperty Content, Headers

# curl
curl "http://localhost:5000/api/v1/evidences/$evidenceId" \
  -H "Authorization: Bearer $token" \
  -v
```

**Expected Response (200) with ETag**:
```http
HTTP/1.1 200 OK
ETag: "1"
Content-Type: application/json

{
  "success": true,
  "data": {
    "id": "evidence-uuid",
    "taskId": "task-uuid",
    "content": "Log content here...",
    "evidenceType": "log",
    "fileName": "access_log.txt",
    "fileSizeBytes": 2048,
    "mimeType": "text/plain",
    "sha256Hash": "abc123def456ghi789...",
    "uploadId": "upload-session-uuid",
    "uploadVerified": true,
    "source": "manual",
    "l1WorkId": null,
    "createdAt": "2026-11-01T10:30:00Z",
    "updatedAt": "2026-11-01T10:30:00Z"
  },
  "meta": {
    "requestId": "req-uuid",
    "timestamp": "2026-11-01T23:45:00Z"
  }
}
```

### **Test 2: ETag Header Present**

```bash
# Verify ETag header is returned
curl -i "http://localhost:5000/api/v1/evidences/$evidenceId" \
  -H "Authorization: Bearer $token" | grep -i etag
```

Expected: `ETag: "1"` (version-based)

### **Test 3: Not Found**

```bash
curl "http://localhost:5000/api/v1/evidences/invalid-uuid" \
  -H "Authorization: Bearer $token"
```

**Expected (404)**:
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Evidence not found",
    "details": null,
    "requestId": "req-uuid"
  },
  "timestamp": "2026-11-01T23:45:00Z"
}
```

---

## **MVP18: POST /api/v1/tasks/{taskId}/evidences/upload - Upload Evidence**

**Purpose**: Upload file evidence with metadata

### **Test 1: Upload a text file**

Create test file:
```bash
# Windows PowerShell
"This is a test log file" | Out-File -FilePath "test_evidence.txt" -Encoding UTF8

# bash
echo "This is a test log file" > test_evidence.txt
```

Upload:
```bash
# PowerShell
$filePath = "test_evidence.txt"
$taskId = "786ed2b9-377e-4ea0-9ff6-5bd5250648d4"

$fileContent = [System.IO.File]::ReadAllBytes($filePath)
$boundary = [System.Guid]::NewGuid().ToString()
$body = @"
--$boundary
Content-Disposition: form-data; name="file"; filename="test_evidence.txt"
Content-Type: text/plain

Test log content here...
--$boundary
Content-Disposition: form-data; name="evidenceType"

log
--$boundary
Content-Disposition: form-data; name="fileName"

test_access_log.txt
--$boundary
Content-Disposition: form-data; name="content"

Access denied from 192.168.1.100
--$boundary--
"@

Invoke-WebRequest -Uri "http://localhost:5000/api/v1/tasks/$taskId/evidences/upload" `
  -Method POST `
  -Headers @{
    "Authorization" = "Bearer $token"
    "Idempotency-Key" = [System.Guid]::NewGuid().ToString()
  } `
  -ContentType "multipart/form-data; boundary=$boundary" `
  -Body $body

# curl
curl -X POST "http://localhost:5000/api/v1/tasks/$taskId/evidences/upload" \
  -H "Authorization: Bearer $token" \
  -H "Idempotency-Key: $(uuidgen)" \
  -F "file=@test_evidence.txt" \
  -F "evidenceType=log" \
  -F "fileName=test_access_log.txt" \
  -F "content=Access denied from 192.168.1.100"
```

**Expected Response (201)**:
```json
{
  "success": true,
  "data": {
    "evidenceId": "evidence-uuid-new",
    "taskId": "task-uuid",
    "fileName": "test_access_log.txt",
    "fileSizeBytes": 24,
    "mimeType": "text/plain",
    "sha256Hash": "abc123def456ghi789jkl012mnopqr",
    "evidenceType": "log",
    "uploadVerified": true,
    "uploadedAt": "2026-11-01T23:46:00Z"
  },
  "meta": {
    "requestId": "req-uuid",
    "timestamp": "2026-11-01T23:46:00Z"
  }
}
```

### **Test 2: Idempotency-Key Retry**

Upload same file with same Idempotency-Key:

```bash
# Use SAME Idempotency-Key as before
curl -X POST "http://localhost:5000/api/v1/tasks/$taskId/evidences/upload" \
  -H "Authorization: Bearer $token" \
  -H "Idempotency-Key: same-key-as-before" \
  -F "file=@test_evidence.txt" \
  -F "evidenceType=log"
```

**Expected (201)** - Returns cached response, no duplicate created:
```json
{
  "success": true,
  "data": {
    "evidenceId": "evidence-uuid-new",  // SAME as before
    "taskId": "task-uuid",
    ...
  },
  "meta": {...}
}
```

### **Test 3: File Size Limit**

Create large file > 100MB:

```bash
# Create 101MB file
dd if=/dev/zero of=large_file.bin bs=1M count=101

# Upload
curl -X POST "http://localhost:5000/api/v1/tasks/$taskId/evidences/upload" \
  -H "Authorization: Bearer $token" \
  -H "Idempotency-Key: $(uuidgen)" \
  -F "file=@large_file.bin" \
  -F "evidenceType=file"
```

**Expected (413)**:
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
  "timestamp": "2026-11-01T23:46:00Z"
}
```

### **Test 4: Missing File**

```bash
curl -X POST "http://localhost:5000/api/v1/tasks/$taskId/evidences/upload" \
  -H "Authorization: Bearer $token" \
  -H "Idempotency-Key: $(uuidgen)" \
  -F "evidenceType=log"
```

**Expected (422)**:
```json
{
  "success": false,
  "error": {
    "code": "UNPROCESSABLE_ENTITY",
    "message": "Missing required field: file",
    "details": null,
    "requestId": "req-uuid"
  },
  "timestamp": "2026-11-01T23:46:00Z"
}
```

### **Test 5: Invalid evidenceType**

```bash
curl -X POST "http://localhost:5000/api/v1/tasks/$taskId/evidences/upload" \
  -H "Authorization: Bearer $token" \
  -H "Idempotency-Key: $(uuidgen)" \
  -F "file=@test_evidence.txt" \
  -F "evidenceType=invalid_type"
```

**Expected (422)**:
```json
{
  "success": false,
  "error": {
    "code": "UNPROCESSABLE_ENTITY",
    "message": "Invalid evidenceType. Must be one of: log, screenshot, file, network_capture",
    "details": null,
    "requestId": "req-uuid"
  },
  "timestamp": "2026-11-01T23:46:00Z"
}
```

---

## **Testing Checklist**

| Test | Endpoint | Expected | Status |
|------|----------|----------|--------|
| ✅ List evidences | MVP05 | 200 camelCase data | Ready |
| ✅ Filter by type | MVP05 | 200 filtered data | Ready |
| ✅ Pagination | MVP05 | 200 with page/perPage | Ready |
| ✅ Unauthorized 404 | MVP05 | 404 (not 403) | Ready |
| ✅ Get detail | MVP06 | 200 with ETag header | Ready |
| ✅ Not found | MVP06 | 404 Not found | Ready |
| ✅ Upload file | MVP18 | 201 created | Ready |
| ✅ Idempotency retry | MVP18 | 201 cached response | Ready |
| ✅ File too large | MVP18 | 413 Payload too large | Ready |
| ✅ Missing file | MVP18 | 422 Validation error | Ready |
| ✅ Invalid type | MVP18 | 422 Validation error | Ready |

---

## **Next Steps**

1. 🧪 Run through all tests above to verify functionality
2. 📊 Document any issues found
3. 🎯 Phase 3: Investigation APIs (MVP08-12)
4. 📚 Phase 4: Knowledge/AI APIs (MVP07, 09, 13-14)
5. 🏢 Phase 5: L1 Work APIs (MVP15-17)

---

**Generated**: 2026-11-01  
**Phase 2 Status**: ✅ COMPLETE AND READY FOR TESTING
