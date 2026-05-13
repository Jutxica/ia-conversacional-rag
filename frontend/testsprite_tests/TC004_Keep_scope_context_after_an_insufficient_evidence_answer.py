import requests
import time

def test_keep_scope_context_after_insufficient_evidence_answer():
    base_url = "http://localhost:5173"
    endpoint = f"{base_url}/api/chat"
    headers = {
        "Accept": "text/event-stream",
        "Content-Type": "application/json"
    }
    payload = {
        "conversation_id": None,
        "scope": "social",
        "query": "What is the influence of Padre Leão Dehon in social movements?",
        "history": []
    }
    timeout = 30

    try:
        with requests.post(endpoint, json=payload, headers=headers, stream=True, timeout=timeout) as response:
            assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
            content_type = response.headers.get("Content-Type", "")
            assert "text/event-stream" in content_type, f"Expected 'text/event-stream' in content type, got {content_type}"

            received_data = []
            uncertainty_detected = False

            for line in response.iter_lines(decode_unicode=True):
                if line.startswith("data: "):
                    data_str = line[len("data: "):].strip()
                    if data_str == "[DONE]":
                        break
                    received_data.append(data_str)

                    # Check for a phrase or token indicating honest uncertainty
                    if any(keyword in data_str.lower() for keyword in ["insufficient evidence", "uncertain", "unknown", "no conclusive answer", "limited evidence"]):
                        uncertainty_detected = True

            full_response = " ".join(received_data).lower()
            # Validate that the response indicates uncertainty
            assert uncertainty_detected or any(word in full_response for word in ["uncertain", "unknown", "no conclusive answer", "limited evidence", "insufficient evidence"]), \
                "The response did not indicate an honest uncertainty despite insufficient evidence."

    except requests.exceptions.RequestException as e:
        assert False, f"Request failed: {e}"

test_keep_scope_context_after_insufficient_evidence_answer()
