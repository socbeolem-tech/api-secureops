#!/bin/bash
# 🔍 POST-DEPLOYMENT VERIFICATION & OPTIMIZATION SCRIPT
# Usage: chmod +x post-deploy-check.sh && ./post-deploy-check.sh

echo "╔════════════════════════════════════════════════════════╗"
echo "║  Post-Deployment Verification & Optimization          ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
PASS=0
FAIL=0

# Function to print test results
test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}: $2"
        ((PASS++))
    else
        echo -e "${RED}❌ FAIL${NC}: $2"
        ((FAIL++))
    fi
}

echo "═══════════════════════════════════════════════════════"
echo "🔍 SYSTEM & SERVICES CHECK"
echo "═══════════════════════════════════════════════════════"
echo ""

# 1. Check Python
python3 --version > /dev/null 2>&1
test_result $? "Python 3 installed"

# 2. Check PostgreSQL
sudo systemctl is-active postgresql > /dev/null 2>&1
test_result $? "PostgreSQL running"

# 3. Check if database exists
sudo -u postgres psql -lqt | grep secureops_db > /dev/null 2>&1
test_result $? "Database 'secureops_db' exists"

# 4. Check API service
sudo systemctl is-active api > /dev/null 2>&1
test_result $? "API service running"

# 5. Check Nginx
sudo systemctl is-active nginx > /dev/null 2>&1
test_result $? "Nginx running"

# 6. Check if Gunicorn is listening
curl -s http://127.0.0.1:5000/health > /dev/null 2>&1
test_result $? "Gunicorn responding on port 5000"

# 7. Check Nginx proxy
curl -s http://127.0.0.1/health > /dev/null 2>&1
test_result $? "Nginx proxy working"

echo ""
echo "═══════════════════════════════════════════════════════"
echo "🗂️  DIRECTORY & FILE PERMISSIONS"
echo "═══════════════════════════════════════════════════════"
echo ""

# 8. Check project directory
[ -d "/home/apiuser/api_project" ]
test_result $? "Project directory exists"

# 9. Check virtual environment
[ -d "/home/apiuser/api_project/venv" ]
test_result $? "Virtual environment created"

# 10. Check uploads directory
[ -d "/home/apiuser/api_project/uploads" ]
test_result $? "Uploads directory exists"

# 11. Check .env file
[ -f "/home/apiuser/api_project/.env" ]
test_result $? ".env configuration file exists"

# 12. Check requirements.txt
[ -f "/home/apiuser/api_project/requirements.txt" ]
test_result $? "requirements.txt present"

echo ""
echo "═══════════════════════════════════════════════════════"
echo "📡 API ENDPOINT TESTS"
echo "═══════════════════════════════════════════════════════"
echo ""

SERVER_IP=$(hostname -I | awk '{print $1}')
echo "Testing endpoints on http://$SERVER_IP"
echo ""

