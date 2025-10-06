import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    CORS(app, origins=[
        "http://localhost:3000",  # Local development
        "https://company-frontend.onrender.com",  # Render frontend
        "https://your-app.vercel.app"  # Vercel frontend (if using)
    ])

    # Database configuration
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost:5432/marynola'

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

    # File upload configuration
    if os.environ.get('RENDER'):
        # On Render - use persistent disk
        app.config['UPLOAD_FOLDER'] = '/opt/render/project/src/uploads'
    else:
        # Local development
        app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads')

    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    jwt = JWTManager(app)

    from backend.routes import main
    app.register_blueprint(main)

    return app
