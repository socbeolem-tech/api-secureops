# 📚 QUICK REFERENCE: Lệnh Triển Khai VPS

**VPS Details**: Ubuntu 24.04 LTS | 2GB RAM | IP-based (no domain yet)

---

## 🚀 ĐỀ NGHỊ: TRIỂN KHAI NHANH (5 PHÚT)

Nếu đã có file `deploy.sh`, chạy một lệnh duy nhất trên VPS:

```bash
# Từ trên VPS (as apiuser)
cd /home/apiuser/api_project
chmod +x deploy.sh
./deploy.sh

# Hoặc từ máy local
ssh apiuser@YOUR_VPS_IP "cd /home/apiuser/api_project && bash deploy.sh"
```

✅ Lệnh này sẽ tự động làm tất cả!

---

## 📋 BƯỚC BỘ TÁCH (Nếu chạy manual)

### 1️⃣  Chuẩn bị VPS
```bash
# SSH vào VPS
ssh root@YOUR_VPS_IP

# Cập nhật & cài tools
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.10 python3.10-venv python3-pip postgresql postgresql-contrib nginx git curl

# Tạo user không phải root (bảo mật)
sudo adduser apiuser
su - apiuser

# Thiết lập firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2️⃣  Upload code từ máy local
```bash
# TỪ MÁY LOCAL (chứ không phải VPS)
scp -r ./api_project/* apiuser@YOUR_VPS_IP:/home/apiuser/api_project/
```

### 3️⃣  Cài đặt PostgreSQL
```bash
# VÀO VPS
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Tạo DB & user
sudo -u postgres psql << 'SQL'
CREATE DATABASE secureops_db;
CREATE USER secureops_user WITH PASSWORD 'scopATAAI@2026';
GRANT ALL PRIVILEGES ON DATABASE secureops_db TO secureops_user;
\c secureops_db
GRANT ALL ON SCHEMA public TO secureops_user;
\q
SQL
```

### 4️⃣  Cài Python & Dependencies
```bash
cd /home/apiuser/api_project
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5️⃣  Cấu hình Environment
```bash
cat > .env << 'EOF'
FLASK_ENV=production
FLASK_APP=app.py
DATABASE_URL=postgresql://secureops_user:scopATAAI@2026@localhost:5432/secureops_db
JWT_SECRET_KEY=$(openssl rand -hex 32)
UPLOAD_DIR=/home/apiuser/api_project/uploads
MAX_UPLOAD_SIZE_MB=100
EOF

mkdir -p uploads
chmod 755 uploads
```

### 6️⃣  Chạy Migrations (nếu có)
```bash
source venv/bin/activate
alembic upgrade head

# Hoặc test connection
python3 -c "from app import create_app; app = create_app('production'); print('✅ OK')"
```

### 7️⃣  Cài Gunicorn & Tạo Service
```bash
source venv/bin/activate
pip install gunicorn==21.2.0

# Tạo systemd service
sudo tee /etc/systemd/system/api.service > /dev/null << 'SERVICE'
[Unit]
Description=SecureOps API
After=network.target

[Service]
User=apiuser
WorkingDirectory=/home/apiuser/api_project
Environment="PATH=/home/apiuser/api_project/venv/bin"
ExecStart=/home/apiuser/api_project/venv/bin/gunicorn --bind=127.0.0.1:5000 --workers=2 app:app
Restart=always

[Install]
WantedBy=multi-user.target
SERVICE

sudo systemctl daemon-reload
sudo systemctl enable api
sudo systemctl start api
```

### 8️⃣  Cấu hình Nginx
```bash
# Lấy IP VPS
SERVER_IP=$(hostname -I | awk '{print $1}')

# Tạo Nginx config
sudo tee /etc/nginx/sites-available/api > /dev/null << EOF
server {
    listen 80;
    server_name $SERVER_IP;
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -s /etc/nginx/sites-available/api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx
```

---

## 🧪 KIỂM TRA TRIỂN KHAI

```bash
# ✅ 1. Kiểm tra services
sudo systemctl status api postgresql nginx

# ✅ 2. Kiểm tra port
curl http://127.0.0.1:5000/health

# ✅ 3. Test qua Nginx
curl http://127.0.0.1/health

# ✅ 4. Xem logs
sudo tail -f /var/log/api_error.log
sudo tail -f /var/log/nginx/error.log
```

---

## 📊 QUẢN LÝ SERVICES

```bash
# Khởi động/Dừng/Restart
sudo systemctl {start|stop|restart|status} api
sudo systemctl {start|stop|restart|status} postgresql
sudo systemctl {start|stop|restart|status} nginx

# Xem logs realtime
sudo journalctl -u api -f
sudo tail -f /var/log/api_error.log /var/log/api_access.log

# Kiểm tra process
ps aux | grep gunicorn
ps aux | grep nginx
```

---

## 🔄 BACKUP & RESTORE DATABASE

```bash
# 💾 BACKUP (Auto)
pg_dump -U secureops_user -h localhost secureops_db | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# 📥 RESTORE từ backup
gunzip < backup_20261106_120000.sql.gz | psql -U secureops_user -h localhost secureops_db

# 🔄 BACKUP TỰ ĐỘNG HÀNG NGÀY (Crontab)
sudo crontab -e
# Thêm dòng:
# 0 2 * * * pg_dump -U secureops_user secureops_db | gzip > /home/apiuser/backups/db_$(date +\%Y\%m\%d).sql.gz
```

---

## 🔒 OPTIONAL: SETUP SSL (Let's Encrypt)

```bash
# Cài certbot
sudo apt install -y certbot python3-certbot-nginx

# Nếu sau này có domain (ví dụ: api.yourdomain.com)
sudo certbot --nginx -d api.yourdomain.com

# Auto-renew
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

---

## 🆘 TROUBLESHOOTING

### ❌ "Connection refused 127.0.0.1:5000"
```bash
# Check Gunicorn
sudo systemctl status api
sudo journalctl -u api -n 20

# Restart
sudo systemctl restart api
```

### ❌ "502 Bad Gateway"
```bash
# Check if Gunicorn responds
curl http://127.0.0.1:5000

# Check Nginx config
sudo nginx -t

# Restart services
sudo systemctl restart api nginx
```

### ❌ "Database connection failed"
```bash
# Check PostgreSQL
sudo systemctl status postgresql

# Test connection
psql -U secureops_user -h localhost -d secureops_db -c "SELECT 1"

# Restart DB
sudo systemctl restart postgresql
```

### ❌ "Permission denied"
```bash
# Fix file permissions
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_rsa
chmod 600 ~/.ssh/authorized_keys

# Fix directory permissions
sudo chown -R apiuser:apiuser /home/apiuser/api_project
chmod 755 /home/apiuser/api_project
```

---

## 📈 OPTIMIZE CẤU HÌNH

### Tăng số lượng Gunicorn workers
```bash
# Mở service file
sudo nano /etc/systemd/system/api.service

# Đổi:
# --workers=2
# Thành:
# --workers=4  (nếu máy có 4+ cores)

sudo systemctl daemon-reload
sudo systemctl restart api
```

### Tối ưu hóa Nginx
```bash
sudo nano /etc/nginx/nginx.conf

# Thêm vào http block:
keepalive_timeout 65;
gzip on;
gzip_types text/plain text/css application/json;
```

---

## 📞 KIỂM TRA NHANH - CHECKLIST

```
☐ VPS SSH accessible: ssh apiuser@YOUR_VPS_IP
☐ Python 3.10+: python3 --version
☐ PostgreSQL running: sudo systemctl status postgresql
☐ Database created: psql -U secureops_user -d secureops_db -c "SELECT 1"
☐ Code deployed: ls /home/apiuser/api_project/*.py
☐ Virtual env: source /home/apiuser/api_project/venv/bin/activate
☐ Dependencies: pip list | grep -i flask
☐ Gunicorn running: sudo systemctl status api
☐ Nginx running: sudo systemctl status nginx
☐ Health check: curl http://YOUR_VPS_IP/health
☐ Logs configured: sudo tail -f /var/log/api_error.log
☐ Firewall open: sudo ufw status
```

---

## 🎯 API ENDPOINTS

Sau khi triển khai, API sẽ có sẵn tại:

```
Health:       http://YOUR_VPS_IP/health
Token:        http://YOUR_VPS_IP/auth/test-token?role=CTV
Tasks:        http://YOUR_VPS_IP/api/v1/my/tasks
Evidence:     http://YOUR_VPS_IP/api/v1/tasks/{taskId}/evidences
Upload:       http://YOUR_VPS_IP/api/v1/tasks/{taskId}/evidences/upload
```

---

## 🚀 NEXT STEPS SAU KHI TRIỂN KHAI

1. **SSL Certificate** (Nên làm)
   - Domain → Certbot → Auto-renew
   
2. **Monitoring** (Quan trọng)
   - Install: Prometheus, DataDog, hoặc Uptime Robot
   
3. **Backups** (Bắt buộc)
   - Crontab database backup hàng ngày
   - Upload backups to S3/Cloud
   
4. **Scaling** (Sau này nếu cần)
   - Separate PostgreSQL server
   - Load balancer (HAProxy/Nginx)
   - Multiple API instances

---

## 📚 TÀI LIỆU THAM KHẢO

- Full Guide: `DEPLOYMENT_GUIDE_VPS.md`
- Auto Deploy: `deploy.sh`
- Verification: `post-deploy-check.sh`

---

Generated: 2026-11-06 | Quick Reference v1.0
