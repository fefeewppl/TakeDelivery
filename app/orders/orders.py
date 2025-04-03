from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_required, current_user
from app.models import Restaurant, Product, Order, OrderItem  # Changed from .models import Restaurant, Product, Order, OrderItem
from app.extensions import db
from datetime import datetime

orders = Blueprint('orders', __name__)

@orders.route('/cart')
def view_cart():
    cart = session.get('cart', [])
    cart_items = []
    total = 0
    restaurant = None
    
    if cart:
        # Check if cart is a list (new structure) or dict (old structure)
        if isinstance(cart, list):
            # New structure: list of items
            restaurant_id = cart[0]['restaurant_id']
            restaurant = Restaurant.query.get_or_404(restaurant_id)
            
            # Get all products in the cart
            for item in cart:
                product = Product.query.get(item['product_id'])
                if product:
                    subtotal = product.price * item['quantity']
                    cart_items.append({
                        'product': product,
                        'quantity': item['quantity'],
                        'subtotal': subtotal
                    })
                    total += subtotal
        else:
            # Old structure: dictionary with 'items' and 'restaurant_id'
            restaurant_id = cart.get('restaurant_id')
            if restaurant_id:
                restaurant = Restaurant.query.get_or_404(restaurant_id)
                
                # Get all products in the cart
                for product_id, item in cart.get('items', {}).items():
                    product = Product.query.get(int(product_id))
                    if product:
                        subtotal = product.price * item['quantity']
                        cart_items.append({
                            'product': product,
                            'quantity': item['quantity'],
                            'subtotal': subtotal
                        })
                        total += subtotal
    
    return render_template('orders/cart.html', cart_items=cart_items, total=total, restaurant=restaurant)

@orders.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product_id = request.form.get('product_id')
    restaurant_id = request.form.get('restaurant_id')
    quantity = int(request.form.get('quantity', 1))
    
    # Initialize session cart if it doesn't exist or convert dict to list
    if 'cart' not in session:
        session['cart'] = []
    elif isinstance(session['cart'], dict):
        # Convert old dict structure to new list structure
        old_cart = session['cart']
        new_cart = []
        
        if 'items' in old_cart and 'restaurant_id' in old_cart:
            for prod_id, item in old_cart['items'].items():
                new_cart.append({
                    'product_id': int(prod_id),
                    'restaurant_id': old_cart['restaurant_id'],
                    'quantity': item['quantity']
                })
        
        session['cart'] = new_cart
    
    # Now cart is guaranteed to be a list
    cart = session['cart']
    
    # Check if cart is empty
    if not cart:
        # Empty cart, just add the item
        cart_item = {
            'product_id': int(product_id),
            'restaurant_id': int(restaurant_id),
            'quantity': quantity
        }
        cart.append(cart_item)
        session.modified = True
        flash('Item added to cart!', 'success')
        return redirect(url_for('restaurants.restaurant_detail', restaurant_id=restaurant_id))
    
    # Check if adding from a different restaurant
    if len(cart) > 0:
        first_item = cart[0]
        if isinstance(first_item, dict) and 'restaurant_id' in first_item:
            if first_item['restaurant_id'] != int(restaurant_id):
                flash('You can only order from one restaurant at a time. Clear your cart first.', 'warning')
                return redirect(url_for('restaurants.restaurant_detail', restaurant_id=restaurant_id))
    
    # Add item to cart
    cart_item = {
        'product_id': int(product_id),
        'restaurant_id': int(restaurant_id),
        'quantity': quantity
    }
    
    # Check if product already in cart
    for i, item in enumerate(cart):
        if isinstance(item, dict) and 'product_id' in item:
            if item['product_id'] == int(product_id):
                item['quantity'] += quantity
                session.modified = True
                flash('Cart updated!', 'success')
                return redirect(url_for('restaurants.restaurant_detail', restaurant_id=restaurant_id))
    
    # Add new item
    cart.append(cart_item)
    session.modified = True
    flash('Item added to cart!', 'success')
    return redirect(url_for('restaurants.restaurant_detail', restaurant_id=restaurant_id))

@orders.route('/debug_cart')
def debug_cart():
    from flask import session as flask_session, jsonify
    cart_data = flask_session.get('cart', {})
    return jsonify({
        'cart': cart_data,
        'session_id': id(flask_session),
        'session_keys': list(flask_session.keys())
    })

@orders.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    cart = session.get('cart', [])
    
    if isinstance(cart, list):
        # New structure: list of items
        for i, item in enumerate(cart):
            if item['product_id'] == product_id:
                cart.pop(i)
                break
    else:
        # Old structure: dictionary with 'items'
        if 'items' in cart and str(product_id) in cart['items']:
            del cart['items'][str(product_id)]
    
    session['cart'] = cart
    session.modified = True
    flash('Item removido do carrinho', 'success')
    
    return redirect(url_for('orders.view_cart'))

@orders.route('/clear_cart')
def clear_cart():
    session.pop('cart', None)
    session.modified = True
    flash('Carrinho esvaziado', 'info')
    return redirect(url_for('main.index'))

