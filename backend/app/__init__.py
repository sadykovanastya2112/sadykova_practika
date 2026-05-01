from config import Config
from flask import Flask, send_from_directory
from flask_jwt_extended import JWTManager
from flask_session import Session
from flask_smorest import Api

from app.auth import auth_bp
from app.client import clients_bp
from app.documents import documents_bp
from app.extension import bcrypt, cors, db, ma, migrate
from app.logto import init_logto
from app.models import seed_role
from app.moderation import moderation_bp
from app.payments import payments_bp
from app.slots import slots_bp
from app.specialist import specialist_bp
from app.admin import admin_bp
from app.calendars import cal_bp


def create_app(config_Class=Config):
    app = Flask(__name__, static_url_path='/static')
    app.config.from_object(config_Class)

    app.config["SQLALCHEMY_DATABASE_URI"] = config_Class.SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = Config.UPLOAD_FOLDER
    app.config["MAX_CONTENT_LENGTH"] = Config.MAX_CONTENT_LENGTH
    app.config["API_TITLE"] = "My API"
    app.config["API_VERSION"] = "v1.0"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/apidocs"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    api = Api(app)

    # инициализация расширений
    Session(app)
    bcrypt.init_app(app)
    cors.init_app(app)
    ma.init_app(app)
    init_logto(app)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt = JWTManager(app)

    with app.app_context():
        seed_role()

    # регистрация blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(specialist_bp, url_prefix='/specialist')
    app.register_blueprint(payments_bp, url_prefix='/payments')
    app.register_blueprint(slots_bp, url_prefix='/slots')
    app.register_blueprint(clients_bp, url_prefix='/clients')
    app.register_blueprint(moderation_bp, url_prefix='/moderation')
    app.register_blueprint(documents_bp, url_prefix='/documents')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(cal_bp, url_prefix='/calendars')

    # статический Swagger UI
    @app.route('/docs')
    def docs():
        return send_from_directory('static', 'swagger-ui.html')

    @app.route('/static/openapi.yaml')
    def openapi_yaml():
        return send_from_directory('static', 'openapi.yaml')

    return app