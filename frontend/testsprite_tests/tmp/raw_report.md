
# TestSprite AI Testing Report(MCP)

---

## 1️⃣ Document Metadata
- **Project Name:** frontend
- **Date:** 2026-05-11
- **Prepared by:** TestSprite AI Team

---

## 2️⃣ Requirement Validation Summary

#### Test TC001 Ask a social scope question and review cited sources
- **Test Code:** [TC001_Ask_a_social_scope_question_and_review_cited_sources.py](./TC001_Ask_a_social_scope_question_and_review_cited_sources.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/26f0b386-a63a-4311-a805-ba964e484c6c/3996d0c9-8b4c-43b0-ad21-963ec4f83ffb
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC002 Ask about André Prévot in biographical scope and inspect recipient sources
- **Test Code:** [TC002_Ask_about_Andr_Prvot_in_biographical_scope_and_inspect_recipient_sources.py](./TC002_Ask_about_Andr_Prvot_in_biographical_scope_and_inspect_recipient_sources.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 54, in <module>
  File "<string>", line 52, in test_ask_about_andre_prevot_biographical_scope
  File "<string>", line 41, in test_ask_about_andre_prevot_biographical_scope
AssertionError

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/26f0b386-a63a-4311-a805-ba964e484c6c/d8baacbf-bb1d-479a-90af-7fd2015703fc
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC003 Search an exact theological term and compare the retrieved sources
- **Test Code:** [TC003_Search_an_exact_theological_term_and_compare_the_retrieved_sources.py](./TC003_Search_an_exact_theological_term_and_compare_the_retrieved_sources.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 53, in <module>
  File "<string>", line 44, in test_search_exact_theological_term_oblação
AssertionError: Response does not contain the searched exact term 'oblação'.

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/26f0b386-a63a-4311-a805-ba964e484c6c/63145a30-967a-4d4d-9951-c7a59622f45b
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC004 Keep scope context after an insufficient-evidence answer
- **Test Code:** [TC004_Keep_scope_context_after_an_insufficient_evidence_answer.py](./TC004_Keep_scope_context_after_an_insufficient_evidence_answer.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 47, in <module>
  File "<string>", line 41, in test_keep_scope_context_after_insufficient_evidence_answer
AssertionError: The response did not indicate an honest uncertainty despite insufficient evidence.

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/26f0b386-a63a-4311-a805-ba964e484c6c/df1a9c17-286d-4d15-818e-340d2189a14d
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC005 Switch scope and ask a new question without losing context
- **Test Code:** [TC005_Switch_scope_and_ask_a_new_question_without_losing_context.py](./TC005_Switch_scope_and_ask_a_new_question_without_losing_context.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 81, in <module>
  File "<string>", line 48, in test_switch_scope_and_ask_new_question_without_losing_context
AssertionError: conversation_id missing from all events

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/26f0b386-a63a-4311-a805-ba964e484c6c/f6ac17cc-358a-4a24-940e-0d290983070a
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC006 Verify backend connectivity through the health check
- **Test Code:** [TC006_Verify_backend_connectivity_through_the_health_check.py](./TC006_Verify_backend_connectivity_through_the_health_check.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/26f0b386-a63a-4311-a805-ba964e484c6c/29bcb644-5c2f-4f51-9dc8-09881971d1eb
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC007 Review source metadata after receiving a cited answer
- **Test Code:** [TC007_Review_source_metadata_after_receiving_a_cited_answer.py](./TC007_Review_source_metadata_after_receiving_a_cited_answer.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 107, in <module>
  File "<string>", line 98, in test_review_source_metadata_after_cited_answer
AssertionError: Did not find source authority metadata in streamed response.

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/26f0b386-a63a-4311-a805-ba964e484c6c/d28ca117-30d4-4f83-9faf-81d2bfbef2c4
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC008 Handle a malformed chat request gracefully
- **Test Code:** [TC008_Handle_a_malformed_chat_request_gracefully.py](./TC008_Handle_a_malformed_chat_request_gracefully.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/26f0b386-a63a-4311-a805-ba964e484c6c/d084e3ff-2d9a-48a7-ac7d-ce6c348056cd
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---


## 3️⃣ Coverage & Matching Metrics

- **37.50** of tests passed

| Requirement        | Total Tests | ✅ Passed | ❌ Failed  |
|--------------------|-------------|-----------|------------|
| ...                | ...         | ...       | ...        |
---


## 4️⃣ Key Gaps / Risks
{AI_GNERATED_KET_GAPS_AND_RISKS}
---