"""Helper functions for GET/POST requests."""

import pathlib
import hashlib
import uuid
import flask
import insta485


def authenticate():
    """Authenticate user in REST API operations."""
    connection = insta485.model.get_db()  # connect to db
    username = ""
    if flask.request.authorization:
        # trying to use HTTP Basic Access Authentication
        # need to do authentication from here
        username = flask.request.authorization["username"]
        password = flask.request.authorization["password"]
        db_passwd = connection.execute(
            """
            SELECT password FROM users WHERE username = ?;
            """,
            (username, )
        ).fetchone()
        if not db_passwd:
            # user does not exist
            flask.abort(403)
        db_passwd = db_passwd["password"]
        hashed_passwd = regen_password(password, db_passwd)
        if hashed_passwd != db_passwd:
            # passwords do not match
            flask.abort(403)
    else:
        if "username" not in flask.session:
            flask.abort(403)
        username = flask.session["username"]
    return username


def delete_file(filename):
    """Delete file described by "filename"."""
    path = insta485.app.config["UPLOAD_FOLDER"]/filename
    path.unlink()


def delete_pfp():
    """Delete the pfp of the logged in user."""
    connection = insta485.model.get_db()
    filename = connection.execute(
        """
        SELECT filename FROM users WHERE username = ?;
        """,
        (flask.session["username"], )
    ).fetchone()["filename"]
    delete_file(filename)


def delete_posts():
    """Delete all posts under a logged in user."""
    connection = insta485.model.get_db()
    cur = connection.execute(
        """
        SELECT filename FROM posts WHERE owner = ?;
        """,
        (flask.session["username"], )
    )
    filenames_dict = cur.fetchall()
    for elt in filenames_dict:
        filename = elt["filename"]
        delete_file(filename)


def generate_img_uuid(file):
    """Generate UUID for image uploaded."""
    stem = uuid.uuid4().hex  # for image processing
    filename = file.filename
    suffix = pathlib.Path(filename).suffix.lower()
    uuid_basename = f"{stem}{suffix}"
    path = insta485.app.config["UPLOAD_FOLDER"]/uuid_basename
    file.save(path)
    return uuid_basename


def generate_new_password(raw):
    """Generate hashed password from raw input."""
    algorithm = "sha512"
    hash_obj = hashlib.new(algorithm)
    salt = uuid.uuid4().hex  # for password hashing
    salted = salt + raw
    hash_obj.update(salted.encode('utf-8'))
    password_hash = hash_obj.hexdigest()
    password = "$".join([algorithm, salt, password_hash])
    return password


def regen_password(raw, db):
    """Regenerates a password given a password to check against."""
    algorithm = "sha512"
    hash_obj = hashlib.new(algorithm)
    salt = db.split('$')[1]
    salted = salt + raw
    hash_obj.update(salted.encode('utf-8'))
    password_hash = hash_obj.hexdigest()
    password = "$".join([algorithm, salt, password_hash])
    return password
