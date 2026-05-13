import requests
import time

def test_ask_social_scope_question_and_review_cited_sources():
    base_url = "http://localhost:5173"
    url = f"{base_url}/api/chat"
    headers = {
        "Accept": "text/event-stream",
        "Content-Type": "application/json"
    }
    payload = {
        "scope": "social",
        "question": "What is the impact of Padre Leão Dehon's social work in the community?"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30, stream=True)
        response.raise_for_status()
        assert response.headers.get("content-type", "").startswith("text/event-stream"), "Response is not SSE"

        full_answer = ""
        cited_sources_found = False

        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith("data: "):
                data_line = line[len("data: "):].strip()
                if data_line == "[DONE]":
                    break
                full_answer += data_line

                # Check presence of citation markers (heuristic: presence of [source] or similar pattern)
                if "source" in data_line.lower() or "doc" in data_line.lower() or "citation" in data_line.lower():
                    cited_sources_found = True

        # Validate received answer content is not empty
        assert len(full_answer) > 0, "No answer data received in SSE stream"

        # Validate cited sources indicators were found in the streamed data
        assert cited_sources_found, "No cited sources found in the streamed answer"

    except requests.exceptions.RequestException as e:
        assert False, f"Request failed: {e}"

test_ask_social_scope_question_and_review_cited_sources()