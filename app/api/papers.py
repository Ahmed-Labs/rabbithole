from flask import request, jsonify
from app.api import bp


@bp.route("/papers", methods=["GET"])
def papers():
    return jsonify({"message": "Papers endpoint"})
