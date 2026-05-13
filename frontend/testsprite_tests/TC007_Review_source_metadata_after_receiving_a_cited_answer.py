import requests
import json

BASE_URL = "http://localhost:5173"
CHAT_ENDPOINT = "/api/chat"
TIMEOUT = 30

def parse_sse(response):
    """
    Parses Server-Sent Events from the response content.
    Yields each data payload as a dict.
    """
    buffer = ""
    for chunk in response.iter_lines(decode_unicode=True):
        if chunk.startswith("data: "):
            data_str = chunk[6:].strip()
            if data_str == "[DONE]":
                break
            try:
                data_json = json.loads(data_str)
                yield data_json
            except json.JSONDecodeError:
                continue

def test_review_source_metadata_after_cited_answer():
    """
    Test that after receiving a cited answer from /api/chat,
    the source metadata such as authority and language can be found and inspected.
    """
    headers = {
        "Accept": "text/event-stream",
        "Content-Type": "application/json"
    }
    payload = {
        "messages": [
            {
                "role": "user",
                "content": "What sources support the translation choices in Padre Leão Dehon's documents?"
            }
        ],
        "scope": "research",
        "stream": True
    }

    url = BASE_URL + CHAT_ENDPOINT
    try:
        with requests.post(url, headers=headers, json=payload, stream=True, timeout=TIMEOUT) as response:
            assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
            content_type = response.headers.get("content-type", "")
            assert "text/event-stream" in content_type, f"Expected 'text/event-stream' content-type but got {content_type}"
            
            found_authority = False
            found_language = False
            found_citation = False
            for event in parse_sse(response):
                # We expect a chunk with answer and possibly a sources array or metadata info
                # Inspecting for source metadata keys like authority and language
                if 'choices' in event:
                    choices = event.get('choices', [])
                    for choice in choices:
                        delta = choice.get('delta', {})
                        if not delta:
                            continue
                        # The chunk typically contains text increments; we skip but collect metadata if present
                        if 'sources' in delta:
                            sources = delta['sources']
                            for source in sources:
                                authority = source.get('authority')
                                language = source.get('language')
                                if authority:
                                    found_authority = True
                                if language:
                                    found_language = True
                                if source.get('citation') or source.get('title') or source.get('sigla'):
                                    found_citation = True

                # In case the event itself has a 'source' or 'metadata' key at root level
                if "source" in event:
                    source = event["source"]
                    authority = source.get('authority')
                    language = source.get('language')
                    if authority:
                        found_authority = True
                    if language:
                        found_language = True
                    found_citation = found_citation or ('citation' in source or 'title' in source)

                # Also some implementations may embed metadata in a separate 'metadata' section
                if "metadata" in event:
                    metadata = event["metadata"]
                    if isinstance(metadata, dict):
                        if "authority" in metadata:
                            found_authority = True
                        if "language" in metadata:
                            found_language = True

            # Assert at least one source metadata was found including authority and language
            assert found_authority, "Did not find source authority metadata in streamed response."
            assert found_language, "Did not find source language metadata in streamed response."
            assert found_citation, "Did not find citation metadata in streamed response."

    except requests.Timeout:
        assert False, "Request timed out"
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"

test_review_source_metadata_after_cited_answer()