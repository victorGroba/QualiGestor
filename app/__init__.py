import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'segredo')
    
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, '..', 'instance', 'banco.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = False

    # ✅ Versão do sistema
    versao_path = os.path.join(os.getcwd(), 'version.txt')
    try:
        with open(versao_path, 'r') as f:
            app.config['VERSAO'] = f.read().strip()
    except FileNotFoundError:
        app.config['VERSAO'] = '0.0.0.0'

    @app.context_processor
    def inject_version():
        return dict(versao=app.config['VERSAO'])

    # ✅ Importa a função auxiliar para uso em templates (PDF)
    from app.utils.helpers import opcao_pergunta_por_id

    @app.context_processor
    def inject_custom_functions():
        return dict(opcao_pergunta_por_id=opcao_pergunta_por_id)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from .models import Usuario

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    from .auth.routes import auth_bp
    from .main.routes import main_bp
    from .cli.routes import cli_bp
    from .panorama.routes import panorama_bp
    from .admin.routes import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(cli_bp, url_prefix='/cli')
    app.register_blueprint(panorama_bp, url_prefix='/panorama')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    return app

# Expõe db para importação relativa em outros módulos (como auth.routes)
__all__ = ['db']
