from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

main_bp = Blueprint('main', __name__, template_folder='templates')

@main_bp.route('/')
@login_required
def home():
    return render_template('main/home.html', usuario=current_user)

@main_bp.route('/painel')
@login_required
def painel():
    return render_template('main/painel.html', usuario=current_user)
