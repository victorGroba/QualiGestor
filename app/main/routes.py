from flask import Blueprint, render_template
from flask_login import login_required, current_user

main_bp = Blueprint('main', __name__, template_folder='templates')

@main_bp.route('/')
@login_required
def home():
    # ALTERAÇÃO: Agora carrega o html do painel diretamente na home
    return render_template('main/painel.html', usuario=current_user)

@main_bp.route('/painel')
@login_required
def painel():
    return render_template('main/painel.html', usuario=current_user)