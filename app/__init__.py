# app/__init__.py
import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional
from flask import Flask, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from dotenv import load_dotenv

# CSRF (opcional, se Flask-WTF estiver instalado)
try:
    from flask_wtf import CSRFProtect
    from flask_wtf.csrf import generate_csrf
except Exception:
    CSRFProtect = None
    generate_csrf = None

# ----------------------------
# Extensões globais
# ----------------------------
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

# Instância global do CSRF
csrf = None
if CSRFProtect is not None:
    try:
        csrf = CSRFProtect()
    except Exception as e:
        print(f"[WARN] Falha ao instanciar CSRFProtect: {e}")
        csrf = None

# Carrega variáveis do .env (se existir)
load_dotenv()


def _sqlite_uri(db_path: Path) -> str:
    """
    Monta uma URI SQLite compatível com Windows/macOS/Linux.
    """
    return f"sqlite:///{db_path.as_posix()}"

# --- FUNÇÃO AUXILIAR PARA VERIFICAR EXTENSÕES DE ARQUIVO ---
def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """Verifica se o nome de arquivo tem uma extensão permitida."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions
# -----------------------------------------------------------


def create_app() -> Flask:
    # Define pastas padrão (dentro de app/)
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # -------------------------------------------------------------------------
    # Configurações básicas
    # -------------------------------------------------------------------------
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "chave-secreta-desenvolvimento")
    
    # --- CONFIGURAÇÃO DA IA (ESSENCIAL PARA O GEMINI FUNCIONAR) ---
    app.config["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY")
    # --------------------------------------------------------------

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = False  # em produção com HTTPS -> True
    app.url_map.strict_slashes = False  # normaliza trailing slash

    # -------------------------------------------------------------------------
    # Caminhos do projeto
    # -------------------------------------------------------------------------
    base_dir = Path(__file__).resolve().parent      # .../QualiGestor/app
    root_dir = base_dir.parent                      # .../QualiGestor
    instance_dir = root_dir / "instance"
    instance_dir.mkdir(parents=True, exist_ok=True)

    # --- Configuração da pasta de upload ---
    UPLOAD_FOLDER = instance_dir / "uploads" / "fotos_respostas"
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True) 
    app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER) 
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'} 
    # ----------------------------------------------

    # Banco em instance/banco.db
    # -------------------------------------------------------------------------
    # Configuração de Banco de Dados (Inteligente)
    # -------------------------------------------------------------------------
    # 1. Tenta pegar a URL do banco do arquivo .env (Para PostgreSQL no Linux)
    database_uri = os.getenv("SQLALCHEMY_DATABASE_URI")

    if database_uri:
        app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
        print(f"LOG: Usando banco de dados configurado no .env")
    else:
        # 2. Se não tiver nada no .env, usa SQLite automático (Padrão Windows)
        db_path = instance_dir / "banco.db"
        app.config["SQLALCHEMY_DATABASE_URI"] = _sqlite_uri(db_path)
        print(f"LOG: Usando banco SQLite local (Padrão)")

    # -------------------------------------------------------------------------
    # Versão do sistema
    # -------------------------------------------------------------------------
    versao_path = root_dir / "version.txt"
    try:
        app.config["VERSAO"] = versao_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        app.config["VERSAO"] = "1.4.0-beta"

    @app.context_processor
    def inject_version():
        return dict(versao=app.config.get("VERSAO", "dev"))

    # -------------------------------------------------------------------------
    # Helpers para templates
    # -------------------------------------------------------------------------
   
        from .utils.helpers import opcao_pergunta_por_id  # type: ignore

        @app.context_processor
        def inject_custom_functions():
            return dict(
                opcao_pergunta_por_id=opcao_pergunta_por_id,
                allowed_file=allowed_file
            )
    

    # Helpers de navegação globais
    def has_endpoint(name: str) -> bool:
        try:
            if app.url_map:
                return name in {rule.endpoint for rule in app.url_map.iter_rules()}
            return False
        except Exception:
            return False

    def url_for_safe(endpoint: str, **values) -> str:
        try:
            return url_for(endpoint, **values)
        except Exception:
            try:
                with app.app_context():
                    if has_endpoint('cli.index'):
                        return url_for('cli.index')
                    else:
                        return '/'
            except Exception:
                return '/'

    @app.context_processor
    def inject_nav_helpers():
        return dict(
            has_endpoint=has_endpoint,
            url_for_safe=url_for_safe,
        )

    # -------------------------------------------------------------------------
    # Extensões
    # -------------------------------------------------------------------------
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Por favor, faça login para acessar esta página."
    login_manager.login_message_category = "info"

    # CSRFProtect
    if csrf is not None:
        try:
            app.config.setdefault("WTF_CSRF_TIME_LIMIT", None)
            csrf.init_app(app)
        except Exception as e:
            print(f"[WARN] CSRFProtect não habilitado: {e}")

    @app.context_processor
    def inject_csrf():
        if generate_csrf:
            return {"csrf_token": generate_csrf}
        return {}

    try:
        if generate_csrf:
            @app.after_request
            def set_csrf_cookie(response):
                try:
                    token_val = generate_csrf()
                    response.set_cookie(
                        "csrf_token_debug",
                        token_val,
                        httponly=False,
                        samesite=app.config.get("SESSION_COOKIE_SAMESITE", "Lax"),
                        secure=app.config.get("SESSION_COOKIE_SECURE", False)
                    )
                except Exception:
                    pass
                return response
    except Exception:
        pass

    # -------------------------------------------------------------------------
    # Models e user loader
    # -------------------------------------------------------------------------
    with app.app_context():
        from . import models

    @login_manager.user_loader
    def load_user(user_id: str) -> Optional["models.Usuario"]:
        try:
            return models.Usuario.query.get(int(user_id))
        except Exception as e:
            app.logger.error(f"Erro ao carregar usuário {user_id}: {e}")
            return None

    # -------------------------------------------------------------------------
    # Blueprints
    # -------------------------------------------------------------------------
    from .auth.routes import auth_bp
    from .main.routes import main_bp
    from .cli.routes import cli_bp
    from .panorama.routes import panorama_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(cli_bp, url_prefix="/cli")
    app.register_blueprint(panorama_bp, url_prefix="/panorama")

    try:
        from .admin.routes import admin_bp
        app.register_blueprint(admin_bp, url_prefix="/admin")
    except ImportError:
         print("[INFO] Blueprint Admin não encontrado ou não importado.")
    except Exception as e:
         print(f"[WARN] Erro ao registrar blueprint Admin: {e}")

    # -------------------------------------------------------------------------
    # CONFIGURAÇÃO DE LOGGING (BLINDADA PARA WINDOWS)
    # -------------------------------------------------------------------------
    
    # 1. Limpa handlers antigos para evitar conflitos de arquivo preso
    for handler in app.logger.handlers[:]:
        app.logger.removeHandler(handler)

    app.logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    
    # 2. SEMPRE adiciona um StreamHandler (Console)
    # Isso garante que você veja os logs no terminal, mesmo se o arquivo falhar.
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    app.logger.addHandler(stream_handler)

    # 3. Tenta configurar o FileHandler de forma segura
    log_file = instance_dir / 'app.log'
    
    # No Windows (nt) ou Debug, usamos FileHandler simples com delay=True.
    if os.name == 'nt' or app.debug:
        try:
            file_handler = logging.FileHandler(str(log_file), encoding='utf-8', delay=True)
            file_handler.setFormatter(formatter)
            app.logger.addHandler(file_handler)
            print("LOG: Logging em arquivo ativado (Modo Windows/Debug)")
        except Exception as e:
            # Se falhar (permissão), não quebra o app. Apenas avisa no console.
            print(f"AVISO CRÍTICO: Não foi possível criar 'app.log'. Logs apenas no console. Erro: {e}")
            
    else:
        # Modo Produção (Linux): Usa rotação de logs
        try:
            file_handler = RotatingFileHandler(str(log_file), maxBytes=1_000_000, backupCount=5, encoding='utf-8')
            file_handler.setFormatter(formatter)
            app.logger.addHandler(file_handler)
            print("LOG: Logging rotativo configurado (Modo Produção)")
        except Exception as e:
            print(f"AVISO: Falha ao configurar log rotativo: {e}")

    app.logger.info('QualiGestor iniciado com sucesso.')
    
    # -------------------------------------------------------------------------

    return app

# Exportações do módulo
__all__ = ["db", "create_app", "csrf", "allowed_file"]