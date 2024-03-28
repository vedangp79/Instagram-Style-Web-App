"""Insta485 REST API for posts."""
import flask
import insta485
from insta485 import helpers


@insta485.app.route("/api/v1/posts/", methods=["GET"])
def get_posts():
    """
    GET /api/v1/posts/.

    Includes the support for size, page, postid_lte arguments.
    """
    # authentication
    logname = helpers.authenticate()

    # check if URL arguments provided
    size_arg = flask.request.args.get("size", 10, int)
    if size_arg <= 0:
        # size_arg must be strictly positive
        flask.abort(400)
    page_arg = flask.request.args.get("page", 0, int)
    if page_arg < 0:
        # page_arg must be nonnegative
        flask.abort(400)
    connection = insta485.model.get_db()  # connect to db
    # the below is only here to provide a default value to postid_lte_arg
    followed_posts = connection.execute(
        """
        SELECT postid FROM posts
        WHERE owner IN
            (SELECT username2 FROM following WHERE username1 = ?)
        OR owner = ? ORDER BY postid DESC LIMIT 1;
        """,
        (logname, logname)
    ).fetchone()
    postid_lte_arg = flask.request.args.get("postid_lte",
                                            followed_posts["postid"], int)
    posts = connection.execute(
        # selects size_arg posts in page = page_arg in descending order
        #   that are from users that are followed by logname or are from
        #   logname and occur before or at postid = postid_lte_arg
        # the third line defines the set of all usernames that logname is
        #   following
        # -ORDER BY DESC sorts in descending order
        # -LIMIT size_arg limits query to just size_arg posts
        """
        SELECT postid FROM posts
        WHERE postid <= ? AND (owner IN
            (SELECT username2 FROM following WHERE username1 = ?)
        OR owner = ?) ORDER BY postid DESC
        LIMIT ? OFFSET ?;
        """,
        (postid_lte_arg, logname, logname, size_arg, page_arg * size_arg)
    ).fetchall()  # fetchall() as this is expected to return more than 1 thing
    size = len(posts)

    # either exactly size_arg such posts or more than:
    #    indicative of a "next" page
    next_url = ""
    if size == size_arg:
        next_url = f"/api/v1/posts/?size={size_arg}" \
               f"&page={page_arg + 1}&postid_lte={postid_lte_arg}"
    results = []
    for post in posts:
        postid = post["postid"]
        results.append({"postid": postid,
                        "url": f"/api/v1/posts/{postid}/"})
    url = "/api/v1/posts/"
    if flask.request.args:
        url += "?"  # beginning of query parts
        for key in flask.request.args:
            url += "&" + key + "=" + flask.request.args[key]
        url = url.replace("&", "", 1)

    context = {
        "next": next_url,
        "results": results,
        "url": url
    }
    return flask.jsonify(**context)


@insta485.app.route("/api/v1/posts/<int:postid>/",
                    methods=["GET"])
def get_post_details(postid):
    """GET /api/v1/posts/<postid>/."""
    # authenticate
    logname = helpers.authenticate()

    connection = insta485.model.get_db()  # connect to db
    post_info = connection.execute(
        """
        SELECT p.postid, p.filename, p.owner, p.created, u.filename AS pfp,
        (SELECT COUNT(*) FROM likes WHERE postid = p.postid) AS num_likes
        FROM posts p JOIN users u ON p.owner = u.username
        WHERE p.postid = ?;
        """,
        (postid, )
    ).fetchone()
    if not post_info:  # post not found
        flask.abort(404)
    comments = connection.execute(
        # ownerShowUrl, url appear here such that order may be mainted
        #   in the dict when printing out the context
        """
        SELECT commentid, owner == ? AS lognameOwnsThis, owner,
        owner AS ownerShowUrl, text, commentid AS url
        FROM comments WHERE postid = ?;
        """,
        (logname, postid)
    ).fetchall()

    # edit comment values to match output desired
    for comment in comments:
        val = comment["lognameOwnsThis"]
        # the below converts 0 -> False, 1 -> True
        comment["lognameOwnsThis"] = val == 1
        val = comment["ownerShowUrl"]
        comment["ownerShowUrl"] = f"/users/{val}/"
        val = comment["url"]
        comment["url"] = f"/api/v1/comments/{val}/"

    # get post info for ease of use
    created = post_info["created"]
    cur = connection.execute(
        """
        SELECT likeid FROM likes WHERE owner = ? AND postid = ?;
        """,
        (logname, postid)
    ).fetchone()
    # url is to a likeid: only exists if lognameLikesThis
    likes = {
        "lognameLikesThis": bool(cur),
        "numLikes": post_info["num_likes"],
        "url": f"/api/v1/likes/{cur['likeid']}/" if cur else None
    }
    owner = post_info["owner"]

    context = {
        "comments": comments,
        "comments_url": f"/api/v1/comments/?postid={postid}",
        "created": created,
        "imgUrl": f"/uploads/{post_info['filename']}",
        "likes": likes,
        "owner": owner,
        "ownerImgUrl": f"/uploads/{post_info['pfp']}",
        "ownerShowUrl": f"/users/{owner}/",
        "postShowUrl": f"/posts/{postid}/",
        "postid": postid,
        "url": f"/api/v1/posts/{postid}/"
    }
    return flask.jsonify(**context)
