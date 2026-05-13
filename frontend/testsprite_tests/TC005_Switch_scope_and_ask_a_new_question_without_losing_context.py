import requests
import json

BASE_URL = "http://localhost:5173"
CHAT_ENDPOINT = f"{BASE_URL}/api/chat"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "text/event-stream"
}
TIMEOUT = 30

def parse_sse_events(response):
    """
    Generator to parse SSE events from a streaming response.
    Yields each event's data as a dict parsed from JSON string.
    """
    buffer = ""
    for line in response.iter_lines(decode_unicode=True):
        if line.startswith("data: "):
            data_str = line[len("data: "):].strip()
            if data_str == "[DONE]":
                break
            try:
                event_data = json.loads(data_str)
                yield event_data
            except json.JSONDecodeError:
                continue

def test_switch_scope_and_ask_new_question_without_losing_context():
    conversation_id = None
    try:
        # Step 1: Start conversation - ask initial question in scope "social"
        payload_1 = {
            "question": "What is the significance of Padre Leão Dehon's social work?",
            "scope": "social",
            "conversation_id": None
        }
        with requests.post(CHAT_ENDPOINT, headers=HEADERS, json=payload_1, timeout=TIMEOUT, stream=True) as resp1:
            assert resp1.status_code == 200, f"Expected status 200, got {resp1.status_code}"
            events = list(parse_sse_events(resp1))
            assert len(events) > 0, "No SSE chat events received for first question."
            # Extract conversation_id from first event that contains it
            conversation_id = None
            for e in events:
                conversation_id = e.get("conversation_id")
                if conversation_id is not None:
                    break
            assert conversation_id is not None, "conversation_id missing from all events"
            # Check at least one answer chunk text exists
            answer_texts = [e.get("text", "") for e in events if "text" in e]
            assert any(len(t.strip()) > 0 for t in answer_texts), "No answer text received for first question."
            # Verify scope echoes
            scopes = {e.get("scope") for e in events if "scope" in e}
            assert "social" in scopes, f"Scope 'social' not found in events scopes: {scopes}"

        # Step 2: Switch scope to "biographical" and ask a new question in same conversation
        payload_2 = {
            "question": "Tell me about André Prévot's early life.",
            "scope": "biographical",
            "conversation_id": conversation_id
        }
        with requests.post(CHAT_ENDPOINT, headers=HEADERS, json=payload_2, timeout=TIMEOUT, stream=True) as resp2:
            assert resp2.status_code == 200, f"Expected status 200, got {resp2.status_code}"
            events2 = list(parse_sse_events(resp2))
            assert len(events2) > 0, "No SSE chat events received for second question."
            # Check conversation_id preserved and matches
            for e in events2:
                assert e.get("conversation_id") == conversation_id, "Conversation ID changed during scope switch"
            # Check answer text present
            answer_texts2 = [e.get("text", "") for e in events2 if "text" in e]
            assert any(len(t.strip()) > 0 for t in answer_texts2), "No answer text received for second question."
            # Verify new scope
            scopes2 = {e.get("scope") for e in events2 if "scope" in e}
            assert "biographical" in scopes2, f"Scope 'biographical' not found in events scopes: {scopes2}"
            
            # Verify that context likely preserved by checking that events have "conversation_id" matching first

    except requests.RequestException as ex:
        assert False, f"Request failed: {ex}"

test_switch_scope_and_ask_new_question_without_losing_context()
