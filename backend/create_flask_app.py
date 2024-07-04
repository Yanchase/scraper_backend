import os
import shutil
import sys


def create_flask_app(project_name):
    # Define the directory structure
    directories = [
        f"{project_name}/app",
        f"{project_name}/app/static",
        f"{project_name}/app/templates",
        f"{project_name}/app/main",
        f"{project_name}/app/auth",
        f"{project_name}/app/errors",
        f"{project_name}/migrations",
    ]

    # Define the files to create with basic content
    files = {
        f"{project_name}/manage.py": manage_py_content(),
        f"{project_name}/config.py": config_py_content(),
        f"{project_name}/app/__init__.py": app_init_py_content(),
        f"{project_name}/app/main/__init__.py": blueprint_init_py_content("main"),
        f"{project_name}/app/main/routes.py": routes_py_content("main"),
        f"{project_name}/app/auth/__init__.py": blueprint_init_py_content("auth"),
        f"{project_name}/app/auth/routes.py": routes_py_content("auth"),
        f"{project_name}/app/errors/__init__.py": blueprint_init_py_content("errors"),
        f"{project_name}/app/errors/handlers.py": handlers_py_content(),
    }

    # Create directories
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

    # Create files with content
    for file_path, content in files.items():
        with open(file_path, "w") as file:
            file.write(content)

    print(f"Flask project '{project_name}' created successfully!")


def manage_py_content():
    return """from app import create_app, db
from flask_migrate import Migrate

app = create_app()
migrate = Migrate(app, db)

if __name__ == '__main__':
    app.run(debug=True)
"""


def config_py_content():
    return """import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
"""


def app_init_py_content():
    return """from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    return app
"""


def blueprint_init_py_content(blueprint_name):
    return f"""from flask import Blueprint

bp = Blueprint('{blueprint_name}', __name__)

from app.{blueprint_name} import routes
"""


def routes_py_content(blueprint_name):
    return f"""from flask import render_template
from app.{blueprint_name} import bp

@bp.route('/')
def index():
    return render_template('{blueprint_name}/index.html', title='Home')
"""


def handlers_py_content():
    return """from flask import render_template
from app.errors import bp

@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@bp.app_errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500
"""


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python create_flask_app.py <project_name>")
        sys.exit(1)
    project_name = sys.argv[1]
    create_flask_app(project_name)
