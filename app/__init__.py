from celery import Celery, Task
from flask import Flask
from flask_cors import CORS

from app.api import bp as api_bp
from app.services.graph_query import GraphQueryService
from db import KnowledgeGraphReader, KnowledgeGraphWriter, Neo4jClient, Neo4jConfig
from relevance_scoring import RelevanceScorer
from relevance_scoring.llm_scorer import LLMScorer


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


def init_extensions(app: Flask) -> None:
    neo4j_config = Neo4jConfig.from_env()
    neo4j_client = Neo4jClient(neo4j_config)
    reader = KnowledgeGraphReader(neo4j_client)
    graph_writer = KnowledgeGraphWriter(neo4j_client)
    graph_service = GraphQueryService(reader)

    app.extensions["neo4j_client"] = neo4j_client
    app.extensions["graph_service"] = graph_service
    app.extensions["graph_writer"] = graph_writer
    app.extensions["relevance_scorer"] = RelevanceScorer()
    app.extensions["llm_scorer"] = LLMScorer()


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

    # Initialize extensions
    celery_init_app(app)
    init_extensions(app)

    # Register blueprints
    app.register_blueprint(api_bp, url_prefix="/api")

    return app
