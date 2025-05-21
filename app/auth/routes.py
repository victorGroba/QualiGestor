from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from ..models import Usuario



auth_bp = Blueprint('auth', __name__, template_folder='templates')

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash
from app.models import Usuario

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
            session['tipo'] = usuario.tipo
            session['nome'] = usuario.nome  # opcional, pode usar em saudação no painel, por exemplo
            return redirect(url_for('main.painel'))

        print("[DEBUG] Email ou senha inválidos.")
        flash('E-mail ou senha inválidos.', 'danger')

    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()  # limpa também as variáveis da sessão
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('auth.login'))

