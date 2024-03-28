"""Insta485 explore view."""

import flask
import insta485


@insta485.app.route('/explore/', methods=['GET'])
def show_explore():
    """Display /explore/ route."""
    # Check if user is logged in
    if 'username' not in flask.session:
        return flask.redirect(flask.url_for('show_login'))

    # Connect to database
    connection = insta485.model.get_db()

    # Query database to find users that the logged-in user is not following
    logname = flask.session["username"]
    query = '''
        SELECT username, filename AS user_image
        FROM users
        WHERE username NOT IN
            (SELECT username2 FROM following WHERE username1 = ?)
            AND username != ?
    '''
    cur = connection.execute(query, (logname, logname))
    users_not_followed = cur.fetchall()

    # Add database info to context
    context = {
        "logname": logname,
        "users_not_followed": users_not_followed
    }
    return flask.render_template("explore.html", **context)
