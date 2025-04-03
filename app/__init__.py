from flask import Flask
from .config import config
from .extensions import db, migrate, login_manager, bcrypt
from datetime import timedelta

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Ensure session configuration
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    
    # Make session permanent
    @app.before_request
    def make_session_permanent():
        from flask import session
        session.permanent = True
    
    # Register blueprints
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    from .restaurants import restaurants as restaurants_blueprint
    app.register_blueprint(restaurants_blueprint, url_prefix='/restaurants')
    
    from .orders import orders as orders_blueprint
    app.register_blueprint(orders_blueprint, url_prefix='/orders')
    
    # Register the users blueprint
    from .users import users as users_blueprint
    app.register_blueprint(users_blueprint, url_prefix='/users')
    
    return app