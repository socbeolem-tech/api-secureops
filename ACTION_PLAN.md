# 📌 ACTION PLAN: BẠN CẦN LÀM GÌ NGAY HÔM NAY?

**Date**: 2026-11-06  
**For**: Bạn - để deploy API lên VPS Ubuntu 24.04  
**Time needed**: ~15-20 phút (nếu đã có VPS + code ready)

---

## ✅ CHECKLIST CHUẨN BỊ

Trước khi bắt đầu, hãy kiểm tra:

```
☐ VPS server đã có + có IP address (YOUR_VPS_IP)
☐ Bạn biết root password hoặc SSH key
☐ Source code đã sẵn sàng trong folder: d:\SOC\AI profile\Viết API\api_project
☐ Máy tính của bạn có thể SSH vào VPS
☐ PostgreSQL chưa cài trên VPS (deploy script sẽ cài)
☐ Port 80 (HTTP) chưa bị sử dụng trên VPS
```

Nếu đủ tất cả → Bắt đầu ngay!

---

## 🚀 5 BƯỚC TRIỂN KHAI (15 phút)

### ⏱️ BƯỚC 1 (2 phút): SSH vào VPS

**Trên máy local (Terminal / PowerShell / Git Bash)**:

```bash
ssh root@YOUR_VPS_IP
# Nhập mật khẩu root
```

**Kết quả**: Bạn thấy dòng prompt: `root@ubuntu:~#`

---

### ⏱️ BƯỚC 2 (3 phút): Tạo user & chuẩn bị

**Vẫn trên VPS (terminal)**:

```bash
# Cập nhật hệ thống
apt update && apt upgrade -y

# Tạo user apiuser (mật khẩu: tạo mật khẩu mạnh)
adduser apiuser

# Cấp quyền
usermod -aG sudo apiuser

# Chuyển user
su - apiuser
# Hoặc logout rồi: ssh apiuser@YOUR_VPS_IP
```

**Kết quả**: Bạn đang logged in as `apiuser`

---

### ⏱️ BƯỚC 3 (3 phút): Upload code

**Trên máy local (tạm dừng VPS terminal)**:

```bash
# Vào folder code
cd "d:\SOC\AI profile\Viết API\api_project"

# Upload toàn bộ
scp -r ./* apiuser@YOUR_VPS_IP:/home/apiuser/api_project/

# Kiểm tra
ssh apiuser@YOUR_VPS_IP "ls /home/apiuser/api_project/ | head"
```

**Kết quả**: Thấy các file như: `app.py`, `models.py`, `requirements.txt`, `deploy.sh`

---

### ⏱️ BƯỚC 4 (5-10 phút): Chạy script tự động deploy

**Quay lại VPS terminal** (hoặc SSH mới):

```bash
ssh apiuser@YOUR_VPS_IP

# Chạy script
cd /home/apiuser/api_project
chmod +x deploy.sh
./deploy.sh

# Đợi hoàn thành (~10 phút)
# Sẽ thấy: "✅ DEPLOYMENT COMPLETE!"
```

**Kết quả**: 
```
API Endpoints:
  Token: http://YOUR_VPS_IP/auth/test-token?role=CTV
  Tasks: http://YOUR_VPS_IP/api/v1/my/tasks
```

---

### ⏱️ BƯỚC 5 (2 phút): Kiểm tra

**Trên máy local (browser hoặc curl)**:

```bash
# Test health
curl http://YOUR_VPS_IP/health

# Hoặc mở browser
# http://YOUR_VPS_IP/health

# Hoặc lấy token + test tasks
TOKEN=$(curl -s http://YOUR_VPS_IP/auth/test-token?role=CTV \
  -H "Authorization: Bearer test" | jq -r '.data.token')

curl http://YOUR_VPS_IP/api/v1/my/tasks \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

**Kết quả**: Thấy JSON response ✅

---

## 🎯 BƯỚC TIẾP THEO (Sau khi deploy thành công)

### Tuần tới:

```
☐ 1. Setup domain name (nếu có)
☐ 2. Setup SSL certificate: 
     sudo certbot --nginx -d yourdomain.com
☐ 3. Configure automated backups
☐ 4. Test uploading evidence files
☐ 5. Check logs for any errors: sudo tail -f /var/log/api_error.log
```

### Tháng tới:

```
☐ 6. Setup monitoring (Prometheus/DataDog/Uptime Robot)
☐ 7. Performance testing
☐ 8. Increase Gunicorn workers if needed
☐ 9. Setup Redis caching (optional)
☐ 10. Document custom configurations
```

---

## 🆘 NẾU CÓ VẤN ĐỀ

### Script bị lỗi:
```bash
# Xem lỗi chi tiết
sudo journalctl -u api -n 50

# Hoặc check logs
sudo tail -100 /var/log/api_error.log

