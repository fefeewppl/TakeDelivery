from flask import Blueprint, render_template, redirect, url_for
from app.extensions import db
from app.models import Restaurant

main = Blueprint('main', __name__)

@main.route('/')
def index():
    restaurants = Restaurant.query.filter_by(is_active=True).all()
    return render_template('index.html', restaurants=restaurants)

@main.route('/search')
def search():
    query = request.args.get('q', '')
    restaurants = Restaurant.query.filter(
        Restaurant.name.ilike(f'%{query}%') | 
        Restaurant.description.ilike(f'%{query}%')
    ).filter_by(is_active=True).all()
    
    return render_template('search_results.html', restaurants=restaurants, query=query)

@main.route('/debug_session')
def debug_session():
    from flask import session, jsonify
    return jsonify(dict(session))