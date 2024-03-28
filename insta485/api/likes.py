"""Insta485 REST API for likes."""
import flask
import insta485
from insta485 import helpers


@insta485.app.route("/api/v1/likes/", methods=["POST"])
def post_like():
    """POST /app/v1/likes/?postid=<postid>."""
    # authenticate
    logname = helpers.authenticate()

    postid = flask.request.args.get("postid", -1, int)

    connection = insta485.model.get_db()  # connect to db

    post_exists = connection.execute(
        """
        SELECT postid FROM posts WHERE postid = ?;
        """,
        (postid, )
    ).fetchone()
    if not post_exists:
        flask.abort(404)

    like = connection.execute(
        """
        SELECT likeid FROM likes WHERE owner = ? AND postid = ?;
        """,
        (logname, postid)
    ).fetchone()
    if like:  # like already exists
        likeid = like["likeid"]
        context = {
            "likeid": likeid,
            "url": f"/api/v1/likes/{likeid}/"
        }
        return flask.jsonify(**context), 200

    connection.execute(
        """
        INSERT INTO likes(owner, postid)
        VALUES (?, ?);
        """,
        (logname, postid)
    )
    likeid = connection.execute(
        "SELECT last_insert_rowid();"
    ).fetchone()["last_insert_rowid()"]

    context = {
        "likeid": likeid,
        "url": f"/api/v1/likes/{likeid}/"
    }
    return flask.jsonify(**context), 201


@insta485.app.route("/api/v1/likes/<likeid>/", methods=["DELETE"])
def delete_like(likeid):
    """DELETE /api/v1/likes/<likeid>/."""
    # authenticate
    logname = helpers.authenticate()

    connection = insta485.model.get_db()  # connect to db

    like_exists = connection.execute(
        """
        SELECT likeid FROM likes WHERE likeid = ?;
        """,
        (likeid, )
    ).fetchone()
    if not like_exists:
        flask.abort(404)

    like_owned = connection.execute(
        """
        SELECT likeid FROM likes WHERE owner = ? AND likeid = ?;
        """,
        (logname, likeid)
    ).fetchone()
    if not like_owned:
        flask.abort(403)

    connection.execute(
        """
        DELETE FROM likes WHERE likeid = ?;
        """,
        (likeid, )
    )

    return "", 204
