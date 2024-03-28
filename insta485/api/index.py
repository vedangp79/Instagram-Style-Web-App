"""Insta485 REST API for resources."""
import flask
import insta485


@insta485.app.route("/api/v1/", methods=["GET"])
def get_index():
    """GET /api/v1/."""
    context = {
        "comments": "/api/v1/comments/",
        "likes": "/api/v1/likes/",
        "posts": "/api/v1/posts/",
        "url": "/api/v1/"
    }
    return flask.jsonify(**context)
