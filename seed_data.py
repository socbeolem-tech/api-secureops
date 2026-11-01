"""
Seed database with test data for development
Run: python seed_data.py
"""
from app import create_app
from models import db, User, System, Task
import uuid

def seed_data():
    """Create test users, systems, and tasks"""
    app = create_app()
    
    with app.app_context():
        # Check if data already exists
        if User.query.count() > 0:
            print("ℹ️ Data already exists. Skipping seed.")
            return
        
        # ====================================================================
        # CREATE USERS
        # ====================================================================
        users = [
            User(
                id=str(uuid.uuid4()),
                email='ctv@secureops.local',
                full_name='Analyst CTV 001',
                role='CTV',
                is_active=True
            ),
            User(
                id=str(uuid.uuid4()),
                email='l2@secureops.local',
                full_name='L2 Analyst',
                role='L2',
                is_active=True
            ),
            User(
                id=str(uuid.uuid4()),
                email='l3@secureops.local',
                full_name='L3 Team Lead',
                role='L3',
                is_active=True
            ),
            User(
                id=str(uuid.uuid4()),
                email='l4@secureops.local',
                full_name='L4 Manager',
                role='L4',
                is_active=True
            ),
            User(
                id=str(uuid.uuid4()),
                email='admin@secureops.local',
                full_name='System Administrator',
                role='ADMIN',
                is_active=True
            )
        ]
        
        for user in users:
            db.session.add(user)
        
        db.session.commit()
        print(f"✅ Created {len(users)} users")
        
        # Get CTV user for later
        ctv_user = User.query.filter_by(email='ctv@secureops.local').first()
        
        # ====================================================================
        # CREATE SYSTEMS
        # ====================================================================
        systems = [
            System(
                id=str(uuid.uuid4()),
                name='critical_infrastructure',
                description='Critical infrastructure systems',
                sensitivity_level='Top Secret',
                is_active=True
            ),
            System(
                id=str(uuid.uuid4()),
                name='network_security',
                description='Network security monitoring',
                sensitivity_level='Confidential',
                is_active=True
            ),
            System(
                id=str(uuid.uuid4()),
                name='application_security',
                description='Application security systems',
                sensitivity_level='Internal',
                is_active=True
            )
        ]
        
        for system in systems:
            db.session.add(system)
        
        db.session.commit()
        print(f"✅ Created {len(systems)} systems")
        
        # ====================================================================
        # ASSIGN USERS TO SYSTEMS
        # ====================================================================
        for user in users:
            # All users can access all systems (for testing)
            for system in systems:
                user.assigned_systems.append(system)
        
        db.session.commit()
        print(f"✅ Assigned users to systems")
        
        # ====================================================================
        # CREATE TASKS
        # ====================================================================
        critical_sys = systems[0]
        
        tasks = [
            Task(
                id=str(uuid.uuid4()),
                title='Investigate suspicious network activity',
                description='Multiple failed login attempts detected on admin accounts',
                status='in_progress',
                priority='critical',
                system_id=critical_sys.id,
                assigned_to=ctv_user.id,
                assessment=None,
                version=1
            ),
            Task(
                id=str(uuid.uuid4()),
                title='Review firewall configuration',
                description='Quarterly review of firewall rules and policies',
                status='pending',
                priority='high',
                system_id=critical_sys.id,
                assigned_to=ctv_user.id,
                assessment=None,
                version=1
            ),
            Task(
                id=str(uuid.uuid4()),
                title='Patch management execution',
                description='Apply security patches to critical servers',
                status='completed',
                priority='high',
                system_id=critical_sys.id,
                assigned_to=ctv_user.id,
                assessment='All patches applied successfully. Systems rebooted and verified operational.',
                version=2
            )
        ]
        
        for task in tasks:
            db.session.add(task)
        
        db.session.commit()
        print(f"✅ Created {len(tasks)} tasks")
        
        # ====================================================================
        # SUMMARY
        # ====================================================================
        print("\n" + "="*60)
        print("✅ Database seeded successfully!")
        print("="*60)
        print(f"\nTest Users (use email + get token):")
        for user in users:
            print(f"  - {user.email} ({user.role})")
        print(f"\nTest Systems:")
        for system in systems:
            print(f"  - {system.name}")
        print(f"\nTest Tasks:")
        for task in tasks:
            print(f"  - {task.title} (assigned to {ctv_user.email})")
        
        print("\n" + "="*60)
        print("Next Steps:")
        print("="*60)
        print("1. Get test token:")
        print("   curl http://localhost:5000/auth/test-token?role=CTV")
        print("\n2. Use token to test endpoints:")
        print("   curl -H 'Authorization: Bearer <token>' \\")
        print("        http://localhost:5000/api/v1/my/tasks")
        print("="*60 + "\n")

if __name__ == '__main__':
    seed_data()
