from flask import request, jsonify
from app.api import bp


@bp.route("/embeddings", methods=["POST"])
def embeddings():
    return jsonify({"message": "Embeddings endpoint"})
