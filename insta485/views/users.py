"""Insta485 users view."""

import flask
import insta485


@insta485.app.route('/users/<user_url_slug>/', methods=['GET'])
def show_user(user_url_slug):
    """GET /users/<user_url_slug>/."""
    if "username" not in flask.session:
        return flask.redirect(flask.url_for('show_login'))

    connection = insta485.model.get_db()  # connect to db
    # User information/existence
    cur = connection.execute(
        """
        SELECT * FROM users WHERE username = ?;
        """,
        (user_url_slug, )
    )
    user = cur.fetchone()
    if not user:  # returned empty dict -> no user of this name
        flask.abort(404)

    logname = flask.session["username"]

    # Is logged in user following this user?
    check = connection.execute(
        """
        SELECT username1 FROM following WHERE username1 = ? AND username2 = ?;
        """,
        (logname, user_url_slug)
    ).fetchone()
    is_following = False
    if check:
        is_following = True  # if query returned nonempty, u1 follows u2

    # Post information
    cur = connection.execute(
        """
        SELECT postid, filename FROM posts WHERE owner = ?;
        """,
        (user_url_slug, )
    )
    posts = cur.fetchall()  # list of dictionaries

    # Number of followers
    cur = connection.execute(
        """
        SELECT COUNT(*) AS num_followers FROM following WHERE username2 = ?;
        """,
        (user_url_slug, )
    )
    fwerdata = cur.fetchone()
    # Number following
    cur = connection.execute(
        """
        SELECT COUNT(*) AS num_following FROM following WHERE username1 = ?;
        """,
        (user_url_slug, )
    )
    fwingdata = cur.fetchone()

    context = {
        "logname": logname,
        "user": user,
        "is_following": is_following,
        "posts": posts,
        "num_followers": fwerdata["num_followers"],
        "num_following": fwingdata["num_following"]
    }

    return flask.render_template("user.html", **context)


@insta485.app.route('/users/<user_url_slug>/followers/', methods=['GET'])
def show_followers(user_url_slug):
    """GET /users/<user_url_slug>/followers/."""
    if "username" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))

    connection = insta485.model.get_db()  # connect to db
    # User data/existence
    cur = connection.execute(
        """
        SELECT username FROM users WHERE username = ?;
        """,
        (user_url_slug, )
    )
    user = cur.fetchone()["username"]
    if not user:  # user does not exist in DB
        flask.abort(404)

    logname = flask.session["username"]

    # the below, line by line:
    #   set A:
    #   the set of all user_url_slug's followers
    #   set B:
    #   "indicator" set of if logname is following somebody who
    #      follows user_url_slug
    #   1. select set A
    #   2. if set B empty for a username then denote withg 0 - not following
    #   3. left join set A with set B: this yields a set with
    #         information regarding logname following users followers
    #   4. defines set B
    #   5-6. where username is in the set of those following user_url_slug
    cur = connection.execute(
        """
        SELECT u.username, u.filename,
        CASE WHEN f.username1 IS NULL THEN 0 ELSE 1 END AS is_following
        FROM users u LEFT JOIN following f
        ON u.username = f.username2 AND f.username1 = ?
        WHERE u.username
            IN (SELECT username1 FROM following WHERE username2 = ?);
        """,
        (logname, user_url_slug)
    )
    followers = cur.fetchall()
    context = {
        "logname": logname,
        "user": user,
        "followers": followers
    }
    return flask.render_template("followers.html", **context)


@insta485.app.route('/users/<user_url_slug>/following/', methods=['GET'])
def show_following(user_url_slug):
    """GET /users/<user_url_slug>/following/."""
    if "username" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))

    connection = insta485.model.get_db()  # connect to db
    # User data/existence
    cur = connection.execute(
        """
        SELECT username FROM users WHERE username = ?;
        """,
        (user_url_slug, )
    )
    user = cur.fetchone()
    if not user:  # user does not exist in DB
        flask.abort(404)

    logname = flask.session["username"]

    # the below, line by line:
    #   set A:
    #   the set of all user_url_slug's following
    #   set B:
    #   "indicator" set of if logname is following somebody who
    #      user_url_slug follows
    cur = connection.execute(
        """
        SELECT u.username, u.filename,
        CASE WHEN f.username1 IS NULL THEN 0 ELSE 1 END AS is_following
        FROM users u LEFT JOIN following f
        ON u.username = f.username2 AND f.username1 = ?
        WHERE u.username
            IN (SELECT username2 FROM following WHERE username1 = ?);
        """,
        (logname, user_url_slug)
    )
    following = cur.fetchall()

    context = {
        "logname": logname,
        "following": following
    }

    return flask.render_template("following.html", **context)


@insta485.app.route('/following/', methods=['POST'])
def manage_following():
    """POST /following/?target=URL."""
    if "username" not in flask.session:
        flask.abort(403, "You must be logged in to follow or unfollow users.")
    logname = flask.session["username"]

    operation = flask.request.form["operation"]
    username = flask.request.form["username"]

    connection = insta485.model.get_db()  # connect to db
    # the below is rather redundant: form only appears for real users
    cur = connection.execute(
        """
        SELECT username FROM users WHERE username = ?;
        """,
        (username, )
    )
    check = cur.fetchone()
    if not check:
        flask.abort(403, "User does not exist.")

    cur = connection.execute(
        """
        SELECT username1, username2 FROM following
        WHERE username1 = ? AND username2 = ?;
        """,
        (logname, username)
    )
    following_status = cur.fetchone()  # existence implies following

    if operation == "follow":
        if following_status:
            flask.abort(409, "Cannot follow user you are already following.")
        connection.execute(
            """
            INSERT INTO following (username1, username2)
            VALUES (?, ?);
            """,
            (logname, username)
        )

    elif operation == "unfollow":
        if not following_status:
            flask.abort(409, "Cannot unfollow user you are not following.")
        connection.execute(
            """
            DELETE FROM following
            WHERE username1 = ? AND username2 = ?;
            """,
            (logname, username)
        )

    else:
        flask.abort(400, "Invalid operation.")

    target_url = flask.request.args.get('target', flask.url_for('show_index'))
    return flask.redirect(target_url)
