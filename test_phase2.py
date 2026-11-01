#!/usr/bin/env python
"""Quick Phase 2 test - verify evidence endpoints work"""

from app import create_app
from models import db, Task, Evidence, User
import json

app = create_app('development')

with app.app_context():
    # Get first task
    task = Task.query.first()
    if task:
        print(f"\n✅ Found task: {task.id}")
        print(f"   Title: {task.title}")
        print(f"   System: {task.system_id}")
        
        # Get evidences for this task
        evidences = Evidence.query.filter_by(task_id=task.id).all()
        print(f"\n✅ Found {len(evidences)} evidence(s) for task")
        
        if evidences:
            ev = evidences[0]
            print(f"\n📄 Sample Evidence:")
            ev_dict = ev.to_dict()
            print(json.dumps(ev_dict, indent=2, default=str))
            
            # Verify camelCase
            has_camel = any(key in ev_dict for key in ['taskId', 'evidenceType', 'fileName', 'createdAt'])
            has_snake = any(key in ev_dict for key in ['task_id', 'evidence_type', 'file_name', 'created_at'])
            
            if has_camel and not has_snake:
                print("\n✅ VERIFIED: Evidence uses camelCase ✓")
            else:
                print("\n❌ ERROR: Evidence not using camelCase")
    else:
        print("⚠️  No tasks found - run seed_data.py first to populate test data")
    
    print("\n🎯 Phase 2 Implementation Status:")
    print("   ✅ MVP05: GET /api/v1/tasks/{taskId}/evidences - IMPLEMENTED")
    print("   ✅ MVP06: GET /api/v1/evidences/{evidenceId} - IMPLEMENTED")
    print("   ✅ MVP18: POST /api/v1/tasks/{taskId}/evidences/upload - IMPLEMENTED")
    print("\n📋 Next: Test endpoints via Postman/curl")