@orders.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart = session.get('cart', [])
    
    if not cart:
        flash('Seu carrinho está vazio', 'info')
        return redirect(url_for('main.index'))
    
    products = []
    total = 0
    restaurant = None
    
    # Handle both cart structures
    if isinstance(cart, list):
        # New structure: list of items
        if not cart:
            flash('Seu carrinho está vazio', 'info')
            return redirect(url_for('main.index'))
            
        restaurant_id = cart[0]['restaurant_id']
        restaurant = Restaurant.query.get_or_404(restaurant_id)
        
        for item in cart:
            product = Product.query.get(item['product_id'])
            if product:
                quantity = item['quantity']
                price = product.price
                subtotal = price * quantity
                total += subtotal
                
                products.append({
                    'id': product.id,
                    'name': product.name,
                    'price': price,
                    'quantity': quantity,
                    'subtotal': subtotal
                })
    else:
        # Old structure: dictionary with 'items' and 'restaurant_id'
        if not cart or 'items' not in cart or not cart['items']:
            flash('Seu carrinho está vazio', 'info')
            return redirect(url_for('main.index'))
            
        restaurant_id = cart.get('restaurant_id')
        restaurant = Restaurant.query.get_or_404(restaurant_id)
        cart_items = cart.get('items', {})
        
        for product_id, item in cart_items.items():
            product = Product.query.get(int(product_id))
            if product:
                quantity = item['quantity']
                price = product.price
                subtotal = price * quantity
                total += subtotal
                
                products.append({
                    'id': product.id,
                    'name': product.name,
                    'price': price,
                    'quantity': quantity,
                    'subtotal': subtotal
                })
    
    if restaurant and total < restaurant.min_order:
        flash(f'O valor mínimo do pedido é R$ {restaurant.min_order}', 'warning')
        return redirect(url_for('orders.view_cart'))
    
    # Check if user is logged in
    is_guest = not current_user.is_authenticated
    
    if request.method == 'POST':
        delivery_address = request.form.get('address')
        customer_name = request.form.get('name')
        customer_email = request.form.get('email')
        customer_phone = request.form.get('phone')
        
        # Create guest user if needed
        user_id = None
        if current_user.is_authenticated:
            user_id = current_user.id
        
        # Create order
        order = Order(
            user_id=user_id,
            restaurant_id=restaurant_id,
            total=total + restaurant.delivery_fee,
            delivery_address=delivery_address,
            customer_name=customer_name if is_guest else current_user.username,
            customer_email=customer_email if is_guest else current_user.email,
            customer_phone=customer_phone if is_guest else current_user.phone,
            is_guest=is_guest
        )
        
        db.session.add(order)
        db.session.flush()  # Get the order ID
        
        # Create order items - handle both cart structures
        if isinstance(cart, list):
            for item in cart:
                product = Product.query.get(item['product_id'])
                if product:
                    order_item = OrderItem(
                        order_id=order.id,
                        product_id=product.id,
                        quantity=item['quantity'],
                        price=product.price
                    )
                    db.session.add(order_item)
        else:
            for product_id, item in cart.get('items', {}).items():
                product = Product.query.get(int(product_id))
                if product:
                    order_item = OrderItem(
                        order_id=order.id,
                        product_id=product.id,
                        quantity=item['quantity'],
                        price=product.price
                    )
                    db.session.add(order_item)
        
        db.session.commit()
        
        # Clear cart
        session.pop('cart', None)
        session.modified = True
        
        flash('Seu pedido foi realizado com sucesso!', 'success')
        return redirect(url_for('orders.order_confirmation', order_id=order.id))
    
    return render_template('orders/checkout.html', 
                          products=products, 
                          total=total, 
                          restaurant=restaurant,
                          delivery_fee=restaurant.delivery_fee if restaurant else 0,
                          grand_total=total + (restaurant.delivery_fee if restaurant else 0),
                          is_guest=is_guest)

@orders.route('/my_orders')
@login_required
def my_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('orders/my_orders.html', orders=orders)

@orders.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Check if the order belongs to the current user or the restaurant owner
    restaurant = Restaurant.query.get(order.restaurant_id)
    if order.user_id != current_user.id and restaurant.user_id != current_user.id:
        flash('Você não tem permissão para visualizar este pedido', 'danger')
        return redirect(url_for('main.index'))
    
    return render_template('orders/order_detail.html', order=order)

@orders.route('/restaurant_orders')
@login_required
def restaurant_orders():
    if not current_user.is_restaurant:
        flash('Você precisa registrar um restaurante primeiro', 'warning')
        return redirect(url_for('restaurants.register_restaurant'))
    
    restaurant = Restaurant.query.filter_by(user_id=current_user.id).first_or_404()
    orders = Order.query.filter_by(restaurant_id=restaurant.id).order_by(Order.created_at.desc()).all()
    
    return render_template('orders/restaurant_orders.html', orders=orders)

@orders.route('/update_order_status/<int:order_id>', methods=['POST'])
@login_required
def update_order_status(order_id):
    if not current_user.is_restaurant:
        return jsonify({'success': False, 'message': 'Não autorizado'}), 403
    
    order = Order.query.get_or_404(order_id)
    restaurant = Restaurant.query.filter_by(user_id=current_user.id).first_or_404()
    
    if order.restaurant_id != restaurant.id:
        return jsonify({'success': False, 'message': 'Não autorizado'}), 403
    
    status = request.form.get('status')
    valid_statuses = ['pendente', 'confirmado', 'preparando', 'em_entrega', 'entregue', 'cancelado']
    
    if status not in valid_statuses:
        return jsonify({'success': False, 'message': 'Status inválido'}), 400
    
    order.status = status
    order.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Status do pedido atualizado'})


@orders.route('/order_confirmation/<int:order_id>')
def order_confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    
    # For guest users, we don't check ownership
    if current_user.is_authenticated and order.user_id != current_user.id:
        flash('Você não tem permissão para visualizar este pedido', 'danger')
        return redirect(url_for('main.index'))
    
    return render_template('orders/order_confirmation.html', order=order)