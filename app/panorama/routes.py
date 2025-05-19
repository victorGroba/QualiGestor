from flask import Blueprint, render_template
from ..utils.decorators import login_required

panorama_bp = Blueprint('panorama', __name__, template_folder='templates')

@panorama_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('panorama/dashboard.html')
