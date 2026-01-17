from flask import jsonify

from app.api import bp
from app.tasks import add


@bp.route("/health")
def health():
    return jsonify({"status": "ok"})


@bp.route("/add")
def run_task():
    result = add.delay(2, 3)
    return jsonify(task_id=result.id)
