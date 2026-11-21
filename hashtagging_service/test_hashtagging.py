from unittest.mock import patch, MagicMock
import sys
import os

# Ensure import paths work
sys.path.insert(0, os.path.dirname(__file__))

import hashtagging_pb2
from hashtagging_service import generate_hashtag, HashtagServiceServicer


@patch("hashtagging_service.get_client")
def test_generate_hashtag_success(mock_get_client):
    # Test that hashtag generation works and extracts the tag when Gemini returns normally
    mock_response = MagicMock()
    mock_response.text = "#nature"
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response
    mock_get_client.return_value = mock_client

    tag = generate_hashtag("A beautiful hike in the mountains")
    assert tag == "#nature"


@patch("hashtagging_service.get_client")
def test_generate_hashtag_fallback_on_error(mock_get_client):
    # If Gemini throws an error or rate limits, it should fall back to #bskypost
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("API rate limited")
    mock_get_client.return_value = mock_client

    tag = generate_hashtag("Some post content")
    assert tag == "#bskypost"


@patch("hashtagging_service.generate_hashtag")
def test_servicer_get_hashtag(mock_gen_hashtag):
    # Test that the gRPC servicer GetHashtag method calls generate_hashtag
    mock_gen_hashtag.return_value = "#coding"
    servicer = HashtagServiceServicer()
    request = hashtagging_pb2.HashtagRequest(post_content="Finished building my app")
    context = MagicMock()

    response = servicer.GetHashtag(request, context)
    assert response.hashtag == "#coding"
    mock_gen_hashtag.assert_called_once_with("Finished building my app")

