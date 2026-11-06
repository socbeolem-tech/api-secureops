# 🚀 HƯỚNG DẪN TRIỂN KHAI API + PostgreSQL TRÊN VPS

**Môi trường**: Ubuntu 24.04 LTS | 2GB RAM | Production  
**Date**: 2026-11-06  
**Status**: Sẵn sàng triển khai

---

## 📋 PHẦN 1: CÁC BƯỚC CỰC KỲ QUAN TRỌNG TRƯỚC TRIỂN KHAI

### 1.1 Chuẩn bị VPS
```bash
# Bước 1: SSH vào VPS (thay YOUR_VPS_IP)
ssh root@YOUR_VPS_IP

# Bước 2: Cập nhật hệ thống
sudo apt update && sudo apt upgrade -y

# Bước 3: Đặt timezone (Việt Nam)
sudo timedatectl set-timezone Asia/Ho_Chi_Minh
timedatectl

# Bước 4: Tạo user không phải root (bảo mật)
sudo adduser apiuser
sudo usermod -aG sudo apiuser
su - apiuser
```

### 1.2 Cải thiện bảo mật cơ bản
```bash
# Tạo SSH key trên máy local (nếu chưa có)
ssh-keygen -t rsa -b 4096 -f ~/.ssh/vps_key

# Copy public key lên VPS (chạy từ máy local)
ssh-copy-id -i ~/.ssh/vps_key.pub apiuser@YOUR_VPS_IP

# Thiết lập firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## 📦 PHẦN 2: CÀI ĐẶT CÁC DEPENDENCY

### 2.1 Cài Python 3.10+
```bash
sudo apt install -y python3.10 python3.10-venv python3-pip python3-dev

# Kiểm tra phiên bản
python3 --version
pip3 --version
```

### 2.2 Cài PostgreSQL 15
```bash
# Cài PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Khởi động service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Kiểm tra trạng thái
sudo systemctl status postgresql

# Kết nối vào PostgreSQL
sudo -u postgres psql
```

### 2.3 Cấu hình PostgreSQL

**Chạy các lệnh trong psql prompt**:
```sql
-- Tạo database
CREATE DATABASE secureops_db;

-- Tạo user PostgreSQL
CREATE USER secureops_user WITH PASSWORD 'scopATAAI@2026';

-- Gán quyền
ALTER ROLE secureops_user SET client_encoding TO 'utf8';
ALTER ROLE secureops_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE secureops_user SET default_transaction_deferrable TO on;
ALTER ROLE secureops_user SET default_transaction_isolation TO 'read committed';
GRANT ALL PRIVILEGES ON DATABASE secureops_db TO secureops_user;

-- Kết nối vào DB mới
\c secureops_db

-- Cấp quyền schema
GRANT ALL ON SCHEMA public TO secureops_user;

-- Thoát
\q
```

### 2.4 Cài đặt các công cụ cần thiết
```bash
sudo apt install -y git curl wget supervisor nginx
```

---

## 🚀 PHẦN 3: TRIỂN KHAI ỨNG DỤNG

### 3.1 Clone/Upload code từ GitHub/local
```bash
# Cách 1: Clone từ GitHub (nếu có)
cd /home/apiuser
git clone https://github.com/YOUR_REPO/api_project.git
cd api_project

