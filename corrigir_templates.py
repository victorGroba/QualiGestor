# CORREÇÃO 1: Adicionar SUPER_ADMIN ao enum TipoUsuario no models.py

# Abra o arquivo app/models.py e modifique o enum TipoUsuario:

class TipoUsuario(enum.Enum):
    """Tipos de usuário do sistema"""
    SUPER_ADMIN = "super_admin"  # <- ADICIONAR ESTA LINHA
    ADMIN = "admin"
    GESTOR = "gestor"
    AUDITOR = "auditor"
    USUARIO = "usuario"
    VISUALIZADOR = "visualizador"

# CORREÇÃO 2: Rotas adicionais para compatibilidade no CLI routes

# Adicione estas rotas no final do arquivo app/cli/routes.py:

@cli_bp.route('/checklists')
@cli_bp.route('/listar-checklists')
@login_required
def listar_checklists():
    """Redirecionamento para listar questionários (compatibilidade)"""
    return redirect(url_for('cli.listar_questionarios'))

@cli_bp.route('/checklist/novo')
@cli_bp.route('/novo-checklist')
@login_required
def novo_checklist():
    """Redirecionamento para novo questionário (compatibilidade)"""
    return redirect(url_for('cli.novo_questionario'))

# CORREÇÃO 3: Função auxiliar para verificar permissões

# Adicione no final do arquivo app/cli/routes.py:

def verificar_permissao_admin():
    """Verifica se usuário tem permissão de admin"""
    if not current_user.is_authenticated:
        return False
    return current_user.tipo in [TipoUsuario.ADMIN, TipoUsuario.SUPER_ADMIN]

# Modifique o decorator admin_required para usar a nova função:
def admin_required(f):
    """Decorator para exigir permissões de administrador"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not verificar_permissao_admin():
            flash('Acesso restrito a administradores.', 'error')
            return redirect(url_for('cli.index'))
        return f(*args, **kwargs)
    return decorated_function

# CORREÇÃO 4: Atualizar script de inicialização

# Modifique o arquivo inicializar_sistema.py na parte de criação do admin:

# Substitua esta linha:
# tipo=TipoUsuario.ADMIN,

# Por esta:
tipo=TipoUsuario.SUPER_ADMIN,  # Usar SUPER_ADMIN para o primeiro usuário