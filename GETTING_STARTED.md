# 🚀 GETTING STARTED: Triển Khai lên VPS

**Document này hướng dẫn từng bước cơ bản nhất để đưa code lên VPS và chạy**

---

## ✅ CÓ NHỮNG GÌ?

Trước khi bắt đầu, hãy chắc chắn bạn có:

- ✅ VPS server (Ubuntu 24.04 LTS, IP: YOUR_VPS_IP)
- ✅ Root password hoặc SSH key access
- ✅ Toàn bộ source code trong folder `api_project`
- ✅ Terminal/SSH client (PuTTY, Git Bash, hoặc terminal native)

---

## 🔑 BƯỚC 1: KẾT NỐI VPS BẰNG SSH

### Từ Mac / Linux:
```bash
ssh root@YOUR_VPS_IP
# Nhập mật khẩu root
```

### Từ Windows (PowerShell):
```powershell
ssh root@YOUR_VPS_IP
# Nếu không có ssh, cài Git Bash hoặc dùng PuTTY
```

### Sau khi login thành công:
```bash
# Bạn sẽ thấy:
root@ubuntu:~# 
```

---

## 👤 BƯỚC 2: TẠO USER AN TOÀN (Bắt buộc cho production)

```bash
# Tạo user mới
adduser apiuser

# Hỏi mật khẩu - tạo mật khẩu mạnh
# Tên thật, số điện thoại, v.v. - nhấn Enter để bỏ qua

# Cấp quyền sudo
usermod -aG sudo apiuser

# Chuyển sang user mới
su - apiuser
# Hoặc logout rồi ssh lại: ssh apiuser@YOUR_VPS_IP
```

---

## 📦 BƯỚC 3: UPLOAD CODE LÊN VPS

### Cách A: Dùng SCP (Từ máy local - TỪ TERMINAL MÁY LOCAL, KHÔNG PHẢI VPS)

```bash
# Vào folder chứa code
cd ~/path/to/api_project

# Upload toàn bộ
scp -r ./* apiuser@YOUR_VPS_IP:/home/apiuser/api_project/

# Hoặc nếu folder chưa tồn tại trên VPS:
scp -r ./* apiuser@YOUR_VPS_IP:/home/apiuser/
mv /home/apiuser/api_project /home/apiuser/api_project_backup
mkdir /home/apiuser/api_project
scp -r ./* apiuser@YOUR_VPS_IP:/home/apiuser/api_project/
```

### Cách B: Dùng Git (Nếu code đã trên GitHub)

```bash
# Từ VPS:
cd /home/apiuser
git clone https://github.com/YOUR_USERNAME/api_project.git
cd api_project
```

### Xác nhận code đã upload:
```bash
# Từ VPS:
ls -la /home/apiuser/api_project/
# Bạn sẽ thấy: app.py, models.py, routes_*.py, requirements.txt, etc.
```

---

## 🚀 BƯỚC 4: TRIỂN KHAI TỰ ĐỘNG (CHỈ 1 LỆnh)

Cách **NHANH NHẤT** là dùng script tự động:

```bash
# Từ VPS, đăng nhập bằng user apiuser
ssh apiuser@YOUR_VPS_IP

# Chạy script triển khai
cd /home/apiuser/api_project
chmod +x deploy.sh
./deploy.sh

# Script sẽ tự động:
# ✅ Cài Python, PostgreSQL, Nginx
# ✅ Tạo database
# ✅ Cài dependencies
# ✅ Cấu hình Gunicorn
# ✅ Cấu hình Nginx
# ⏱️ Mất khoảng 5-10 phút
```

### Nếu script hoàn thành thành công:
```
✅ DEPLOYMENT COMPLETE!
API Endpoints:
  Health: http://YOUR_VPS_IP/health
  Tasks: http://YOUR_VPS_IP/api/v1/my/tasks
```

---

## 🧪 BƯỚC 5: KIỂM TRA TRIỂN KHAI

### Test trực tiếp từ VPS:
```bash
# Kiểm tra health endpoint
curl http://127.0.0.1/health

# Response sẽ tương tự:
# {"status":"ok"}
```

### Test từ máy local (trên browser hoặc curl):
```bash
# Mở browser
http://YOUR_VPS_IP/health

# Hoặc dùng curl:
curl http://YOUR_VPS_IP/health

# Response:
# {"status":"ok"}
```

### Test API endpoint:
```bash
# Từ máy local:
TOKEN=$(curl -s http://YOUR_VPS_IP/auth/test-token?role=CTV \
  -H "Authorization: Bearer test" | jq -r '.data.token')

curl http://YOUR_VPS_IP/api/v1/my/tasks \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

---

## 📋 BƯỚC 6: KIỂM TRA SERVICES

```bash
# Check tất cả services
sudo systemctl status api postgresql nginx

