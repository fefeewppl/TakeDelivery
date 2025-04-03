from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.models import Restaurant, Category, Product, User  # Changed from .models import Restaurant, Category, Product, User
from app.extensions import db
import os
from werkzeug.utils import secure_filename
import uuid

restaurants = Blueprint('restaurants', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

def save_picture(form_picture):
    random_hex = uuid.uuid4().hex
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/uploads', picture_fn)
    form_picture.save(picture_path)
    return picture_fn

# Adicione esta rota ao seu arquivo restaurants.py

@restaurants.route('/<int:restaurant_id>')
def restaurant_detail(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    categories = Category.query.filter_by(restaurant_id=restaurant_id).all()
    products = Product.query.filter_by(restaurant_id=restaurant_id).all()
    return render_template('restaurants/detail.html', restaurant=restaurant, categories=categories, products=products)

@restaurants.route('/register', methods=['GET', 'POST'])
@login_required
def register_restaurant():
    if current_user.is_restaurant:
        flash('You already have a registered restaurant', 'info')
        return redirect(url_for('restaurants.dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        address = request.form.get('address')
        phone = request.form.get('phone')
        delivery_fee = float(request.form.get('delivery_fee', 0))
        min_order = float(request.form.get('min_order', 0))
        
        # Debug print
        print("Form data:", request.form)
        print("Files:", request.files)
        
        logo = None
        if 'image' in request.files:  # Note: your form uses 'image' not 'logo'
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                logo = save_picture(file)
                print(f"Logo saved as: {logo}")  # Debug print
        
        restaurant = Restaurant(
            name=name,
            description=description,
            address=address,
            phone=phone,
            delivery_fee=delivery_fee,
            min_order=min_order,
            user_id=current_user.id,
            logo=logo  # Make sure this is set
        )
        
        db.session.add(restaurant)
        db.session.commit()
        
        # After commit, verify the logo was saved
        print(f"Restaurant created with logo: {restaurant.logo}")  # Debug print
        
        current_user.is_restaurant = True
        db.session.commit()
        
        flash('Your restaurant has been registered!', 'success')
        return redirect(url_for('restaurants.dashboard'))
    
    return render_template('restaurants/register.html')

@restaurants.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_restaurant:
        flash('You need to register a restaurant first', 'warning')
        return redirect(url_for('restaurants.register_restaurant'))
    
    restaurant = Restaurant.query.filter_by(user_id=current_user.id).first_or_404()
    categories = Category.query.filter_by(restaurant_id=restaurant.id).all()
    products = Product.query.filter_by(restaurant_id=restaurant.id).all()
    
    return render_template('restaurants/dashboard.html', 
                          restaurant=restaurant, 
                          categories=categories, 
                          products=products)

@restaurants.route('/category/add', methods=['GET', 'POST'])
@login_required
def add_category():
    if not current_user.is_restaurant:
        flash('You need to register a restaurant first', 'warning')
        return redirect(url_for('restaurants.register_restaurant'))
    
    restaurant = Restaurant.query.filter_by(user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        name = request.form.get('name')
        
        category = Category(name=name, restaurant_id=restaurant.id)
        db.session.add(category)
        db.session.commit()
        
        flash('Category added successfully!', 'success')
        return redirect(url_for('restaurants.dashboard'))
    
    return render_template('restaurants/add_category.html')

@restaurants.route('/product/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if not current_user.is_restaurant:
        flash('You need to register a restaurant first', 'warning')
        return redirect(url_for('restaurants.register_restaurant'))
    
    restaurant = Restaurant.query.filter_by(user_id=current_user.id).first_or_404()
    categories = Category.query.filter_by(restaurant_id=restaurant.id).all()
    
    if not categories:
        flash('You need to add a category first', 'warning')
        return redirect(url_for('restaurants.add_category'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        category_id = int(request.form.get('category_id'))
        
        image = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                image = save_picture(file)
        
        product = Product(
            name=name,
            description=description,
            price=price,
            category_id=category_id,
            restaurant_id=restaurant.id
        )
        
        if image:
            product.image = image
        
        db.session.add(product)
        db.session.commit()
        
        flash('Product added successfully!', 'success')
        return redirect(url_for('restaurants.dashboard'))
    
    return render_template('restaurants/add_product.html', categories=categories)

@restaurants.route('/edit', methods=['GET', 'POST'])
@login_required
def edit_restaurant():
    if not current_user.is_restaurant:
        flash('You need to register a restaurant first', 'warning')
        return redirect(url_for('restaurants.register_restaurant'))
    
    restaurant = Restaurant.query.filter_by(user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        restaurant.name = request.form.get('name')
        restaurant.description = request.form.get('description')
        restaurant.address = request.form.get('address')
        restaurant.phone = request.form.get('phone')
        restaurant.delivery_fee = float(request.form.get('delivery_fee', 0))
        restaurant.min_order = float(request.form.get('min_order', 0))
        restaurant.is_active = 'is_active' in request.form
        
        if 'logo' in request.files:
            file = request.files['logo']
            if file and file.filename != '' and allowed_file(file.filename):
                logo = save_picture(file)
                restaurant.logo = logo
        
        db.session.commit()
        flash('Restaurant information updated successfully!', 'success')
        return redirect(url_for('restaurants.dashboard'))
    
    return render_template('restaurants/edit_restaurant.html', restaurant=restaurant)


@restaurants.route('/debug_restaurant')
@login_required
def debug_restaurant():
    restaurant = Restaurant.query.filter_by(user_id=current_user.id).first()
    if restaurant:
        return f"Restaurant: {restaurant.name}, Logo: {restaurant.logo}"
    return "No restaurant found"