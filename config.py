import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'mtb-school-dev-secret-2024'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static', 'uploads')
    FACE_ENCODINGS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static', 'face_encodings')

    @staticmethod
    def init_app(app):
        try:
            os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
            os.makedirs(Config.FACE_ENCODINGS_FOLDER, exist_ok=True)
        except Exception:
            pass  # Vercel serverless has a read-only filesystem

class DevelopmentConfig(Config):
    DEBUG = True
    _db_url = os.environ.get('DATABASE_URL', 'sqlite:///mtb_school.db')
    if _db_url:
        _db_url = _db_url.strip('"').strip("'")
    if _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = _db_url


class ProductionConfig(Config):
    DEBUG = False
    
    _db_url = os.environ.get('DATABASE_URL')
    if not _db_url:
        # Fallback to sqlite so the app doesn't crash on import, 
        # though it will fail during DB queries if Neon is not linked.
        _db_url = 'sqlite:////tmp/mtb_school.db'
    else:
        _db_url = _db_url.strip('"').strip("'")
        if _db_url.startswith('postgres://'):
            _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
        if '?' in _db_url:
            _db_url = _db_url.split('?')[0]
            
    SQLALCHEMY_DATABASE_URI = _db_url

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        # Check if DB URL is missing and log it
        if not os.environ.get('DATABASE_URL'):
            print("WARNING: DATABASE_URL environment variable is missing in Vercel!")


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
