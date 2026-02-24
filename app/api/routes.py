import traceback

from celery.result import AsyncResult
from flask import current_app, jsonify, request

from app.api import bp
from app.extensions import get_graph_service, get_graph_writer, get_relevance_scorer
from app.services.embedding_task import generate_embeddings_task
from app.services.graph_formatting import ReactFlowFormatter
from app.services.graph_query import GraphFilters
from app.services.llm_task import generate_llm_score
from paper_retrieval.paper_metadata import search
from relevance_scoring.relevance_scorer import RelevanceEdge


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
def embed():
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
        max_depth=request.args.get("max_depth", type=int) or 3,
        min_year=request.args.get("min_year", type=int),
        max_year=request.args.get("max_year", type=int),
        min_citations=request.args.get("min_citations", type=int),
        min_relevance=request.args.get("min_relevance", type=float),
    )

    graph_service = get_graph_service()
    papers, relevance_edges, citation_edges = graph_service.get_filtered_graph(
        paper_id, filters
    )

    if not papers or paper_id not in papers:
        return jsonify({"error": "Paper not found"}), 404

    connected_pids = [pid for pid in papers.keys() if pid != paper_id]
    relevance_pairs = [(r.src_id, r.dest_id) for r in relevance_edges]

    # Generate missing relevance scores from embeddings
    relevance_scorer = get_relevance_scorer()
    new_relevance_edges: list[RelevanceEdge] = []
    llm_targets = []

    p1 = papers.get(paper_id)

    for pid in connected_pids:
        if (paper_id, pid) in relevance_pairs or (pid, paper_id) in relevance_pairs:
            continue

        p2 = papers.get(pid, None)
        if p2 is None:
            continue

        score = relevance_scorer.compute_relevance_score(p1, p2)
        if score.semantic_similarity == 0.0:
            continue

        edge = RelevanceEdge(
            src_id=paper_id,
            dest_id=pid,
            relevance_score=score,
        )

        new_relevance_edges.append(edge)
        llm_targets.append(p2.to_props())

    # Store new relevance edges and add them to response
    task_data = {}
    if len(new_relevance_edges) > 0:
        db = get_graph_writer()
        db.upsert_relevance_edges(new_relevance_edges)
        relevance_edges.extend(new_relevance_edges)

        # Queue LLM task
        task = generate_llm_score.delay(p1.to_props(), llm_targets)
        task_data["task_id"] = task.id
        task_data["status"] = "queued"

    graph_data = ReactFlowFormatter.format_graph(
        papers, relevance_edges, citation_edges, root_id=paper_id
    )

    return jsonify(
        {
            "data": graph_data,
            **task_data,
        }
    )
