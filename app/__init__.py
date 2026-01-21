from celery import Celery, Task
from flask import Flask
from flask_cors import CORS

from app.api import bp as api_bp
from app.main import bp as main_bp


def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app


def create_app():
    app = Flask(__name__)

    # Enable CORS for all routes
    CORS(app, origins=["http://localhost:5173", "http://localhost:5174"])

    # Load configuration from environment variables
    app.config.from_prefixed_env()
    app.config["JSON_AS_ASCII"] = False
    app.config["CELERY"] = {
        "broker_url": app.config.get("CELERY_BROKER_URL", "redis://localhost:6379/0"),
        "result_backend": app.config.get(
            "CELERY_RESULT_BACKEND", "redis://localhost:6379/1"
        ),
    }
    celery_init_app(app)

    # Register blueprints
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(main_bp)

    return app
