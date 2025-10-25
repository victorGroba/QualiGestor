# app/__init__.py
import os
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

# Instância global do CSRF (pode ser None se Flask-WTF não estiver disponível)
csrf = None
if CSRFProtect is not None:
    try:
        csrf = CSRFProtect()
    except Exception as e:
        # Falha ao instanciar CSRFProtect; deixamos csrf = None
        print(f"[WARN] Falha ao instanciar CSRFProtect: {e}")
        csrf = None

# Carrega variáveis do .env (se existir)
load_dotenv()


def _sqlite_uri(db_path: Path) -> str:
    """
    Monta uma URI SQLite compatível com Windows/macOS/Linux,
    evitando problemas com barras invertidas e espaços.
    """
    return f"sqlite:///{db_path.as_posix()}"

# --- FUNÇÃO AUXILIAR PARA VERIFICAR EXTENSÕES DE ARQUIVO ---
# Colocada aqui para fácil acesso, pode ser movida para utils/helpers.py depois
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
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = False  # em produção com HTTPS -> True
    app.url_map.strict_slashes = False  # normaliza trailing slash

    # -------------------------------------------------------------------------
    # Caminhos do projeto
    # -------------------------------------------------------------------------
    base_dir = Path(__file__).resolve().parent            # .../QualiGestor/app
    root_dir = base_dir.parent                            # .../QualiGestor
    instance_dir = root_dir / "instance"
    instance_dir.mkdir(parents=True, exist_ok=True)

    # --- ADIÇÃO: Configuração da pasta de upload ---
    UPLOAD_FOLDER = instance_dir / "uploads" / "fotos_respostas"
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True) # Garante que a pasta exista
    app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER) # Armazena como string no config
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'} # Tipos permitidos
    # ----------------------------------------------

    # Banco em instance/banco.db
    db_path = instance_dir / "banco.db"
    app.config["SQLALCHEMY_DATABASE_URI"] = _sqlite_uri(db_path)

    # -------------------------------------------------------------------------
    # Versão do sistema (lida a partir de version.txt na raiz)
    # -------------------------------------------------------------------------
    versao_path = root_dir / "version.txt"
    try:
        app.config["VERSAO"] = versao_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        app.config["VERSAO"] = "1.4.0-beta" # Mantive o seu default

    @app.context_processor
    def inject_version():
        return dict(versao=app.config.get("VERSAO", "dev"))

    # -------------------------------------------------------------------------
    # Helpers para templates
    # -------------------------------------------------------------------------
    try:
        from .utils.helpers import opcao_pergunta_por_id  # type: ignore

        @app.context_processor
        def inject_custom_functions():
            # Adiciona allowed_file ao contexto dos templates também, se útil
            return dict(
                opcao_pergunta_por_id=opcao_pergunta_por_id,
                allowed_file=allowed_file # Permite usar no template se precisar
            )
    except Exception:
        @app.context_processor
        def inject_custom_functions():
             # Adiciona allowed_file mesmo se outros helpers falharem
            return dict(allowed_file=allowed_file)

    # Helpers de navegação globais
    def has_endpoint(name: str) -> bool:
        try:
            # Garante que app.url_map existe antes de iterar
            if app.url_map:
                return name in {rule.endpoint for rule in app.url_map.iter_rules()}
            return False
        except Exception:
            return False

    def url_for_safe(endpoint: str, **values) -> str:
        """
        Tenta gerar a URL do endpoint; se falhar, cai no índice do CLI ou '/'.
        """
        try:
            return url_for(endpoint, **values)
        except Exception:
            try:
                # Tenta gerar url_for dentro do contexto da app para garantir que url_map está pronto
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


    # CSRFProtect (se disponível) - iniciando a instância global 'csrf'
    if csrf is not None:
        try:
            app.config.setdefault("WTF_CSRF_TIME_LIMIT", None)
            csrf.init_app(app)
        except Exception as e:
            print(f"[WARN] CSRFProtect não habilitado: {e}")

    # Expor csrf_token() nos templates (só se Flask-WTF estiver disponível)
    @app.context_processor
    def inject_csrf():
        if generate_csrf:
            return {"csrf_token": generate_csrf}
        return {}

    # Cookie de debug CSRF (REMOVER EM PRODUÇÃO)
    # (Código mantido como no original)
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

    # -------------------------------------------------------------------------
    # Models e user loader
    # -------------------------------------------------------------------------
    # É importante que os modelos sejam importados DEPOIS que 'db' foi inicializado
    # e ANTES dos blueprints que os usam serem registrados.
    with app.app_context():
        from . import models # Importa tudo de models.py

    @login_manager.user_loader
    def load_user(user_id: str) -> Optional["models.Usuario"]:
        try:
            # Acessa Usuario através do módulo importado
            return models.Usuario.query.get(int(user_id))
        except Exception as e:
            app.logger.error(f"Erro ao carregar usuário {user_id}: {e}")
            return None

    # -------------------------------------------------------------------------
    # Blueprints
    # -------------------------------------------------------------------------
    # Importar DEPOIS da inicialização do app e db
    from .auth.routes import auth_bp
    from .main.routes import main_bp
    from .cli.routes import cli_bp
    from .panorama.routes import panorama_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)                 # '/' e '/painel'
    app.register_blueprint(cli_bp, url_prefix="/cli")
    app.register_blueprint(panorama_bp, url_prefix="/panorama")

    # Admin opcional
    try:
        from .admin.routes import admin_bp
        app.register_blueprint(admin_bp, url_prefix="/admin")
    except ImportError:
         print("[INFO] Blueprint Admin não encontrado ou não importado.")
    except Exception as e:
         print(f"[WARN] Erro ao registrar blueprint Admin: {e}")


    # Adicionar um logger básico para debug se não estiver em produção
    if not app.debug:
        import logging
        from logging.handlers import RotatingFileHandler
        # Exemplo: Log para instance/app.log
        log_file = instance_dir / 'app.log'
        file_handler = RotatingFileHandler(str(log_file), maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('QualiGestor startup')

    return app


# Exportações do módulo - MANTIDAS IGUAIS
__all__ = ["db", "create_app", "csrf", "allowed_file"] # Adicionei allowed_file aqui