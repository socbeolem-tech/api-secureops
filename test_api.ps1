# Test SecureOps API Endpoints (PowerShell)
# Run: powershell -ExecutionPolicy Bypass -File test_api.ps1

$baseUrl = "http://localhost:5000"

Write-Host "================================================" -ForegroundColor Green
Write-Host "Testing SecureOps API - Phase 1 (MVP01-04)" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green

# Step 1: Health Check
Write-Host "`n[1] Health Check" -ForegroundColor Yellow
Write-Host "GET $baseUrl/health"
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/health" -UseBasicParsing | ConvertFrom-Json
    Write-Host ($response | ConvertTo-Json -Depth 10) -ForegroundColor White
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
}

# Step 2: Generate test token
Write-Host "`n[2] Generate Test Token (CTV)" -ForegroundColor Yellow
Write-Host "GET $baseUrl/auth/test-token?role=CTV"
try {
    $tokenResponse = Invoke-WebRequest -Uri "$baseUrl/auth/test-token?role=CTV&email=ctv@secureops.local" -UseBasicParsing
    $tokenJson = $tokenResponse.Content | ConvertFrom-Json
    $token = $tokenJson.token
    Write-Host "✅ Token generated successfully" -ForegroundColor Green
    Write-Host "Token: $token" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    exit 1
}

# Step 3: Verify token
Write-Host "`n[3] Verify Token (Who Am I)" -ForegroundColor Yellow
Write-Host "GET $baseUrl/auth/whoami"
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/auth/whoami" -Headers @{"Authorization" = "Bearer $token"} -UseBasicParsing
    $json = $response.Content | ConvertFrom-Json
    Write-Host ($json | ConvertTo-Json -Depth 10) -ForegroundColor White
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
}

# Step 4: MVP01 - Get my tasks
Write-Host "`n[4] MVP01 - Get My Tasks" -ForegroundColor Yellow
Write-Host "GET $baseUrl/api/v1/my/tasks"
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/api/v1/my/tasks" -Headers @{"Authorization" = "Bearer $token"} -UseBasicParsing
    $json = $response.Content | ConvertFrom-Json
    Write-Host ($json | ConvertTo-Json -Depth 10) -ForegroundColor White
    
    # Extract task ID for next tests
    if ($json.data -and $json.data.Count -gt 0) {
        $taskId = $json.data[0].id
        Write-Host "`n✅ Found task: $taskId" -ForegroundColor Green
        
        # Step 5: MVP02 - Get task detail
        Write-Host "`n[5] MVP02 - Get Task Detail" -ForegroundColor Yellow
        Write-Host "GET $baseUrl/api/v1/tasks/$taskId"
        try {
            $response = Invoke-WebRequest -Uri "$baseUrl/api/v1/tasks/$taskId" -Headers @{"Authorization" = "Bearer $token"} -UseBasicParsing
            $json = $response.Content | ConvertFrom-Json
            Write-Host ($json | ConvertTo-Json -Depth 10) -ForegroundColor White
            
            # Store version for If-Match header
            $version = $json.data.version
            Write-Host "`n✅ Task version: $version" -ForegroundColor Green
            
            # Step 6: MVP03 - Mark updates seen
            Write-Host "`n[6] MVP03 - Mark Updates Seen" -ForegroundColor Yellow
            Write-Host "POST $baseUrl/api/v1/tasks/$taskId/actions/mark-updates-seen"
            try {
                $body = @{} | ConvertTo-Json
                $response = Invoke-WebRequest -Uri "$baseUrl/api/v1/tasks/$taskId/actions/mark-updates-seen" `
                    -Method POST `
                    -Headers @{"Authorization" = "Bearer $token"; "Content-Type" = "application/json"} `
                    -Body $body `
                    -UseBasicParsing
                $json = $response.Content | ConvertFrom-Json
                Write-Host ($json | ConvertTo-Json -Depth 10) -ForegroundColor White
            } catch {
                Write-Host "❌ Error: $_" -ForegroundColor Red
            }
            
            # Step 7: MVP04 - Update assessment
            Write-Host "`n[7] MVP04 - Update Task Assessment (with If-Match)" -ForegroundColor Yellow
            Write-Host "PUT $baseUrl/api/v1/tasks/$taskId/assessment"
            try {
                $body = @{
                    assessment = "Investigation completed. No critical issues found. System status: HEALTHY"
                } | ConvertTo-Json
                
                $response = Invoke-WebRequest -Uri "$baseUrl/api/v1/tasks/$taskId/assessment" `
                    -Method PUT `
                    -Headers @{
                        "Authorization" = "Bearer $token"
                        "Content-Type" = "application/json"
                        "If-Match" = "`"$version`""
                    } `
                    -Body $body `
                    -UseBasicParsing
                
                $json = $response.Content | ConvertFrom-Json
                Write-Host ($json | ConvertTo-Json -Depth 10) -ForegroundColor White
                Write-Host "`n✅ Assessment updated successfully" -ForegroundColor Green
            } catch {
                Write-Host "❌ Error: $_" -ForegroundColor Red
            }
        } catch {
            Write-Host "❌ Error: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "❌ No tasks found" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
}

Write-Host "`n================================================" -ForegroundColor Green
Write-Host "✅ All tests completed!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
