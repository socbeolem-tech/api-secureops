# 📚 VPS DEPLOYMENT RESOURCES INDEX

**Complete deployment kit for Ubuntu 24.04 LTS VPS**  
**Generated**: 2026-11-06  
**Status**: Production-ready 🚀

---

## 📖 DOCUMENTATION FILES (READ THESE)

### 🚀 START HERE (Pick your learning style)

| File | Best for | Duration | Start here? |
|------|----------|----------|-------------|
| **ACTION_PLAN.md** | I need to deploy NOW | 5 min | ✅ YES - Immediate guide |
| **GETTING_STARTED.md** | I'm new, need step-by-step | 15 min | ✅ YES - Beginner friendly |
| **DEPLOYMENT_SUMMARY.md** | I want overview first | 10 min | ✅ YES - High-level view |
| **DEPLOYMENT_QUICK_REFERENCE.md** | I need command reference | On-demand | ✅ YES - For copy-paste |
| **DEPLOYMENT_GUIDE_VPS.md** | I want full technical details | 30 min | ⏭️ AFTER basics |

### 🔧 SCRIPT FILES (RUN THESE)

| File | Purpose | When to run | How |
|------|---------|------------|-----|
| **deploy.sh** | Automated full deployment | During deployment | `chmod +x deploy.sh && ./deploy.sh` |
| **post-deploy-check.sh** | Verify deployment successful | After deploy.sh completes | `chmod +x post-deploy-check.sh && ./post-deploy-check.sh` |

---

## 🎯 QUICK START (Choose your path)

### Path A: "I just want it working NOW" ⚡
```
1. Read: ACTION_PLAN.md (5 min)
2. Run: deploy.sh (10 min)
3. Test: curl http://YOUR_VPS_IP/health
```

### Path B: "I want to understand everything" 📚
```
1. Read: GETTING_STARTED.md (15 min)
2. Read: DEPLOYMENT_SUMMARY.md (10 min)
3. Run: deploy.sh (10 min)
4. Read: DEPLOYMENT_GUIDE_VPS.md (20 min)
5. Reference: DEPLOYMENT_QUICK_REFERENCE.md (as needed)
```

### Path C: "I want manual control" 🔧
```
1. Read: DEPLOYMENT_GUIDE_VPS.md (30 min)
2. Follow manual steps section
3. Execute commands from DEPLOYMENT_QUICK_REFERENCE.md
4. Verify with post-deploy-check.sh
```

---

## 📋 WHAT YOU NEED BEFORE STARTING

✅ Checklist:

```
☐ Ubuntu 24.04 LTS VPS (or equivalent)
☐ 2GB RAM minimum
☐ 1-2 CPU cores
☐ SSH access (root or sudo)
☐ API source code ready
☐ PostgreSQL NOT pre-installed
☐ Port 80 (HTTP) available
☐ Port 443 (HTTPS) available for future SSL
```

---

## 🚀 3-STEP DEPLOYMENT PROCESS

### Step 1: Upload Code (5 min)
```bash
# From your local machine
cd ~/path/to/api_project
scp -r ./* apiuser@YOUR_VPS_IP:/home/apiuser/api_project/
```

### Step 2: Run Deploy Script (10 min)
```bash
# SSH to VPS
ssh apiuser@YOUR_VPS_IP

# Run automation
cd /home/apiuser/api_project
chmod +x deploy.sh
./deploy.sh
```

### Step 3: Verify (2 min)
```bash
# Test from local machine
curl http://YOUR_VPS_IP/health

# Or run verification script
ssh apiuser@YOUR_VPS_IP "bash /home/apiuser/api_project/post-deploy-check.sh"
```

---

## 📊 WHAT GETS INSTALLED

The `deploy.sh` script automatically installs & configures:

### System Level:
- Python 3.10+ with venv support
- PostgreSQL 15 + client
- Nginx web server
- UFW firewall
- Git, curl, wget, supervisor

### Application Level:
- Flask 3.0.0
- SQLAlchemy 2.1+
- Gunicorn WSGI server
- Marshmallow validation
- PyJWT authentication
- psycopg database driver
- All dependencies from requirements.txt

### Services:
- **Gunicorn** on port 5000 (internal)
- **Nginx** on port 80 (external)
- **PostgreSQL** on port 5432 (internal)
- **Systemd service** for auto-restart

---

## 🎯 EXPECTED OUTCOMES

After successful deployment:

