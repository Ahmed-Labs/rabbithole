import traceback

from celery.result import AsyncResult
from flask import current_app, jsonify, request

from app.api import bp
from app.services.graph_formatting import ReactFlowFormatter
from app.services.graph_query import GraphFilters
from app.services.embedding_task import generate_embeddings_task
from paper_retrieval.paper_metadata import search


@bp.route("/health")
def health():
    return jsonify({"status": "ok"})


@bp.route("/search", methods=["GET"])
def search_papers():
    query = request.args.get("query")
    if not query:
        return jsonify({"error": "Missing 'query' parameter"}), 400

    limit = 10

    papers = search(query, limit=limit)
    papers_data = [paper.to_props() for paper in papers]

    return jsonify({"papers": papers_data})


@bp.route("/embed", methods=["POST"])
def get_relevance():
    data = request.get_json(silent=True) or {}

    query = data.get("query")
    if not query:
        return jsonify({"error": "Missing 'query'"}), 400

    max_depth = int(data.get("max_depth", 1))
    max_references = int(data.get("max_references", 10))

    task = generate_embeddings_task.delay(
        query=query,
        max_depth=max_depth,
        max_references=max_references,
    )

    return jsonify({"task_id": task.id, "status": "queued"}), 202


@bp.route("/task-status/<task_id>")
def task_status(task_id: str):
    result = AsyncResult(task_id)

    response = {
        "task_id": task_id,
        "status": result.state,
    }

    if result.successful():
        response["result"] = result.result
    elif result.failed():
        response["error"] = str(result.info)

    return jsonify(response)


def get_graph_service():
    """Get graph service from app extensions."""
    return current_app.extensions["graph_service"]


@bp.route("/graph/<paper_id>", methods=["GET"])
def get_graph(paper_id: str):
    """
    Get knowledge graph for React Flow visualization.

    Query params:
        - min_year: Filter papers by minimum year
        - max_year: Filter papers by maximum year
        - min_citations: Filter papers by minimum citations
        - min_relevance: Filter edges by minimum relevance (0.0-1.0)

    Returns:
        JSON with nodes and edges in React Flow format
    """
    filters = GraphFilters(
        min_year=request.args.get("min_year", type=int),
        max_year=request.args.get("max_year", type=int),
        min_citations=request.args.get("min_citations", type=int),
        min_relevance=request.args.get("min_relevance", type=float),
    )

    graph_service = get_graph_service()
    papers, relevance_edges, citation_edges = graph_service.get_filtered_graph(
        paper_id, filters
    )

    if not papers:
        return jsonify({"error": "Paper not found"}), 404

    graph_data = ReactFlowFormatter.format_graph(
        papers, relevance_edges, citation_edges, root_id=paper_id
    )

    return jsonify(graph_data)
