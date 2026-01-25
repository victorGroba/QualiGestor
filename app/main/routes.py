import os
from flask import Blueprint, render_template, send_from_directory, current_app
from flask_login import login_required, current_user

main_bp = Blueprint('main', __name__, template_folder='templates')

@main_bp.route('/')
@login_required
def home():
    return render_template('main/painel.html', usuario=current_user)

@main_bp.route('/painel')
@login_required
def painel():
    return render_template('main/painel.html', usuario=current_user)

# --- ROTA ESSENCIAL PARA O PWA ---
@main_bp.route('/service-worker.js')
def service_worker():
    """Serve o arquivo JS na raiz para habilitar o escopo global"""
    return send_from_directory(
        os.path.join(current_app.root_path, 'static', 'js'),
        'service-worker.js',
        mimetype='application/javascript'
    )