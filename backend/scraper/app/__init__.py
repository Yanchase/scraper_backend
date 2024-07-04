from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    CORS(app)

    from app.scrape.routes import bp as scrape_bp

    app.register_blueprint(scrape_bp, url_prefix="/scrape")

    from app.emails.routes import bp as emails_bp

    app.register_blueprint(emails_bp, url_prefix="/emails")

    from app.linkedin.routes import bp as linkedin_bp

    app.register_blueprint(linkedin_bp, url_prefix="/linkedin")

    from app.web_gpt.routes import bp as webgpt_bp

    app.register_blueprint(webgpt_bp, url_prefix="/webgpt")

    return app
