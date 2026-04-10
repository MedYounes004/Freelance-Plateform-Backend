from flask import Flask
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from .config import Config

mongo = PyMongo()
bcrypt = Bcrypt()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    mongo.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    CORS(app)

    @jwt.unauthorized_loader
    def unauthorized_callback(reason):
        return {'message': f'Unauthorized: {reason}'}, 401

    @jwt.invalid_token_loader
    def invalid_token_callback(reason):
        return {'message': f'Invalid token: {reason}'}, 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {'message': 'Token has expired'}, 401

    from app.routes.auth import auth_bp
    from app.routes.projects import projects_bp
    from app.routes.proposals import proposals_bp
    from app.routes.cv import cv_bp
    from app.routes.messages import messages_bp
    from app.routes.users import users_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(proposals_bp)
    app.register_blueprint(cv_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(users_bp)

    return app