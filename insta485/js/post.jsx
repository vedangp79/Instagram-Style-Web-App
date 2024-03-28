import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";
import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";
import utc from "dayjs/plugin/utc";

// The parameter of this function is an object with a string called url inside it.
// url is a prop for the Post component.
export default function Post({ url }) {
  /* Display image and post owner of a single post */

  // the number of these useStates can probably be decreased
  //   by making one that is a list of static items for a post
  //   i.e. filename, owner, owner_pfp, urls related to those
  const [ownerImgUrl, setOwnerImgUrl] = useState("");
  const [owner, setOwner] = useState("");
  const [ownerShowUrl, setOwnerShowUrl] = useState("");
  const [postShowUrl, setPostShowUrl] = useState("");
  const [created, setCreated] = useState();
  const [imgUrl, setImgUrl] = useState("");
  const [postid, setPostid] = useState("");
  const [likes, setLikes] = useState({});
  const [comments, setComments] = useState([]);

  useEffect(() => {
    // Declare a boolean flag that we can use to cancel the API request.
    let ignoreStaleRequest = false;

    // Call REST API to get the post's information
    fetch(url, { credentials: "same-origin" })
      .then((response) => {
        if (!response.ok) throw Error(response.statusText);
        return response.json();
      })
      .then((data) => {
        // If ignoreStaleRequest was set to true, we want to ignore the results of the
        // the request. Otherwise, update the state to trigger a new render.
        if (!ignoreStaleRequest) {
          setOwnerImgUrl(data.ownerImgUrl)
          setOwner(data.owner);
          setOwnerShowUrl(data.ownerShowUrl);
          setPostShowUrl(data.postShowUrl);
          dayjs.extend(relativeTime);
          dayjs.extend(utc);
          const timeCreated = dayjs(data.created).utc(true).fromNow();
          setCreated(timeCreated);
          setImgUrl(data.imgUrl);
          setPostid(data.postid);
          setLikes(data.likes);
          setComments(data.comments);
        }
      })
      .catch((error) => console.log(error));

    return () => {
      // This is a cleanup function that runs whenever the Post component
      // unmounts or re-renders. If a Post is about to unmount or re-render, we
      // should avoid updating state.
      ignoreStaleRequest = true;
    };
  }, [url]);


  const handleLike = () => {
    console.log("like!")
    fetch(`/api/v1/likes/?postid=${postid}`, {
        method: 'POST',
        credentials: 'include',
        // headers: {
        // 'Content-Type': 'application/json',
        // },
    })
    .then((response) => response.json())
    .then((data) => {
        setLikes({
        ...likes,
        lognameLikesThis: true,
        numLikes: likes.numLikes + 1,
        url: data.url,
        });
    })
    .catch((error) => console.error('Error liking the post:', error));
  };


  const handleUnlike = () => {
    console.log("unlike!");
    if (!likes.url) return; // check if like URL exists
    fetch(likes.url, {
      method: 'DELETE',
      credentials: 'include',  // same-origin??
    })
    .then(() => {
      setLikes({
        ...likes,
        lognameLikesThis: false,
        numLikes: likes.numLikes - 1,
        url: null,
      });
    })
    .catch(error => console.error('Error unliking the post:', error));
  };


  const handleComment = (commentText) => {
    console.log("commenting!")
    fetch(`/api/v1/comments/?postid=${postid}`, {
      method: 'POST',
      credentials: 'include',
      body: JSON.stringify({ "text": commentText }),
    })
    .then(response => {
      if (!response.ok) throw new Error('Failed to post comment');
      return response.json();
    })
    .then(data => {
      // Update component's state here to include new comment
      console.log('Comment posted', data);
    })
    .catch(error => console.error('Error posting comment:', error));
  };


  const handleDeleteComment = (commentid) => {
    console.log("deleting comment!");
    fetch(`/api/v1/comments/${commentid}/`, {
      method: 'DELETE',
      credentials: 'include',
    })
    .then(response => {
      if (!response.ok) throw new Error('Failed to delete comment');
      // Update component's state to remove the deleted comment
      console.log('Comment deleted successfully');
    })
    .catch(error => console.error('Error deleting comment:', error));
  };


  const renderedComments = comments.map((comment) => (
      <div key={`commentid=${comment.commentid}`}>
        <a href={comment.ownerShowUrl} className="link">{comment.owner}</a>
        <span> {" "}{comment.text}</span>
        {comment.lognameOwnsThis && (
          <span>
            {" "}
            <button type="button" onClick={handleDeleteComment} data-testid="delete-comment-button">
              delete comment
            </button>
          </span>
        )}
      </div>
    )
  );
  

  // Render post image and post owner
  return (
    <div className="post">
      <p>
        <img src={ownerImgUrl} alt={`${owner}`} />
        <a href={ownerShowUrl} className="link">
          {" "}{owner}
        </a>
        <a href={postShowUrl} className="timestamp">{created}</a>
      </p>
      <img src={imgUrl} onDoubleClick={!likes.lognameLikesThis && handleLike} alt={`${owner}'s post`} className="post-image" />
      <div className="post-footer">
        <button type="button" onClick={likes.lognameLikesThis ? handleUnlike : handleLike} data-testid="like-unlike-button">
          {likes.lognameLikesThis ? "unlike" : "like"}
        </button>
        {" "}{likes.numLikes} {likes.numLikes === 1 ? "like" : "likes"}
        {renderedComments}
        <form onSubmit={handleComment} data-testid="comment-form">
          <input type="text" />
        </form>
      </div>
    </div>
  );
}

Post.propTypes = {
  url: PropTypes.string.isRequired,
};
