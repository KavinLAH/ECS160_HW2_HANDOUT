import csv
import sys
import requests

MODERATION_URL = "http://localhost:8001/moderate"


def load_posts(input_path: str):
    # Load social media posts from input CSV file
    posts = []
    with open(input_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            posts.append(row)
    return posts


def get_top_posts(posts, limit: int = 10):
    # Sort posts by like_count descending and take the top limit
    def get_likes(post):
        return int(post.get("like_count", 0))

    sorted_posts = sorted(posts, key=get_likes, reverse=True)
    return sorted_posts[:limit]


def send_to_pipeline(post_content: str) -> str:
    # Send a post to the moderation service.
    # Returns the hashtag string on success, or 'FAILED' if moderation fails.
    try:
        response = requests.post(
            MODERATION_URL,
            json={"post_content": post_content},
            timeout=30,
        )
        if response.status_code == 200:
            return response.json()["result"]
    except Exception as e:
        print(f"Error calling moderation service: {e}")
    return "FAILED"


def process_post(post: dict, index: int):
    # Process a single post through the pipeline and prints formatted output
    author = post.get("author_handle", "unknown")
    text = post.get("text", "")
    likes = post.get("like_count", "0")
    replies = post.get("reply_count", "0")

    result = send_to_pipeline(text)

    print(f"--- Post {index} (Author: @{author}, Likes: {likes}) ---")
    if result == "FAILED":
        print("[DELETED]")
    else:
        print(f"{text} {result}")

    # Reply info indicator
    print(f"--> {replies} replies\n")


def main():
    input_path = sys.argv[1] if len(sys.argv) > 1 else "input.csv"

    posts = load_posts(input_path)
    top_posts = get_top_posts(posts, limit=10)

    print(f"Processing {len(top_posts)} most-liked posts...\n")

    for i, post in enumerate(top_posts, start=1):
        process_post(post, i)


if __name__ == "__main__":
    main()