### API Endpoints Available:
```
http://YOUR_VPS_IP/health
http://YOUR_VPS_IP/auth/test-token?role=CTV
http://YOUR_VPS_IP/api/v1/my/tasks
http://YOUR_VPS_IP/api/v1/tasks/{id}
http://YOUR_VPS_IP/api/v1/tasks/{id}/evidences
http://YOUR_VPS_IP/api/v1/evidences/{id}
http://YOUR_VPS_IP/api/v1/tasks/{id}/evidences/upload
```

### Services Running:
```
✅ Nginx (reverse proxy) - port 80
✅ Gunicorn (Flask app) - port 5000 (internal)
✅ PostgreSQL (database) - port 5432 (internal)
✅ UFW firewall (protection)
```

### Files Created:
```
/home/apiuser/api_project/           # Application code
/home/apiuser/api_project/uploads/   # Evidence files
/etc/systemd/system/api.service      # Auto-startup config
/etc/nginx/sites-available/api       # Nginx config
/var/log/api_*.log                   # Application logs
```

---

## 📖 DOCUMENTATION BREAKDOWN

### ACTION_PLAN.md
- Quick 5-step checklist
- 20-minute deployment timeline
- Success indicators
- Common issues quick fixes

### GETTING_STARTED.md
- Beginner-friendly step-by-step
- SSH login instructions
- User creation
- Code upload guide
- Service management
- Basic troubleshooting

### DEPLOYMENT_SUMMARY.md
- High-level overview
- Architecture diagram
- Service structure
- Performance expectations
- Security features
- Reference to other docs

### DEPLOYMENT_QUICK_REFERENCE.md
- Command reference
- Service management
- Backup/restore procedures
- Database management
- SSL setup
- Troubleshooting guide
- Performance tuning

### DEPLOYMENT_GUIDE_VPS.md
- Complete 10-part guide
- Detailed explanations
- Full command walkthroughs
- Security configuration
- Monitoring setup
- Backup strategies
- Troubleshooting deep-dive

---

## 🔧 COMMON TASKS

### Start/Stop/Restart API
```bash
sudo systemctl start api
sudo systemctl stop api
sudo systemctl restart api
sudo systemctl status api
```

### View Logs
```bash
# Real-time logs
sudo tail -f /var/log/api_error.log
sudo tail -f /var/log/nginx/error.log

# Get last 50 lines
sudo tail -50 /var/log/api_error.log

# Search for errors
sudo grep -i error /var/log/api_error.log | tail -20
```

### Backup Database
```bash
pg_dump -U secureops_user secureops_db | gzip > backup_$(date +%Y%m%d).sql.gz
```

### SSH Access
```bash
# Connect as apiuser
ssh apiuser@YOUR_VPS_IP

# Connect as root
ssh root@YOUR_VPS_IP

# SCP file upload
scp yourfile.txt apiuser@YOUR_VPS_IP:/home/apiuser/
```

---

## 🆘 TROUBLESHOOTING MATRIX

| Symptom | Solution | Reference |
|---------|----------|-----------|
| "Connection refused" | Check Gunicorn status | DEPLOYMENT_QUICK_REFERENCE.md |
| "502 Bad Gateway" | Restart Nginx + Gunicorn | DEPLOYMENT_QUICK_REFERENCE.md |
| "Database connection failed" | Check PostgreSQL service | DEPLOYMENT_QUICK_REFERENCE.md |
| "Permission denied" | Fix file permissions | DEPLOYMENT_GUIDE_VPS.md |
| Script failed | Check logs, re-run script | GETTING_STARTED.md |
| SSL certificate issues | Use certbot | DEPLOYMENT_GUIDE_VPS.md |

---

## 🚀 NEXT STEPS AFTER DEPLOYMENT

### Immediate (Today):
- ✅ Test API endpoints work
- ✅ Check logs for errors
- ✅ Verify database connected

### This Week:
- [ ] Setup domain name (optional)
- [ ] Configure SSL certificate
- [ ] Setup automated backups
- [ ] Configure log rotation

### This Month:
- [ ] Setup monitoring/alerting
- [ ] Performance testing
- [ ] Security audit
- [ ] Documentation update

### Long-term:
- [ ] Scale if needed (more workers/instances)
- [ ] Separate DB server (if high traffic)
- [ ] Add caching layer (Redis)
- [ ] Load balancer setup

---

## 📊 DEPLOYMENT CHECKLIST

