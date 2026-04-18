from config import Config
from flask import Flask
from flask_session import Session

from app.auth import auth_bp
from app.extension import bcrypt, cors, db, ma, migrate
from app.logto import init_logto
from app.models import seed_role
from app.payments import payments_bp
from app.slots import slots_bp
from app.specialist import specialist_bp
from app.client import clients_bp


def create_app(config_Class=Config):
    app = Flask(__name__)
    app.config.from_object(config_Class)

    app.config["SQLALCHEMY_DATABASE_URI"]
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH

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




    

    # @app.errorhandler(Exception)
    # def hendle_experere(e):
    #     import traceback
    #     traceback.print_exc()
    #     return jsonify({"error": str(e)}),500

    return app
