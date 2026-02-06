from celery import Celery, Task
from flask import Flask

from app.api import bp as api_bp
from app.api.graph_service import GraphQueryService
from app.main import bp as main_bp
from db import KnowledgeGraphReader, Neo4jClient, Neo4jConfig


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


def init_neo4j(app: Flask) -> None:
    """Initialize Neo4j client and services."""
    neo4j_config = Neo4jConfig.from_env()
    neo4j_client = Neo4jClient(neo4j_config)
    reader = KnowledgeGraphReader(neo4j_client)
    graph_service = GraphQueryService(reader)

    app.extensions["neo4j_client"] = neo4j_client
    app.extensions["graph_service"] = graph_service


def create_app():
    app = Flask(__name__)

    # Load configuration from environment variables
    app.config.from_prefixed_env()
    app.config["JSON_AS_ASCII"] = False
    app.config["CELERY"] = {
        "broker_url": app.config.get("CELERY_BROKER_URL", "redis://localhost:6379/0"),
        "result_backend": app.config.get(
            "CELERY_RESULT_BACKEND", "redis://localhost:6379/1"
        ),
    }

    # Initialize extensions
    celery_init_app(app)
    init_neo4j(app)

    # Register blueprints
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(main_bp)

    return app
