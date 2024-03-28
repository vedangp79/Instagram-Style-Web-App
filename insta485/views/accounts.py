"""Insta485 account-related views."""

import flask
import insta485
from insta485 import helpers


# below are routes for the web app
@insta485.app.route('/accounts/login/', methods=['GET'])
def show_login():
    """GET /accounts/login/."""
    # if already logged in, go to home
    if "username" in flask.session:
        return flask.redirect(flask.url_for('show_index'))

    return flask.render_template("login.html")


@insta485.app.route('/accounts/create/', methods=['GET'])
def show_account_create():
    """GET /accounts/create/."""
    if "username" in flask.session:
        return flask.redirect(flask.url_for("show_edit"))

    return flask.render_template("create.html")


@insta485.app.route('/accounts/delete/', methods=['GET'])
def show_account_delete():
    """GET /accounts/delete/."""
    if "username" not in flask.session:
        flask.redirect(flask.url_for('show_login'))
    logname = flask.session["username"]
    context = {"logname": logname}
    return flask.render_template("delete_account.html", **context)


@insta485.app.route('/accounts/edit/', methods=['GET'])
def show_account_edit():
    """GET /accounts/edit/."""
    if "username" not in flask.session:
        flask.redirect(flask.url_for('show_login'))
    logname = flask.session["username"]

    connection = insta485.model.get_db()  # connect to db
    cur = connection.execute(
        """
        SELECT filename, username, fullname, email
        FROM users WHERE username = ?;
        """,
        (logname, )
    )
    context = cur.fetchone()
    context["logname"] = logname

    return flask.render_template("edit_account.html", **context)


@insta485.app.route('/accounts/password/', methods=['GET'])
def show_update_password():
    """GET /accounts/password/."""
    if "username" not in flask.session:
        flask.redirect(flask.url_for('show_login'))
    logname = flask.session["username"]

    context = {"logname": logname}
    return flask.render_template("password.html", **context)


@insta485.app.route('/accounts/auth/', methods=['GET'])
def auth():
    """GET /accounts/auth/."""
    if "username" in flask.session:
        return ""  # or flask.Response(status=200)
    flask.abort(403)


@insta485.app.route('/accounts/logout/', methods=['POST'])
def handle_logout():
    """POST /accounts/logout/."""
    # logout user, i.e. clear cookies
    flask.session.clear()

    return flask.redirect(flask.url_for("show_login"))


def handle_login():
    """Handle account login."""
    username = flask.request.form["username"]
    raw_password = flask.request.form["password"]

    if username == "" or raw_password == "":
        # username or password was left empty
        flask.abort(400)

    connection = insta485.model.get_db()  # connect to db
    cur = connection.execute(
        """
        SELECT password FROM users WHERE username = ?;
        """,
        (username, )
    )
    db_password = cur.fetchone()
    if not db_password:
        flask.abort(403, "Account does not exist.")
    # hash input password
    db_password = db_password["password"]
    password = helpers.regen_password(raw_password, db_password)
    if password != db_password:
        # if db_password isn't equal to password_db_string, auth
        #   failed: either passwords mismatch, or usernames mismatch
        flask.abort(403, "Password incorrect.")

    flask.session["username"] = username

    target_url = flask.request.args.get("target", flask.url_for('show_index'))
    return flask.redirect(target_url)


def handle_create():
    """Handle account creation."""
    username = flask.request.form["username"]
    raw_password = flask.request.form["password"]
    fullname = flask.request.form["fullname"]
    email = flask.request.form["email"]
    file = flask.request.files["file"]  # of file type

    # if any field is left empty, abort with code 400
    if username == "" or raw_password == "" or fullname == "":
        flask.abort(400)
    if email == "" or not file:
        flask.abort(400)

    connection = insta485.model.get_db()  # connect to db
    cur = connection.execute(
        """
        SELECT username FROM users WHERE username = ?;
        """,
        (username, )
    )
    matches = cur.fetchall()
    if matches:  # if matches is nonempty, then username already in use
        flask.abort(409)

    # convert filename to UUID, save to disk (/var/uploads/)
    filename = helpers.generate_img_uuid(file)

    # hash password to store it
    password = helpers.generate_new_password(raw_password)

    connection.execute(
        """
        INSERT INTO users (username, fullname, email, filename, password)
        VALUES (?, ?, ?, ?, ?);
        """,
        (username, fullname, email, filename, password)
    )

    flask.session["username"] = username

    target_url = flask.request.args.get("target", flask.url_for('show_index'))
    return flask.redirect(target_url)