# Restart
sudo systemctl restart api
```

### Không kết nối được:
```bash
# Check services
sudo systemctl status api postgresql nginx

# Check ports
sudo lsof -i :80
sudo lsof -i :5000

# Restart tất cả
sudo systemctl restart api nginx postgresql
```

### Lỗi database:
```bash
# Test connection
psql -U secureops_user -h localhost -d secureops_db -c "SELECT 1"

# Check PostgreSQL status
sudo systemctl status postgresql

# Check logs
sudo tail -f /var/log/postgresql/*.log
```

### Mất kết nối SSH:
```bash
# SSH lại
ssh apiuser@YOUR_VPS_IP

# Hoặc SSH with root
ssh root@YOUR_VPS_IP
```

---

## 📊 TRACKING DEPLOYMENT

Sử dụng checklist này để track progress:

```
CHUẨN BỊ:
  ☐ VPS ready
  ☐ Code ready
  ☐ SSH access OK

TRIỂN KHAI:
  ☐ Step 1: SSH login
  ☐ Step 2: Create user & install basics
  ☐ Step 3: Upload code (check with ls)
  ☐ Step 4: Run ./deploy.sh (wait for "DEPLOYMENT COMPLETE")
  ☐ Step 5: Test health endpoint

KỲ VỌI:
  ☐ API responds on port 80
  ☐ Can get token
  ☐ Can list tasks
  ☐ Can see logs without errors
  ☐ Database connected
```

---

## 💬 GHI CHÚ QUAN TRỌNG

1. **YOUR_VPS_IP** = IP address của VPS bạn (ví dụ: `123.45.67.89`)
   - Tìm nó ở email VPS provider, hoặc SSH vào rồi chạy: `hostname -I`

2. **Mật khẩu apiuser** = Mật khẩu bạn vừa tạo
   - Ghi nhớ nó! (hoặc dùng SSH key thay thế)

3. **deploy.sh** = Script sẽ tự động cài:
   - Python 3.10+
   - PostgreSQL 15
   - Gunicorn
   - Nginx
   - Firewall
   - Tất cả dependencies

4. **Không cần cài gì thêm** = Tất cả trong script rồi!

---

## 📁 FILE THAM KHẢO

Nếu cần chi tiết, mở các file này:

| File | Dùng khi | Chứa |
|------|----------|------|
| `GETTING_STARTED.md` | Lần đầu, cần giải thích chi tiết | Step-by-step guide |
| `deploy.sh` | Tự động hóa | Script chạy tất cả |
| `post-deploy-check.sh` | Kiểm tra sau deploy | 20+ automated tests |
| `DEPLOYMENT_QUICK_REFERENCE.md` | Tra cứu lệnh nhanh | Commands + troubleshooting |
| `DEPLOYMENT_GUIDE_VPS.md` | Cần tìm hiểu sâu | Full 10-part guide |

---

## ⏰ TIMELINE DỰ KIẾN

```
Prepare:              2 minutes
SSH login:            1 minute
User setup:           2 minutes
Upload code:          3 minutes
Run deploy.sh:        10 minutes (script chạy)
Testing:              2 minutes
───────────────────────────────
TOTAL:               ~20 minutes
```

---

## ✨ SUCCESS INDICATORS

Bạn biết deploy thành công khi:

1. ✅ Script kết thúc với: "✅ DEPLOYMENT COMPLETE!"
2. ✅ `curl http://YOUR_VPS_IP/health` → trả về JSON
3. ✅ `sudo systemctl status api` → "active (running)"
4. ✅ `sudo systemctl status postgresql` → "active (running)"
5. ✅ `sudo systemctl status nginx` → "active (running)"
6. ✅ Có thể get token: `http://YOUR_VPS_IP/auth/test-token?role=CTV`
7. ✅ `/var/log/api_error.log` → không có error

---

## 🎉 DONE!

Sau khi hoàn thành 5 bước, API của bạn đã sẵn sàng!

**API address**: `http://YOUR_VPS_IP`

**Công việc tiếp theo**:
- Monitor logs hàng ngày
- Backup database thường xuyên
- Cập nhật bảo mật
- Scale up khi cần

---

## 📞 QUICK COMMANDS TO REMEMBER

```bash
# SSH vào VPS
ssh apiuser@YOUR_VPS_IP

# Check services
sudo systemctl status api postgresql nginx

# Restart API
sudo systemctl restart api

# View logs
sudo tail -f /var/log/api_error.log

# Test API
curl http://YOUR_VPS_IP/health
```

---

**READY TO DEPLOY?** 🚀

Bây giờ hãy:
1. Mở Terminal/PowerShell
2. Chạy: `ssh root@YOUR_VPS_IP`
3. Làm theo 5 bước phía trên
4. Enjoy production API! 🎉

---

Good luck! 💻

Tạo ngày: 2026-11-06
Phiên bản: 1.0
