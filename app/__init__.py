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
        app.config["VERSAO"] = "1.4.0-beta"

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
            return dict(opcao_pergunta_por_id=opcao_pergunta_por_id)
    except Exception:
        @app.context_processor
        def inject_custom_functions():
            return dict()

    # Helpers de navegação globais
    def has_endpoint(name: str) -> bool:
        try:
            return name in {rule.endpoint for rule in app.url_map.iter_rules()}
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
                return url_for('cli.index') if has_endpoint('cli.index') else '/'
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

    # CSRFProtect (se disponível) - iniciando a instância global 'csrf'
    if csrf is not None:
        try:
            # Opções úteis para desenvolvimento/diagnóstico:
            # - desativa limite de tempo do token (útil para testes locais). Em produção,
            #   remova ou ajuste conforme desejado.
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

    # Adiciona um cookie de debug com o token CSRF (APENAS para desenvolvimento)
    # -------------------------------------------------------------------------
    # Esse cookie facilita testes manuais e com curl (ex.: pegar token facilmente).
    # NÃO deixar esse cookie habilitado em produção — remova ou comente o bloco abaixo
    # quando migrar para ambiente público/HTTPS.
    try:
        if generate_csrf:
            @app.after_request
            def set_csrf_cookie(response):
                try:
                    # gera token e seta cookie legível via DevTools (httponly=False) para debug
                    token_val = generate_csrf()
                    response.set_cookie(
                        "csrf_token_debug",
                        token_val,
                        httponly=False,  # debug only
                        samesite=app.config.get("SESSION_COOKIE_SAMESITE", "Lax"),
                        secure=app.config.get("SESSION_COOKIE_SECURE", False)
                    )
                except Exception:
                    # não interrompe a resposta se algo falhar aqui
                    pass
                return response
    except Exception:
        # se algo de import/availability falhar, continuamos sem o cookie de debug
        pass
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # Models e user loader
    # -------------------------------------------------------------------------
    from .models import Usuario  # import local para evitar ciclos

    @login_manager.user_loader
    def load_user(user_id: str) -> Optional["Usuario"]:
        try:
            return Usuario.query.get(int(user_id))
        except Exception:
            return None

    # -------------------------------------------------------------------------
    # Blueprints
    # -------------------------------------------------------------------------
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
    except Exception:
        pass

    return app


# Exportações do módulo
__all__ = ["db", "create_app", "csrf"]
