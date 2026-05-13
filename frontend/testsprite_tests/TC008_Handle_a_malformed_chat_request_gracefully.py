import requests

BASE_URL = "http://localhost:5173"

def parse_sse_events(response):
    """
    Generator to parse Server-Sent Events from the response text stream.
    Yields the data content from each event.
    """
    buffer = ""
    for line in response.iter_lines(decode_unicode=True):
        if line:
            if line.startswith("data: "):
                yield line[6:]
            elif line == "":
                # End of event
                pass

def test_malformed_chat_request_gracefully():
    url = f"{BASE_URL}/api/chat"
    headers = {
        "Accept": "text/event-stream",
        "Content-Type": "application/json",
    }
    # Incomplete/malformed payload: missing 'messages' array or required fields
    malformed_payload = {
        # Intentionally missing fields, e.g. empty or invalid structure
    }

    try:
        with requests.post(url, json=malformed_payload, headers=headers, stream=True, timeout=30) as response:
            assert response.status_code == 400 or response.status_code == 422, f"Expected 4xx error, got {response.status_code}"
            content_type = response.headers.get("Content-Type", "")
            assert "text/event-stream" in content_type, f"Expected text/event-stream content type, got {content_type}"

            # Parse SSE events from the streaming response
            error_messages = []
            for data in parse_sse_events(response):
                if data:
                    error_messages.append(data)

            assert error_messages, "Expected at least one error message in SSE stream"
            # Check if error message contains validation hints / clear validation error info
            joined_errors = "\n".join(error_messages).lower()
            validation_keywords = ["error", "validation", "missing", "invalid", "required"]
            assert any(keyword in joined_errors for keyword in validation_keywords), "No clear validation error found in SSE stream"

    except requests.exceptions.RequestException as e:
        raise AssertionError(f"Request to /api/chat failed: {e}")


if __name__ == "__main__":
    test_malformed_chat_request_gracefully()
