"""
Insta485 index (main) view.

URLs include:
/
/uploads/<filename>
"""
import flask
import arrow
import insta485


@insta485.app.route('/', methods=['GET'])
def show_index():
    """GET /."""
    if "username" not in flask.session:
        return flask.redirect(flask.url_for("show_login"))
    logname = flask.session["username"]

    # Connect to database
    connection = insta485.model.get_db()
    # Query database
    cur = connection.execute(
        # Selects the post ID, image filename, owner (username), and
        #   creation timestamp
        # from the posts table, aliased as p, also renames filename as
        #   user_image
        "SELECT p.postid, p.filename, p.owner, p.created, "
        "u.filename AS user_image, "
        # A subquery that counts the number of likes for each post and
        #   labels this count as likes.
        "(SELECT COUNT(*) FROM likes WHERE postid = p.postid) AS likes "
        # indicates that the above selected data should be fetched from
        #   a inner join of the posts table and users table (rows combine)
        #   where owner and username match
        "FROM posts p JOIN users u ON p.owner = u.username "
        # specifies to only inclulde information from users followed by the
        #   current user
        "WHERE p.owner IN "
        "(SELECT username2 FROM following WHERE username1 = ?) "
        # this condition includes the owners own posts in descending order
        #   by postid
        "OR p.owner = ? ORDER BY p.postid DESC",
        (logname, logname)
    )

    # Fetching all rows of a query result, returning them as a list of tuples.
    posts = cur.fetchall()

    for post in posts:
        post['created'] = arrow.get(post['created']).humanize()

        cur = connection.execute(
            """
            SELECT likeid AS is_liked
            FROM likes WHERE postid = ? AND owner = ?;
            """,
            (post["postid"], logname)
        )
        is_liked = cur.fetchone()
        post["is_liked"] = is_liked

        cur = connection.execute(
            """
            SELECT owner, text FROM comments WHERE postid = ?;
            """,
            (post["postid"], )
        )
        comments = cur.fetchall()
        post["comments"] = comments

    # Add database info to context
    # Creates a dictionary named context with a key "users".
    context = {
        "logname": logname,
        "posts": posts
    }

    # render a template, specifically "index.html".
    # The render_template function is provided by Flask to render a
    #    template file.
    # The **context syntax is used to pass the context dictionary as
    #    keyword arguments to the template.
    return flask.render_template("index.html", **context)


@insta485.app.route('/uploads/<filename>', methods=['GET'])
def uploaded_file(filename):
    """GET /uploads/<filename>."""
    # Check if the user is authenticated
    if 'username' not in flask.session:
        # If user is not authenticated, return 403 Forbidden
        flask.abort(403)

    connection = insta485.model.get_db()  # connect to db
    cur = connection.execute(
        """
        SELECT * FROM posts WHERE filename = ?;
        """,
        (filename, )
    )
    check = cur.fetchall()
    if not check:
        flask.abort(404)  # not found

    folder = insta485.app.config['UPLOAD_FOLDER']
    return flask.send_from_directory(folder, filename)
