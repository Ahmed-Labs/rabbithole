from flask import current_app

from app.services.graph_query import GraphQueryService
from db import KnowledgeGraphWriter
from relevance_scoring import LLMScorer, RelevanceScorer


def get_graph_service() -> GraphQueryService:
    """Get graph service from app extensions."""
    return current_app.extensions["graph_service"]


def get_relevance_scorer() -> RelevanceScorer:
    """Get relevance scorer from app extensions."""
    return current_app.extensions["relevance_scorer"]


def get_graph_writer() -> KnowledgeGraphWriter:
    return current_app.extensions["graph_writer"]


def get_llm_scorer() -> LLMScorer:
    return current_app.extensions["llm_scorer"]
