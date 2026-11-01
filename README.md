# SecureOps API Project

## Cấu trúc Project

```
api_project/
├── app.py                 # Ứng dụng Flask chính
├── config.py             # Cấu hình ứng dụng
├── models.py             # Database models
├── routes_tasks.py       # Routes cho Tasks
├── routes_evidence.py    # Routes cho Evidence
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables
└── venv/                 # Virtual environment
```

## Thiết lập

### 1. Kích hoạt Virtual Environment

**Windows:**
```bash
cd "D:\SOC\AI profile\Viết API\api_project"
venv\Scripts\activate
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

### 2. Cài đặt Dependencies

```bash
pip install -r requirements.txt
```

### 3. Cấu hình Database

Sửa file `.env`:
```
DATABASE_URL=postgresql://your_user:your_password@localhost:5432/secureops_db
```

### 4. Chạy ứng dụng

```bash
python app.py
```

Server sẽ chạy tại: `http://localhost:5000`

## APIs Hiện có

### Tasks
- `GET /api/v1/my/tasks` - Danh sách tasks
- `GET /api/v1/tasks/{taskId}` - Chi tiết task
- `POST /api/v1/tasks` - Tạo task
- `PUT /api/v1/tasks/{taskId}` - Cập nhật task
- `DELETE /api/v1/tasks/{taskId}` - Xóa task

### Evidence
- `GET /api/v1/tasks/{taskId}/evidences` - Danh sách bằng chứng
- `POST /api/v1/tasks/{taskId}/evidences` - Thêm bằng chứng
- `DELETE /api/v1/evidences/{evidenceId}` - Xóa bằng chứng

### Health Check
- `GET /health` - Kiểm tra trạng thái server

## Test APIs

Sử dụng Postman hoặc curl:

```bash
# Get health
curl http://localhost:5000/health

# Get all tasks
curl http://localhost:5000/api/v1/my/tasks

# Create task
curl -X POST http://localhost:5000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Task 1","description":"Description","priority":"high"}'
```

## Next Steps

1. Thêm authentication (JWT)
2. Thêm validation cho input
3. Thêm logging
4. Viết unit tests
5. Deploy lên production
