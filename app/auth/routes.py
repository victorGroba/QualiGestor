# app/auth/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user

from werkzeug.security import generate_password_hash, check_password_hash
from .. import db
from ..models import Usuario, Cliente




auth_bp = Blueprint('auth', __name__, template_folder='templates')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        print(f"[DEBUG] Tentativa de login: {email}")

        usuario = Usuario.query.filter_by(email=email).first()
        print(f"[DEBUG] Usuário encontrado: {usuario is not None}")

        if usuario and check_password_hash(usuario.senha, senha):
            print("[DEBUG] Senha válida. Logando...")
            login_user(usuario)
            session['perfil'] = usuario.perfil

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
    if current_user.perfil != 'admin':
        flash('Acesso negado.')
        return redirect(url_for('auth.login'))

    clientes = Cliente.query.all()

    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        perfil = request.form['perfil']
        cliente_id = request.form['cliente_id']

        novo_usuario = Usuario(
            nome=nome,
            email=email,
            senha=generate_password_hash(senha),
            perfil=perfil,
            cliente_id=cliente_id
        )
        db.session.add(novo_usuario)
        db.session.commit()
        flash('Usuário cadastrado com sucesso!')
        return redirect(url_for('auth.cadastrar_usuario'))

    return render_template('auth/cadastrar_usuario.html', clientes=clientes)

@auth_bp.route('/usuarios')
@login_required
def listar_usuarios():
    if current_user.perfil != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.painel'))

    usuarios = Usuario.query.all()
    return render_template('auth/usuarios.html', usuarios=usuarios)


@auth_bp.route('/usuarios/editar/<int:usuario_id>', methods=['GET', 'POST'])
@login_required
def editar_usuario(usuario_id):
    if current_user.perfil != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.painel'))

    usuario = Usuario.query.get_or_404(usuario_id)
    clientes = Cliente.query.all()

    if request.method == 'POST':
        usuario.nome = request.form['nome']
        usuario.email = request.form['email']
        usuario.perfil = request.form['perfil']
        usuario.cliente_id = request.form['cliente_id']
        db.session.commit()
        flash('Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('auth.listar_usuarios'))

    return render_template('auth/editar_usuario.html', usuario=usuario, clientes=clientes)


@auth_bp.route('/usuarios/excluir/<int:usuario_id>')
@login_required
def excluir_usuario(usuario_id):
    if current_user.perfil != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.painel'))

    usuario = Usuario.query.get_or_404(usuario_id)
    db.session.delete(usuario)
    db.session.commit()
    flash('Usuário excluído com sucesso!', 'success')
    return redirect(url_for('auth.listar_usuarios'))

