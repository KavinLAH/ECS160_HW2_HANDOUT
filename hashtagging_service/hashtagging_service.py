import grpc
from concurrent import futures
import os
import re

from google import genai

# Each microservice should be developed as an individual Python project (separate directory)
# Using try/except so imports work both when running directly inside hashtagging_service/
# and when running pytest from the project root.
try:
    import hashtagging_pb2
    import hashtagging_pb2_grpc
except ImportError:
    from hashtagging_service import hashtagging_pb2
    from hashtagging_service import hashtagging_pb2_grpc

MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")


# Unit tests for the hashtagging microservice should not assume that the Gemini API is available.
# Wrapping client initialization in a helper so importing this file doesn't crash if GOOGLE_API_KEY isn't set yet,
# which allows pytest to easily mock it.
def get_client():
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    return genai.Client(api_key=api_key)


def generate_hashtag(post_content: str) -> str:
    # If the LLM refuses to generate a hashtag for some reason,
    # tag it with a default tag such as #bskypost.
    try:
        client = get_client()
        prompt = (
            "Generate exactly ONE relevant hashtag for this social media post. "
            "Return ONLY the hashtag starting with '#' and nothing else (no explanation, no punctuation, no other words).\n\n"
            f"Post: {post_content}"
        )
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
        )
        text = response.text.strip() if response and response.text else ""

        # Extract first hashtag pattern
        match = re.search(r"#[A-Za-z0-9_]+", text)
        if match:
            return match.group(0)

        # If single word was returned without '#', prepend '#'
        words = text.split()
        if words:
            clean_word = re.sub(r"[^\w]", "", words[0])
            if clean_word:
                return f"#{clean_word}"

        return "#bskypost"
    except Exception:
        return "#bskypost"


class HashtagServiceServicer(hashtagging_pb2_grpc.HashtagServiceServicer):
    def GetHashtag(self, request, context):
        tag = generate_hashtag(request.post_content)
        return hashtagging_pb2.HashtagResponse(hashtag=tag)


def serve(port: int = 50051):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    hashtagging_pb2_grpc.add_HashtagServiceServicer_to_server(HashtagServiceServicer(), server)
    server.add_insecure_port(f"0.0.0.0:{port}")
    server.start()
    print(f"Hashtagging service running on port {port}...")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
