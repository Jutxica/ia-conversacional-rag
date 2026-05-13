import requests

def test_ask_about_andre_prevot_biographical_scope():
    base_url = "http://localhost:5173"
    endpoint = "/api/chat"
    url = base_url + endpoint

    headers = {
        "Accept": "text/event-stream",
        "Content-Type": "application/json"
    }

    payload = {
        "question": "Tell me about André Prévot",
        "scope": "biographical"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, stream=True, timeout=30)
        response.raise_for_status()
        assert response.headers.get("Content-Type", "").startswith("text/event-stream")

        # Parse SSE stream lines that start with "data: "
        answer_chunks = []
        source_mentions = []
        for line in response.iter_lines(decode_unicode=True):
            if line is None or line.strip() == "":
                continue
            if line.startswith("data: "):
                data_str = line[len("data: "):].strip()
                if data_str == "[DONE]":
                    break
                answer_chunks.append(data_str)

        full_answer = "".join(answer_chunks)

        # Basic assertions on the full answer text
        assert isinstance(full_answer, str)
        assert len(full_answer) > 0
        # We expect answer to mention André Prévot
        assert "André" in full_answer or "Prévot" in full_answer

        # We expect cited sources info, typically source references or recipient mentions might be in included texts
        # Let's check for common keywords that indicate citations or recipient sources
        citation_keywords = ["source", "cited", "recipient", "document", "sigla", "references", "panel"]
        found_citation_info = any(keyword.lower() in full_answer.lower() for keyword in citation_keywords)
        assert found_citation_info

    except requests.RequestException as e:
        assert False, f"Request failed: {e}"
    except AssertionError as e:
        raise e

test_ask_about_andre_prevot_biographical_scope()