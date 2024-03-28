"""Insta485 posts view."""

import flask
import arrow
import insta485
from insta485 import helpers


@insta485.app.route('/posts/<postid_url_slug>/', methods=['GET'])
def show_post(postid_url_slug):
    """GET /posts/<postid_url_slug>/."""
    if "username" not in flask.session:
        return flask.redirect(flask.url_for('show_login'))

    connection = insta485.model.get_db()  # connect to db
    cur = connection.execute(
        """
        SELECT p.*, u.filename AS user_image,
        (SELECT COUNT(*) FROM likes WHERE postid = p.postid) AS likes
        FROM posts p JOIN users u ON p.owner = u.username
        WHERE p.postid = ?;
        """,
        (postid_url_slug, )
    )
    post = cur.fetchone()
    if not post:
        # not necessarily said in the spec, but trying to access something
        #    like a post that was deleted or DNE should result in "not found"
        flask.abort(404)

    post['created'] = arrow.get(post['created']).humanize()
    logname = flask.session["username"]

    cur = connection.execute(
        """
        SELECT * FROM likes WHERE postid = ? AND owner = ?;
        """,
        (post["postid"], logname)
    )
    is_liked = cur.fetchone()
    post["is_liked"] = is_liked

    cur = connection.execute(
        """
        SELECT owner, commentid, text FROM comments WHERE postid = ?
        ORDER BY commentid ASC;
        """,
        (postid_url_slug, )
    )
    comments = cur.fetchall()

    context = {
        "logname": logname,
        "post": post,
        "comments": comments
    }

    return flask.render_template("post.html", **context)


@insta485.app.route('/posts/', methods=['POST'])
def handle_post():
    """POST /posts/?target=URL."""
    if "username" not in flask.session:
        # not listed in the spec, but this page shouldn't be accessible
        #    to someone who is not logged in
        flask.abort(403)
    logname = flask.session["username"]

    operation = flask.request.form["operation"]
    if operation == "delete":
        postid = flask.request.form["postid"]
        connection = insta485.model.get_db()  # connect to db
        cur = connection.execute(
            """
            SELECT filename FROM posts WHERE postid = ? AND owner = ?;
            """,
            (postid, logname)
        )
        filename = cur.fetchone()
        if not filename:  # empty
            flask.abort(403)
        filename = filename["filename"]
        helpers.delete_file(filename)

        connection.execute(
            """
            DELETE FROM posts WHERE postid = ?;
            """,
            (postid, )
        )
    elif operation == "create":
        file = flask.request.files["file"]  # of file type
        # file empty/not provided, abort with code 400
        if not file:
            flask.abort(400)
        filename = helpers.generate_img_uuid(file)
        connection = insta485.model.get_db()  # connect to db
        connection.execute(
            """
            INSERT INTO posts (filename, owner)
            VALUES (?, ?);
            """,
            (filename, logname)
        )
    else:
        flask.abort(400)  # unknown operation

    alt_url = flask.url_for("show_user", user_url_slug=logname)
    target_url = flask.request.args.get("target", alt_url)
    return flask.redirect(target_url)


@insta485.app.route('/likes/', methods=['POST'])
def handle_like():
    """POST /likes/?target=URL."""
    if "username" not in flask.session:
        flask.abort(403)
    logname = flask.session["username"]

    operation = flask.request.form["operation"]
    postid = flask.request.form["postid"]
    target_url = flask.request.args.get('target', flask.url_for('show_index'))

    connection = insta485.model.get_db()
    cur = connection.execute(
        """
        SELECT * FROM likes WHERE postid = ? AND owner = ?;
        """,
        (postid, logname)
    )
    like_exists = cur.fetchone()
    if operation == "like" and not like_exists:
        connection.execute(
            """
            INSERT INTO likes (postid, owner)
            VALUES (?, ?);
            """,
            (postid, logname)
        )
    elif operation == "unlike" and like_exists:
        connection.execute(
            """
            DELETE FROM likes WHERE postid = ? AND owner = ?;
            """,
            (postid, logname)
        )
    else:
        # If trying to like an already liked post or unlike a not liked post
        flask.abort(409)

    return flask.redirect(target_url)


@insta485.app.route('/comments/', methods=['POST'])
def handle_comment():
    """POST /comments/?target=URL."""
    if "username" not in flask.session:
        flask.redirect(flask.url_for("show_login"))
    logname = flask.session["username"]

    operation = flask.request.form["operation"]

    if operation == "delete":
        commentid = flask.request.form["commentid"]
        connection = insta485.model.get_db()  # connect to db
        cur = connection.execute(
            """
            SELECT owner FROM comments WHERE commentid = ?;
            """,
            (commentid, )
        )
        owner = cur.fetchone()["owner"]
        if owner != logname:
            flask.abort(403, "Cannot delete another's comment.")
        connection.execute(
            """
            DELETE FROM comments WHERE commentid = ?;
            """,
            (commentid, )
        )
    elif operation == "create":
        postid = flask.request.form["postid"]
        text = flask.request.form["text"]
        if not text:
            flask.abort(400)  # tried to do empty comment
        connection = insta485.model.get_db()  # connect to db
        connection.execute(
            """
            INSERT INTO comments (owner, postid, text)
            VALUES (?, ?, ?);
            """,
            (logname, postid, text)
        )
    else:
        flask.abort(400)

    target_url = flask.request.args.get("target", flask.url_for('show_index'))
    return flask.redirect(target_url)
