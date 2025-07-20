from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import config

# Extensiones Flask
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()

def create_app(config_name='default'):
    """Factory pattern para crear la aplicación Flask"""
    app = Flask(__name__, 
                template_folder='../../frontend/templates',
                static_folder='../../frontend/static')
    
    # Cargar configuración
    app.config.from_object(config[config_name])
    
    # Inicializar extensiones
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    # Configuración de Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'
    
    # Filtros personalizados de Jinja2
    @app.template_filter('dateformat')
    def dateformat(value, format='%d/%m/%Y'):
        """Filtro para formatear fechas de manera segura"""
        if value is None:
            return "No disponible"
        try:
            return value.strftime(format)
        except (AttributeError, ValueError):
            return "Fecha inválida"
    
    @app.template_filter('datetimeformat')
    def datetimeformat(value, format='%d/%m/%Y %H:%M'):
        """Filtro para formatear fechas y horas de manera segura"""
        if value is None:
            return "No disponible"
        try:
            return value.strftime(format)
        except (AttributeError, ValueError):
            return "Fecha inválida"
    
    # Funciones globales para templates
    @app.template_global()
    def csrf_token():
        """Hacer el token CSRF disponible globalmente en templates"""
        from flask_wtf.csrf import generate_csrf
        return generate_csrf()
    
    # Registrar Blueprints
    from app.routes.auth import bp as auth_bp
    from app.routes.admin import bp as admin_bp
    from app.routes.doctor import bp as doctor_bp
    from app.routes.receptionist import bp as receptionist_bp
    from app.routes.nurse import bp as nurse_bp
    from app.routes.main import bp as main_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(doctor_bp, url_prefix='/doctor')
    app.register_blueprint(receptionist_bp, url_prefix='/receptionist')
    app.register_blueprint(nurse_bp, url_prefix='/nurse')
    app.register_blueprint(main_bp)
    
    return app
