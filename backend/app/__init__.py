from flask import Flask, g, jsonify
import time
from config import Config
from app.logto import init_logto
from app.extension import bcrypt, cors, ma, migrate, db
from app.auth import auth_bp
from app.users import users_bp
from app.payments import payments_bp
from flask_session import Session
from app import models

def create_app(config_Class=Config):
    app = Flask(__name__)
    app.config.from_object(config_Class)
    
    app.config['SQLALCHEMY_DATABASE_URI']
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    #инициализация расширений
    Session(app)
    bcrypt.init_app(app)
    cors.init_app(app)
    ma.init_app(app)
    init_logto(app)
    db.init_app(app)
    migrate.init_app(app, db)


    

    #регистрация blueprints
    app.register_blueprint(auth_bp, url_prefix = '/auth')
    app.register_blueprint(users_bp, url_prefix = '/users')
    app.register_blueprint(payments_bp, url_prefix = '/payments')

    # @app.errorhandler(Exception)
    # def hendle_experere(e):
    #     import traceback
    #     traceback.print_exc()
    #     return jsonify({"error": str(e)}),500


    return app

