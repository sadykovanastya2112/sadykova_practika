from config import Config
from flask import Flask
from flask_session import Session
from flasgger import Swagger
from flask_smorest import Api


from app.auth import auth_bp
from app.extension import bcrypt, cors, db, ma, migrate
from app.logto import init_logto
from app.models import seed_role
from app.payments import payments_bp
from app.slots import slots_bp
from app.specialist import specialist_bp
from app.client import clients_bp
from app.moderation import moderation_bp
from app.documents import documents_bp

def create_app(config_Class=Config):
    app = Flask(__name__)
    app.config.from_object(config_Class)

    app.config["SQLALCHEMY_DATABASE_URI"]
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
    app.config["API_TITLE"] = "My API"
    app.config["API_VERSION"] = "v1.0"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/apidocs"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger"
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


    with app.app_context():
        seed_role()

    # регистрация blueprints
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(specialist_bp, url_prefix="/specialist")
    app.register_blueprint(payments_bp, url_prefix="/payments")
    app.register_blueprint(slots_bp, url_prefix="/slots")
    app.register_blueprint(clients_bp, url_prefix="/client")
    app.register_blueprint(moderation_bp, url_prefix="/moderation")
    app.register_blueprint(documents_bp, url_prefix="/documents")
    



    

    # @app.errorhandler(Exception)
    # def hendle_experere(e):
    #     import traceback
    #     traceback.print_exc()
    #     return jsonify({"error": str(e)}),500

    return app