# 13. Health check
HEALTH=$(curl -s http://127.0.0.1/health)
echo "Health endpoint response:"
echo "  $HEALTH" | head -c 80
echo ""
[ ! -z "$HEALTH" ]
test_result $? "Health endpoint responding"

# 14. Token generation
TOKEN=$(curl -s http://127.0.0.1/auth/test-token?role=CTV -H "Authorization: Bearer test" 2>/dev/null | grep -o '"token":"[^"]*"' | head -1)
[ ! -z "$TOKEN" ]
test_result $? "Token endpoint working"

# 15. Task list access
if [ ! -z "$TOKEN" ]; then
    TOKEN_VAL=$(echo $TOKEN | cut -d'"' -f4)
    TASKS=$(curl -s http://127.0.0.1/api/v1/my/tasks -H "Authorization: Bearer $TOKEN_VAL" 2>/dev/null)
    echo "Tasks endpoint response: $(echo $TASKS | head -c 100)..."
    echo $TASKS | grep -q "success"
    test_result $? "Task list endpoint accessible"
fi

echo ""
echo "═══════════════════════════════════════════════════════"
echo "📊 LOG FILES CHECK"
echo "═══════════════════════════════════════════════════════"
echo ""

# 16. Check if log files exist and are being written
[ -f "/var/log/api_access.log" ]
test_result $? "API access log exists"

[ -f "/var/log/api_error.log" ]
test_result $? "API error log exists"

# 17. Check recent entries
[ -s "/var/log/api_access.log" ]
test_result $? "API access log has entries"

echo ""
echo "📝 Recent log entries:"
echo "  Access log:"
sudo tail -2 /var/log/api_access.log 2>/dev/null | sed 's/^/    /'
echo ""
echo "  Error log:"
sudo tail -2 /var/log/api_error.log 2>/dev/null | sed 's/^/    /'

echo ""
echo "═══════════════════════════════════════════════════════"
echo "🔐 SECURITY & FIREWALL"
echo "═══════════════════════════════════════════════════════"
echo ""

# 18. Check firewall
sudo ufw status > /dev/null 2>&1
test_result $? "Firewall configured"

# 19. Check if port 80 is open
sudo ufw status | grep -i "80/tcp" | grep "allow" > /dev/null 2>&1
test_result $? "Port 80 open in firewall"

# 20. Check if SSH key-based auth is possible
[ -f "/home/apiuser/.ssh/authorized_keys" ]
test_result $? "SSH public key authentication configured"

echo ""
echo "═══════════════════════════════════════════════════════"
echo "📈 PERFORMANCE METRICS"
echo "═══════════════════════════════════════════════════════"
echo ""

echo "System resources:"
echo "  CPU: $(grep -c "^processor" /proc/cpuinfo) cores"
echo "  RAM: $(free -h | awk '/^Mem:/ {print $2}')"
echo "  Disk: $(df -h / | awk 'NR==2 {print $2}')"
echo ""

echo "Database info:"
sudo -u postgres psql -c "SELECT datname, pg_size_pretty(pg_database_size(datname)) FROM pg_database WHERE datname='secureops_db';" 2>/dev/null

echo ""
echo "Service memory usage:"
sudo ps aux | grep -E "(gunicorn|nginx|postgres)" | grep -v grep | awk '{printf "  %s: %s MB\n", $11, int($6/1024)}'

echo ""
echo "═══════════════════════════════════════════════════════"
echo "📋 RECOMMENDATIONS & NEXT STEPS"
echo "═══════════════════════════════════════════════════════"
echo ""

# Check for issues
if [ "$FAIL" -gt 0 ]; then
    echo "${RED}⚠️  $FAIL issue(s) detected!${NC}"
    echo ""
    echo "Common fixes:"
    echo "  1. Restart services: sudo systemctl restart api postgresql nginx"
    echo "  2. Check logs: sudo tail -f /var/log/api_error.log"
    echo "  3. Verify DB: psql -U secureops_user -d secureops_db -c '\\dt'"
    echo ""
fi

echo "Recommendations for production:"
echo "  ☐ Setup SSL certificate: sudo certbot --nginx -d yourdomain.com"
echo "  ☐ Configure automated backups: crontab -e (add backup script)"
echo "  ☐ Monitor logs: Install logrotate for log rotation"
echo "  ☐ Setup monitoring: Consider tools like Prometheus, DataDog, or New Relic"
echo "  ☐ Rate limiting: Add rate limiting to Nginx for API endpoints"
echo "  ☐ Database tuning: Optimize PostgreSQL for your workload"
echo "  ☐ Increase workers: Adjust Gunicorn workers based on CPU cores"
echo "  ☐ Add caching: Redis for session caching (if needed)"

echo ""
echo "═══════════════════════════════════════════════════════"
echo "🎯 SUMMARY"
echo "═══════════════════════════════════════════════════════"
echo ""
echo -e "Tests Passed: ${GREEN}$PASS${NC}"
echo -e "Tests Failed: ${RED}$FAIL${NC}"
echo ""

if [ "$FAIL" -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED!${NC}"
    echo ""
    echo "Your API is ready for production!"
    echo ""
    echo "Access your API at:"
    echo "  http://$SERVER_IP"
    echo ""
    echo "Manage services:"
    echo "  sudo systemctl {start|stop|restart|status} api"
    echo "  sudo systemctl {start|stop|restart|status} nginx"
    echo "  sudo systemctl {start|stop|restart|status} postgresql"
else
    echo -e "${RED}❌ ISSUES DETECTED - Please fix before going to production${NC}"
    echo ""
    echo "Debug tips:"
    echo "  1. Check service status: sudo systemctl status api"
    echo "  2. View error logs: sudo journalctl -u api -n 50"
    echo "  3. Test manually: curl http://127.0.0.1:5000/health"
fi

echo ""
