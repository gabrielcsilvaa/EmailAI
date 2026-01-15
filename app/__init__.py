from flask import Flask
from app.routes.rotas_api import api_bp
from app.routes.rotas_site import web_bp

def create_app():
    app = Flask(__name__)

    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(web_bp)

    return app
