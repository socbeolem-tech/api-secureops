"""
Script để khởi tạo database PostgreSQL
Chạy: python db_init.py
"""
from app import create_app
from models import db, Task

def init_db():
    """Tạo các bảng trong database"""
    app = create_app()
    
    with app.app_context():
        # Tạo tất cả tables
        db.create_all()
        print("✅ Database tables created successfully!")
        
        # Thêm sample data (optional)
        if Task.query.count() == 0:
            sample_tasks = [
                Task(
                    title='Setup PostgreSQL',
                    description='Cài đặt và cấu hình PostgreSQL',
                    status='completed',
                    priority='high'
                ),
                Task(
                    title='Viết API endpoints',
                    description='Viết các API endpoints chính',
                    status='in_progress',
                    priority='high'
                ),
                Task(
                    title='Viết unit tests',
                    description='Viết tests cho các APIs',
                    status='pending',
                    priority='medium'
                )
            ]
            
            for task in sample_tasks:
                db.session.add(task)
            
            db.session.commit()
            print("✅ Sample data inserted successfully!")
        else:
            print("ℹ️ Database already has data, skipping sample insertion")

if __name__ == '__main__':
    init_db()
