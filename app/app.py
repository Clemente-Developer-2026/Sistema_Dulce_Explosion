from flask import Flask
from flask_migrate import Migrate
from app.extensions import db, bcrypt, login_manager
from app.models import Usuario
from datetime import datetime

migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object("app.config.Config")
    db.init_app(app)
    bcrypt.init_app(app) 
    login_manager.init_app(app)
    migrate.init_app(app, db)

    @app.context_processor
    def inject_datetime():
        """Inyecta datetime en todos los templates"""
        return {'datetime': datetime}

    from app.utils import get_image_url
    @app.context_processor
    def inject_image_helpers():
        return {
            'get_image_url': get_image_url
        }
    
    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'

    from app.main import main_bp
    from app.auth import usuarios_bp
    from app.admin import administrador_bp

    app.register_blueprint(main_bp)  
    app.register_blueprint(usuarios_bp, url_prefix='/auth')
    app.register_blueprint(administrador_bp, url_prefix='/admin') 

    with app.app_context():
        db.create_all()

    return app