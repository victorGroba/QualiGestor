from flask import Blueprint

panorama_bp = Blueprint('panorama', __name__, template_folder='templates')

from . import routes
