import os
from app import create_app, db
from app.models import User, Restaurant, Category, Product, Order, OrderItem

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Restaurant=Restaurant, 
                Category=Category, Product=Product, 
                Order=Order, OrderItem=OrderItem)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)