# Check từng cái:
sudo systemctl status api          # API Flask
sudo systemctl status postgresql   # Database
sudo systemctl status nginx        # Web server

# Tất cả phải là: active (running) ✅
```

---

## 📝 BƯỚC 7: XEM LOGS (nếu có vấn đề)

```bash
# API logs
sudo tail -f /var/log/api_error.log
sudo tail -f /var/log/api_access.log

# Nginx logs
sudo tail -f /var/log/nginx/error.log

# Database logs
sudo tail -f /var/log/postgresql/*.log

# Application logs (realtime)
sudo journalctl -u api -f
```

---

## ✨ HOÀN THÀNH!

Nếu tất cả hoạt động bình thường, bạn đã triển khai thành công!

### API của bạn hiện có sẵn tại:

```
http://YOUR_VPS_IP
```

### Các endpoint:

| Endpoint | Mục đích |
|----------|---------|
| `/health` | Kiểm tra server hoạt động |
| `/auth/test-token?role=CTV` | Lấy token test |
| `/api/v1/my/tasks` | Liệt kê tasks |
| `/api/v1/tasks/{id}` | Chi tiết task |
| `/api/v1/tasks/{id}/evidences` | Liệt kê evidence |
| `/api/v1/tasks/{id}/evidences/upload` | Upload file |

---

## 🆘 CÓ VẤN ĐỀ?

### ❌ "Connection refused"
```bash
# Check services
sudo systemctl status api

# Nếu chưa chạy, start nó
sudo systemctl start api

# Restart tất cả
sudo systemctl restart api nginx postgresql
```

### ❌ "502 Bad Gateway"
```bash
# Check Nginx config
sudo nginx -t

# Restart
sudo systemctl restart nginx api
```

### ❌ "Database connection failed"
```bash
# Check PostgreSQL
sudo systemctl status postgresql

# Test connection
psql -U secureops_user -h localhost -d secureops_db -c "SELECT 1"
```

### ❌ Logs không có gì
```bash
# Check file permissions
ls -la /home/apiuser/api_project/

# Fix permissions
sudo chown -R apiuser:apiuser /home/apiuser/api_project
chmod 755 /home/apiuser/api_project
```

---

## 🔍 THAM KHẢO THÊM

- **Chi tiết đầy đủ**: Xem `DEPLOYMENT_GUIDE_VPS.md`
- **Lệnh nhanh**: Xem `DEPLOYMENT_QUICK_REFERENCE.md`
- **Kiểm tra sau triển khai**: Chạy `post-deploy-check.sh`

---

## 🛠️ COMMANDS THƯỜNG DÙNG

```bash
# Restart API
sudo systemctl restart api

# View logs
sudo tail -50 /var/log/api_error.log

# Stop/Start Nginx
sudo systemctl stop nginx
sudo systemctl start nginx

# Check if port is open
sudo lsof -i :80
sudo lsof -i :5000

# SSH vào VPS
ssh apiuser@YOUR_VPS_IP

# Upload file
scp -r ./folder apiuser@YOUR_VPS_IP:/home/apiuser/

# Connect to database
psql -U secureops_user -h localhost -d secureops_db
```

---

## 📞 TIẾP THEO

Sau khi API chạy bình thường:

1. **Setup SSL** (Khi có domain)
   ```bash
   sudo certbot --nginx -d yourdomain.com
   ```

2. **Backup database** (Hàng ngày)
   ```bash
   pg_dump -U secureops_user secureops_db | gzip > backup_$(date +%Y%m%d).sql.gz
   ```

3. **Monitor logs**
   - Kiểm tra logs thường xuyên
   - Setup alerts

4. **Performance tuning**
   - Tăng Gunicorn workers
   - Optimize PostgreSQL

---

## ✅ CHECKLIST TRIỂN KHAI

```
☐ SSH vào VPS
☐ Tạo user apiuser
☐ Upload code
☐ Chạy ./deploy.sh
☐ Kiểm tra services
☐ Test API health
☐ Xem logs có lỗi không
☐ Backup database
☐ Setup monitoring (optional)
☐ Setup SSL (khi có domain)
```

---

## 🎉 XONG!

Chúc mừng! API của bạn đã lên production! 🚀

Nếu có vấn đề, hãy:
1. Xem logs: `sudo tail -f /var/log/api_error.log`
2. Check services: `sudo systemctl status api`
3. Kiểm tra database: `psql -U secureops_user -d secureops_db -c "\dt"`

Happy coding! 💻
