import requests

BASE_URL = "http://localhost:5173"
API_CHAT_ENDPOINT = f"{BASE_URL}/api/chat"
TIMEOUT = 30

def test_search_exact_theological_term_oblação():
    headers = {
        "Accept": "text/event-stream",
        "Content-Type": "application/json",
    }
    payload = {
        "question": "oblação",
        "scope": "theological",
        "exact_match": True
    }

    # Send POST request to /api/chat with SSE response expected
    try:
        response = requests.post(API_CHAT_ENDPOINT, json=payload, headers=headers, stream=True, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as e:
        assert False, f"Request exception occurred: {e}"

    # Parse SSE stream: consider lines starting with "data: "
    collected_data = []
    try:
        for line_bytes in response.iter_lines():
            if line_bytes:
                line = line_bytes.decode('utf-8').strip()
                if line.startswith("data: "):
                    data_part = line[len("data: "):]
                    if data_part == "[DONE]":
                        break
                    collected_data.append(data_part)

        assert collected_data, "No data events received from SSE stream."

        # Join all chunks and examine result
        full_response_text = "".join(collected_data)

        # Basic validation: the response text should contain the term "oblação" lexically
        # and indication of anchored citations and multilingual source info.
        assert "oblação" in full_response_text.lower(), "Response does not contain the searched exact term 'oblação'."
        assert any(tag in full_response_text.lower() for tag in ["citation", "source", "anchored"]), \
            "Response does not contain anchored citations or source information."
        assert any(lang_tag in full_response_text.lower() for lang_tag in ["portuguese", "english", "multilingual", "tradução", "commentary"]), \
            "Response does not show multilingual source support or commentary."

    finally:
        response.close()

test_search_exact_theological_term_oblação()