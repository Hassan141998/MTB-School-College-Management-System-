from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config
import os

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
        if config_name == 'development':
            config_name = 'development'
        else:
            config_name = 'production'

    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)
    login_manager.init_app(app)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.students import students_bp
    from app.routes.teachers import teachers_bp
    from app.routes.fees import fees_bp
    from app.routes.attendance import attendance_bp
    from app.routes.face_recognition import face_bp
    from app.routes.exams import exams_bp
    from app.routes.library import library_bp
    from app.routes.reports import reports_bp
    from app.routes.settings import settings_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/')
    app.register_blueprint(students_bp, url_prefix='/students')
    app.register_blueprint(teachers_bp, url_prefix='/teachers')
    app.register_blueprint(fees_bp, url_prefix='/fees')
    app.register_blueprint(attendance_bp, url_prefix='/attendance')
    app.register_blueprint(face_bp, url_prefix='/face')
    app.register_blueprint(exams_bp, url_prefix='/exams')
    app.register_blueprint(library_bp, url_prefix='/library')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(settings_bp, url_prefix='/settings')

    # Create upload directories
    os.makedirs(os.path.join(app.static_folder, 'uploads', 'students'), exist_ok=True)
    os.makedirs(os.path.join(app.static_folder, 'uploads', 'teachers'), exist_ok=True)
    os.makedirs(os.path.join(app.static_folder, 'face_encodings'), exist_ok=True)

    @app.context_processor
    def inject_globals():
        from flask_login import current_user
        from app.models import Announcement
        announcements = []
        try:
            announcements = Announcement.query.filter_by(is_active=True).order_by(
                Announcement.created_at.desc()).limit(3).all()
        except Exception:
            pass
        return dict(current_user=current_user, announcements=announcements)

    return app
