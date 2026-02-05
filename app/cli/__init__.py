# app/cli/__init__.py
from flask import Blueprint

# 1. Cria o Blueprint
cli_bp = Blueprint('cli', __name__, template_folder='templates', static_folder='static')

# 2. Importa o CSRF (ajuste o caminho se seu 'extensions.py' estiver em outro lugar)
# Geralmente está em app/__init__.py ou app/extensions.py
# Se der erro de importação circular, use import dentro das funções ou verifique sua estrutura.
try:
    from ..extensions import csrf
except ImportError:
    # Fallback se não usar extensions.py
    from .. import csrf 

# 3. Importa as Views (Isso registra as rotas no Blueprint)
# A ordem importa pouco, mas ajuda na organização mental
from .views import (
    admin,          # Cadastros, Usuários, Configs
    questionarios,  # Criação de Modelos
    aplicacoes,     # Execução de Auditorias
    planos_acao,    # Gestão de NCs
    relatorios,     # Dashboard e Gráficos
    uploads,        # Gestão de Arquivos
    api             # AJAX e Utilitários JSON
)

# Se tiver algum processador de contexto global (para injetar vars em todos templates)
@cli_bp.app_context_processor
def inject_context():
    from flask_login import current_user
    # Exemplo: injetar notificações não lidas globalmente
    notif_count = 0
    if current_user.is_authenticated:
        try:
            from ..models import Notificacao
            notif_count = Notificacao.query.filter_by(usuario_id=current_user.id, lida=False).count()
        except: pass
    return dict(notif_count=notif_count)