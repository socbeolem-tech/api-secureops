#!/bin/bash
# 🚀 DEPLOYMENT AUTOMATION SCRIPT FOR VPS
# Usage: chmod +x deploy.sh && ./deploy.sh
# Run this script on your VPS as apiuser

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════╗"
echo "║  SecureOps API - VPS Production Deployment (Ubuntu)    ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# ============================================================
# VARIABLES
# ============================================================
PROJECT_DIR="/home/apiuser/api_project"
VENV_DIR="$PROJECT_DIR/venv"
DB_USER="secureops_user"
DB_PASSWORD="scopATAAI@2026"
DB_NAME="secureops_db"
APP_PORT="5000"

# ============================================================
# STEP 1: SYSTEM UPDATES
# ============================================================
echo "📦 [1/8] Updating system packages..."
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip python3-dev
sudo apt install -y postgresql postgresql-contrib
sudo apt install -y git curl wget supervisor nginx

# Check Python version
echo "✅ Python version: $(python3 --version)"

# ============================================================
# STEP 2: POSTGRESQL SETUP
# ============================================================
echo "🗄️  [2/8] Configuring PostgreSQL..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql <<EOF
CREATE DATABASE IF NOT EXISTS $DB_NAME;
CREATE USER IF NOT EXISTS $DB_USER WITH PASSWORD '$DB_PASSWORD';
ALTER ROLE $DB_USER SET client_encoding TO 'utf8';
ALTER ROLE $DB_USER SET default_transaction_isolation TO 'read committed';
ALTER ROLE $DB_USER SET default_transaction_deferrable TO on;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
\c $DB_NAME
GRANT ALL ON SCHEMA public TO $DB_USER;
EOF

echo "✅ PostgreSQL setup complete"

# ============================================================
# STEP 3: CODE DEPLOYMENT
# ============================================================
echo "📂 [3/8] Preparing application directory..."

if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ Error: $PROJECT_DIR not found!"
    echo "Please upload/clone your code first:"
    echo "  scp -r ./api_project/* apiuser@YOUR_VPS_IP:/home/apiuser/api_project/"
    exit 1
fi

cd "$PROJECT_DIR"
echo "✅ Application directory ready at $PROJECT_DIR"

# ============================================================
# STEP 4: PYTHON VIRTUAL ENVIRONMENT
# ============================================================
echo "🐍 [4/8] Setting up Python virtual environment..."

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
pip install --upgrade pip wheel setuptools
pip install -r requirements.txt

echo "✅ Virtual environment ready"

# ============================================================
# STEP 5: ENVIRONMENT CONFIGURATION
# ============================================================
echo "⚙️  [5/8] Creating .env configuration..."

if [ ! -f "$PROJECT_DIR/.env" ]; then
    cat > "$PROJECT_DIR/.env" << 'ENVFILE'
FLASK_ENV=production
FLASK_APP=app.py
FLASK_DEBUG=0

DATABASE_URL=postgresql://secureops_user:scopATAAI%402026@localhost:5432/secureops_db
JWT_SECRET_KEY=$(openssl rand -hex 32)
UPLOAD_DIR=/home/apiuser/api_project/uploads
MAX_UPLOAD_SIZE_MB=100
IDEMPOTENCY_KEY_TTL_SECONDS=86400
ENVFILE

    # Generate JWT secret
    JWT_SECRET=$(openssl rand -hex 32)
    sed -i "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET/" "$PROJECT_DIR/.env"
fi

mkdir -p "$PROJECT_DIR/uploads"
chmod 755 "$PROJECT_DIR/uploads"

echo "✅ .env configuration created"

# ============================================================
# STEP 6: DATABASE MIGRATIONS
# ============================================================
echo "🔄 [6/8] Running database migrations..."

cd "$PROJECT_DIR"
source "$VENV_DIR/bin/activate"

# Run Alembic migrations if available
if [ -d "alembic" ]; then
    alembic upgrade head
    echo "✅ Migrations applied"
else
    echo "⏭️  No Alembic migrations found (will create tables on app startup)"
fi

# Test database connection
python3 -c "
from app import create_app, db
app = create_app('production')
with app.app_context():
    try:
        db.engine.connect()
        print('✅ Database connection successful')
    except Exception as e:
        print(f'❌ Database connection failed: {e}')
        exit(1)
"

# ============================================================
# STEP 7: SYSTEMD SERVICE FOR GUNICORN
# ============================================================
echo "🔧 [7/8] Configuring Gunicorn as systemd service..."

source "$VENV_DIR/bin/activate"
pip install gunicorn==21.2.0

# Create systemd service file
sudo tee /etc/systemd/system/api.service > /dev/null << 'SERVICEFILE'
[Unit]
Description=SecureOps API - Flask Application
After=network.target postgresql.service

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

# Security
PrivateTmp=yes
NoNewPrivileges=yes

[Install]
WantedBy=multi-user.target
SERVICEFILE

# Create log files with proper permissions
sudo touch /var/log/api_access.log /var/log/api_error.log
sudo chown apiuser:www-data /var/log/api_access.log /var/log/api_error.log
sudo chmod 640 /var/log/api_access.log /var/log/api_error.log

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable api
sudo systemctl start api

echo "✅ Gunicorn service configured"

# ============================================================
# STEP 8: NGINX REVERSE PROXY
# ============================================================
echo "🌐 [8/8] Configuring Nginx reverse proxy..."

# Detect server IP
SERVER_IP=$(hostname -I | awk '{print $1}')

sudo tee /etc/nginx/sites-available/api > /dev/null << NGINXFILE
server {
    listen 80;
    server_name $SERVER_IP;
    
    client_max_body_size 100M;
    
    # API proxy
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Static files / uploads
    location /uploads {
        alias /home/apiuser/api_project/uploads;
        expires 30d;
        access_log off;
    }
}
NGINXFILE

# Enable site and remove default
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/api /etc/nginx/sites-enabled/

# Test and start nginx
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx

echo "✅ Nginx configured"

# ============================================================
# VERIFICATION
# ============================================================
echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  ✅ DEPLOYMENT COMPLETE!                               ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "📊 SERVICE STATUS:"
echo ""

# Check services
for service in api postgresql nginx; do
    status=$(sudo systemctl is-active $service)
    if [ "$status" = "active" ]; then
        echo "  ✅ $service: RUNNING"
    else
        echo "  ❌ $service: NOT RUNNING"
    fi
done

echo ""
echo "🌐 API ENDPOINTS:"
echo "  Token: http://$SERVER_IP/auth/test-token?role=CTV"
echo "  Tasks: http://$SERVER_IP/api/v1/my/tasks"
echo "  Health: http://$SERVER_IP/health"
echo ""
echo "📝 LOGS:"
echo "  App:    tail -f /var/log/api_error.log"
echo "  Nginx:  tail -f /var/log/nginx/error.log"
echo "  DB:     sudo tail -f /var/log/postgresql/*.log"
echo ""
echo "📌 NEXT STEPS:"
echo "  1. Test API: curl http://$SERVER_IP/health"
echo "  2. Add domain & SSL (optional): certbot --nginx -d yourdomain.com"
echo "  3. Setup monitoring & backups"
echo "  4. Change JWT_SECRET_KEY in .env"
echo ""
echo "Happy coding! 🚀"
