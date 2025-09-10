# app/auth/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from .. import db
from ..models import Usuario, Cliente, TipoUsuario


auth_bp = Blueprint('auth', __name__, template_folder='templates')

# -------- helpers --------
def str_para_tipo_usuario(valor: str) -> TipoUsuario:
    """
    Converte strings legadas de 'perfil' do formulário em TipoUsuario.
    Aceita variações comuns e retorna VISUALIZADOR por padrão.
    """
    if not valor:
        return TipoUsuario.VISUALIZADOR
    v = valor.strip().lower()
    mapa = {
        'super_admin': TipoUsuario.SUPER_ADMIN,
        'superadmin': TipoUsuario.SUPER_ADMIN,
        'root': TipoUsuario.SUPER_ADMIN,
        'admin': TipoUsuario.ADMIN,
        'gestor': TipoUsuario.GESTOR if hasattr(TipoUsuario, 'GESTOR') else TipoUsuario.ADMIN,
        'auditor': TipoUsuario.AUDITOR if hasattr(TipoUsuario, 'AUDITOR') else TipoUsuario.VISUALIZADOR,
        'usuario': TipoUsuario.VISUALIZADOR,
        'visualizador': TipoUsuario.VISUALIZADOR,
        'viewer': TipoUsuario.VISUALIZADOR,
    }
    return mapa.get(v, TipoUsuario.VISUALIZADOR)


def exige_admin():
    """
    Retorna True se o usuário atual for ADMIN ou SUPER_ADMIN.
    Use para gates simples em rotas.
    """
    if not current_user.is_authenticated:
        return False
    # current_user.tipo é um Enum; compare com os membros existentes
    tipos_admin = [TipoUsuario.ADMIN, getattr(TipoUsuario, 'SUPER_ADMIN', None)]
    tipos_admin = [t for t in tipos_admin if t is not None]
    return current_user.tipo in tipos_admin
# -------------------------


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')
        print(f"[DEBUG] Tentativa de login: {email}")

        usuario = Usuario.query.filter_by(email=email).first()
        print(f"[DEBUG] Usuário encontrado: {usuario is not None}")

        if usuario and check_password_hash(usuario.senha, senha):
            print("[DEBUG] Senha válida. Logando...")
            login_user(usuario)

            # Sessão (usar 'tipo' em vez de 'perfil')
            tipo_str = usuario.tipo.name if hasattr(usuario.tipo, "name") else str(usuario.tipo)
            session['tipo'] = tipo_str
            session['nome'] = usuario.nome

            return redirect(url_for('main.painel'))

        print("[DEBUG] Email ou senha inválidos.")
        flash('E-mail ou senha inválidos.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/cadastrar-usuario', methods=['GET', 'POST'])
@login_required
def cadastrar_usuario():
    # Gate de acesso (ADMIN ou SUPER_ADMIN)
    if not exige_admin():
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.painel'))

    clientes = Cliente.query.all()

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')
        perfil_form = request.form.get('perfil')  # vindo do select legado
        cliente_id = request.form.get('cliente_id')

        # Converte 'perfil' legado para Enum TipoUsuario
        tipo_usuario = str_para_tipo_usuario(perfil_form)

        # Hash da senha
        senha_hash = generate_password_hash(senha)

        novo_usuario = Usuario(
            nome=nome,
            email=email,
            senha=senha_hash,
            tipo=tipo_usuario,
            cliente_id=cliente_id
        )
        db.session.add(novo_usuario)
        db.session.commit()
        flash('Usuário cadastrado com sucesso!', 'success')
        return redirect(url_for('auth.cadastrar_usuario'))

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
