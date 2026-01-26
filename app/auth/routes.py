# app/auth/routes.py - VERSÃO CORRIGIDA (LOGOUT ROBUSTO)
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from .. import db
from ..models import Usuario, Cliente, TipoUsuario

auth_bp = Blueprint('auth', __name__, template_folder='templates')

# -------- helpers --------
def str_para_tipo_usuario(valor: str) -> TipoUsuario:
    """Converte strings legadas de 'perfil' do formulário em TipoUsuario."""
    if not valor:
        return TipoUsuario.VISUALIZADOR
    v = valor.strip().lower()
    mapa = {
        'super_admin': TipoUsuario.SUPER_ADMIN,
        'superadmin': TipoUsuario.SUPER_ADMIN,
        'root': TipoUsuario.SUPER_ADMIN,
        'admin': TipoUsuario.ADMIN,
        'gestor': TipoUsuario.GESTOR,
        'auditor': TipoUsuario.AUDITOR,
        'usuario': TipoUsuario.VISUALIZADOR,
        'visualizador': TipoUsuario.VISUALIZADOR,
        'viewer': TipoUsuario.VISUALIZADOR,
    }
    return mapa.get(v, TipoUsuario.VISUALIZADOR)

def exige_admin():
    """Retorna True se o usuário atual for ADMIN ou SUPER_ADMIN."""
    if not current_user.is_authenticated:
        return False
    return current_user.tipo in [TipoUsuario.ADMIN, TipoUsuario.SUPER_ADMIN]

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Se já estiver logado, redireciona direto para o painel
    if current_user.is_authenticated:
        return redirect(url_for('main.painel'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')
        
        # O checkbox agora é opcional, pois forçamos a sessão abaixo
        remember_me = True if request.form.get('remember') else False

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and usuario.check_password(senha):
            # Loga o usuário no Flask-Login
            login_user(usuario, remember=remember_me)

            # === CONFIGURAÇÃO CRÍTICA PARA MOBILE/IPHONE ===
            # Força a sessão a ser permanente (duração de 3h configurada no __init__.py)
            # Isso garante que o cookie não seja apagado ao fechar o navegador.
            session.permanent = True
            # ===============================================

            # Salva dados úteis na sessão
            tipo_str = usuario.tipo.name if hasattr(usuario.tipo, "name") else str(usuario.tipo)
            session['tipo'] = tipo_str
            session['nome'] = usuario.nome

            # Redirecionamento seguro
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('main.painel')

            return redirect(next_page)

        flash('E-mail ou senha inválidos.', 'danger')

    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    """
    Função de logout blindada. Garante que a sessão seja destruída,
    mesmo que tenha sido marcada como permanente anteriormente.
    """
    # 1. Desloga do Flask-Login
    logout_user()
    
    # 2. Desativa a permanência (anula o session.permanent = True do login)
    session.permanent = False
    
    # 3. Limpa todo o dicionário da sessão
    session.clear()
    
    # 4. Prepara o redirecionamento
    response = redirect(url_for('auth.login'))
    
    # 5. FORÇA BRUTA: Deleta os cookies do navegador manualmente
    # Isso garante que o iPhone não "reaproveite" o cookie antigo
    response.delete_cookie('session')
    response.delete_cookie('remember_token')
    
    flash('Você saiu do sistema.', 'info')
    return response

@auth_bp.route('/cadastrar-usuario', methods=['GET', 'POST'])
@login_required
def cadastrar_usuario():
    if not exige_admin():
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.painel'))

    clientes = Cliente.query.all()

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')
        perfil_form = request.form.get('perfil')
        cliente_id = request.form.get('cliente_id')

        tipo_usuario = str_para_tipo_usuario(perfil_form)
        senha_hash = generate_password_hash(senha) if senha else None

        # --- monta kwargs apenas com colunas válidas do modelo Usuario ---
        try:
            cols = [c.name for c in Usuario.__table__.columns]
        except Exception:
            cols = []

        data = {}
        if 'nome' in cols and nome:
            data['nome'] = nome
        if 'email' in cols and email:
            data['email'] = email
        if 'tipo' in cols and tipo_usuario is not None:
            data['tipo'] = tipo_usuario
        
        if 'cliente_id' in cols:
            try:
                data['cliente_id'] = int(cliente_id) if cliente_id not in (None, '', 'None') else None
            except Exception:
                data['cliente_id'] = None

        novo_usuario = Usuario(**data)

        possiveis_campos_senha = ['senha_hash', 'password_hash', 'hash_senha', 'password', 'senha']
        campo_setado = None
        for campo in possiveis_campos_senha:
            if campo in cols:
                if senha_hash is not None:
                    setattr(novo_usuario, campo, senha_hash)
                campo_setado = campo
                break

        if senha_hash is not None and campo_setado is None:
            setattr(novo_usuario, 'senha', senha_hash)

        db.session.add(novo_usuario)
        try:
            db.session.commit()
            flash('Usuário cadastrado com sucesso!', 'success')
            return redirect(url_for('auth.cadastrar_usuario'))
        except Exception as e:
            db.session.rollback()
            print("Erro ao inserir usuário:", e)
            flash('Erro ao cadastrar usuário. Verifique os logs.', 'danger')
            return render_template('auth/cadastrar_usuario.html', clientes=clientes)

    return render_template('auth/cadastrar_usuario.html', clientes=clientes)

@auth_bp.route('/usuarios')
@login_required
def listar_usuarios():
    if not exige_admin():
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.painel'))

    usuarios = Usuario.query.all()
    return render_template('auth/usuarios.html', usuarios=usuarios)

@auth_bp.route('/usuarios/editar/<int:usuario_id>', methods=['GET', 'POST'])
@login_required
def editar_usuario(usuario_id):
    if not exige_admin():
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.painel'))

    usuario = Usuario.query.get_or_404(usuario_id)
    clientes = Cliente.query.all()

    if request.method == 'POST':
        usuario.nome = request.form.get('nome', '').strip()
        usuario.email = request.form.get('email', '').strip()
        perfil_form = request.form.get('perfil')
        usuario.tipo = str_para_tipo_usuario(perfil_form)
        usuario.cliente_id = request.form.get('cliente_id')
        db.session.commit()
        flash('Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('auth.listar_usuarios'))

    return render_template('auth/editar_usuario.html', usuario=usuario, clientes=clientes)

@auth_bp.route('/usuarios/excluir/<int:usuario_id>')
@login_required
def excluir_usuario(usuario_id):
    if not exige_admin():
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.painel'))

    usuario = Usuario.query.get_or_404(usuario_id)
    db.session.delete(usuario)
    db.session.commit()
    flash('Usuário excluído com sucesso!', 'success')
    return redirect(url_for('auth.listar_usuarios'))


@auth_bp.route('/alterar-senha', methods=['GET', 'POST'])
@login_required
def alterar_senha():
    if request.method == 'POST':
        senha_atual = request.form.get('senha_atual')
        nova_senha = request.form.get('nova_senha')
        confirmar_senha = request.form.get('confirmar_senha')

        if not current_user.check_password(senha_atual):
            flash('Sua senha atual está incorreta.', 'danger')
            return redirect(url_for('auth.alterar_senha'))

        if nova_senha != confirmar_senha:
            flash('A nova senha e a confirmação não conferem.', 'warning')
            return redirect(url_for('auth.alterar_senha'))

        if len(nova_senha) < 6:
            flash('A nova senha deve ter pelo menos 6 caracteres.', 'warning')
            return redirect(url_for('auth.alterar_senha'))

        current_user.set_password(nova_senha)
        db.session.commit()

        flash('Senha alterada com sucesso!', 'success')
        return redirect(url_for('main.painel'))

    return render_template('auth/alterar_senha.html')