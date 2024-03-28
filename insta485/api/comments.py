"""Insta485 REST API for comments."""
import flask
import insta485
from insta485 import helpers


@insta485.app.route("/api/v1/comments/", methods=["POST"])
def post_comment():
    """POST /api/v1/comments/?postid=<postid>."""
    # authenticate
    logname = helpers.authenticate()

    postid = flask.request.args.get("postid")
    text = flask.request.json.get("text", None)
    connection = insta485.model.get_db()  # connect to db

    post_exists = connection.execute(
        """
        SELECT postid FROM posts WHERE postid = ?;
        """,
        (postid, )
    ).fetchone()
    if not post_exists:
        flask.abort(404)

    connection.execute(
        """
        INSERT INTO comments(owner, postid, text)
        VALUES (?, ?, ?);
        """,
        (logname, postid, text)
    )
    commentid = connection.execute(
        """
        SELECT last_insert_rowid();
        """
    ).fetchone()["last_insert_rowid()"]

    context = {
        "commentid": commentid,
        "lognameOwnsThis": True,
        "owner": logname,
        "ownerShowUrl": f"/users/{logname}/",
        "text": text,
        "url": f"/api/v1/comments/{commentid}/"
    }
    return flask.jsonify(**context), 201


@insta485.app.route("/api/v1/comments/<commentid>/", methods=["DELETE"])
def delete_comment(commentid):
    """DELETE /api/v1/comments/<commentid>/."""
    # authenticate
    logname = helpers.authenticate()

    connection = insta485.model.get_db()  # connect to db

    comment_exists = connection.execute(
        """
        SELECT commentid FROM comments WHERE commentid = ?;
        """,
        (commentid, )
    ).fetchone()
    if not comment_exists:
        flask.abort(404)

    owner = connection.execute(
        """
        SELECT owner FROM comments WHERE owner = ? AND commentid = ?;
        """,
        (logname, commentid)
    ).fetchone()
    if not owner:
        flask.abort(403)

    connection.execute(
        """
        DELETE FROM comments WHERE commentid = ?;
        """,
        (commentid, )
    )

    return "", 204