# Cách 2: Upload từ máy local bằng SCP
# Chạy từ máy local:
scp -r -i ~/.ssh/vps_key ./api_project/* apiuser@YOUR_VPS_IP:/home/apiuser/api_project/
```

### 3.2 Tạo Virtual Environment
```bash
cd /home/apiuser/api_project

# Tạo virtual environment
python3 -m venv venv

# Kích hoạt
source venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt

# Kiểm tra cài đặt
python3 -c "import flask; print(f'Flask {flask.__version__} OK')"
```

### 3.3 Cấu hình Environment
```bash
# Tạo file .env
cat > .env << 'EOF'
FLASK_ENV=production
FLASK_APP=app.py
FLASK_DEBUG=0

DATABASE_URL=postgresql://secureops_user:scopATAAI@2026@localhost:5432/secureops_db
JWT_SECRET_KEY=your-secret-key-change-this-in-production-$(openssl rand -hex 32)
UPLOAD_DIR=/home/apiuser/api_project/uploads
MAX_UPLOAD_SIZE_MB=100
IDEMPOTENCY_KEY_TTL_SECONDS=86400
EOF

# Tạo folder uploads
mkdir -p uploads
chmod 755 uploads
```

### 3.4 Chạy Database Migrations
```bash
# Kích hoạt venv
source venv/bin/activate

# Chạy migrations (nếu dùng Alembic)
alembic upgrade head

# Nếu muốn kiểm tra
python3 -c "from app import create_app, db; app = create_app('production'); print('✅ Database connected')"
```

---

## 🔧 PHẦN 4: CHẠY FLASK VỚI GUNICORN (Production WSGI Server)

### 4.1 Cài Gunicorn
```bash
source /home/apiuser/api_project/venv/bin/activate
pip install gunicorn==21.2.0
```

### 4.2 Tạo Systemd Service
```bash
# Tạo file service
sudo cat > /etc/systemd/system/api.service << 'EOF'
[Unit]
Description=SecureOps API - Flask Application
After=network.target

[Service]
User=apiuser
Group=www-data
WorkingDirectory=/home/apiuser/api_project

Environment="PATH=/home/apiuser/api_project/venv/bin"
Environment="FLASK_ENV=production"
Environment="FLASK_APP=app.py"

ExecStart=/home/apiuser/api_project/venv/bin/gunicorn \
    --workers=2 \
    --worker-class=sync \
    --bind=127.0.0.1:5000 \
    --timeout=30 \
    --access-logfile=/var/log/api_access.log \
    --error-logfile=/var/log/api_error.log \
    app:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Kích hoạt service
sudo systemctl daemon-reload
sudo systemctl enable api
sudo systemctl start api

# Kiểm tra trạng thái
sudo systemctl status api
sudo tail -f /var/log/api_error.log
```

---

## 🌐 PHẦN 5: CẤU HÌNH NGINX (Reverse Proxy)

### 5.1 Tạo Nginx Config
```bash
# Tạo file config
sudo cat > /etc/nginx/sites-available/api << 'EOF'
server {
    listen 80;
    server_name YOUR_VPS_IP;
    
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    location /uploads {
        alias /home/apiuser/api_project/uploads;
        expires 30d;
    }
}
EOF

# Kích hoạt site
sudo ln -s /etc/nginx/sites-available/api /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Kiểm tra config
sudo nginx -t

# Khởi động Nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

### 5.2 Test Nginx
```bash
# Kiểm tra trạng thái
sudo systemctl status nginx

# Xem log
sudo tail -f /var/log/nginx/error.log
```

---

## 🔒 PHẦN 6: SETUP SSL/TLS (Let's Encrypt - Optional nhưng nên làm)

### 6.1 Cài Certbot
```bash
sudo apt install -y certbot python3-certbot-nginx

# Nếu có domain, chạy:
sudo certbot --nginx -d your-domain.com

# Nếu chưa có domain, bỏ qua bước này, tạm dùng HTTP thôi
```

### 6.2 Auto-renew certificate
```bash
# Certbot tự động renew, kiểm tra:
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

---

## 📊 PHẦN 7: MONITORING & LOGS

### 7.1 Xem logs
```bash
# Flask app logs
sudo tail -f /var/log/api_error.log
sudo tail -f /var/log/api_access.log

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql.log
```

### 7.2 Kiểm tra trạng thái services
```bash
# Toàn bộ services
sudo systemctl status api
sudo systemctl status postgresql
sudo systemctl status nginx

# Khởi động lại nếu cần
sudo systemctl restart api
sudo systemctl restart nginx
```

---

## 🧪 PHẦN 8: TEST TRIỂN KHAI

### 8.1 Test API từ VPS
```bash
# Test token endpoint
curl -s http://YOUR_VPS_IP/auth/test-token?role=CTV \
  -H "Authorization: Bearer test" | jq '.'

# Test task list
TOKEN=$(curl -s http://YOUR_VPS_IP/auth/test-token?role=CTV \
  -H "Authorization: Bearer test" | jq -r '.data.token')
curl -s http://YOUR_VPS_IP/api/v1/my/tasks \
  -H "Authorization: Bearer $TOKEN" | jq '.meta'
```

### 8.2 Test từ máy local
```bash
# Thay YOUR_VPS_IP
curl -s http://YOUR_VPS_IP/api/v1/my/tasks \
  -H "Authorization: Bearer $TOKEN"
```

### 8.3 Test Health Check
```bash
curl -s http://YOUR_VPS_IP/health | jq '.'
```

---

## 🔄 PHẦN 9: BACKUP & RESTORE DATABASE

### 9.1 Backup tự động
```bash
# Tạo script backup
sudo cat > /usr/local/bin/backup-db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/apiuser/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

pg_dump -U secureops_user -h localhost secureops_db | \
  gzip > $BACKUP_DIR/secureops_db_$TIMESTAMP.sql.gz

# Giữ lại 7 bản backup gần nhất
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
EOF

sudo chmod +x /usr/local/bin/backup-db.sh

# Chạy backup hàng ngày lúc 2AM
sudo crontab -e
# Thêm dòng:
# 0 2 * * * /usr/local/bin/backup-db.sh
```

### 9.2 Restore từ backup
```bash
# Restore từ file backup
gunzip < /home/apiuser/backups/secureops_db_TIMESTAMP.sql.gz | \
  psql -U secureops_user -h localhost secureops_db
```

---

## 📝 PHẦN 10: KIỂM TRA DANH SÁCH CUỐI CÙNG (Checklist)

```bash
☐ VPS SSH access: ssh apiuser@YOUR_VPS_IP
☐ Python 3.10+: python3 --version
☐ PostgreSQL running: sudo systemctl status postgresql
☐ Database created: psql -U secureops_user -d secureops_db -c "SELECT 1"
☐ Code deployed: ls /home/apiuser/api_project
☐ Virtual env: source /home/apiuser/api_project/venv/bin/activate
☐ Dependencies installed: pip list | grep -i flask
☐ Flask app runnable: python3 -c "from app import create_app; app = create_app('production'); print('OK')"
☐ Gunicorn started: sudo systemctl status api
☐ Nginx running: sudo systemctl status nginx
☐ API accessible: curl http://YOUR_VPS_IP/health
☐ Database migrated: psql -U secureops_user -d secureops_db -c "\dt"
☐ Logs configured: tail -f /var/log/api_error.log
☐ Firewall open: sudo ufw status
☐ SSL certificate (optional): sudo certbot certificates
```

---

## 🆘 TROUBLESHOOTING

### Lỗi: "ECONNREFUSED 127.0.0.1:5000"
```bash
# Check Gunicorn status
sudo systemctl status api

# Check logs
sudo systemctl journal-ctl -u api -n 50

# Restart
sudo systemctl restart api
```

### Lỗi: "psycopg error: could not connect to server"
```bash
# Check PostgreSQL
sudo systemctl status postgresql

# Check listen address
sudo -u postgres psql -c "SHOW listen_addresses"

# Fix if needed: edit /etc/postgresql/15/main/postgresql.conf
sudo nano /etc/postgresql/15/main/postgresql.conf
# Uncomment: listen_addresses = 'localhost'

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### Lỗi: "Permission denied (publickey)"
```bash
# Fix SSH permissions
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub
chmod 600 ~/.ssh/authorized_keys
```

### Nginx 502 Bad Gateway
```bash
# Check if Gunicorn is running
curl http://127.0.0.1:5000

# Check Nginx config
sudo nginx -t

# Check Nginx logs
sudo tail -20 /var/log/nginx/error.log

# Restart
sudo systemctl restart api
sudo systemctl restart nginx
```

---

## 📞 CHÚC MỪNG! 🎉

Nếu bạn đã hoàn thành tất cả các bước trên, API của bạn đã sẵn sàng trên production!

### API URLs:
```
Token: http://YOUR_VPS_IP/auth/test-token?role=CTV
Tasks: http://YOUR_VPS_IP/api/v1/my/tasks
Health: http://YOUR_VPS_IP/health
```

### Next Steps:
1. ✅ Cấu hình domain name + SSL
2. ✅ Setup monitoring & alerting
3. ✅ Cấu hình rate limiting
4. ✅ Backup tự động hàng ngày
5. ✅ Cách ly database (separate server nếu traffic cao)

**Contact**: Nếu có vấn đề, kiểm tra logs trước: `/var/log/api_error.log`

---

Generated: 2026-11-06 | Version 1.0
