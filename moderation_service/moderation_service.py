import re
from fastapi import FastAPI
from pydantic import BaseModel
import grpc

# Each microservice should be developed as an individual Python project (separate directory)
# Using try/except so imports work both when running directly inside moderation_service/
# and when running pytest from the project root.
try:
    import hashtagging_pb2
    import hashtagging_pb2_grpc
except ImportError:
    from moderation_service import hashtagging_pb2
    from moderation_service import hashtagging_pb2_grpc

app = FastAPI()

BANNED_WORDS = ["illegal", "fraud", "scam", "exploit", "dox", "swatting",
    "hack", "crypto", "bots",
]

class ModerateRequest(BaseModel):
    post_content: str


class ModerateResponse(BaseModel):
    result: str


def check_moderation(text: str) -> bool:
    
    # Return true if text passes moderation 
    # But false if text contains any banned words.

    for word in BANNED_WORDS:
        # Match banned word with word boundaries to avoid false positives 
        # (for example "dox" in "paradox")
        # Use the \b for that
        # For case sensitivity, use re.IGNORECASE
        if re.search(rf"\b{re.escape(word)}\b", text, re.IGNORECASE):
            return False
    return True


def get_hashtag_from_service(post_content: str, host: str = "localhost:50051") -> str:
    # Call the Hashtagging gRPC service and returns the generated hashtag.
    try:
        with grpc.insecure_channel(host) as channel:
            stub = hashtagging_pb2_grpc.HashtagServiceStub(channel)
            request = hashtagging_pb2.HashtagRequest(post_content=post_content)
            response = stub.GetHashtag(request)
            return response.hashtag
    except Exception as e:
        # If the LLM refuses to generate a hashtag for some reason, you can tag it with a default tag such as
        # #bskypost
        return "#bskypost"


@app.post("/moderate", response_model=ModerateResponse)
def moderate(request: ModerateRequest):
    # In case any post fails the moderation, display it as "FAILED"
    if not check_moderation(request.post_content):
        return ModerateResponse(result="FAILED")

    # Otherwise append the hashtag to post content
    hashtag = get_hashtag_from_service(request.post_content)
    return ModerateResponse(result=hashtag)
