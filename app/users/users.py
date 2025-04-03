from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import User  # Changed from .models import User
from app.extensions import db, bcrypt

users = Blueprint('users', __name__)

@users.route('/profile')
@login_required
def profile():
    return render_template('users/profile.html')

@users.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        address = request.form.get('address')
        phone = request.form.get('phone')
        
        # Check if username is taken by another user
        if username != current_user.username and User.query.filter_by(username=username).first():
            flash('Username already taken', 'danger')
            return redirect(url_for('users.edit_profile'))
        
        # Check if email is taken by another user
        if email != current_user.email and User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('users.edit_profile'))
        
        current_user.username = username
        current_user.email = email
        current_user.address = address
        current_user.phone = phone
        
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('users.profile'))
    
    return render_template('users/edit_profile.html')

@users.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_user.check_password(current_password):
            flash('Current password is incorrect', 'danger')
            return redirect(url_for('users.change_password'))
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'danger')
            return redirect(url_for('users.change_password'))
        
        current_user.set_password(new_password)
        db.session.commit()
        flash('Your password has been updated!', 'success')
        return redirect(url_for('users.profile'))
    
    return render_template('users/change_password.html')