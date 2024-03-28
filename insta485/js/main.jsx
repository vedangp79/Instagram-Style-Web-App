import React, { StrictMode, useState, useEffect } from "react";
import { createRoot } from "react-dom/client";
import InfiniteScroll from 'react-infinite-scroll-component';
import Post from "./post";

function Feed() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [nextUrl, setNextUrl] = useState('/api/v1/posts/');
  const [hasMore, setHasMore] = useState(true);

  useEffect(() => {
    if (nextUrl && hasMore) {
      fetch(nextUrl, { credentials: "same-origin" })
        .then((response) => {
          if (!response.ok) throw Error(response.statusText);
          return response.json();
        })
        .then((data) => {
          setPosts((oldPosts) => [...oldPosts, ...data.results]);
          setNextUrl(data.next);
          setLoading(false);
          if (!data.next) setHasMore(false);
        })
        .catch((error) => console.log(error));
    }
  }, [nextUrl]);

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <InfiniteScroll
      dataLength={posts.length}
      next={fetchPosts}
      hasMore={hasMore}
      loader={<h4>Loading...</h4>}
      endMessage={
        <p style={{ textAlign: "center" }}>
          <b>Yay! You have seen it all</b>
        </p>
      }
    >
      <div className="content">
        {posts.map((post) => (
          <Post key={post.postid} url={`/api/v1/posts/${post.postid}/`} />
        ))}
      </div>
    </InfiniteScroll>
  );
}

const root = createRoot(document.getElementById("reactEntry"));
root.render(
  <StrictMode>
    <Feed />
  </StrictMode>
);
