from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.exceptions import HTTPException
from config import config
import os

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'


def create_app(config_name='default'):
    # Force instance_path to /tmp on Vercel to bypass read-only filesystem
    instance_path = '/tmp/instance' if os.environ.get('VERCEL') == '1' else None

    app = Flask(__name__, instance_path=instance_path)
    app.config.from_object(config[config_name])

    # Force evaluation of DATABASE_URL directly inside the app factory
    # to guarantee Vercel reads the environment variable at runtime
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        db_url = db_url.strip('"').strip("'")
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        if '?' in db_url:
            db_url = db_url.split('?')[0]
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url

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

    # Create upload directories (Will fail gracefully on Vercel's read-only FS)
    try:
        os.makedirs(os.path.join(app.static_folder, 'uploads', 'students'), exist_ok=True)
        os.makedirs(os.path.join(app.static_folder, 'uploads', 'teachers'), exist_ok=True)
        os.makedirs(os.path.join(app.static_folder, 'face_encodings'), exist_ok=True)
    except OSError:
        pass

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

    # Catch unhandled errors so Vercel never shows its own generic crash page —
    # but let normal HTTP errors (404, 403, etc.) pass through untouched.
    @app.errorhandler(Exception)
    def handle_exception(e):
        if isinstance(e, HTTPException):
            return e

        import traceback
        tb = traceback.format_exc()
        app.logger.error(tb)

        if app.debug:
            return f"<pre>INTERNAL SERVER ERROR:\n\n{tb}</pre>", 500

        db_hint = ""
        if "no such table" in tb or "OperationalError" in tb or "psycopg2" in tb:
            db_hint = (
                "<p>This usually means the database isn't connected or "
                "hasn't been initialized yet. If you're the administrator, "
                "check that <code>DATABASE_URL</code> is set in your Vercel "
                "project settings and that <code>flask seed-db</code> has "
                "been run against it.</p>"
            )
        return (
            "<div style=\"font-family:sans-serif;max-width:640px;margin:60px auto;"
            "text-align:center;color:#334155\">"
            "<h2>Something went wrong</h2>"
            "<p>We hit an unexpected error. Please try again shortly.</p>"
            f"{db_hint}"
            "</div>"
        ), 500

    @app.template_filter('currency')
    def currency_filter(value):
        try:
            return f"PKR {float(value):,.0f}"
        except (TypeError, ValueError):
            return "PKR 0"

    @app.template_filter('initials')
    def initials_filter(name):
        if not name:
            return '?'
        parts = str(name).split()
        return ''.join(p[0].upper() for p in parts[:2]) if parts else '?'

    @app.template_filter('date_fmt')
    def date_fmt_filter(value, fmt='%d %b %Y'):
        if not value:
            return '—'
        if hasattr(value, 'strftime'):
            return value.strftime(fmt)
        # Handle plain ISO date strings too.
        try:
            from datetime import datetime as _dt
            return _dt.strptime(str(value), '%Y-%m-%d').strftime(fmt)
        except (ValueError, TypeError):
            return str(value)

    @app.template_filter('percentage')
    def percentage_filter(value, decimals=1):
        try:
            return f"{float(value):.{decimals}f}%"
        except (TypeError, ValueError):
            return "0%"

    @app.template_filter('truncate_text')
    def truncate_text_filter(text, length=50):
        if not text:
            return ''
        text = str(text)
        return text if len(text) <= length else text[:length].rstrip() + '…'

    @app.template_filter('grade_color')
    def grade_color_filter(grade):
        colors = {
            'A+': 'success', 'A': 'success',
            'B': 'primary', 'C': 'warning',
            'D': 'warning', 'F': 'danger',
        }
        return colors.get(str(grade).upper(), 'secondary')

    return app