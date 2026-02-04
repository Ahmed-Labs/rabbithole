from celery.result import AsyncResult
from flask import jsonify, request

from app.api import bp
from app.services.relevance_tasks import get_relevance_task
from db import KnowledgeGraphReader, Neo4jClient, Neo4jConfig
from db.services import GraphFilters, GraphQueryService, ReactFlowFormatter
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


@bp.route("/get-relevance", methods=["POST"])
def get_relevance():
    data = request.get_json(silent=True) or {}

    query = data.get("query")
    if not query:
        return jsonify({"error": "Missing 'query'"}), 400

    max_depth = int(data.get("max_depth", 1))
    max_references = int(data.get("max_references", 10))

    task = get_relevance_task.delay(
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


# Initialize services (in production, use app factory pattern)
neo4j_client = Neo4jClient(Neo4jConfig.from_env())
reader = KnowledgeGraphReader(neo4j_client)
graph_service = GraphQueryService(reader)


@bp.route("/graph/<paper_id>", methods=["GET"])
def get_graph(paper_id: str):
    """
    Get knowledge graph for React Flow visualization.

    Query params:
        - min_year: Filter papers by minimum year
        - max_year: Filter papers by maximum year
        - min_citations: Filter papers by minimum citations
        - min_similarity: Filter edges by minimum relevance (0.0-1.0)
        - show_citations: Include citation edges (default: true)

    Returns:
        JSON with nodes and edges in React Flow format
    """
    # Parse filters from request
    filters = GraphFilters(
        min_year=request.args.get("min_year", type=int),
        max_year=request.args.get("max_year", type=int),
        min_citations=request.args.get("min_citations", type=int),
        min_similarity=request.args.get("min_similarity", type=float),
        include_citations=request.args.get("show_citations", "true").lower() == "true",
    )

    # Call service layer
    papers, relevance_edges, citation_edges = graph_service.get_filtered_graph(
        paper_id, filters
    )

    if not papers:
        return jsonify({"error": "Paper not found"}), 404

    # Format for frontend
    graph_data = ReactFlowFormatter.format_graph(
        papers, relevance_edges, citation_edges, root_id=paper_id
    )

    # Add stats
    graph_data["stats"] = {
        "total_papers": len(papers),
        "total_edges": len(relevance_edges) + len(citation_edges),
    }

    return jsonify(graph_data)


@bp.route("/paper/<paper_id>", methods=["GET"])
def get_paper_details(paper_id: str):
    """
    Get detailed paper information for Inspector panel.

    Returns:
        JSON with paper metadata and aggregated relevance scores
    """
    # Call service layer
    result = graph_service.get_paper_with_scores(paper_id)

    if not result:
        return jsonify({"error": "Paper not found"}), 404

    # Format for frontend
    details = ReactFlowFormatter.format_paper_details(
        result["paper"], result["relevance_scores"], result["explanation"]
    )

    return jsonify(details)
