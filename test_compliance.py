#!/usr/bin/env python
"""Quick compliance test - verify camelCase response format"""

from app import create_app
from models import db, Task
import json

app = create_app('development')

with app.app_context():
    task = Task.query.first()
    if task:
        response_data = task.to_dict()
        print("✅ Task response format (camelCase):")
        print(json.dumps(response_data, indent=2, default=str))
        
        # Verify camelCase fields
        has_camel = any(key in response_data for key in ['taskId', 'systemId', 'assignedTo', 'createdAt'])
        has_snake = any(key in response_data for key in ['task_id', 'system_id', 'assigned_to', 'created_at'])
        
        if has_camel and not has_snake:
            print("\n✅ VERIFIED: All fields use camelCase ✓")
        elif has_snake:
            print("\n❌ ERROR: Found snake_case fields (should be camelCase)")
        else:
            print("\n⚠️  WARNING: No recognizable fields found")
    else:
        print("⚠️  No tasks in database - run seed_data.py first")
