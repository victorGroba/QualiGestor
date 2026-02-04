from functools import wraps
from flask import session, redirect, url_for, flash
from flask_login import current_user

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Você precisa estar logado para acessar esta página.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# --- ADICIONE ESTA FUNÇÃO NOVA ---
def admin_required(f):
    """
    Protege rotas que só podem ser acessadas por Admins ou Super Admins.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verifica se está logado
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
            
        is_admin = False
        
        # 1. Verifica pelo ENUM (Padrão do seu models.py)
        # Verifica se o tipo tem propriedade 'name' e se é ADMIN ou SUPER_ADMIN
        if hasattr(current_user, 'tipo') and hasattr(current_user.tipo, 'name'):
            if current_user.tipo.name in ['SUPER_ADMIN', 'ADMIN']:
                is_admin = True
                
        # 2. Verifica pelo ID (Compatibilidade com seu template antigo)
        if hasattr(current_user, 'tipo_id') and current_user.tipo_id == 1:
            is_admin = True

        if not is_admin:
            flash('Acesso Negado: Você não tem permissão de administrador.', 'danger')
            return redirect(url_for('main.painel')) # Manda de volta pro painel
            
        return f(*args, **kwargs)
    return decorated_function