def handle_delete():
    """Handle account deletion."""
    if "username" not in flask.session:
        flask.abort(403)

    helpers.delete_pfp()
    helpers.delete_posts()

    connection = insta485.model.get_db()
    connection.execute(
        """
        DELETE FROM users WHERE username = ?;
        """,
        (flask.session["username"], )
    )

    flask.session.clear()

    alt_url = flask.url_for('show_account_create')
    target_url = flask.request.args.get("target", alt_url)
    return flask.redirect(target_url)


def handle_edit_account():
    """Handle account editing."""
    if "username" not in flask.session:
        flask.abort(403)

    file = flask.request.files["file"]  # of file type
    fullname = flask.request.form["fullname"]
    email = flask.request.form["email"]

    if fullname == "" or email == "":
        flask.abort(400)

    filename = ""  # set to empty string for boolean usage
    if file:
        helpers.delete_pfp()  # delete old pfp
        filename = helpers.generate_img_uuid(file)  # generate new pfp

    # Below, connect to the DB and update fields under user entry.
    connection = insta485.model.get_db()  # connect to db
    if filename:
        connection.execute(
            """
            UPDATE users
            SET fullname = ?, email = ?, filename = ?
            WHERE username = ?;
            """,
            (fullname, email, filename, flask.session["username"])
        )
    else:
        connection.execute(
            """
            UPDATE users
            SET fullname = ?, email = ?
            WHERE username = ?
            """,
            (fullname, email, flask.session["username"])
        )

    target_url = flask.request.args.get("target", flask.url_for('show_index'))
    return flask.redirect(target_url)


def handle_update_password():
    """Handle updating password."""
    if "username" not in flask.session:
        flask.abort(403)

    raw_password = flask.request.form["password"]
    raw_password1 = flask.request.form["new_password1"]
    raw_password2 = flask.request.form["new_password2"]

    if raw_password == "" or raw_password1 == "" or raw_password2 == "":
        flask.abort(400)

    connection = insta485.model.get_db()  # connect to db
    old_db_pass = connection.execute(
        """
        SELECT password FROM users WHERE username = ?;
        """,
        (flask.session["username"], )
    ).fetchone()["password"]
    old_pass = helpers.regen_password(raw_password, old_db_pass)
    if old_pass != old_db_pass:
        # password verification failed, abort with code 403
        flask.abort(403, "Original passwords mismatch.")

    new_password1 = helpers.generate_new_password(raw_password1)
    new_password2 = helpers.regen_password(raw_password2, new_password1)
    if new_password1 != new_password2:
        # mismatch in new passwords, abort with code 401
        flask.abort(401, "New passwords do not match.")

    connection.execute(
        """
        UPDATE users SET password = ? WHERE username = ?;
        """,
        (new_password1, flask.session["username"])
    )

    # error check here: look into usage of ?target
    target_url = flask.request.args.get("target", flask.url_for('show_index'))
    return flask.redirect(target_url)


@insta485.app.route('/accounts/', methods=['POST'])
def handle_account():
    """POST /accounts/?target=URL."""
    operation = flask.request.form["operation"]
    val = ""
    if operation == "login":
        val = handle_login()
    elif operation == "create":
        val = handle_create()
    elif operation == "delete":
        val = handle_delete()
    elif operation == "edit_account":
        val = handle_edit_account()
    elif operation == "update_password":
        val = handle_update_password()

    return val
