from flask import render_template
from app.auth import bp

@bp.route('/')
def index():
    return render_template('auth/index.html', title='Home')
