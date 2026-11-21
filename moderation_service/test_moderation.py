from unittest.mock import patch
from fastapi.testclient import TestClient
import sys
import os

# Make sure import paths work
sys.path.insert(0, os.path.dirname(__file__))

from moderation_service import app, check_moderation, BANNED_WORDS

client = TestClient(app)


def test_banned_words_detected():
    # Make sure every single banned word from the list fails moderation
    for word in BANNED_WORDS:
        content = f"Hey everyone, this is totally {word}!"
        assert check_moderation(content) is False


def test_case_insensitive_detection():
    # Make sure words like HACK or SCAM are caught regardless of casing
    assert check_moderation("HACK the planet") is False
    assert check_moderation("Beware of this SCAM now") is False


def test_clean_post_passes():
    # Normal post without banned words should pass
    assert check_moderation("Just enjoyed a nice walk in the park!") is True


@patch("moderation_service.get_hashtag_from_service")
def test_moderate_endpoint_clean_post_calls_hashtagging(mock_get_hashtag):
    # If the post is clean, /moderate should call the hashtag service and return its tag
    mock_get_hashtag.return_value = "#sunset"
    response = client.post("/moderate", json={"post_content": "Beautiful sunset today"})
    assert response.status_code == 200
    assert response.json()["result"] == "#sunset"
    mock_get_hashtag.assert_called_once_with("Beautiful sunset today")


@patch("moderation_service.get_hashtag_from_service")
def test_moderate_endpoint_banned_post_blocks_grpc(mock_get_hashtag):
    # If the post has banned words, return FAILED right away and don't call gRPC
    response = client.post("/moderate", json={"post_content": "This is a crypto scam"})
    assert response.status_code == 200
    assert response.json()["result"] == "FAILED"
    mock_get_hashtag.assert_not_called()

