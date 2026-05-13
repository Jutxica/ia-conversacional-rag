# TestSprite AI Testing Report(MCP)

---

## 1️⃣ Document Metadata
- **Project Name:** frontend
- **Date:** 2026-05-11
- **Prepared by:** TestSprite AI Team / Antigravity

---

## 2️⃣ Requirement Validation Summary

#### Requirement 1: Basic Chat and Connectivity

**Test TC001 Ask a social scope question and review cited sources**
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/26f0b386-a63a-4311-a805-ba964e484c6c/3996d0c9-8b4c-43b0-ad21-963ec4f83ffb
- **Status:** ✅ Passed
- **Analysis / Findings:** The chat endpoint successfully processes the request and returns a valid SSE response containing cited sources.

**Test TC006 Verify backend connectivity through the health check**
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/26f0b386-a63a-4311-a805-ba964e484c6c/29bcb644-5c2f-4f51-9dc8-09881971d1eb
- **Status:** ✅ Passed
- **Analysis / Findings:** Backend connectivity is established.

**Test TC008 Handle a malformed chat request gracefully**
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/26f0b386-a63a-4311-a805-ba964e484c6c/d084e3ff-2d9a-48a7-ac7d-ce6c348056cd
- **Status:** ✅ Passed
- **Analysis / Findings:** The system correctly handles malformed requests and returns expected HTTP error codes instead of crashing.

---

#### Requirement 2: Search and Context Handling

**Test TC002 Ask about André Prévot in biographical scope and inspect recipient sources**
- **Test Error:** AssertionError
- **Status:** ❌ Failed
- **Analysis / Findings:** The response for the biographical scope test didn't meet the assertion expectations. It might be due to the specific data missing from the database or the backend not returning the expected structured metadata.

**Test TC003 Search an exact theological term and compare the retrieved sources**
- **Test Error:** AssertionError: Response does not contain the searched exact term 'oblação'.
- **Status:** ❌ Failed
- **Analysis / Findings:** The term 'oblação' wasn't returned in the SSE chunks. The backend likely does not return the exact term or the retrieval system isn't matching the specific theological term from the knowledge base.

**Test TC004 Keep scope context after an insufficient-evidence answer**
- **Test Error:** AssertionError: The response did not indicate an honest uncertainty despite insufficient evidence.
- **Status:** ❌ Failed
- **Analysis / Findings:** The LLM prompt or backend logic may not be enforcing a strict "I don't know" or "insufficient evidence" response when the context lacks information.

**Test TC005 Switch scope and ask a new question without losing context**
- **Test Error:** AssertionError: conversation_id missing from all events
- **Status:** ❌ Failed
- **Analysis / Findings:** The `/api/chat` response stream does not include `conversation_id` in its payload, making it impossible for the frontend to maintain context across requests by using the conversation ID.

**Test TC007 Review source metadata after receiving a cited answer**
- **Test Error:** AssertionError: Did not find source authority metadata in streamed response.
- **Status:** ❌ Failed
- **Analysis / Findings:** The backend does not appear to emit authority metadata chunks in the SSE stream, or the structure differs from what the test expects.

---

## 3️⃣ Coverage & Matching Metrics

- **37.50%** of tests passed (3/8)

| Requirement | Total Tests | ✅ Passed | ❌ Failed |
| --- | --- | --- | --- |
| Basic Chat and Connectivity | 3 | 3 | 0 |
| Search and Context Handling | 5 | 0 | 5 |

---

## 4️⃣ Key Gaps / Risks

1. **Context Management (Conversation ID):** The backend does not stream the `conversation_id` in the response, making it difficult for clients to correlate messages and maintain context in a multi-turn conversation.
2. **Missing Metadata/Citations:** Expected source authority and recipient metadata might be missing in the chunks, indicating the backend might not be extracting or sending the correct fields.
3. **Hallucination / Fallback Handling:** The system fails to express honest uncertainty when evidence is insufficient, presenting a hallucination risk.
4. **Search Term Accuracy:** The system fails to return expected exact theological terms like 'oblação', suggesting potential issues with RAG retrieval or the LLM's adherence to the retrieved context.
