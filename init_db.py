import os
import sys

# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import User, Restaurant, Category, Product, Order, OrderItem

app = create_app('development')

with app.app_context():
    # Create all tables
    db.create_all()
    
    # Check if admin user exists
    admin = User.query.filter_by(email='admin@example.com').first()
    if not admin:
        # Create admin user
        admin = User(
            username='admin',
            email='admin@example.com',
            is_admin=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('Admin user created successfully!')
    
    print('Database initialized successfully!')