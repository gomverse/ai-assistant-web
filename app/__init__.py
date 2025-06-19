from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os
import secrets
from datetime import timedelta
import logging

def create_app():
    load_dotenv()
    app = Flask(__name__, template_folder="app/templates", static_folder="app/static")
    app.secret_key = os.getenv("SECRET_KEY", secrets.token_hex(16))
    app.config["SESSION_TYPE"] = os.getenv("SESSION_TYPE", "filesystem")
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=int(os.getenv("SESSION_DAYS", 5)))
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": ["http://localhost:5000", "http://127.0.0.1:5000"],
                "methods": ["GET", "POST", "OPTIONS"],
                "allow_headers": ["Content-Type", "Accept"],
            }
        },
    )
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler()]
    )
    app.logger = logging.getLogger("flask.app")
    # Blueprint 등록
    from .routes import main_bp
    app.register_blueprint(main_bp)
    # 에러 핸들러 예시
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal server error: {error}")
        return "서버 내부 오류가 발생했습니다.", 500
    return app
