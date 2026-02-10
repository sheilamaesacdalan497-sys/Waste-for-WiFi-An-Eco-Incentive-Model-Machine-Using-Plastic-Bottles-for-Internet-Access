from flask import Blueprint, render_template, request, redirect, url_for, current_app, jsonify
from db import add_rating

bp = Blueprint("rating", __name__)


@bp.route("/rating/<session_id>", methods=("GET", "POST"))
def rating(session_id):
    if request.method == "POST":
        # support both form and json
        if request.is_json:
            data = request.get_json()
            rating_value = int(data.get("rating", 0))
            comment = data.get("comment")
        else:
            rating_value = int(request.form.get("rating", 0))
            comment = request.form.get("comment")
        add_rating(session_id, rating_value, comment)
        # If JSON requested, return JSON so front-end can show modal
        if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"ok": True})
        return render_template("thank_you.html")
    return render_template("rating.htmo", session_id=session_id)


@bp.route("/api/rating/<session_id>", methods=("POST",))
def api_rating(session_id):
    data = request.get_json() or {}
    rating_value = int(data.get("rating", 0))
    comment = data.get("comment")
    add_rating(session_id, rating_value, comment)
    return jsonify({"ok": True})
