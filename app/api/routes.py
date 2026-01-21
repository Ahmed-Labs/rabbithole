import traceback

from celery.result import AsyncResult
from flask import jsonify, request

from app.api import bp
from app.services.relevance_tasks import get_relevance_task
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
