from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from . import users
from app.extensions import db
from app.models import User

@users.route('/profile')
@login_required
def profile():
    return render_template('users/profile.html', user=current_user)

@users.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    # Placeholder for now
    return render_template('users/edit_profile.html', user=current_user)

@users.route('/address/add', methods=['GET', 'POST'])
@login_required
def add_address():
    # Placeholder for now
    return render_template('users/add_address.html')