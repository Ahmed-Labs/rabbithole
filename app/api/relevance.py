from flask import request, jsonify
from app.api import bp


@bp.route("/relevance", methods=["POST"])
def relevance():
    return jsonify({"message": "Relevance endpoint"})
