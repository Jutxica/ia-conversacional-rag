# Fase 3: LLM Integration Strategy

## 📋 Objetivo
Definir estratégia completa de integração com modelos LLM, incluindo seleção, routing, context management e quality assurance.

## 🎯 Deliverables

### D3.1 Model Selection Document
- [x] Comparação entre modelos (GPT-4, Claude, Gemini, open-source)
- [x] Critérios de seleção (latência, custo, qualidade, context window)
- [x] Decision matrix com scoring

### D3.2 LLM Router Specification
- [x] Algoritmo de routing (redundância, fallback, cost optimization)
- [x] Configuration file format
- [x] Fallback strategy

### D3.3 Context Window Management
- [x] Cálculo dinâmico de tokens disponíveis
- [x] Estratégia de truncagem (recent history vs. summarization)
- [x] Token counting implementation

### D3.4 API Integration Code Skeleton
- [x] LLM adapter pattern (interfaces abstratas)
- [x] Error handling & retry strategy
- [x] Rate limit management
- [x] Streaming implementation

## 🤖 Model Selection Analysis

### Primary Models

**Claude (Anthropic)**
- Context: 100K tokens
- Cost: $0.008/$0.024 per 1K tokens (input/output)
- Speed: ~150-400ms latency
- Quality: Excellent for summarization
- Pros: Strong summarization, ethical AI focus
- Cons: Limited availability, less versatile than GPT-4

**Gemini (Google)**
- Context: 256K tokens
- Cost: TBD
- Speed: ~100-300ms latency
- Quality: High for reasoning and multimodal tasks
- Pros: Cutting-edge, Google ecosystem integration
- Cons: Limited documentation, early-stage product

**Open-Source Models (LLaMA, Falcon)**
- Context: 4K-32K tokens (varies by model)
- Cost: Free (self-hosted)
- Speed: Depends on infrastructure
- Quality: Good for specific tasks, but less general
- Pros: No vendor lock-in, customizable
- Cons: Requires infrastructure, lower quality for general tasks

### Decision Matrix
| Model         | Context Tokens | Cost       | Latency   | Quality       | Pros                  | Cons                  |
|---------------|----------------|------------|-----------|---------------|-----------------------|-----------------------|
| GPT-4 Turbo   | 128K           | High       | Moderate  | Excellent     | Best quality          | Expensive            |
| Claude        | 100K           | Moderate   | Fast      | Excellent     | Ethical AI, Summaries | Limited availability |
| Gemini        | 256K           | TBD        | Very Fast | High          | Cutting-edge          | Early-stage          |
| Open-Source   | 4K-32K         | Free       | Variable  | Task-specific | Customizable          | Infrastructure-heavy |

**Escolha Final**: GPT-4 Turbo como modelo primário, com Claude como fallback para sumarização e Gemini como opção futura.

## 🔄 Router Strategy

```
Request comes in
    │
    ├─ Check tenant config (preferred model)
    │
    ├─ Try Primary Model
    │   ├─ Success → Stream response
    │   └─ Fail → Try Secondary
    │
    ├─ Try Secondary Model
    │   ├─ Success → Stream response
    │   └─ Fail → Try Tertiary
    │
    ├─ Try Tertiary Model
    │   ├─ Success → Stream response
    │   └─ Fail → Return error
    │
    └─ Log all fallbacks for monitoring
```

### Router Logic (Pseudocode)

```typescript
interface ModelConfig {
  modelId: string;
  apiKey: string;
  maxTokens: number;
  temperature: number;
  concurrency: number;
}

class LLMRouter {
  private models: Map<string, ModelConfig>;
  private failureLog: Map<string, number>; // track failures
  
  async route(
    prompt: string, 
    context: string, 
    tenantId: string
  ): Promise<AsyncIterable<string>> {
    const preferredModel = await getTenantPreference(tenantId);
    const models = [preferredModel, ...fallbackModels];
    
    for (const model of models) {
      try {
        return await this.callModel(model, prompt, context);
      } catch (error) {
        this.logFailure(model);
        continue; // try next
      }
    }
    
    throw new Error("All models failed");
  }
}
```

## 📊 Context Window Management

### Token Calculation

```
Available Tokens = Model Max - System Prompt - User Message - RAG Context

Example (GPT-4 Turbo):
- Model max: 128,000 tokens
- System prompt: ~500 tokens
- User message: variable
- RAG context: variable
- Response buffer: 2,000 tokens (reserve for output)
- Available for history: Remaining tokens
```

### Truncation Strategy

**Option A:** Keep recent N messages
- Pro: Simple, predictable
- Con: Loses older context
- Implementation: Slice last 10 messages

**Option B:** Summarize old messages
- Pro: Maintains continuity
- Con: Requires LLM call, latency
- Implementation: Summarize oldest 5 messages into 200 tokens

**Option C:** Hybrid (Recommended)
- Pro: Balances simplicity with context retention
- Con: More complex
- Implementation: Keep last 5 messages, summarize 6-20

## 🛡️ Error Handling

```
LLM API Call → Timeout (>30s)?
              → Rate limited (429)?
              → Server error (500)?
              → Invalid request (400)?

Action:
- Timeout: Retry with exponential backoff, max 3 attempts
- Rate limited: Queue job, try again in 60s
- Server error: Fallback to next model
- Invalid request: Return error immediately
```

## ✅ Quality Assurance

- [ ] Latency benchmarks established
- [ ] Cost tracking implemented
- [ ] Quality metrics defined (coherence, factuality, safety)
- [ ] Fallback strategy tested
- [ ] Token counting validated
- [ ] Streaming tested end-to-end

## 📝 Notas

---

**Status:** ⏳ Aguardando especificação
**Próximo:** Fase 4 — RAG System Design
