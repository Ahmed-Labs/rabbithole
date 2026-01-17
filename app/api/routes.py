from flask import jsonify, request

from app.api import bp
from app.services.relevance_tasks import get_relevance_task
from app.tasks import add


@bp.route("/health")
def health():
    return jsonify({"status": "ok"})


@bp.route("/add")
def run_task():
    result = add.delay(2, 3)
    return jsonify(task_id=result.id)


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

    return (
        jsonify(
            {
                "task_id": task.id,
                "status": "queued",
            }
        ),
        202,
    )
