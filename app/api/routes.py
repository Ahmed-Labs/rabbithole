from flask import jsonify
from app.api import bp


@bp.route("/health")
def health():
    return jsonify({"status": "ok"})
