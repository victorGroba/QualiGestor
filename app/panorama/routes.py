from flask import Blueprint, render_template
from flask_login import login_required

panorama_bp = Blueprint('panorama', __name__, template_folder='templates')

@panorama_bp.route('/')
@login_required
def index():
    return render_template('panorama/index.html')

@panorama_bp.route('/filtros')
@login_required
def filtros():
    return render_template('panorama/filtros.html')
