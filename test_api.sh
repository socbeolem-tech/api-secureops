#!/bin/bash
# Test SecureOps API Endpoints
# Run: bash test_api.sh

BASE_URL="http://localhost:5000"

echo "================================================"
echo "Testing SecureOps API - Phase 1 (MVP01-04)"
echo "================================================"

# Step 1: Get health check
echo -e "\n[1] Health Check"
echo "GET $BASE_URL/health"
curl -s "$BASE_URL/health" | python -m json.tool
echo ""

# Step 2: Generate test token for CTV
echo -e "\n[2] Generate Test Token (CTV)"
echo "GET $BASE_URL/auth/test-token?role=CTV"
TOKEN_RESPONSE=$(curl -s "$BASE_URL/auth/test-token?role=CTV&email=ctv@secureops.local")
TOKEN=$(echo $TOKEN_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin)['token'])")
echo "Token: $TOKEN"
echo ""

# Step 3: Verify token
echo -e "\n[3] Verify Token (Who Am I)"
echo "GET $BASE_URL/auth/whoami"
curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/auth/whoami" | python -m json.tool
echo ""

# Step 4: MVP01 - Get my tasks
echo -e "\n[4] MVP01 - Get My Tasks"
echo "GET $BASE_URL/api/v1/my/tasks"
curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/v1/my/tasks" | python -m json.tool
echo ""

# Step 5: MVP02 - Get task detail (requires task ID)
# First extract a task ID from previous response
TASK_ID=$(curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/v1/my/tasks" | python -c "import sys, json; tasks = json.load(sys.stdin)['data']; print(tasks[0]['id'] if tasks else '')")

if [ -n "$TASK_ID" ]; then
    echo -e "\n[5] MVP02 - Get Task Detail"
    echo "GET $BASE_URL/api/v1/tasks/$TASK_ID"
    curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/v1/tasks/$TASK_ID" | python -m json.tool
    echo ""
    
    # Step 6: MVP03 - Mark updates seen
    echo -e "\n[6] MVP03 - Mark Updates Seen"
    echo "POST $BASE_URL/api/v1/tasks/$TASK_ID/actions/mark-updates-seen"
    curl -s -X POST \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{}' \
        "$BASE_URL/api/v1/tasks/$TASK_ID/actions/mark-updates-seen" | python -m json.tool
    echo ""
    
    # Step 7: MVP04 - Update assessment
    echo -e "\n[7] MVP04 - Update Task Assessment"
    echo "PUT $BASE_URL/api/v1/tasks/$TASK_ID/assessment"
    
    # Get ETag from previous response
    ETAG=$(curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/v1/tasks/$TASK_ID" -w "\n%{http_code}" | head -1)
    
    curl -s -X PUT \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -H "If-Match: \"1\"" \
        -d '{"assessment":"Investigation completed. No critical issues found."}' \
        "$BASE_URL/api/v1/tasks/$TASK_ID/assessment" | python -m json.tool
    echo ""
else
    echo "❌ Could not extract task ID"
fi

echo "================================================"
echo "✅ All tests completed!"
echo "================================================"