Use this to track your progress:

```
PREPARATION:
  ☐ VPS server ready
  ☐ Ubuntu 24.04 installed
  ☐ SSH access working
  ☐ Source code ready

DEPLOYMENT:
  ☐ Read ACTION_PLAN.md (5 min)
  ☐ Upload code via SCP (5 min)
  ☐ SSH into VPS (1 min)
  ☐ Create apiuser (2 min)
  ☐ Run ./deploy.sh (10 min)
  ☐ Wait for completion

VERIFICATION:
  ☐ Test health endpoint
  ☐ Check services running
  ☐ View logs for errors
  ☐ Test API endpoints
  ☐ Run post-deploy-check.sh

POST-DEPLOY:
  ☐ Setup monitoring
  ☐ Configure backups
  ☐ Add SSL (if domain)
  ☐ Update documentation
```

---

## 🎓 LEARNING RESOURCES

### Understanding the Stack:
1. **Flask** - Web framework (app.py)
2. **Gunicorn** - WSGI application server
3. **Nginx** - Reverse proxy & load balancer
4. **PostgreSQL** - Database
5. **Systemd** - Service management

### Key Concepts:
- **Reverse Proxy**: Nginx receives requests, forwards to Gunicorn
- **WSGI Server**: Gunicorn runs Python app and handles requests
- **Database**: PostgreSQL stores application data
- **Systemd**: Manages service auto-start and restart

---

## 📞 HELP & SUPPORT

If you get stuck:

1. **Check logs first**:
   ```bash
   sudo tail -f /var/log/api_error.log
   sudo tail -f /var/log/nginx/error.log
   ```

2. **Read troubleshooting section**:
   - DEPLOYMENT_QUICK_REFERENCE.md → Troubleshooting
   - DEPLOYMENT_GUIDE_VPS.md → Troubleshooting

3. **Run verification script**:
   ```bash
   bash /home/apiuser/api_project/post-deploy-check.sh
   ```

4. **Check service status**:
   ```bash
   sudo systemctl status api postgresql nginx
   ```

---

## 🎉 SUCCESS!

You'll know it's working when:

✅ Health endpoint responds  
✅ Can get JWT token  
✅ Can list tasks  
✅ Can upload files  
✅ Logs show no errors  
✅ Database is connected  

---

## 📝 QUICK REFERENCE CARDS

### Useful commands (copy-paste ready):

**Check if everything is running:**
```bash
sudo systemctl status api postgresql nginx
```

**Restart API:**
```bash
sudo systemctl restart api
```

**View live logs:**
```bash
sudo tail -f /var/log/api_error.log
```

**Test API health:**
```bash
curl http://YOUR_VPS_IP/health
```

**SSH to VPS:**
```bash
ssh apiuser@YOUR_VPS_IP
```

---

## 🏆 DEPLOYMENT COMPLETE!

Once you've finished all steps:

**Your API is live at**: `http://YOUR_VPS_IP`

**Next**: Monitor logs, backup data, scale as needed.

---

## 📋 FILE MANIFEST

```
Deployment Documentation:
├── ACTION_PLAN.md                    # Quick 5-step plan
├── GETTING_STARTED.md                # Beginner guide
├── DEPLOYMENT_SUMMARY.md             # Overview
├── DEPLOYMENT_QUICK_REFERENCE.md     # Command reference
├── DEPLOYMENT_GUIDE_VPS.md           # Full detailed guide

Automation Scripts:
├── deploy.sh                         # Main deployment
├── post-deploy-check.sh              # Verification
└── requirements.txt                  # Python dependencies

Application Code:
├── app.py                            # Flask app
├── models.py                         # Database models
├── auth.py                           # Authentication
├── routes_tasks.py                   # Task APIs
├── routes_evidence.py                # Evidence APIs
├── utils.py                          # Utilities
└── schemas.py                        # Marshmallow schemas

Configuration:
├── config.py                         # Flask config
├── .env                              # Runtime config (created by deploy)
└── alembic/                          # Database migrations

Database:
└── uploads/                          # Evidence files (created on first use)
```

---

**Version**: 1.0  
**Date**: 2026-11-06  
**Status**: Production-Ready 🚀  
**Ubuntu**: 24.04 LTS  
**RAM Required**: 2GB minimum  
**Deployment Time**: ~20 minutes  

**READY TO DEPLOY?** Start with ACTION_PLAN.md! 🎯
