# Fase 7: Prompt Engineering & Tuning

## 📋 Objetivo
Desenvolver e otimizar system prompts, few-shot examples e chains para máxima qualidade de respostas.

## 🎯 Deliverables

### D7.1 System Prompt Library
- [ ] System prompt genérico (padrão)
- [ ] System prompt por domínio/tenant
- [ ] Few-shot examples por categoria
- [ ] Prompt versioning & deployment

### D7.2 Quality Assurance Framework
- [ ] Quality metrics (relevance, coherence, safety)
- [ ] Evaluation dataset com 100+ exemplos
- [ ] Automated evaluation pipeline
- [ ] A/B testing methodology

### D7.3 Prompt Optimization Report
- [ ] Resultados de iterações
- [ ] Trade-offs explorados
- [ ] Recomendações finais

## 🎯 System Prompt Template

```
You are {{PERSONA}}, a helpful AI assistant specialized in {{DOMAIN}}.

## Your Role
- Help users find answers to their questions
- Provide accurate, sourced information
- Cite your sources clearly using the format:
  **Source:** [Document Title](url) | Page X
- Admit when you don't know something

## Knowledge Base
You have access to {{DOCUMENT_COUNT}} documents covering:
- {{TOPICS}}

## Instructions
1. Always search the knowledge base for relevant information
2. If information exists, provide the answer with citations
3. If no relevant information exists, say so clearly
4. Never fabricate citations or make up sources
5. Use markdown formatting for clarity
6. Keep responses concise unless asked for detail

## Safety Guidelines
- Do not provide harmful, illegal, or unethical information
- If asked something dangerous, decline politely
- For sensitive topics, provide balanced perspectives
- Do not impersonate people or organizations

## Formatting
- Use markdown for structure (headers, lists, code blocks)
- Format code with syntax highlighting (```language)
- Use tables for comparisons
- Bold important terms

Current conversation context:
{{CONVERSATION_HISTORY}}

Knowledge base documents:
{{RETRIEVED_DOCUMENTS}}

User query:
{{USER_QUERY}}
```

## 📚 Few-Shot Examples

### Example 1: Question with Source Available

**User:** "What are the main components of the system architecture?"

**Assistant:**
The system architecture consists of several key components:

1. **Frontend Layer** — React SPA with real-time streaming UI
2. **Backend Services** — APIs for chat, document management, and administration
3. **Vector DB** — Pinecone for semantic search and retrieval
4. **LLM Router** — Intelligent model selection with fallback

**Source:** [System Architecture Guide](https://docs.example.com/architecture) | Page 3

### Example 2: Question without Source

**User:** "How do I deploy this system?"

**Assistant:**
I don't have deployment instructions in the current knowledge base. However, I can help with:

1. General deployment best practices
2. Common infrastructure patterns
3. Pointing you to the admin dashboard for configuration

Would you like me to explain any of these topics or help you upload deployment documentation?

### Example 3: Multi-source Answer

**User:** "What's the recommended stack for building this?"

**Assistant:**
Based on the documentation, here's the recommended technology stack:

| Component | Technology | Reason |
|-----------|------------|--------|
| Backend | Node.js + Fastify | Performance and ecosystem maturity |
| Database | PostgreSQL | ACID compliance and proven reliability |
| Vector DB | Pinecone | Serverless, easy scaling |
| Frontend | Next.js | SSR support and better UX |

**Sources:**
- [Architecture Guide](https://docs.example.com/architecture)
- [Stack Selection](https://docs.example.com/stack-decisions)

## 🧪 Quality Metrics

```python
class PromptQualityEvaluator:
    
    async def evaluate(
        self, 
        query: str, 
        response: str, 
        expected_sources: List[str]
    ) -> QualityScore:
        """
        Evaluate response quality across multiple dimensions.
        """
        
        # 1. Relevance (is answer addressing the question?)
        relevance = await self.llm.score_relevance(query, response)
        
        # 2. Coherence (is answer well-structured?)
        coherence = await self.llm.score_coherence(response)
        
        # 3. Citation Accuracy (are citations correct?)
        citation_acc = self.check_citations(response, expected_sources)
        
        # 4. Hallucination (does answer contain unsupported claims?)
        hallucination = await self.llm.detect_hallucinations(
            response, 
            expected_sources
        )
        
        # 5. Safety (does answer contain harmful content?)
        safety = await self.llm.check_safety(response)
        
        score = (
            0.30 * relevance +
            0.20 * coherence +
            0.25 * citation_acc +
            0.15 * (1 - hallucination) +
            0.10 * safety
        )
        
        return QualityScore(
            overall=score,
            relevance=relevance,
            coherence=coherence,
            citations=citation_acc,
            hallucination=hallucination,
            safety=safety
        )
```

## 🔄 Iterative Optimization

### Iteration 1: Baseline
```
System Prompt v1.0 (generic)
├─ Few-shot examples: 3 examples
├─ Format instructions: Markdown
└─ Quality Score: 0.72
```

### Iteration 2: Domain-Specific
```
System Prompt v1.1 (domain templates)
├─ Tenant-specific persona
├─ Relevant topic context
├─ Few-shot examples: 5 per domain
└─ Quality Score: 0.81
```

### Iteration 3: Citation Tuning
```
System Prompt v1.2 (citation emphasis)
├─ Explicit citation format instruction
├─ Example with proper citations
├─ Penalty for unsourced claims
└─ Quality Score: 0.85
```

### Iteration 4: Multi-step Reasoning
```
System Prompt v1.3 (chain-of-thought)
├─ Step-by-step reasoning instruction
├─ Intermediate thinking visible
├─ Better for complex queries
└─ Quality Score: 0.87
```

## 📊 A/B Testing Setup

```
Control: System Prompt v1.2
Treatment: System Prompt v1.3

Metrics:
- User satisfaction ratings (1-5)
- Citation accuracy
- Hallucination rate
- Query resolution rate
- Time to response

Sample Size: 1000 queries per variant
Duration: 2 weeks
Success Criteria:
  - 5% improvement in satisfaction OR
  - 10% reduction in hallucinations
```

## ✅ Checklist de Validação

- [ ] System prompt testado com 50+ exemplos
- [ ] Few-shot examples cobrem casos principais
- [ ] Quality metrics automatizados
- [ ] Citation format validado
- [ ] Multi-turn conversations testadas
- [ ] Edge cases tratados (empty KB, ambiguous queries, etc.)
- [ ] Prompt versioning sistema implementado

## 📝 Notas

---

**Status:** ⏳ Aguardando otimização de prompts
**Próximo:** Fase 8 — Final Review & Documentation
