import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
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

    # ✅ Lê a versão do version.txt automaticamente
    versao_path = os.path.join(os.getcwd(), 'version.txt')

    try:
        with open(versao_path, 'r') as f:
            app.config['VERSAO'] = f.read().strip()
    except FileNotFoundError:
        app.config['VERSAO'] = '0.0.0.0'

    # ✅ Injeta a versão em todos os templates
    @app.context_processor
    def inject_version():
        return dict(versao=app.config['VERSAO'])

    db.init_app(app)
    login_manager.init_app(app)

    from .models import Usuario

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    from app.auth.routes import auth_bp
    from app.main.routes import main_bp
    from app.cli.routes import cli_bp
    from app.panorama.routes import panorama_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(cli_bp, url_prefix='/cli')
    app.register_blueprint(panorama_bp, url_prefix='/panorama')

    return app
